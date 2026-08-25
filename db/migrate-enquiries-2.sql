-- ============================================================
-- MIGRATION 2: what the company actually makes, and whether it was paid
-- ============================================================
-- The register came out of Power BI with one money column, "Kaina be PVM".
-- One number per line cannot answer the question the register exists to
-- answer, which is what Litprofit earns on a part -- so the supplier's price
-- goes in beside it and the difference is computed, never typed. A margin that
-- is entered by hand is a margin that disagrees with its own two figures the
-- first time one of them is corrected.
--
-- price_ex_vat keeps its meaning: what the CLIENT is charged. cost_ex_vat is
-- what the SUPPLIER charges us. The 216 imported rows have no cost -- the
-- report never carried one -- so their margin is null, not zero. Null means
-- "not known yet" and zero means "we made nothing", and a register that
-- confuses the two will quietly report a loss on every historic line.
--
-- Safe to run more than once. Run after migrate-enquiries.sql.
--   psql "$SUPABASE_DB_URL" -v ON_ERROR_STOP=1 -f db/migrate-enquiries-2.sql

begin;

alter table public.enquiries add column if not exists cost_ex_vat numeric(14,2);
alter table public.enquiries add column if not exists paid        boolean not null default false;
alter table public.enquiries add column if not exists paid_date   date;
alter table public.enquiries add column if not exists invoice_no  text;

create index if not exists enquiries_paid_idx on public.enquiries (paid);

-- Margin in one place. Computed in the view rather than stored, for the same
-- reason days_unquoted is: a stored copy is a second version of the truth that
-- nothing keeps in step.
--
-- DROP and create, not `create or replace`. Replace can only append columns to
-- a view; it cannot reorder them, and putting cost_ex_vat in front of
-- price_ex_vat reads to Postgres as renaming the existing column:
--   ERROR: cannot change name of view column "price_ex_vat" to "cost_ex_vat"
-- The view holds no data, so dropping it costs nothing; the grant below puts
-- the permission back in the same transaction.
drop view if exists public.enquiries_v;
create view public.enquiries_v as
select
  e.id, e.number, e.client, e.description, e.enquiry_date,
  e.sent_to_supplier, e.supplier, e.quoted_to_client,
  public.enquiry_days_unquoted(e.quoted_to_client, e.enquiry_date, e.status) as days_unquoted,
  e.status, e.po_date,
  e.cost_ex_vat, e.price_ex_vat,
  case when e.cost_ex_vat is null then null
       else e.price_ex_vat - e.cost_ex_vat end as margin_eur,
  case when e.cost_ex_vat is null or e.price_ex_vat = 0 then null
       else round((e.price_ex_vat - e.cost_ex_vat) / e.price_ex_vat, 4) end as margin_pct,
  e.delivered, e.paid, e.paid_date, e.invoice_no,
  e.owner, e.note,
  e.rev, e.created_at, e.updated_at, e.updated_by
from public.enquiries e
where public.sees_money();

create or replace function public.save_enquiry(p_id uuid, p_rev bigint, p_row jsonb)
returns public.enquiries
language plpgsql security definer set search_path = ''
as $$
declare r public.enquiries;
begin
  if not public.sees_money() then
    raise exception 'not permitted' using errcode = '42501';
  end if;
  update public.enquiries set
    number = coalesce(p_row->>'number', number),
    client = p_row->>'client',
    description = p_row->>'description',
    enquiry_date = nullif(p_row->>'enquiry_date','')::date,
    sent_to_supplier = coalesce((p_row->>'sent_to_supplier')::boolean, false),
    supplier = p_row->>'supplier',
    quoted_to_client = coalesce((p_row->>'quoted_to_client')::boolean, false),
    status = coalesce(p_row->>'status', status),
    po_date = nullif(p_row->>'po_date','')::date,
    -- nullif before the cast, so an empty box stays "not known" instead of
    -- becoming a cost of zero and inventing a 100% margin
    cost_ex_vat = nullif(p_row->>'cost_ex_vat','')::numeric,
    price_ex_vat = coalesce((p_row->>'price_ex_vat')::numeric, 0),
    delivered = coalesce((p_row->>'delivered')::boolean, false),
    paid = coalesce((p_row->>'paid')::boolean, false),
    paid_date = nullif(p_row->>'paid_date','')::date,
    invoice_no = p_row->>'invoice_no',
    owner = p_row->>'owner',
    note = p_row->>'note',
    rev = rev + 1,
    updated_at = now(),
    updated_by = auth.uid()
  where id = p_id and rev = p_rev
  returning * into r;
  if not found then
    raise exception 'conflict' using errcode = '40001';
  end if;
  return r;
end $$;

create or replace function public.create_enquiry(p_row jsonb)
returns public.enquiries
language plpgsql security definer set search_path = ''
as $$
declare r public.enquiries;
begin
  if not public.sees_money() then
    raise exception 'not permitted' using errcode = '42501';
  end if;
  insert into public.enquiries (number, client, description, enquiry_date,
      sent_to_supplier, supplier, quoted_to_client, status, po_date,
      cost_ex_vat, price_ex_vat, delivered, paid, paid_date, invoice_no, owner, note)
  values (coalesce(nullif(p_row->>'number',''), 'NEW'),
      p_row->>'client', p_row->>'description', nullif(p_row->>'enquiry_date','')::date,
      coalesce((p_row->>'sent_to_supplier')::boolean, false), p_row->>'supplier',
      coalesce((p_row->>'quoted_to_client')::boolean, false),
      coalesce(nullif(p_row->>'status',''), 'Vykdoma'), nullif(p_row->>'po_date','')::date,
      nullif(p_row->>'cost_ex_vat','')::numeric,
      coalesce((p_row->>'price_ex_vat')::numeric, 0),
      coalesce((p_row->>'delivered')::boolean, false),
      coalesce((p_row->>'paid')::boolean, false),
      nullif(p_row->>'paid_date','')::date, p_row->>'invoice_no',
      p_row->>'owner', p_row->>'note')
  returning * into r;
  return r;
end $$;

revoke all on public.enquiries_v from anon;
grant select on public.enquiries_v to authenticated;

commit;
