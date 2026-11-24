"""Turn the SharePoint export of "Litprofit tiekimo užklausos" into SQL that
brings public.enquiries up to date.

    python3 tools/import-enquiries.py "Litprofit tiekimo užklausos.csv" > /somewhere/outside/the/repo.sql

The output carries client names, suppliers and prices, so it is written to
stdout and never into this repository -- the repo is public. Paste it into the
Supabase SQL editor in one go; it is one transaction.

What it does, row by row, matching on the enquiry number (trimmed). A number
that appears more than once -- the list uses that for two lines under one
enquiry -- is matched in order of appearance:

  matched    every column the list owns is overwritten from the export;
             what only the calculator holds is kept: cost_ex_vat, invoice_no,
             note, paid_date
  new        inserted
  not in the export   left alone and listed by the final SELECT, so nobody's
             row disappears because the export did not carry it

The history trigger is off for the transaction (Supabase's postgres role
cannot set session_replication_role): an import is not 2,000 field edits, and
enquiry_history would otherwise record it as if somebody had typed every one. Run after migrate-enquiries-5.sql."""
import csv, sys, datetime as dt

ORIGIN = "https://litprofit370.sharepoint.com"

# Rows the SharePoint list still carries that repeat an SK order exactly --
# same status, amount and folder -- removed from the calculator on 24 Nov 2026
# so the order is not counted twice. Skipped here, or every import would bring
# them back until they are fixed in SharePoint itself.
EXCLUDE = {"26.3-04.3", "26.4-22.1", "26.5-21"}

def money(s):
    s = (s or "").replace("€", "").replace(",", "").strip()
    return s if s else None

def date(s):
    try: return dt.datetime.strptime((s or "").strip(), "%m/%d/%Y").date().isoformat()
    except ValueError: return None

def lit(v):
    if v is None: return "null"
    if isinstance(v, bool): return "true" if v else "false"
    return "'" + str(v).replace("'", "''") + "'"

def txt(s):
    s = " ".join((s or "").split())
    return s or None

def main(path):
    rows = list(csv.DictReader(open(path, encoding="utf-8-sig")))
    vals = []
    rows = [r for r in rows if " ".join(r["Numeris"].split()) not in EXCLUDE]
    for i, r in enumerate(rows):
        folder = (r.get("Aplanko nuoroda") or "").strip()
        # the origin is prefixed in SQL rather than repeated on 339 lines
        paid = money(r.get("Apmokėta"))
        rec = [i, txt(r["Numeris"]), txt(r["Klientas"]), txt(r["Aprašymas"]), date(r["Užklausos data"]),
               (r["Užklausa tiekėjams išsiųsta"] or "").strip() == "Taip", txt(r["Tiekėjas"]),
               (r["Pasiūlymas klientui"] or "").strip() == "Taip", txt(r["Užklausos būsena"]) or "Vykdoma",
               date(r["PO Data"]), money(r["Kaina be PVM"]) or "0", money(r["Išstatyta"]), paid,
               paid is not None and float(paid) > 0, (r["Pristatymas"] or "").strip() == "Pristatyta",
               txt(r["Atsakingas"]), folder or None, date(r.get("Galutinio pristatymo data"))]
        vals.append("(" + ", ".join(lit(v) if not (j in (10, 11, 12) and v is not None) else str(v)
                                   for j, v in enumerate(rec)) + ")")
    out = sys.stdout
    out.write("-- generated from the SharePoint export, %d rows. Do not commit.\nbegin;\n" % len(rows))
    out.write("alter table public.enquiries disable trigger enquiries_history;\n")
    out.write("""create temp table imp (ord int, number text, client text, description text, enquiry_date date,
  sent_to_supplier boolean, supplier text, quoted_to_client boolean, status text, po_date date,
  price_ex_vat numeric(14,2), invoiced_ex_vat numeric(14,2), paid_ex_vat numeric(14,2), paid boolean,
  delivered boolean, owner text, folder_url text, final_delivery_date date) on commit drop;
insert into imp values
""")
    out.write(",\n".join(vals) + ";\n")
    out.write("""
update imp set folder_url = 'https://litprofit370.sharepoint.com' || folder_url where folder_url like '/%';

create temp table pairs on commit drop as
with i as (select *, row_number() over (partition by number order by ord) rn from imp),
     e as (select id, btrim(number) n, row_number() over (partition by btrim(number) order by created_at, id) rn
             from public.enquiries)
select i.ord, e.id from i left join e on e.n = i.number and e.rn = i.rn;

update public.enquiries t set
  number = i.number, client = i.client, description = i.description, enquiry_date = i.enquiry_date,
  sent_to_supplier = i.sent_to_supplier, supplier = i.supplier, quoted_to_client = i.quoted_to_client,
  status = i.status, po_date = i.po_date, price_ex_vat = i.price_ex_vat,
  invoiced_ex_vat = i.invoiced_ex_vat, paid_ex_vat = i.paid_ex_vat, paid = i.paid or t.paid,
  delivered = i.delivered, owner = coalesce(i.owner, t.owner), folder_url = i.folder_url,
  final_delivery_date = i.final_delivery_date, rev = t.rev + 1, updated_at = now()
from imp i join pairs p on p.ord = i.ord
where t.id = p.id;

insert into public.enquiries (number, client, description, enquiry_date, sent_to_supplier, supplier,
  quoted_to_client, status, po_date, price_ex_vat, invoiced_ex_vat, paid_ex_vat, paid, delivered,
  owner, folder_url, final_delivery_date)
select i.number, i.client, i.description, i.enquiry_date, i.sent_to_supplier, i.supplier,
  i.quoted_to_client, i.status, i.po_date, i.price_ex_vat, i.invoiced_ex_vat, i.paid_ex_vat, i.paid,
  i.delivered, i.owner, i.folder_url, i.final_delivery_date
from imp i join pairs p on p.ord = i.ord where p.id is null order by i.ord;

-- what the export did not carry, left as it was
select number, client, status, price_ex_vat from public.enquiries
 where id not in (select id from pairs where id is not null)
   and created_at < now() - interval '1 second';
alter table public.enquiries enable trigger enquiries_history;
commit;
""")

if __name__ == "__main__":
    main(sys.argv[1])
