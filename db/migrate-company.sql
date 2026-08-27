-- ============================================================
-- COMPANY: people, fixed costs, and what they add up to
-- ============================================================
-- The calculator knew what money came IN -- projects and enquiries -- and
-- nothing at all about what goes OUT. Every margin in it was therefore a
-- guess: cost was whatever somebody typed. This adds the other half.
--
-- SAFE TO RUN MORE THAN ONCE. `create trigger` and `create policy` have no
-- `if not exists` form, so both are dropped first. Running schema.sql against
-- a live database once reported success on nothing for exactly that reason.
--
-- ------------------------------------------------------------
-- WHO MAY SEE WHAT, AND WHY IT IS NOT sees_money()
-- ------------------------------------------------------------
-- sees_money() is admin OR manager, and it is right for prices, costs and
-- margins: a manager has to price a job. It is wrong for pay. A manager
-- reading a colleague's salary is a different kind of disclosure, and once it
-- has happened it cannot be undone by tightening the rule afterwards.
--
-- So payroll gets its own gate, sees_payroll(), and it is the owner alone.
-- The people table is closed by row level security with no policy on it, so
-- there is no path to the rows except through functions that check.
--
-- The COMPANY TOTAL is gated the same way, deliberately. A monthly payroll
-- figure beside a headcount is an average salary, and in a company this size
-- that is close enough to individual pay to matter. If the owner decides a
-- manager should see the break-even line, changing sees_payroll() to include
-- 'manager' in company_burn() alone is a one-line change -- but it should be
-- his decision, made once, on purpose.
-- ============================================================

create or replace function public.sees_payroll()
returns boolean
language sql stable
security definer set search_path = ''
as $$ select public.my_role() = 'admin' $$;


-- ------------------------------------------------------------
-- PEOPLE
-- ------------------------------------------------------------
-- monthly_cost is the FULL cost to the company: gross pay plus employer
-- taxes plus any fixed allowance. Not take-home. Everything downstream is
-- only as true as this one number, so the app labels it in those words.
--
-- hours_month is the productive hours a month, and it is the number people
-- get wrong. 168 is a month of calendar hours and it is not what anybody
-- sells: holidays, sick days, travel to the vessel and workshop downtime are
-- all paid for and none of them is billable. 130 is a realistic default for a
-- yard; the owner should set his own once he has a month of timesheets.
--
-- start_date / end_date are how a pay rise is recorded: end the old row,
-- start a new one. That keeps last year's burn last year's burn instead of
-- rewriting history every time somebody gets a raise.
create table if not exists public.people (
  id            uuid primary key default gen_random_uuid(),
  name          text not null,
  job_title     text not null default '',
  department    text not null default '',
  monthly_cost  numeric(12,2) not null default 0,
  hours_month   numeric(6,1) not null default 130,
  start_date    date,
  end_date      date,
  note          text,
  rev           bigint not null default 1,
  created_at    timestamptz not null default now(),
  created_by    uuid references auth.users(id) default auth.uid(),
  updated_at    timestamptz not null default now(),
  updated_by    uuid references auth.users(id) default auth.uid()
);

create index if not exists people_dept_idx  on public.people (department);
create index if not exists people_dates_idx on public.people (start_date, end_date);
alter table public.people enable row level security;


-- ------------------------------------------------------------
-- FIXED MONTHLY COSTS
-- ------------------------------------------------------------
-- Dated for the same reason people are: a lease that ended in March must not
-- appear in April's burn, and must not disappear from February's.
create table if not exists public.overheads (
  id            uuid primary key default gen_random_uuid(),
  name          text not null,
  category      text not null default 'other'
                check (category in ('premises', 'vehicles', 'insurance',
                                    'software', 'utilities', 'finance',
                                    'tools', 'other')),
  amount_month  numeric(12,2) not null default 0,
  start_date    date,
  end_date      date,
  note          text,
  rev           bigint not null default 1,
  created_at    timestamptz not null default now(),
  created_by    uuid references auth.users(id) default auth.uid(),
  updated_at    timestamptz not null default now(),
  updated_by    uuid references auth.users(id) default auth.uid()
);

