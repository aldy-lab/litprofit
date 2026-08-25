-- ============================================================
-- MIGRATION: add the enquiry register to an EXISTING database
-- ============================================================
-- Run this, not schema.sql.
--
-- schema.sql is written for an empty project: it carries `create trigger` and
-- `create policy` statements with no `if not exists` on them, and Postgres has
-- no such form for either. On a database that already has the projects tables
-- the first of those aborts the whole script -- which is why running
-- schema.sql against the live project reported success on nothing and left
-- public.enquiries uncreated.
--
-- Everything below is safe to run more than once: create table if not exists,
-- create or replace for every function and the view, create index if not
-- exists, and enable row level security, which is idempotent. Verified by
-- running this file twice in a row against a real PostgreSQL 18, then seeding
-- and re-checking the totals.
--
--   psql "$SUPABASE_DB_URL" -v ON_ERROR_STOP=1 -f db/migrate-enquiries.sql
--   psql "$SUPABASE_DB_URL" -v ON_ERROR_STOP=1 -f db/seed-enquiries.sql
--
-- In the Supabase SQL editor, paste the whole file and run it in one go --
-- running it in pieces is what leaves a half-applied migration behind.

-- ============================================================
-- ENQUIRIES  (Užklausų registras)
-- ============================================================
-- This register lived in a Power BI report published to the web, reading from
-- a spreadsheet. Two problems with leaving it there: a publish-to-web link is
-- readable by anyone who has the URL -- client names, suppliers and prices for
-- 216 enquiries, 2.6 M EUR of them -- and the spreadsheet behind it was a
-- second place where the truth lived. The register moves here, behind the same
-- login and the same roles as everything else in the calculator.
--
-- Columns are the report's own, kept in Lithuanian order but named in English
-- so the SQL reads like the rest of this file:
--   Numeris        -> number          Užklausos data     -> enquiry_date
--   Klientas       -> client          Užklausa tiekėjams -> sent_to_supplier
--   Aprašymas      -> description     Pasiūlymas klientui-> quoted_to_client
--   Tiekėjas       -> supplier        Užklausos būsena   -> status
--   PO Data        -> po_date         Kaina be PVM       -> price_ex_vat
--   Pristatymas    -> delivered       Atsakingas         -> owner
--
-- `number` is NOT unique: the register already carries 26.2-19.2 twice, which
-- is how they record two lines under one enquiry. A unique index here would
-- have rejected the client's own data on import.
create table if not exists public.enquiries (
  id            uuid primary key default gen_random_uuid(),
  number        text not null,
  client        text,
  description   text,
  enquiry_date  date,
  sent_to_supplier boolean not null default false,
  supplier      text,
  quoted_to_client boolean not null default false,
  status        text not null default 'Vykdoma'
                check (status in ('Vykdoma', 'Gautas PO', 'Atmesta užklausa')),
  po_date       date,
  price_ex_vat  numeric(14,2) not null default 0,
  delivered     boolean not null default false,
  owner         text,
  note          text,
  rev           bigint not null default 1,
  created_at    timestamptz not null default now(),
  created_by    uuid references auth.users(id) default auth.uid(),
  updated_at    timestamptz not null default now(),
  updated_by    uuid references auth.users(id) default auth.uid()
);

create index if not exists enquiries_date_idx     on public.enquiries (enquiry_date desc);
create index if not exists enquiries_status_idx   on public.enquiries (status);
create index if not exists enquiries_client_idx   on public.enquiries (client);
create index if not exists enquiries_supplier_idx on public.enquiries (supplier);

alter table public.enquiries enable row level security;

-- "Neišsiųstas pasiūlymas, dienos" was a calculated column in the report: how
-- long an enquiry has been sitting without a quote going back to the client.
-- It is derived, so it is not stored -- a stored copy goes stale overnight,
-- every night, and the report's own value was only right on the day it ran.
create or replace function public.enquiry_days_unquoted(
  p_quoted boolean, p_date date, p_status text)
returns integer
language sql immutable
as $$
  select case
    when p_quoted or p_date is null then 0
    else greatest(0, (current_date - p_date))::integer
  end
$$;

-- Money is the whole point of this table, so there is no redacted variant of
-- it: an employee who cannot see money does not get this register at all. The
-- view returns nothing rather than returning rows with the prices blanked --
-- a register of who asked for what, with the amounts removed, is still the
-- client list and the supplier list, and neither is theirs to have.
create or replace view public.enquiries_v as
select
  e.id, e.number, e.client, e.description, e.enquiry_date,
  e.sent_to_supplier, e.supplier, e.quoted_to_client,
  public.enquiry_days_unquoted(e.quoted_to_client, e.enquiry_date, e.status) as days_unquoted,
  e.status, e.po_date, e.price_ex_vat, e.delivered, e.owner, e.note,
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
    price_ex_vat = coalesce((p_row->>'price_ex_vat')::numeric, 0),
    delivered = coalesce((p_row->>'delivered')::boolean, false),
    owner = p_row->>'owner',
    note = p_row->>'note',
    rev = rev + 1,
    updated_at = now(),
    updated_by = auth.uid()
  where id = p_id and rev = p_rev
  returning * into r;
  if not found then
    -- same contract as save_project: a stale rev is a conflict, not a crash
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
      price_ex_vat, delivered, owner, note)
  values (coalesce(nullif(p_row->>'number',''), 'NEW'),
      p_row->>'client', p_row->>'description', nullif(p_row->>'enquiry_date','')::date,
      coalesce((p_row->>'sent_to_supplier')::boolean, false), p_row->>'supplier',
      coalesce((p_row->>'quoted_to_client')::boolean, false),
      coalesce(nullif(p_row->>'status',''), 'Vykdoma'), nullif(p_row->>'po_date','')::date,
      coalesce((p_row->>'price_ex_vat')::numeric, 0),
      coalesce((p_row->>'delivered')::boolean, false), p_row->>'owner', p_row->>'note')
  returning * into r;
  return r;
end $$;

create or replace function public.delete_enquiry(p_id uuid)
returns void
language plpgsql security definer set search_path = ''
as $$
begin
  if public.my_role() <> 'admin' then
    raise exception 'not permitted' using errcode = '42501';
  end if;
  delete from public.enquiries where id = p_id;
end $$;

-- The table itself is revoked, exactly as public.projects is: the app can only
-- reach the view and the three functions above.
revoke all on public.enquiries   from anon, authenticated;
revoke all on public.enquiries_v from anon;
grant select on public.enquiries_v to authenticated;
grant execute on function public.save_enquiry(uuid, bigint, jsonb) to authenticated;
grant execute on function public.create_enquiry(jsonb)             to authenticated;
grant execute on function public.delete_enquiry(uuid)              to authenticated;
grant execute on function public.enquiry_days_unquoted(boolean, date, text) to authenticated;
