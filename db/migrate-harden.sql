-- ============================================================
-- HARDENING: the doors that are shut but not locked
-- ============================================================
-- Eleven people now have accounts. Nothing in this file fixes a live hole --
-- every one of these was checked by impersonating anon, a fitter and an
-- owner, and every one already refused. What they are is defence that was
-- resting on ONE thing being true, where it can rest on two.
--
-- SAFE TO RUN MORE THAN ONCE.
--
-- ------------------------------------------------------------
-- 1. SIX FUNCTIONS WITHOUT A FIXED SEARCH PATH
-- ------------------------------------------------------------
-- Every other function in this schema pins `search_path = ''`. These six
-- predate that habit. All are SECURITY INVOKER, so they run with the
-- caller's own rights and the exposure is small -- but four of them are
-- TRIGGER functions, which run on somebody else's write, and a trigger that
-- resolves an unqualified name through a search path it does not control is
-- the shape of the problem whether or not this schema can be reached today.
--
-- The bodies do not need rewriting, which is the only reason this is cheap:
-- checked one at a time, every name they use is a parameter, a keyword, or
-- something in pg_catalog, which stays on the path even when it is empty.
-- auth.uid() in sync_project_columns is already qualified.
--
-- What it costs: a SQL function carrying a SET clause can no longer be
-- inlined, so employer_rate and enquiry_days_unquoted become a real call per
-- row in people_v and enquiries_v. At one payroll row and two hundred
-- enquiries that is not measurable, and it is worth saying rather than
-- discovering.
-- ------------------------------------------------------------
alter function public.employer_rate(text)                         set search_path = '';
alter function public.enquiry_days_unquoted(boolean, date, text)  set search_path = '';
alter function public.guard_locked_project()                      set search_path = '';
alter function public.restore_rebills(jsonb, jsonb, text, text[]) set search_path = '';
alter function public.strip_money(jsonb)                          set search_path = '';
alter function public.sync_project_columns()                      set search_path = '';


-- ------------------------------------------------------------
-- 2. TABLE PRIVILEGES NOBODY USES
-- ------------------------------------------------------------
-- acts, act_fields, company_history, documents, overheads and people still
-- carried the default Supabase grants: SELECT, INSERT, UPDATE, DELETE and
-- TRUNCATE, to anon AND authenticated. projects and enquiries had theirs
-- taken away in an earlier pass; these were missed.
--
-- They granted nothing, because every one of those tables has row level
-- security on with no policies at all, which denies everything. That is one
-- thing being true. The day somebody adds a policy to one of these tables
-- for some unrelated reason -- and the reason will be a good one -- the
-- grant behind it wakes up, and it includes DELETE and TRUNCATE for a role
-- that is not even signed in.
--
-- Nothing reads these tables directly. profiles is deliberately NOT in this
-- list: the app reads it to say who last touched a row, and its own policies
-- and role guard are what hold it.
-- ------------------------------------------------------------
revoke all on public.acts            from anon, authenticated;
revoke all on public.act_fields      from anon, authenticated;
revoke all on public.company_history from anon, authenticated;
revoke all on public.documents       from anon, authenticated;
revoke all on public.overheads       from anon, authenticated;
revoke all on public.people          from anon, authenticated;


-- ------------------------------------------------------------
-- 3. NOBODY UNAUTHENTICATED CALLS ANYTHING
-- ------------------------------------------------------------
-- Thirty-two SECURITY DEFINER functions were callable by `anon` over
-- /rest/v1/rpc/. Every one refuses a caller with no auth.uid() on its first
-- line, so this changes nothing that happens; it changes what happens if one
-- of those first lines is ever dropped in an edit.
--
-- WHY THIS REVOKES FROM `public` AS WELL AS FROM `anon`
-- ----------------------------------------------------
-- Because revoking from anon alone did nothing, which the check at the
-- bottom caught on the first attempt: thirty-nine functions were still
-- executable afterwards. Postgres grants EXECUTE on every new function to
-- PUBLIC automatically, so anon held the privilege twice -- once explicitly
-- from Supabase's defaults, once inherited from a grant nobody issued.
-- ------------------------------------------------------------
revoke execute on all functions in schema public from public, anon;
grant  execute on all functions in schema public to authenticated, service_role;
alter default privileges in schema public revoke execute on functions from public, anon;
alter default privileges in schema public grant execute on functions to authenticated, service_role;


