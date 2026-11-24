"""Last pass over the manifest written by 2_extract.py.

Amounts and numbers read off suppliers' invoices are dropped: their layouts
differ per supplier and the totals the pattern found were often a line, a
discount or a page number (0.40 EUR, 7.30 EUR). A wrong amount in the register
is worse than an empty one, so they arrive empty for a person to fill in.
Litprofit's own invoices are re-read with the one pattern its template uses.

Enquiries that have a folder but no row in the SharePoint list get what the
importer creates them with: client from the folder name, Gautas PO for an SK
order folder, a note saying where the row came from.

    python 3_finalize.py manifest.json"""
import json, re, os, sys, pymupdf
ROOT="/Users/aldy/Downloads/Pardavimai 2026"
P=sys.argv[1]; M=json.load(open(P))
STRICT=re.compile(r"I[šs] viso/Total Amount:?\s*\n?\s*([\d][\d .,]*\d)",re.I)
def num(s):
    s=s.strip().replace(" ","")
    if re.match(r"^\d+,\d{1,2}$",s): s=s.replace(",",".")
    try: return round(float(s.replace(",","")),2)
    except ValueError: return None
for e in M["entries"]:
    if e["kind"]=="invoice_in": e["amount"]=None; e["ref"]=None
    if e["kind"]=="invoice_out" and e["rel"].lower().endswith(".pdf"):
        try: t="\n".join(p.get_text() for p in pymupdf.open(os.path.join(ROOT,e["rel"])))
        except Exception: t=""
        m=STRICT.search(t); e["amount"]=num(m.group(1)) if m else None
    if e["kind"]=="invoice_out" and e["amount"]==0: e["amount"]=None
for k,v in M["enquiries"].items():
    if not v["new"]: continue
    name=v["folder"]; rest=re.sub(r"^(SK26-\d{3}|\d{2}\.\d{1,2}\s*-\s*\d{1,2}(?:\.\d+)?[A-Z]?)\s*-?\s*","",name).strip()
    client=re.split(r"\s+-\s+|\s{2,}",rest)[0].strip() if rest else None
    v["create"]={"client":client or None,"description":rest or None,
        "status":"Gautas PO" if k.startswith("SK") else "Vykdoma",
        "note":"Sukurta importuojant aplanką „%s“ — SharePoint sąraše šios eilutės nebuvo. Patikrinkite klientą, būseną ir sumą."%name}
# "nuo Litprofit o" names the sender, which on our own invoice is us: the party
# is the buyer after "Invoice to", or nobody
for e in M["entries"]:
    cp=e.get("counterparty") or ""
    if re.match(r"(?i)litprofit\b",cp) or re.match(r"^\d",cp):
        m=re.search(r"Invoice to\s+(.+?)\s*(?:-|$)",e["rel"].split("/")[-1])
        e["counterparty"]=m.group(1).strip() if m else None
M["year"]=M.get("year") or "2026"
json.dump(M,open(P,"w"),ensure_ascii=False)
