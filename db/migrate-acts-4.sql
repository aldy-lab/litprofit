-- ============================================================
-- ACTS, FOURTH PASS: the number is the server's to give
-- ============================================================
-- Two people made an act on the same job thirteen seconds apart and both got
-- DEMO-03/03. Neither did anything wrong: the app suggests the next free
-- number from what that browser knows, and neither browser had heard of the
-- other's act yet. There is no arrangement of client-side cleverness that
-- fixes this -- two devices out of contact cannot agree on a number -- so the
-- number stops being something a browser decides.
--
-- The app still suggests one, because a fitter typing an act wants to see it
-- before he saves. If the suggestion is taken by the time it arrives, the
-- server picks the next free one and returns it, and the screen updates to
-- what was actually stored.
--
-- Requires migrate-acts-3.sql. SAFE TO RUN MORE THAN ONCE.
--
-- ------------------------------------------------------------
-- WHY A UNIQUE INDEX AND NOT JUST THE LOOKUP
-- ------------------------------------------------------------
-- Because "find the next free number, then insert it" is two statements, and
-- two sessions can run the first before either runs the second. The lookup
-- makes the common case tidy; the index is what makes it true. The insert
-- retries against a fresh lookup when the index refuses it.
-- ============================================================

-- ------------------------------------------------------------
-- THE DUPLICATES THAT ARE ALREADY THERE
-- ------------------------------------------------------------
-- The index cannot be created while they exist. A SIGNED act is never
-- touched: somebody put their name under a document bearing that number, and
-- renaming it afterwards would make the paper in the customer's folder stop
-- matching the record. Where every copy is signed, the migration stops and
-- says so rather than choosing for you.
do $$
declare
  d record;
  keep uuid;
begin
  for d in
    select project_id, number
      from public.acts
     where number <> ''
     group by project_id, number
    having count(*) > 1
  loop
    -- the one that keeps the number: the signed one, else the oldest
    select id into keep from public.acts
     where project_id is not distinct from d.project_id and number = d.number
     order by (signature is not null) desc, created_at asc
     limit 1;

    if (select count(*) from public.acts
         where project_id is not distinct from d.project_id
           and number = d.number and signature is not null) > 1 then
      raise exception
        'Two signed acts both numbered % on the same job. That has to be settled by hand.',
        d.number;
    end if;

    update public.acts a set number = a.number || '-dup'
     where a.project_id is not distinct from d.project_id
       and a.number = d.number and a.id <> keep;

    raise notice 'renumbered % duplicate(s) of %',
      (select count(*) from public.acts
        where project_id is not distinct from d.project_id
          and number = d.number || '-dup'), d.number;
  end loop;
end $$;

-- Partial, because an act may legitimately have no number yet and empty
-- strings would otherwise collide with each other.
create unique index if not exists acts_number_uniq
  on public.acts (project_id, number) where number <> '';


-- ------------------------------------------------------------
-- THE NEXT FREE ONE
-- ------------------------------------------------------------
-- Keeps the stem the caller asked for -- PRJ-014/07 has the stem PRJ-014 --
-- and finds the lowest free two-digit suffix under it. A company that numbers
-- its acts some other way still gets its own number back untouched whenever
-- that number is free, which is every time but this one.
create or replace function public.next_act_number(p_project uuid, p_wanted text)
returns text
language plpgsql stable security definer set search_path = ''
as $$
declare
  stem text;
  n    int := 1;
  try  text;
begin
  if coalesce(p_wanted, '') = '' then return ''; end if;
  if not exists (select 1 from public.acts
                  where project_id is not distinct from p_project
                    and number = p_wanted) then
    return p_wanted;
  end if;

  stem := regexp_replace(p_wanted, '/[0-9]+$', '');
  loop
    try := stem || '/' || lpad(n::text, 2, '0');
    exit when not exists (select 1 from public.acts
                           where project_id is not distinct from p_project
                             and number = try);
    n := n + 1;
    -- A job with a thousand acts is not a numbering problem any more. Rather
    -- than spin, hand back something unmistakably unique and let a human see
    -- it and ask what happened.
    if n > 999 then
      return p_wanted || '-' || substr(replace(gen_random_uuid()::text, '-', ''), 1, 4);
    end if;
  end loop;
  return try;
