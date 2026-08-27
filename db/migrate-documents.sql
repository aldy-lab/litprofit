-- ============================================================
-- DOCUMENTS: a place for the invoices
-- ============================================================
-- A draft, deliberately. It stores files, says what each one is, and ties it
-- to the project or the enquiry it belongs to. It does not read them: no OCR,
-- no totals pulled off a scan, no accounting. The amount and the date are
-- typed, because a number this app reports had better be one somebody meant.
--
-- SAFE TO RUN MORE THAN ONCE, like the others: `create policy` has no
-- `if not exists`, so every policy is dropped first by name.
--
-- ------------------------------------------------------------
-- WHERE THE FILE ACTUALLY LIVES
-- ------------------------------------------------------------
-- In Supabase Storage, in a PRIVATE bucket. Private is the whole point: a
-- public bucket hands every invoice to anyone who guesses a URL, and the URLs
-- are guessable because they contain the filename. Reading a file is a signed
-- URL, minted per request and short-lived.
--
-- The row in public.documents is the record; the object in storage is the
-- file. They are kept in step by storing the object's path on the row, and by
-- deleting the row and the object together.
-- ============================================================

insert into storage.buckets (id, name, public, file_size_limit, allowed_mime_types)
values ('documents', 'documents', false, 26214400, null)
on conflict (id) do update
  set public = false, file_size_limit = 26214400;


-- ------------------------------------------------------------
-- THE RECORD
-- ------------------------------------------------------------
-- kind is a closed list rather than free text. Free text here becomes
-- "invoice", "Invoice", "inv" and "sąskaita" inside a month, and then nothing
-- can be filtered.
create table if not exists public.documents (
  id           uuid primary key default gen_random_uuid(),
  path         text not null unique,        -- the object in the bucket
  filename     text not null,               -- what it was called when uploaded
  mime         text,
  size_bytes   bigint,

  kind         text not null default 'other'
               check (kind in ('invoice_in', 'invoice_out', 'quote', 'contract',
                               'certificate', 'report', 'photo', 'other')),
  doc_date     date,
  amount       numeric(14,2),
  counterparty text,
  note         text,

  -- What it belongs to. Both nullable and both optional: a certificate
  -- belongs to the company and to no job at all.
  project_id   uuid references public.projects(id) on delete set null,
  enquiry_id   uuid references public.enquiries(id) on delete set null,

  rev          bigint not null default 1,
  created_at   timestamptz not null default now(),
  created_by   uuid references auth.users(id) default auth.uid(),
  updated_at   timestamptz not null default now(),
  updated_by   uuid references auth.users(id) default auth.uid()
);

create index if not exists documents_kind_idx     on public.documents (kind);
create index if not exists documents_date_idx     on public.documents (doc_date desc);
create index if not exists documents_project_idx  on public.documents (project_id);
create index if not exists documents_enquiry_idx  on public.documents (enquiry_id);
create index if not exists documents_party_idx    on public.documents (counterparty);

alter table public.documents enable row level security;


-- ------------------------------------------------------------
-- WHO MAY SEE THEM
-- ------------------------------------------------------------
-- sees_money(), not sees_payroll(). An invoice is a price, and a manager
-- prices work. Payroll documents are the exception and they are kept out by
-- kind rather than by hoping nobody uploads one: there is no payroll kind in
-- the list above, and a payslip filed as 'other' would be visible to a
-- manager. That is a policy the owner has to keep, not one the schema can --
-- and it is written down here so it is a decision rather than an oversight.
-- ------------------------------------------------------------

-- Dropped before the view, because create_document and save_document return
-- `setof public.documents_v` and therefore DEPEND on it -- the same trap as
-- migrate-company.sql, hit again on the second run of this file despite
-- knowing about it. Which is the argument for running every migration twice
-- rather than reading it twice.
drop function if exists public.create_document(jsonb);
drop function if exists public.save_document(uuid, bigint, jsonb);

drop view if exists public.documents_v;
create view public.documents_v as
select
  d.id, d.path, d.filename, d.mime, d.size_bytes,
  d.kind, d.doc_date, d.amount, d.counterparty, d.note,
  d.project_id, d.enquiry_id,
  p.project_id  as project_ref,
  e.number      as enquiry_ref,
  d.rev, d.created_at, d.updated_at
from public.documents d
left join public.projects  p on p.id = d.project_id
left join public.enquiries e on e.id = d.enquiry_id
where public.sees_money();


