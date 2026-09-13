-- ============================================================
-- DOCUMENTS, FOURTH PASS: TWO STORES, AND A MANAGER MAY DELETE A JOB'S FILE
-- ============================================================
-- Two things were true at once and should not have been.
--
-- 1. A MANAGER SAW THE COMPANY'S FILES. documents_v was gated on sees_money()
--    and nothing else, so every certificate, flag document and company
--    contract was in a project manager's browser. The Company tab is behind
--    the payroll gate, so nobody SAW them on screen -- but a tab that is not
--    rendered is not a boundary, and the rows were one fetch away.
--
-- 2. A MANAGER COULD NOT DELETE ANYTHING. delete_document required admin, so
--    the delete on a job's own paperwork was always refused. The button was
--    offered and the server said no, which reads as a broken button.
--
-- The line drawn here is the one the work actually has: a document WITH a
-- project belongs to that job, and a document WITHOUT one belongs to the
-- company. A manager gets the first and never the second, in the view, in the
-- delete, and in the bucket. An owner gets both.
--
-- An enquiry-only document falls on the company side on purpose: it is not a
-- job's paperwork, and the application draws the same line in docScoped().
--
-- Requires migrate-documents-3.sql. SAFE TO RUN MORE THAN ONCE.
-- ============================================================


-- ------------------------------------------------------------
-- IS THIS OBJECT A JOB'S FILE?
-- ------------------------------------------------------------
-- SECURITY DEFINER, and that is the whole point of it existing. The bucket
-- policies below have to ask whether an object belongs to a project, and a
-- policy expression is evaluated AS THE CALLER -- who cannot read
-- public.documents at all, because that table is deny-all with no policies.
-- An inline `exists (select ... from public.documents ...)` in a policy
-- therefore answers false for everybody and locks the bucket. This asks on the
-- owner's behalf and returns one boolean.
create or replace function public.doc_is_project_file(p_path text)
returns boolean
language sql stable security definer set search_path = ''
as $$
  select exists (select 1 from public.documents d
                  where d.path = p_path and d.project_id is not null)
$$;

-- An RLS policy runs as the current user, so `authenticated` needs EXECUTE on
-- anything a policy calls. This is the same reason sees_money() is on the
-- keep-list in migrate-harden.sql, and this name has been added there too --
-- without the grant, re-running that file revokes this and every upload and
-- every signed URL stops working, which shows up as a file that will not open
-- rather than as an error.
grant execute on function public.doc_is_project_file(text) to authenticated;


-- ------------------------------------------------------------
-- AND SHUT THE DOOR THIS FILE OPENS
-- ------------------------------------------------------------
-- A function arrives with EXECUTE granted to PUBLIC, and PUBLIC includes
-- `anon` -- the role of somebody who has not signed in. migrate-harden.sql
-- revokes that across the whole schema and asserts, in its own check, that
-- anon can execute nothing at all.
--
-- This file quietly undid that, every time it ran. The view is dropped
-- below, and dropping a view drops the functions that RETURN it: so
-- create_document and save_document go with it and come back as NEW
-- functions carrying the default grant, and doc_is_project_file is new here
-- for the same reason. Three RPCs open to the unsigned-in, with nothing
-- behind them but the sees_money() check inside two of the three.
--
-- Found by the linter three weeks after the hardening pass declared the door
-- shut. It is shut here now -- in the file that opens it, not in the one
-- that has to be remembered afterwards.
--
-- These three lines are at the END of this file, after the view and the
-- functions are rebuilt, because there is nothing to revoke until they
-- exist. See the block below the bucket policies.


-- ------------------------------------------------------------
-- THE VIEW: A JOB'S FILES TO EVERYONE WHO SEES MONEY, THE COMPANY'S TO OWNERS
-- ------------------------------------------------------------
-- THE FUNCTIONS GO FIRST. I had written that dropping the view drops the
-- functions that return it; Postgres does the opposite -- it REFUSES to drop
-- the view while anything depends on its type, and both write functions are
-- declared `returns setof public.documents_v`. The run failed on this line
-- with 2BP01 and named them. The second and third passes of this file already
-- knew it and dropped them first; this one had simply lost the two lines.
--
-- Asked the database rather than guessed which ones: exactly create_document
-- and save_document return the view's type. delete_document returns text and
-- is unaffected.
--
-- Both are recreated below, in the same statement run, so the gap in which the
-- application's writes would fail is the length of this script.
drop function if exists public.create_document(jsonb);
drop function if exists public.save_document(uuid, bigint, jsonb);
drop view if exists public.documents_v;