create index if not exists overheads_cat_idx   on public.overheads (category);
create index if not exists overheads_dates_idx on public.overheads (start_date, end_date);
alter table public.overheads enable row level security;


-- ------------------------------------------------------------
-- VIEWS
-- ------------------------------------------------------------
-- The save_ and create_ functions further down return `setof public.people_v`,
-- which makes them DEPEND on the view. So on a second run `drop view` fails
-- with "cannot drop view people_v because other objects depend on it" and
-- everything after it in this file never runs -- the script reports an error
-- and leaves the database half migrated. Found by running this file twice,
-- which is the only way it can be found.
--
-- Dropped by name rather than with CASCADE: cascade would also remove
-- anything else that had come to depend on the view, and would not say what.
-- Each one is recreated below, in this same file.
drop function if exists public.save_person(uuid, bigint, jsonb);
drop function if exists public.create_person(jsonb);
drop function if exists public.save_overhead(uuid, bigint, jsonb);
drop function if exists public.create_overhead(jsonb);

-- hour_cost is derived, never stored. A stored copy goes stale the moment
-- either input changes, and nobody remembers to recompute it.
drop view if exists public.people_v;
create view public.people_v as
select
  p.id, p.name, p.job_title, p.department,
  p.monthly_cost, p.hours_month,
  case when p.hours_month > 0
       then round(p.monthly_cost / p.hours_month, 2) end as hour_cost,
  p.start_date, p.end_date,
  (p.end_date is null or p.end_date >= current_date) as active,
  p.note, p.rev, p.created_at, p.updated_at, p.updated_by
from public.people p
where public.sees_payroll();

drop view if exists public.overheads_v;
create view public.overheads_v as
select
  o.id, o.name, o.category, o.amount_month,
  o.start_date, o.end_date,
  (o.end_date is null or o.end_date >= current_date) as active,
  o.note, o.rev, o.created_at, o.updated_at, o.updated_by
from public.overheads o
where public.sees_money();


-- ------------------------------------------------------------
-- WHAT IT ADDS UP TO
-- ------------------------------------------------------------
-- One number the owner has never had: what the company spends to exist for a
-- month, before a single job is sold. Everything useful hangs off it -- the
-- break-even line, the runway, and whether a job priced at cost plus ten per
-- cent is worth taking.
create or replace function public.company_burn(p_on date default current_date)
returns table (
  headcount     integer,
  payroll       numeric,
  overheads     numeric,
  burn          numeric,
  hour_cost_avg numeric
)
language plpgsql stable
security definer set search_path = ''
as $$
begin
  -- No rows rather than zeroes. Written first as a set of `where
  -- sees_payroll()` subqueries, it returned headcount 0, payroll 0, burn 0 to
  -- a manager -- which does not read as "you may not see this", it reads as
  -- "the company spends nothing", and it would have been believed. An empty
  -- result the app renders as a dash; a zero it renders as a fact.
  if not public.sees_payroll() then
    return;
  end if;

  return query
  with staff as (
    select p.monthly_cost, p.hours_month from public.people p
     where (p.start_date is null or p.start_date <= p_on)
       and (p.end_date   is null or p.end_date   >= p_on)
  ), fixed as (
    select o.amount_month from public.overheads o
     where (o.start_date is null or o.start_date <= p_on)
       and (o.end_date   is null or o.end_date   >= p_on)
  )
  select
    (select count(*)::int from staff),
    (select coalesce(sum(monthly_cost), 0) from staff),
    (select coalesce(sum(amount_month), 0) from fixed),
    (select coalesce(sum(monthly_cost), 0) from staff)
      + (select coalesce(sum(amount_month), 0) from fixed),
    (select round(avg(monthly_cost / nullif(hours_month, 0)), 2) from staff);
end $$;


