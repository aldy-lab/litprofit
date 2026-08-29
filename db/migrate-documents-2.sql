-- ============================================================
-- DOCUMENTS, SECOND PASS: who put it there
-- ============================================================
-- The row already recorded created_by and the view never returned it, so the
-- screen could show what a file is and not who filed it. In a store several
-- people write to, "who uploaded this" is the question asked immediately
-- after "what is it".
--
-- Requires migrate-documents.sql. SAFE TO RUN MORE THAN ONCE.
--
-- ------------------------------------------------------------
-- WHY FOLDERS ARE NOT PATHS
-- ------------------------------------------------------------
-- The obvious way to give this a folder per kind is to put the kind in the
-- storage path -- invoices/2026-08/... -- and let the bucket show the
-- structure. It is the wrong way here, and the reason is already in the first
-- migration: `path` is deliberately not updatable, because a record that can
-- point somewhere other than where the file is is a store that lies about
-- what it holds.
--
-- kind, on the other hand, IS meant to change: a file is uploaded, somebody
-- looks at it and decides it is a quote rather than an invoice. If the kind
-- were the folder, that edit would have to move the object, and a move is two
-- operations across two systems with no transaction between them -- exactly
-- the failure the upload order was arranged to avoid.
--
-- So the folders are a view of `kind`, and the path stays the dated,
-- randomised name it was given on upload. The bucket is storage; the folders
-- are the filing.
-- ============================================================

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
  d.created_by,
  -- The name if there is one, the email if there is not, and nothing rather
  -- than a raw uuid: an id in this column tells the reader less than a blank
  -- would and looks like a bug.
  nullif(coalesce(nullif(pr.name, ''), nullif(pr.email, '')), '') as uploaded_by,
  d.rev, d.created_at, d.updated_at
from public.documents d
left join public.projects  p  on p.id = d.project_id
left join public.enquiries e  on e.id = d.enquiry_id
left join public.profiles  pr on pr.id = d.created_by
where public.sees_money();


-- Unchanged from the first migration except that they return the new view.
-- Restated here because dropping the view drops them with it.
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


-- ------------------------------------------------------------
-- CHECK IT LANDED
-- ------------------------------------------------------------
do $$
declare n int;
begin
  select count(*) into n from information_schema.columns
   where table_schema = 'public' and table_name = 'documents_v'
     and column_name in ('created_by', 'uploaded_by');
  if n <> 2 then raise exception 'the view is missing the uploader columns'; end if;

  select count(*) into n from pg_proc p join pg_namespace ns on ns.oid = p.pronamespace
   where ns.nspname = 'public' and p.proname in ('create_document', 'save_document');
  if n < 2 then raise exception 'the write functions did not come back'; end if;

  raise notice 'documents second pass OK: the view now says who uploaded';
end $$;