-- ------------------------------------------------------------
-- STORAGE POLICIES
-- ------------------------------------------------------------
-- The bucket is private, so nothing reaches it without a policy. These are
-- the only four. Note they are on storage.objects, which is a table Supabase
-- owns -- dropping by name first, because a second run would otherwise abort
-- the whole script the way schema.sql once did.
drop policy if exists documents_read   on storage.objects;
drop policy if exists documents_insert on storage.objects;
drop policy if exists documents_update on storage.objects;
drop policy if exists documents_delete on storage.objects;

create policy documents_read on storage.objects
  for select using (bucket_id = 'documents' and public.sees_money());

create policy documents_insert on storage.objects
  for insert with check (bucket_id = 'documents' and public.sees_money());

create policy documents_update on storage.objects
  for update using (bucket_id = 'documents' and public.sees_money());

-- Deleting is the owner's. A wrong delete here is a lost invoice, and there
-- is no undo on an object store.
create policy documents_delete on storage.objects
  for delete using (bucket_id = 'documents' and public.my_role() = 'admin');


-- ------------------------------------------------------------
-- WRITES
-- ------------------------------------------------------------
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
                                doc_date, amount, counterparty, note,
                                project_id, enquiry_id)
  values (p_row->>'path', coalesce(p_row->>'filename', 'file'),
          p_row->>'mime', nullif(p_row->>'size_bytes','')::bigint,
          coalesce(p_row->>'kind', 'other'),
          nullif(p_row->>'doc_date','')::date,
          nullif(p_row->>'amount','')::numeric,
          p_row->>'counterparty', p_row->>'note',
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

  -- path and filename are NOT updatable. They name an object that exists;
  -- letting the record point somewhere else while the file stays put is how
  -- a document store starts lying about what it holds.
  update public.documents set
    kind         = coalesce(p_row->>'kind', kind),
    doc_date     = nullif(p_row->>'doc_date','')::date,
    amount       = nullif(p_row->>'amount','')::numeric,
    counterparty = p_row->>'counterparty',
    note         = p_row->>'note',
    project_id   = nullif(p_row->>'project_id','')::uuid,
    enquiry_id   = nullif(p_row->>'enquiry_id','')::uuid,
    rev = rev + 1, updated_at = now(), updated_by = auth.uid()
  where id = p_id;

  return query select * from public.documents_v where id = p_id;
end $$;

-- Returns the path so the caller can remove the object too. The row and the
-- file are deleted in two steps by two different systems and there is no
-- transaction across them; doing the row first would orphan the file with
-- nothing left pointing at it, so the app deletes the object first and calls
-- this after.
create or replace function public.delete_document(p_id uuid)
returns text
language plpgsql security definer set search_path = ''
as $$
declare gone text;
begin
  if public.my_role() <> 'admin' then
    raise exception 'not permitted' using errcode = '42501';
  end if;
  select path into gone from public.documents where id = p_id;
  delete from public.documents where id = p_id;
  return gone;
end $$;


-- ------------------------------------------------------------
-- WHAT IS IN THERE
-- ------------------------------------------------------------
-- Totals by kind and by month, so the screen has something to say beyond a
-- file list. Invoices in against invoices out for a month is the first
-- useful thing a document store can tell an owner.
create or replace function public.document_totals()
returns table (kind text, n integer, total numeric, bytes bigint)
language sql stable
security definer set search_path = ''
as $$
  select d.kind, count(*)::int, coalesce(sum(d.amount), 0),
         coalesce(sum(d.size_bytes), 0)::bigint
    from public.documents d
   where public.sees_money()
   group by d.kind
   order by count(*) desc;
$$;


-- ------------------------------------------------------------
-- CHECK IT LANDED
-- ------------------------------------------------------------
do $$
declare n int;
begin
  select count(*) into n from information_schema.tables
   where table_schema = 'public' and table_name = 'documents';
  if n <> 1 then raise exception 'documents table missing'; end if;

  select count(*) into n from pg_policies
   where schemaname = 'storage' and tablename = 'objects'
     and policyname like 'documents_%';
  if n <> 4 then raise exception 'expected 4 storage policies, found %', n; end if;

  select count(*) into n from pg_proc p join pg_namespace ns on ns.oid = p.pronamespace
   where ns.nspname = 'public'
     and p.proname in ('create_document','save_document','delete_document','document_totals');
  if n < 4 then raise exception 'expected 4 functions, found %', n; end if;

  raise notice 'documents migration OK: 1 table, 1 view, 4 policies, 4 functions';
end $$;