end $$;


create or replace function public.create_act(p_row jsonb)
returns setof public.acts_v
language plpgsql security definer set search_path = ''
as $$
declare
  new_id uuid;
  v_pid  uuid := nullif(p_row->>'project_id','')::uuid;
  v_num  text;
  i      int;
begin
  if auth.uid() is null then
    raise exception 'not permitted' using errcode = '42501';
  end if;

  v_num := public.next_act_number(v_pid, coalesce(p_row->>'number',''));

  -- Five attempts, because the only thing that can make this fail is another
  -- session taking the number between the lookup and the insert, and that
  -- cannot keep happening.
  for i in 1..5 loop
    begin
      insert into public.acts (project_id, number, act_date, customer, imo, object,
                               project_ref, lines, rep_name, note)
      values (v_pid, v_num,
              coalesce(nullif(p_row->>'act_date','')::date, current_date),
              coalesce(p_row->>'customer',''), coalesce(p_row->>'imo',''),
              coalesce(p_row->>'object',''), coalesce(p_row->>'project_ref',''),
              coalesce(p_row->'lines', '[]'::jsonb),
              coalesce(p_row->>'rep_name',''), p_row->>'note')
      returning id into new_id;
      exit;
    exception when unique_violation then
      v_num := public.next_act_number(v_pid, v_num);
      if i = 5 then raise; end if;
    end;
  end loop;

  return query select * from public.acts_v where id = new_id;
end $$;


-- ------------------------------------------------------------
-- AND WHEN SOMEBODY TYPES A NUMBER THAT IS TAKEN
-- ------------------------------------------------------------
-- Not renumbered silently. A number the server chose because nobody had asked
-- for one is one thing; quietly changing a number somebody deliberately typed
-- is another, and they would find out from the paper.
create or replace function public.save_act(p_id uuid, p_rev bigint, p_row jsonb)
returns setof public.acts_v
language plpgsql security definer set search_path = ''
as $$
declare cur public.acts%rowtype;
begin
  if auth.uid() is null then
    raise exception 'not permitted' using errcode = '42501';
  end if;
  select * into cur from public.acts where id = p_id;
  if not found then return; end if;
  if p_rev is not null and cur.rev <> p_rev then return; end if;

  if cur.signature is not null then
    raise exception 'act is signed' using errcode = '42501';
  end if;

  begin
    update public.acts set
      number      = coalesce(p_row->>'number', number),
      act_date    = coalesce(nullif(p_row->>'act_date','')::date, act_date),
      customer    = coalesce(p_row->>'customer', customer),
      imo         = coalesce(p_row->>'imo', imo),
      object      = coalesce(p_row->>'object', object),
      project_ref = coalesce(p_row->>'project_ref', project_ref),
      lines       = coalesce(p_row->'lines', lines),
      rep_name    = coalesce(p_row->>'rep_name', rep_name),
      note        = p_row->>'note',
      rev = rev + 1, updated_at = now(), updated_by = auth.uid()
    where id = p_id;
  exception when unique_violation then
    raise exception 'act number already used on this job' using errcode = '23505';
  end;

  return query select * from public.acts_v where id = p_id;
end $$;


-- ------------------------------------------------------------
-- CHECK IT LANDED
-- ------------------------------------------------------------
do $$
declare n int;
begin
  select count(*) into n from pg_indexes
   where schemaname = 'public' and indexname = 'acts_number_uniq';
  if n <> 1 then raise exception 'the unique index is not there'; end if;

  select count(*) into n from (
    select 1 from public.acts where number <> ''
     group by project_id, number having count(*) > 1) x;
  if n <> 0 then raise exception '% duplicate act numbers survived', n; end if;

  select count(*) into n from pg_proc p join pg_namespace ns on ns.oid = p.pronamespace
   where ns.nspname = 'public' and p.proname = 'next_act_number';
  if n <> 1 then raise exception 'next_act_number missing'; end if;

  raise notice 'acts fourth pass OK: one number per act per job, and the server hands it out';
end $$;