create view public.documents_v as
select
  d.id, d.path, d.filename, d.mime, d.size_bytes,
  d.kind, d.doc_date, d.ref, d.amount, d.counterparty, d.valid_until, d.note,
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
where public.sees_money()
  and (d.project_id is not null or public.my_role() = 'admin');


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

  -- A manager may edit a job's file and must not be able to move it out of
  -- that job, or off it entirely: clearing project_id would push the document
  -- into the company's store, which is the one place they cannot see.
  if public.my_role() <> 'admin'
     and cur.project_id is distinct from nullif(p_row->>'project_id','')::uuid then
    raise exception 'not permitted' using errcode = '42501';
  end if;

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
-- DELETING
-- ------------------------------------------------------------
create or replace function public.delete_document(p_id uuid)
returns text
language plpgsql security definer set search_path = ''
as $$
declare gone text; pid uuid;
begin
  select path, project_id into gone, pid from public.documents where id = p_id;
  if not found then return null; end if;

  -- An owner anywhere. Anyone else who may see money, on a job's file only.
  if public.my_role() <> 'admin'
     and not (public.sees_money() and pid is not null) then
    raise exception 'not permitted' using errcode = '42501';
  end if;

  delete from public.documents where id = p_id;
  return gone;
end $$;


-- ------------------------------------------------------------
-- THE BUCKET
-- ------------------------------------------------------------
-- Reading and deleting are scoped the same way the view is, so a manager
-- cannot sign a URL for a company file or delete its object -- the boundary
-- has to be here as well, because the storage API does not go through the
-- view. Insert and update stay as they were.
drop policy if exists documents_read   on storage.objects;
drop policy if exists documents_delete on storage.objects;

create policy documents_read on storage.objects
  for select using (
    bucket_id = 'documents' and public.sees_money()
    and (public.my_role() = 'admin' or public.doc_is_project_file(name)));

create policy documents_delete on storage.objects
  for delete using (
    bucket_id = 'documents' and public.sees_money()
    and (public.my_role() = 'admin' or public.doc_is_project_file(name)));


-- ------------------------------------------------------------
-- THE DOOR, SHUT
-- ------------------------------------------------------------
-- The three names this file creates or recreates, closed to everybody who
-- has not signed in, and open to everybody who has. Explained in full above.
revoke execute on function public.doc_is_project_file(text)             from public, anon;
revoke execute on function public.create_document(jsonb)                from public, anon;
revoke execute on function public.save_document(uuid, bigint, jsonb)    from public, anon;
grant  execute on function public.doc_is_project_file(text)             to authenticated;
grant  execute on function public.create_document(jsonb)                to authenticated;
grant  execute on function public.save_document(uuid, bigint, jsonb)    to authenticated;


-- ------------------------------------------------------------
-- CHECK IT LANDED
-- ------------------------------------------------------------
do $$
declare n int;
begin
  -- The whole schema, not only the three above: this is the assertion
  -- migrate-harden.sql makes, restated here so that the file which reopened
  -- the hole is also the file that would fail if it ever did again.
  if exists (select 1 from pg_proc p
               join pg_namespace ns on ns.oid = p.pronamespace
              where ns.nspname = 'public'
                and has_function_privilege('anon', p.oid, 'EXECUTE')) then
    raise exception 'anon can execute something in public -- run db/migrate-harden.sql';
  end if;
  if not has_function_privilege('authenticated', 'public.create_document(jsonb)', 'EXECUTE')
     or not has_function_privilege('authenticated', 'public.save_document(uuid, bigint, jsonb)', 'EXECUTE') then
    raise exception 'the cabinet lost EXECUTE on the document functions';
  end if;
  if not exists (select 1 from pg_proc p join pg_namespace ns on ns.oid = p.pronamespace
                  where ns.nspname = 'public' and p.proname = 'doc_is_project_file') then
    raise exception 'doc_is_project_file is missing';
  end if;

  -- The grant a policy cannot do without.
  if not has_function_privilege('authenticated', 'public.doc_is_project_file(text)', 'EXECUTE') then
    raise exception 'authenticated cannot execute doc_is_project_file -- the bucket policies would refuse everybody';
  end if;

  select count(*) into n from pg_policies
   where schemaname = 'storage' and tablename = 'objects'
     and policyname in ('documents_read', 'documents_delete');
  if n <> 2 then raise exception 'expected both bucket policies, found %', n; end if;

  select count(*) into n from pg_proc p join pg_namespace ns on ns.oid = p.pronamespace
   where ns.nspname = 'public'
     and p.proname in ('create_document', 'save_document', 'delete_document');
  if n < 3 then raise exception 'the document functions did not all come back'; end if;

  -- The view must still carry what the third pass added.
  select count(*) into n from information_schema.columns
   where table_schema = 'public' and table_name = 'documents_v'
     and column_name in ('ref', 'valid_until', 'days_left');
  if n <> 3 then raise exception 'the view lost the third pass columns'; end if;

  raise notice 'documents fourth pass OK: company store is the owner''s, a job''s files are the team''s';
end $$;