-- ------------------------------------------------------------
-- 4. SIGNED IN IS NOT THE SAME AS ALLOWED
-- ------------------------------------------------------------
-- The application calls twenty-two RPCs. The list came out of the source --
-- `grep -o "rpc/[a-z_]*"` -- and not out of memory. Everything else in this
-- schema is a trigger function or an internal helper that nothing outside
-- the database has business calling.
--
-- THE THREE THAT STAY BEYOND THOSE TWENTY-TWO
-- -------------------------------------------
-- sees_money(), sees_payroll() and my_role(). The four storage policies on
-- the documents bucket are expressions containing public.sees_money(), and
-- an RLS policy is evaluated as the CURRENT user, not as its author. Revoke
-- it and every upload and every signed URL stops working -- a failure that
-- shows up as a file that will not open, found by a person and not by an
-- error. All three disclose only what the caller already knows about self.
-- ------------------------------------------------------------
do $$
declare
  keep text[] := array[
    'company_burn','create_act','create_document','create_enquiry',
    'create_overhead','create_person','create_project','delete_act',
    'delete_document','delete_enquiry','delete_overhead','delete_person',
    'delete_project','save_act','save_act_fields','save_document',
    'save_enquiry','save_overhead','save_person','save_project',
    'sign_act','unsign_act',
    'sees_money','sees_payroll','my_role'
  ];
  fn record;
begin
  for fn in
    select p.oid::regprocedure as sig
      from pg_proc p join pg_namespace ns on ns.oid = p.pronamespace
     where ns.nspname = 'public'
       and not (p.proname = any(keep))
       and has_function_privilege('authenticated', p.oid, 'EXECUTE')
  loop
    execute format('revoke execute on function %s from authenticated', fn.sig);
  end loop;
end $$;


-- ------------------------------------------------------------
-- 5. AND THE CORRECTION THAT COST: A VIEW DOES NOT LEND ITS PRIVILEGES
-- ------------------------------------------------------------
-- Step 4 broke reading projects_v, for everyone, immediately. The assumption
-- behind it was wrong in a way worth writing down: an owner-privileged view
-- checks the underlying TABLE permissions as the view's owner, but a
-- FUNCTION called inside that view is checked against the CURRENT user. So
-- strip_money -- which exists to hide revenue from a fitter -- is executed
-- BY the fitter.
--
-- Found by reading projects_v as a fitter one statement after the revoke,
-- which is the only reason it never reached anybody.
--
-- These three are granted back by that rule and not by name. restore_rebills,
-- check_act_fields and next_act_number stay revoked: they are called from
-- inside SECURITY DEFINER functions, where the current user IS the definer.
-- ------------------------------------------------------------
grant execute on function public.employer_rate(text)                        to authenticated;
grant execute on function public.enquiry_days_unquoted(boolean, date, text) to authenticated;
grant execute on function public.strip_money(jsonb)                         to authenticated;


