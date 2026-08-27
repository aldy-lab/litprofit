-- ============================================================
-- PAYROLL: what is agreed, what it costs, and the gap between
-- ============================================================
-- The people table asked for one number -- "full monthly cost to the company"
-- -- and nobody knows that number. What an owner knows is the salary he
-- agreed, and he is then expected to do the loading in his head every time he
-- types a row. So the input becomes the gross salary, and the employer's
-- contribution and the total cost are derived from it.
--
-- SAFE TO RUN MORE THAN ONCE. Requires migrate-company.sql to have run first.
--
-- ------------------------------------------------------------
-- THE RATES, AND WHERE THEY CAME FROM
-- ------------------------------------------------------------
-- Lithuania, checked August 2026. The employer's Sodra contribution sits ON
-- TOP of gross pay:
--
--   permanent (neterminuota) contract   1.77 %
--   fixed-term (terminuota) contract    2.49 %
--
-- Sources: teamed.global country guide for Lithuania, and Work in Lithuania's
-- 2026 tax guide, which agree.
--
-- What the EMPLOYEE pays comes out of the same gross and is not the company's
-- cost: Sodra 19.5 % (health insurance 6.98 % of it) plus GPM at 20 / 25 /
-- 32 % by band. Those are deliberately NOT modelled here. Net pay also needs
-- the NPD allowance, which is a formula that changes every year, and a net
-- figure that is quietly a year out of date is worse on an owner's screen
-- than no net figure at all. This file computes only what the company pays.
--
-- THESE RATES CHANGE BY LAW. They are in one function, on purpose. When they
-- change, edit employer_rate() and re-run this file: every stored cost is
-- recomputed from the gross salaries, so nothing has to be retyped.
-- ============================================================

alter table public.people add column if not exists gross_salary numeric(12,2);
alter table public.people add column if not exists contract text not null default 'permanent';

do $$
begin
  if not exists (select 1 from pg_constraint where conname = 'people_contract_chk') then
    alter table public.people add constraint people_contract_chk
      check (contract in ('permanent', 'fixed'));
  end if;
end $$;


create or replace function public.employer_rate(p_contract text)
returns numeric
language sql immutable
as $$ select case when p_contract = 'fixed' then 0.0249 else 0.0177 end $$;


-- Backfill. Existing rows carry a full cost and no gross, so the gross is
-- recovered by dividing it back out -- which is exact, because the full cost
-- was only ever gross times the rate in somebody's head.
update public.people
   set gross_salary = round(monthly_cost / (1 + public.employer_rate(contract)), 2)
 where gross_salary is null;

-- And from here the full cost is never typed again: it is the gross plus the
-- contribution, recomputed on every write and by this line whenever the rates
-- move.
update public.people
   set monthly_cost = round(coalesce(gross_salary, 0) * (1 + public.employer_rate(contract)), 2);


-- ------------------------------------------------------------
-- THE VIEW
-- ------------------------------------------------------------
drop function if exists public.save_person(uuid, bigint, jsonb);
drop function if exists public.create_person(jsonb);
drop view if exists public.people_v;

create view public.people_v as
select
  p.id, p.name, p.job_title, p.department,
  p.contract,
  p.gross_salary,
  -- what the company pays on top, stated as its own number rather than left
  -- to be inferred from the difference between two others
  round(coalesce(p.gross_salary, 0) * public.employer_rate(p.contract), 2) as employer_cost,
  p.monthly_cost,
  p.hours_month,
  case when p.hours_month > 0
       then round(p.monthly_cost / p.hours_month, 2) end as hour_cost,
  p.start_date, p.end_date,
  (p.end_date is null or p.end_date >= current_date) as active,
  p.note, p.rev, p.created_at, p.updated_at, p.updated_by
from public.people p
where public.sees_payroll();


-- ------------------------------------------------------------
-- WRITES
-- ------------------------------------------------------------
-- monthly_cost is no longer accepted from the caller. It is derived, and a
-- derived value that can also be posted is a value that will eventually
-- disagree with what it is derived from.
create or replace function public.save_person(p_id uuid, p_rev bigint, p_row jsonb)
returns setof public.people_v
language plpgsql security definer set search_path = ''
as $$
declare
  cur public.people%rowtype;
  g   numeric;
  c   text;
begin
  if not public.sees_payroll() then
    raise exception 'not permitted' using errcode = '42501';
  end if;
  select * into cur from public.people where id = p_id;
  if not found then return; end if;
  if p_rev is not null and cur.rev <> p_rev then return; end if;

  g := coalesce((p_row->>'gross_salary')::numeric, 0);
  c := case when p_row->>'contract' = 'fixed' then 'fixed' else 'permanent' end;

  update public.people set
    name         = coalesce(p_row->>'name', name),
    job_title    = coalesce(p_row->>'job_title', ''),
    department   = coalesce(p_row->>'department', ''),
    contract     = c,
    gross_salary = g,
    monthly_cost = round(g * (1 + public.employer_rate(c)), 2),
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
declare
  new_id uuid;
  g numeric;
  c text;
begin
  if not public.sees_payroll() then
    raise exception 'not permitted' using errcode = '42501';
  end if;
  g := coalesce((p_row->>'gross_salary')::numeric, 0);
  c := case when p_row->>'contract' = 'fixed' then 'fixed' else 'permanent' end;

  insert into public.people (name, job_title, department, contract, gross_salary,
                             monthly_cost, hours_month, start_date, end_date, note)
  values (coalesce(p_row->>'name', ''), coalesce(p_row->>'job_title', ''),
          coalesce(p_row->>'department', ''), c, g,
          round(g * (1 + public.employer_rate(c)), 2),
          coalesce((p_row->>'hours_month')::numeric, 130),
          nullif(p_row->>'start_date', '')::date,
          nullif(p_row->>'end_date', '')::date,
          p_row->>'note')
  returning id into new_id;
  return query select * from public.people_v where id = new_id;
end $$;


-- The audit trail follows the fields that now exist. A change of contract
-- type moves the cost without touching the salary, which is exactly the sort
-- of change that wants a record.
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
    then array['name','job_title','department','contract','gross_salary',
               'monthly_cost','hours_month','start_date','end_date']
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


-- ------------------------------------------------------------
-- CHECK IT LANDED
-- ------------------------------------------------------------
do $$
declare
  n int;
  g numeric;
  c numeric;
begin
  select count(*) into n from information_schema.columns
   where table_schema = 'public' and table_name = 'people'
     and column_name in ('gross_salary', 'contract');
  if n <> 2 then raise exception 'expected 2 new columns, found %', n; end if;

  select count(*) into n from information_schema.columns
   where table_schema = 'public' and table_name = 'people_v'
     and column_name in ('gross_salary', 'employer_cost', 'contract');
  if n <> 3 then raise exception 'the view is missing the derived columns'; end if;

  -- the arithmetic itself, on both contract types
  if round(1000 * (1 + public.employer_rate('permanent')), 2) <> 1017.70 then
    raise exception 'permanent rate is wrong';
  end if;
  if round(1000 * (1 + public.employer_rate('fixed')), 2) <> 1024.90 then
    raise exception 'fixed-term rate is wrong';
  end if;

  raise notice 'payroll migration OK: gross in, employer cost and total derived';
end $$;
