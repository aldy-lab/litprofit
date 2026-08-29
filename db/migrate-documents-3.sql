-- ============================================================
-- DOCUMENTS, THIRD PASS: a number, and a date it stops being true
-- ============================================================
-- The store had one shape for eight kinds of document, and the shape was an
-- invoice's: date, amount, counterparty. A photograph has no amount. A
-- certificate has no counterparty in the sense an invoice does -- it has an
-- issuer -- and it has the one field that matters most about it, which the
-- table had nowhere to put: the day it expires.
--
-- Two columns, because two are what is missing. Not a jsonb bag of extras:
-- an expiry that lives inside json cannot be indexed, cannot be sorted, and
-- cannot answer "what runs out in the next ninety days" without reading every
-- row in the table.
--
-- Requires migrate-documents-2.sql. SAFE TO RUN MORE THAN ONCE.
-- ============================================================

-- The document's own number. An invoice store with no invoice number was the
-- odd thing about the first pass: it is how everyone refers to the document,
-- and it was only findable by opening the file.
alter table public.documents add column if not exists ref text;

-- The day it stops being true. A certificate, a contract, an insurance policy
-- and a quotation all have one; an invoice and a photograph do not, and the
-- interface asks only where it applies.
alter table public.documents add column if not exists valid_until date;

create index if not exists documents_ref_idx   on public.documents (ref);
create index if not exists documents_valid_idx on public.documents (valid_until)
  where valid_until is not null;


drop function if exists public.create_document(jsonb);
drop function if exists public.save_document(uuid, bigint, jsonb);
drop view if exists public.documents_v;

create view public.documents_v as
select
  d.id, d.path, d.filename, d.mime, d.size_bytes,
  d.kind, d.doc_date, d.ref, d.amount, d.counterparty, d.valid_until, d.note,
  -- Days left, computed rather than stored: a stored countdown is wrong by
  -- one every midnight and by a lot after a weekend.
  case when d.valid_until is null then null
       else (d.valid_until - current_date) end as days_left,
  d.project_id, d.enquiry_id,
  p.project_id  as project_ref,
  e.number      as enquiry_ref,
  d.created_by,
  nullif(coalesce(nullif(pr.name, ''), nullif(pr.email, '')), '') as uploaded_by,
  d.rev, d.created_at, d.updated_at
from public.documents d
left join public.projects  p  on p.id = d.project_id
left join public.enquiries e  on e.id = d.enquiry_id
left join public.profiles  pr on pr.id = d.created_by
where public.sees_money();


create or replace function public.create_document(p_row jsonb)
returns setof public.documents_v
language plpgsql security definer set search_path = ''
as $$
declare new_id uuid;
begin
  if not public.sees_money() then
    raise exception 'not permitted' using errcode = '42501';
  end if;
  insert into public.documents (path, filename, mime, size_bytes, kind,
                                doc_date, ref, amount, counterparty, valid_until,
                                note, project_id, enquiry_id)
  values (p_row->>'path', coalesce(p_row->>'filename', 'file'),
          p_row->>'mime', nullif(p_row->>'size_bytes','')::bigint,
          coalesce(p_row->>'kind', 'other'),
          nullif(p_row->>'doc_date','')::date,
          p_row->>'ref',
          nullif(p_row->>'amount','')::numeric,
          p_row->>'counterparty',
          nullif(p_row->>'valid_until','')::date,
          p_row->>'note',
          nullif(p_row->>'project_id','')::uuid,
          nullif(p_row->>'enquiry_id','')::uuid)
  returning id into new_id;
  return query select * from public.documents_v where id = new_id;
end $$;

create or replace function public.save_document(p_id uuid, p_rev bigint, p_row jsonb)
returns setof public.documents_v
language plpgsql security definer set search_path = ''
as $$
declare cur public.documents%rowtype;
begin
  if not public.sees_money() then
    raise exception 'not permitted' using errcode = '42501';
  end if;
  select * into cur from public.documents where id = p_id;
  if not found then return; end if;
  if p_rev is not null and cur.rev <> p_rev then return; end if;

  -- path and filename stay unwritable, for the reason they always were: a
  -- record that can point somewhere other than where the file is, is a store
  -- that lies about what it holds.
  update public.documents set
    kind         = coalesce(p_row->>'kind', kind),
    doc_date     = nullif(p_row->>'doc_date','')::date,
    ref          = p_row->>'ref',
    amount       = nullif(p_row->>'amount','')::numeric,
    counterparty = p_row->>'counterparty',
    valid_until  = nullif(p_row->>'valid_until','')::date,
    note         = p_row->>'note',
    project_id   = nullif(p_row->>'project_id','')::uuid,
    enquiry_id   = nullif(p_row->>'enquiry_id','')::uuid,
    rev = rev + 1, updated_at = now(), updated_by = auth.uid()
  where id = p_id;

  return query select * from public.documents_v where id = p_id;
end $$;


-- ------------------------------------------------------------
-- CHECK IT LANDED
-- ------------------------------------------------------------
do $$
declare n int;
begin
  select count(*) into n from information_schema.columns
   where table_schema='public' and table_name='documents'
     and column_name in ('ref','valid_until');
  if n <> 2 then raise exception 'expected 2 new columns, found %', n; end if;

  select count(*) into n from information_schema.columns
   where table_schema='public' and table_name='documents_v'
     and column_name in ('ref','valid_until','days_left');
  if n <> 3 then raise exception 'the view is missing the new columns'; end if;

  select count(*) into n from pg_proc p join pg_namespace ns on ns.oid=p.pronamespace
   where ns.nspname='public' and p.proname in ('create_document','save_document');
  if n < 2 then raise exception 'the write functions did not come back'; end if;

  raise notice 'documents third pass OK: ref and valid_until, days_left derived';
end $$;
