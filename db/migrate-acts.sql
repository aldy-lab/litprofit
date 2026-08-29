-- ============================================================
-- ACTS: the specification of work actually carried out
-- ============================================================
-- "Atliktų faktinių remonto darbų specifikacija" -- the sheet the crew fills
-- in on board and the customer's representative signs. It is what turns
-- finished work into something that can be invoiced and, if it comes to it,
-- argued about a year later.
--
-- SAFE TO RUN MORE THAN ONCE.
--
-- ------------------------------------------------------------
-- WHY THE HEADER IS COPIED AND NOT JOINED
-- ------------------------------------------------------------
-- customer, object and project_ref are stored ON the act, even though the
-- project already knows them. That looks like duplication and is not: an act
-- is a SIGNED DOCUMENT. Somebody put their name under those exact words. If
-- the project is renamed next year -- and project numbers do get renamed --
-- a joined header would quietly rewrite what was signed, and the paper in the
-- customer's folder would stop matching the record here.
--
-- The app fills them in from the project when the act is created. After that
-- they belong to the act.
--
-- ------------------------------------------------------------
-- WHO MAY USE IT
-- ------------------------------------------------------------
-- Any signed-in user, and deliberately NOT sees_money(). An act carries no
-- prices at all -- a description, a unit, a quantity -- and the person who
-- should be filling it in is the fitter standing on the vessel, who is
-- exactly the role sees_money() shuts out. It discloses nothing new either:
-- projects_v already shows staff the client and the site, because strip_money
-- removes revenue, the contract, the advance and the rebill flags and leaves
-- the card's own fields alone.
-- ============================================================

create table if not exists public.acts (
  id           uuid primary key default gen_random_uuid(),
  project_id   uuid references public.projects(id) on delete cascade,

  number       text not null default '',
  act_date     date not null default current_date,

  -- copied from the project at creation; see above
  customer     text not null default '',
  imo          text not null default '',
  object       text not null default '',
  project_ref  text not null default '',

  -- [{ work, unit, qty, remarks }] in the order they are printed.
  -- jsonb because the lines are an ordered block, edited together and never
  -- queried one at a time -- the same reasoning public.projects already uses
  -- for its sheets. A child table would buy ordering headaches and nothing.
  lines        jsonb not null default '[]'::jsonb,

  rep_name     text not null default '',   -- who signed for the customer
  note         text,

  rev          bigint not null default 1,
  created_at   timestamptz not null default now(),
  created_by   uuid references auth.users(id) default auth.uid(),
  updated_at   timestamptz not null default now(),
  updated_by   uuid references auth.users(id) default auth.uid()
);

create index if not exists acts_project_idx on public.acts (project_id);
create index if not exists acts_date_idx    on public.acts (act_date desc);
create index if not exists acts_number_idx  on public.acts (number);

alter table public.acts enable row level security;


drop function if exists public.create_act(jsonb);
drop function if exists public.save_act(uuid, bigint, jsonb);
drop view if exists public.acts_v;

create view public.acts_v as
select
  a.id, a.project_id, a.number, a.act_date,
  a.customer, a.imo, a.object, a.project_ref,
  a.lines, a.rep_name, a.note,
  -- how many lines carry a description, so a list can say "8 items" without
  -- shipping every line of every act to draw the list
  (select count(*) from jsonb_array_elements(a.lines) l
    where coalesce(l->>'work','') <> '')::int as line_count,
  nullif(coalesce(nullif(pr.name,''), nullif(pr.email,'')), '') as written_by,
  a.rev, a.created_at, a.updated_at
from public.acts a
left join public.profiles pr on pr.id = a.created_by
where auth.uid() is not null;


create or replace function public.create_act(p_row jsonb)
returns setof public.acts_v
language plpgsql security definer set search_path = ''
as $$
declare new_id uuid;
begin
  if auth.uid() is null then
    raise exception 'not permitted' using errcode = '42501';
  end if;
  insert into public.acts (project_id, number, act_date, customer, imo, object,
                           project_ref, lines, rep_name, note)
  values (nullif(p_row->>'project_id','')::uuid,
          coalesce(p_row->>'number',''),
          coalesce(nullif(p_row->>'act_date','')::date, current_date),
          coalesce(p_row->>'customer',''), coalesce(p_row->>'imo',''),
          coalesce(p_row->>'object',''), coalesce(p_row->>'project_ref',''),
          coalesce(p_row->'lines', '[]'::jsonb),
          coalesce(p_row->>'rep_name',''), p_row->>'note')
  returning id into new_id;
  return query select * from public.acts_v where id = new_id;
end $$;

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

  return query select * from public.acts_v where id = p_id;
end $$;

create or replace function public.delete_act(p_id uuid)
returns void
language plpgsql security definer set search_path = ''
as $$
begin
  if auth.uid() is null then
    raise exception 'not permitted' using errcode = '42501';
  end if;
  delete from public.acts where id = p_id;
end $$;


-- ------------------------------------------------------------
-- CHECK IT LANDED
-- ------------------------------------------------------------
do $$
declare n int;
begin
  select count(*) into n from information_schema.tables
   where table_schema='public' and table_name='acts';
  if n <> 1 then raise exception 'acts table missing'; end if;

  select count(*) into n from information_schema.views
   where table_schema='public' and table_name='acts_v';
  if n <> 1 then raise exception 'acts_v missing'; end if;

  select count(*) into n from pg_proc p join pg_namespace ns on ns.oid=p.pronamespace
   where ns.nspname='public' and p.proname in ('create_act','save_act','delete_act');
  if n < 3 then raise exception 'expected 3 functions, found %', n; end if;

  raise notice 'acts migration OK: 1 table, 1 view, 3 functions';
end $$;