-- ------------------------------------------------------------
-- WRITES
-- ------------------------------------------------------------
-- Same shape as save_project and save_enquiry: the caller states the revision
-- it read, the update matches on it and bumps it, and a stale save matches no
-- row and returns empty, which the app reports as a conflict rather than
-- quietly overwriting somebody else.
--
-- `returns setof <view>` and not `returns <view>`: PostgREST gives an object
-- for the second and an array for the first, and the app reads rows[0]. When
-- save_enquiry returned an object every successful save was reported as a
-- conflict, and nothing errored anywhere.
create or replace function public.save_person(p_id uuid, p_rev bigint, p_row jsonb)
returns setof public.people_v
language plpgsql security definer set search_path = ''
as $$
declare cur public.people%rowtype;
begin
  if not public.sees_payroll() then
    raise exception 'not permitted' using errcode = '42501';
  end if;
  select * into cur from public.people where id = p_id;
  if not found then return; end if;
  if p_rev is not null and cur.rev <> p_rev then return; end if;

  update public.people set
    name         = coalesce(p_row->>'name', name),
    job_title    = coalesce(p_row->>'job_title', ''),
    department   = coalesce(p_row->>'department', ''),
    monthly_cost = coalesce((p_row->>'monthly_cost')::numeric, 0),
    hours_month  = coalesce((p_row->>'hours_month')::numeric, 130),
    start_date   = nullif(p_row->>'start_date', '')::date,
    end_date     = nullif(p_row->>'end_date', '')::date,
    note         = p_row->>'note',
    rev = rev + 1, updated_at = now(), updated_by = auth.uid()
  where id = p_id;

  return query select * from public.people_v where id = p_id;
end $$;

create or replace function public.create_person(p_row jsonb)
returns setof public.people_v
language plpgsql security definer set search_path = ''
as $$
declare new_id uuid;
begin
  if not public.sees_payroll() then
    raise exception 'not permitted' using errcode = '42501';
  end if;
  insert into public.people (name, job_title, department, monthly_cost,
                             hours_month, start_date, end_date, note)
  values (coalesce(p_row->>'name', ''), coalesce(p_row->>'job_title', ''),
          coalesce(p_row->>'department', ''),
          coalesce((p_row->>'monthly_cost')::numeric, 0),
          coalesce((p_row->>'hours_month')::numeric, 130),
          nullif(p_row->>'start_date', '')::date,
          nullif(p_row->>'end_date', '')::date,
          p_row->>'note')
  returning id into new_id;
  return query select * from public.people_v where id = new_id;
end $$;

create or replace function public.delete_person(p_id uuid)
returns void
language plpgsql security definer set search_path = ''
as $$
begin
  if not public.sees_payroll() then
    raise exception 'not permitted' using errcode = '42501';
  end if;
  delete from public.people where id = p_id;
end $$;


create or replace function public.save_overhead(p_id uuid, p_rev bigint, p_row jsonb)
returns setof public.overheads_v
language plpgsql security definer set search_path = ''
as $$
declare cur public.overheads%rowtype;
begin
  if not public.sees_money() then
    raise exception 'not permitted' using errcode = '42501';
  end if;
  select * into cur from public.overheads where id = p_id;
  if not found then return; end if;
  if p_rev is not null and cur.rev <> p_rev then return; end if;

  update public.overheads set
    name         = coalesce(p_row->>'name', name),
    category     = coalesce(p_row->>'category', 'other'),
    amount_month = coalesce((p_row->>'amount_month')::numeric, 0),
    start_date   = nullif(p_row->>'start_date', '')::date,
    end_date     = nullif(p_row->>'end_date', '')::date,
    note         = p_row->>'note',
    rev = rev + 1, updated_at = now(), updated_by = auth.uid()
  where id = p_id;

  return query select * from public.overheads_v where id = p_id;
end $$;

