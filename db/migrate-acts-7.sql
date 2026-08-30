-- ============================================================
-- ACTS, SEVENTH PASS: a signed act does not go with the project
-- ============================================================
-- acts.project_id was declared ON DELETE CASCADE, which is the obvious rule
-- and the wrong one. Deleting a job took its acts with it, silently, signed
-- or not -- and one signed act went that way on the live project before
-- anybody noticed. It was tidying, not vandalism: the job was called DEMO-03
-- and it looked like demo data. Nothing warned that a document was inside it.
--
-- A draft act really is part of the job and can go with it; there is nothing
-- in it that anybody agreed to. A SIGNED act is not part of the job. Somebody
-- put their name under those exact words, and this application is where the
-- only copy lives. It cannot be removed as a side effect of removing
-- something else.
--
-- So the cascade stays for drafts and a project carrying a signed act refuses
-- to be deleted at all, with a message that says what to do about it. If it
-- genuinely has to go, the signature comes off first -- which is a deliberate
-- act, and one the sign_log records.
--
-- Requires migrate-signatures.sql. SAFE TO RUN MORE THAN ONCE.
--
-- ------------------------------------------------------------
-- WHY A TRIGGER AND NOT `ON DELETE RESTRICT`
-- ------------------------------------------------------------
-- RESTRICT would refuse the delete whenever ANY act existed, draft or not,
-- and it would say so in the language of foreign keys. The rule here is not
-- "this job has acts", it is "this job has a document", and the difference is
-- the whole point. A trigger can ask the real question and answer it in a
-- sentence somebody can act on.
-- ============================================================

create or replace function public.guard_signed_acts()
returns trigger
language plpgsql security definer set search_path = ''
as $$
declare
  n    int;
  nums text;
begin
  select count(*), string_agg(number, ', ' order by number)
    into n, nums
    from public.acts
   where project_id = old.id and signature is not null;

  if n > 0 then
    raise exception
      'This job has % signed act(s) on it (%). A signed act is a document, and deleting the job would take it. Clear the signature first if it really has to go.',
      n, nums
      using errcode = 'foreign_key_violation';
  end if;
  return old;
end $$;

drop trigger if exists projects_keep_signed_acts on public.projects;
create trigger projects_keep_signed_acts
  before delete on public.projects
  for each row execute function public.guard_signed_acts();


-- The helper is not an RPC and nothing outside the database calls it. The
-- standing step from migrate-harden.sql, stated rather than assumed.
revoke execute on all functions in schema public from public, anon;
revoke execute on function public.guard_signed_acts() from authenticated;


-- ============================================================
-- CHECK IT LANDED
-- ============================================================
do $$
declare
  pid  uuid;
  aid  uuid;
  ok   boolean := false;
  png  text := 'data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mP8z8BQDwAEhQGAhKmMIQAAAABJRU5ErkJggg==';
begin
  if not exists (select 1 from pg_trigger t join pg_class c on c.oid = t.tgrelid
                  join pg_namespace n on n.oid = c.relnamespace
                 where n.nspname = 'public' and c.relname = 'projects'
                   and t.tgname = 'projects_keep_signed_acts') then
    raise exception 'the trigger is not there';
  end if;

  -- a job with a DRAFT act still deletes, and takes the draft with it
  insert into public.projects (data) values ('{"card":{"projectId":"__G1__"}}'::jsonb)
    returning id into pid;
  insert into public.acts (project_id, number) values (pid, '__G1__/01');
  delete from public.projects where id = pid;
  if exists (select 1 from public.acts where number = '__G1__/01') then
    raise exception 'the draft act survived its project';
  end if;

  -- a job with a SIGNED act refuses
  insert into public.projects (data) values ('{"card":{"projectId":"__G2__"}}'::jsonb)
    returning id into pid;
  insert into public.acts (project_id, number, signature, signed_at)
    values (pid, '__G2__/01', png, now()) returning id into aid;
  begin
    delete from public.projects where id = pid;
  exception when foreign_key_violation then ok := true;
  end;
  if not ok then raise exception 'a project with a signed act was deleted'; end if;
  if not exists (select 1 from public.acts where id = aid) then
    raise exception 'the signed act is gone'; end if;

  -- and it deletes once the signature is off
  update public.acts set signature = null, signed_at = null where id = aid;
  delete from public.projects where id = pid;
  if exists (select 1 from public.projects where data->'card'->>'projectId' = '__G2__') then
    raise exception 'the project survived after the signature came off';
  end if;

  raise notice 'seventh pass OK: drafts go with the job, documents do not';
end $$;