-- ============================================================
-- CHECK IT LANDED
-- ============================================================
do $$
declare n int; bad text;
begin
  select count(*), string_agg(p.proname, ', ') into n, bad
    from pg_proc p join pg_namespace ns on ns.oid = p.pronamespace
   where ns.nspname = 'public' and p.prokind = 'f'
     and not exists (select 1 from unnest(coalesce(p.proconfig, '{}')) as cfg
                      where cfg like 'search_path=%');
  if n > 0 then
    raise exception '% function(s) still have a mutable search_path: %', n, bad;
  end if;

  select count(*), string_agg(distinct table_name, ', ') into n, bad
    from information_schema.role_table_grants
   where table_schema = 'public' and grantee in ('anon', 'authenticated')
     and table_name in ('acts','act_fields','company_history',
                        'documents','overheads','people');
  if n > 0 then raise exception 'grants survive on %', bad; end if;

  select count(*) into n from pg_proc p join pg_namespace ns on ns.oid = p.pronamespace
   where ns.nspname = 'public' and has_function_privilege('anon', p.oid, 'EXECUTE');
  if n > 0 then raise exception 'anon can still execute % function(s)', n; end if;

  -- everything the app calls, and everything the three roles need
  select count(*), string_agg(p.proname, ', ') into n, bad
    from pg_proc p join pg_namespace ns on ns.oid = p.pronamespace
   where ns.nspname = 'public'
     and p.proname in ('company_burn','create_act','create_document','create_enquiry',
        'create_overhead','create_person','create_project','delete_act',
        'delete_document','delete_enquiry','delete_overhead','delete_person',
        'delete_project','save_act','save_act_fields','save_document',
        'save_enquiry','save_overhead','save_person','save_project',
        'sign_act','unsign_act','sees_money','sees_payroll','my_role')
     and not has_function_privilege('authenticated', p.oid, 'EXECUTE');
  if n > 0 then raise exception 'the app lost EXECUTE on: %', bad; end if;

  -- nothing a view calls is unexecutable by whoever reads the view
  with fns as (
    select p.oid, p.proname
      from pg_proc p join pg_namespace ns on ns.oid = p.pronamespace
     where ns.nspname = 'public' and p.prokind = 'f'
       and not has_function_privilege('authenticated', p.oid, 'EXECUTE')
  ), views as (
    select c.relname, pg_get_viewdef(c.oid) as def
      from pg_class c join pg_namespace ns on ns.oid = c.relnamespace
     where ns.nspname = 'public' and c.relkind = 'v'
  )
  select count(*), string_agg(distinct f.proname, ', ') into n, bad
    from fns f join views v on v.def ~ ('\m' || f.proname || '\M');
  if n > 0 then
    raise exception 'a view calls something its readers cannot execute: %', bad;
  end if;

  -- and the internals are shut
  select count(*), string_agg(p.proname, ', ') into n, bad
    from pg_proc p join pg_namespace ns on ns.oid = p.pronamespace
   where ns.nspname = 'public'
     and p.proname in ('restore_rebills','check_act_fields','next_act_number',
                       'handle_new_user','guard_role_change','company_track',
                       'enquiry_track','record_project_history',
                       'sync_project_columns','guard_locked_project','document_totals')
     and has_function_privilege('authenticated', p.oid, 'EXECUTE');
  if n > 0 then raise exception 'still reachable from outside: %', bad; end if;

  select count(*) into n from information_schema.role_table_grants
   where table_schema='public' and table_name='profiles'
     and grantee='authenticated' and privilege_type='SELECT';
  if n <> 1 then raise exception 'authenticated lost SELECT on profiles'; end if;

  raise notice 'hardening OK: paths pinned, table grants gone, anon executes nothing, twenty-five names in';
end $$;


-- ============================================================
-- WHAT IS LEFT, AND WHY IT IS LEFT
-- ============================================================
-- The linter still reports two things about this schema. Both are the design
-- and not an oversight.
--
-- security_definer_view, ERROR, x10. Every *_v view runs with its owner's
-- privileges, so the caller's RLS does not apply -- the `where sees_money()`
-- inside each view is what gates it. The alternative is security_invoker
-- views plus a full set of RLS policies on the tables underneath, which is
-- a real architecture and a different one; switching halfway would give
-- every reader nothing at all, because those tables deny by default. It was
-- checked by impersonation instead: anon and a fitter get zero rows or a
-- refusal from every one of them.
--
-- rls_enabled_no_policy, INFO, x8. Deliberate. Deny-all is the policy; the
-- views and the RPCs are the only way in, and section 2 above is what makes
-- that true twice over.
--
-- One thing is NOT design and cannot be fixed from SQL:
-- auth_leaked_password_protection is off. With eleven accounts whose
-- passwords are their surnames, it is worth an afternoon:
-- Authentication -> Policies -> enable checking against HaveIBeenPwned.
-- ============================================================