create or replace function public.create_overhead(p_row jsonb)
returns setof public.overheads_v
language plpgsql security definer set search_path = ''
as $$
declare new_id uuid;
begin
  if not public.sees_money() then
    raise exception 'not permitted' using errcode = '42501';
  end if;
  insert into public.overheads (name, category, amount_month, start_date, end_date, note)
  values (coalesce(p_row->>'name', ''), coalesce(p_row->>'category', 'other'),
          coalesce((p_row->>'amount_month')::numeric, 0),
          nullif(p_row->>'start_date', '')::date,
          nullif(p_row->>'end_date', '')::date,
          p_row->>'note')
  returning id into new_id;
  return query select * from public.overheads_v where id = new_id;
end $$;

create or replace function public.delete_overhead(p_id uuid)
returns void
language plpgsql security definer set search_path = ''
as $$
begin
  if not public.sees_money() then
    raise exception 'not permitted' using errcode = '42501';
  end if;
  delete from public.overheads where id = p_id;
end $$;


-- ------------------------------------------------------------
-- AUDIT TRAIL
-- ------------------------------------------------------------
-- A pay rise with no record of who made it and when is the one change in this
-- database that most wants a record of who made it and when.
create table if not exists public.company_history (
  id         bigserial primary key,
  entity     text not null check (entity in ('person', 'overhead')),
  row_id     uuid not null,
  label      text,
  field      text not null,
  was        text,
  now        text,
  changed_at timestamptz not null default now(),
  changed_by uuid references auth.users(id) default auth.uid()
);
create index if not exists company_history_idx on public.company_history (changed_at desc);
alter table public.company_history enable row level security;

create or replace function public.company_track()
returns trigger
language plpgsql security definer set search_path = ''
as $$
declare
  ent text := case tg_table_name when 'people' then 'person' else 'overhead' end;
  lbl text := coalesce(new.name, old.name);
  f   text;
  a   text;
  b   text;
begin
  if tg_op = 'INSERT' then
    insert into public.company_history (entity, row_id, label, field, was, now)
    values (ent, new.id, lbl, 'created', null, lbl);
    return new;
  end if;

  foreach f in array (case when ent = 'person'
    then array['name','job_title','department','monthly_cost','hours_month','start_date','end_date']
    else array['name','category','amount_month','start_date','end_date'] end)
  loop
    a := to_jsonb(old) ->> f;
    b := to_jsonb(new) ->> f;
    if a is distinct from b then
      insert into public.company_history (entity, row_id, label, field, was, now)
      values (ent, new.id, lbl, f, a, b);
    end if;
  end loop;
  return new;
end $$;

drop trigger if exists people_track on public.people;
create trigger people_track after insert or update on public.people
  for each row execute function public.company_track();

drop trigger if exists overheads_track on public.overheads;
create trigger overheads_track after insert or update on public.overheads
  for each row execute function public.company_track();

drop view if exists public.company_history_v;
create view public.company_history_v as
select h.id, h.entity, h.row_id, h.label, h.field, h.was, h.now,
       h.changed_at, coalesce(pr.name, '—') as changed_by_name
from public.company_history h
left join public.profiles pr on pr.id = h.changed_by
where public.sees_payroll()
order by h.changed_at desc
limit 200;


-- ------------------------------------------------------------
-- CHECK IT LANDED
-- ------------------------------------------------------------
-- Run this after the script. Three tables, two views, seven functions.
-- Anything less and something above aborted without saying so.
do $$
declare n int;
begin
  select count(*) into n from information_schema.tables
   where table_schema = 'public' and table_name in ('people','overheads','company_history');
  if n <> 3 then raise exception 'expected 3 tables, found %', n; end if;

  select count(*) into n from information_schema.views
   where table_schema = 'public' and table_name in ('people_v','overheads_v','company_history_v');
  if n <> 3 then raise exception 'expected 3 views, found %', n; end if;

  select count(*) into n from pg_proc p join pg_namespace ns on ns.oid = p.pronamespace
   where ns.nspname = 'public'
     and p.proname in ('sees_payroll','company_burn','save_person','create_person',
                       'delete_person','save_overhead','create_overhead','delete_overhead');
  if n < 8 then raise exception 'expected 8 functions, found %', n; end if;

  raise notice 'company migration OK: 3 tables, 3 views, 8 functions';
end $$;
