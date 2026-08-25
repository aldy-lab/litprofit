-- ============================================================
--  LITPROFIT project calculator — database schema
--  Run once, in the Supabase SQL editor, on a fresh project.
--  Safe to re-run: everything is guarded.
--
--  ACCESS MODEL: one shared company workspace. Any signed-in
--  member sees and edits every project. Anonymous visitors get
--  nothing -- the anon key published in the page is useless on
--  its own, which is what makes it safe to publish.
--
--  To become multi-company later: add an `org_id uuid` to
--  projects, a profiles.org_id, and change `using (true)` to
--  `using (org_id = (select org_id from profiles where id = auth.uid()))`.
--  Nothing else in the app assumes a single tenant.
-- ============================================================

-- ---------- who people are ----------
-- auth.users is not readable by the browser, so the parts we
-- want to show -- "closed by Rimantas, 14:20" -- are mirrored
-- into a table that is.
create table if not exists public.profiles (
  id         uuid primary key references auth.users(id) on delete cascade,
  name       text not null default '',
  email      text not null default '',
  created_at timestamptz not null default now()
);

create or replace function public.handle_new_user()
returns trigger
language plpgsql
security definer set search_path = ''
as $$
begin
  insert into public.profiles (id, name, email)
  values (
    new.id,
    coalesce(new.raw_user_meta_data->>'name', split_part(new.email, '@', 1)),
    new.email
  )
  on conflict (id) do nothing;
  return new;
end $$;

drop trigger if exists on_auth_user_created on auth.users;
create trigger on_auth_user_created
  after insert on auth.users
  for each row execute function public.handle_new_user();

-- ---------- the projects ----------
-- The whole project object lives in `data` as JSONB, because the
-- app already works with exactly that shape and normalising six
-- sheets into six tables would buy nothing here -- a project is
-- always read and written whole.
--
-- The columns beside it are DENORMALISED COPIES of fields inside
-- `data`, and they exist so the portfolio can filter and sort in
-- the database instead of downloading every project to do it in
-- the browser. They are maintained by a trigger, never by the
-- client, so they cannot drift out of step with the JSON.
create table if not exists public.projects (
  id          uuid primary key default gen_random_uuid(),
  data        jsonb not null,

  project_id  text not null default '',
  client      text not null default '',
  site        text not null default '',
  pm          text not null default '',
  start_date  date,
  end_date    date,
  currency    text not null default 'EUR',
  locked      boolean not null default false,

  -- Optimistic concurrency. Everyone can edit everything, so two
  -- people CAN open the same job. Each save states the revision it
  -- read; the update matches on it and bumps it. A stale save
  -- matches no row and comes back empty, which the app reports as
  -- a conflict rather than quietly overwriting the other person.
  rev         bigint not null default 1,

  created_at  timestamptz not null default now(),
  created_by  uuid references auth.users(id) on delete set null,
  updated_at  timestamptz not null default now(),
  updated_by  uuid references auth.users(id) on delete set null
);

create index if not exists projects_client_idx     on public.projects (client);
create index if not exists projects_updated_at_idx on public.projects (updated_at desc);
create index if not exists projects_project_id_idx on public.projects (project_id);

-- ---------- keep the columns in step with the JSON ----------
create or replace function public.sync_project_columns()
returns trigger
language plpgsql
as $$
declare
  card jsonb := coalesce(new.data->'card', '{}'::jsonb);
  s    text;
  e    text;
begin
  new.project_id := coalesce(card->>'projectId', '');
  new.client     := coalesce(card->>'client', '');
  new.site       := coalesce(card->>'site', '');
  new.pm         := coalesce(card->>'pm', '');
  new.currency   := coalesce(new.data->'settings'->>'currency', 'EUR');
  new.locked     := coalesce((new.data->>'locked')::boolean, false);

  -- the app stores '' for an unset date, which is not a date
  s := nullif(card->>'start', '');
  e := nullif(card->>'end', '');
  begin new.start_date := s::date; exception when others then new.start_date := null; end;
  begin new.end_date   := e::date; exception when others then new.end_date   := null; end;

  if TG_OP = 'INSERT' then
    new.created_by := auth.uid();
    new.rev := 1;
  else
    -- rev and the stamps belong to the server, never to the client
    new.rev := old.rev + 1;
    new.created_at := old.created_at;
    new.created_by := old.created_by;
  end if;
  new.updated_at := now();
  new.updated_by := auth.uid();
  return new;
end $$;

drop trigger if exists projects_sync on public.projects;
create trigger projects_sync
  before insert or update on public.projects
  for each row execute function public.sync_project_columns();

-- ---------- a closed project is closed ----------
-- Closing a job made it read-only in the browser and nowhere else: the app
-- disabled the inputs, and a PATCH straight to the API rewrote it anyway.
-- Verified before this existed -- a closed project was renamed to "HACKED"
-- through the REST endpoint. For a tool whose point is that a finished job
-- cannot be changed by accident, the rule has to live where the data does.
--
-- Reopening is still allowed, because that is the way back in: the guard only
-- refuses a write that leaves the project closed. It reads `new.data`, not
-- `new.locked`, because the column is filled in by sync_project_columns and
-- BEFORE triggers fire in name order -- projects_guard runs first, while
-- new.locked still holds the old value.
create or replace function public.guard_locked_project()
returns trigger
language plpgsql
as $$
begin
  if old.locked and coalesce((new.data->>'locked')::boolean, false) then
    raise exception 'Project % is closed. Reopen it before editing.', old.project_id
      using errcode = 'check_violation';
  end if;
  return new;
end $$;

drop trigger if exists projects_guard on public.projects;
create trigger projects_guard
  before update on public.projects
  for each row execute function public.guard_locked_project();

-- ---------- history ----------
-- Every saved revision is kept. This is what lets the tool be
-- called a source of truth rather than a spreadsheet: you can say
-- what a job looked like last month and who changed it. Trimmed to
-- the most recent 50 revisions per project so a busy job cannot
-- quietly eat the 500 MB free tier.
create table if not exists public.project_history (
  id         bigserial primary key,
  project    uuid not null references public.projects(id) on delete cascade,
  rev        bigint not null,
  data       jsonb not null,
  changed_at timestamptz not null default now(),
  changed_by uuid references auth.users(id) on delete set null
);

create index if not exists project_history_project_idx
  on public.project_history (project, rev desc);

create or replace function public.record_project_history()
returns trigger
language plpgsql
security definer set search_path = ''
as $$
begin
  insert into public.project_history (project, rev, data, changed_by)
  values (new.id, new.rev, new.data, auth.uid());

  delete from public.project_history
   where project = new.id
     and id not in (
       select id from public.project_history
        where project = new.id
        order by rev desc
        limit 50
     );
  return null;
end $$;

drop trigger if exists projects_history on public.projects;
create trigger projects_history
  after insert or update on public.projects
  for each row execute function public.record_project_history();

-- ---------- row level security ----------
-- RLS is the whole reason the anon key can be published. With it
-- ON and no policy for the anon role, an unauthenticated request
-- reads nothing, whatever it asks for.
alter table public.projects        enable row level security;
alter table public.project_history enable row level security;
alter table public.profiles        enable row level security;

drop policy if exists projects_team on public.projects;
create policy projects_team on public.projects
  for all to authenticated using (true) with check (true);

-- History is written by the trigger and read by people; nobody
-- edits it, which is the point of an audit trail.
drop policy if exists history_read on public.project_history;
create policy history_read on public.project_history
  for select to authenticated using (true);

drop policy if exists profiles_read on public.profiles;
create policy profiles_read on public.profiles
  for select to authenticated using (true);

drop policy if exists profiles_self on public.profiles;
create policy profiles_self on public.profiles
  for update to authenticated using (id = auth.uid()) with check (id = auth.uid());

-- ---------- table privileges ----------
-- RLS filters rows; a GRANT decides whether the role may touch the table at
-- all. Supabase's default privileges normally hand new public tables to both
-- roles, so this is usually redundant -- but "usually" is not a security
-- model, and a project whose defaults were ever changed would end up with
-- policies that look right and a table nobody can read. Stated explicitly:
grant usage on schema public to anon, authenticated;
grant select, insert, update, delete on public.projects to authenticated;
grant select                         on public.project_history to authenticated;
grant select, update                 on public.profiles to authenticated;

-- Nothing is anonymous here. RLS would refuse it anyway; this refuses it one
-- layer earlier, so a policy edited by mistake cannot open the data up.
revoke all on public.projects        from anon;
revoke all on public.project_history from anon;
revoke all on public.profiles        from anon;

-- ============================================================
--  ROLES
--  admin    -- you: everything, plus the ability to set roles
--  manager  -- the director: everything, including revenue and
--              the portfolio
--  staff    -- everyone else: costs only. No revenue, no
--              contract value, no margin, no portfolio.
--
--  This is enforced HERE and not in the browser. Any signed-in
--  user can call the REST API with their own token, so a tab
--  hidden in JavaScript is a tab, not a permission -- the same
--  lesson as the closed-project lock, which was read-only on
--  screen and rewritable through a PATCH until the rule moved
--  into a trigger.
--
--  The mechanism: the table is taken away from the app
--  entirely. Everything goes through a view that redacts, and
--  through functions that decide what a caller may write. A
--  staff member asking the API for a project does not get a
--  filtered answer -- the revenue keys are not in the row that
--  comes back.
-- ============================================================

alter table public.profiles
  add column if not exists role text not null default 'staff';
alter table public.profiles drop constraint if exists profiles_role_chk;
alter table public.profiles
  add constraint profiles_role_chk check (role in ('admin', 'manager', 'staff'));

-- Nobody edits their own way up. profiles_self already restricts UPDATE to
-- your own row; this stops that row's role being one of the things you change.
create or replace function public.guard_role_change()
returns trigger
language plpgsql
security definer set search_path = ''
as $$
begin
  -- auth.uid() is null when this is not an API call: the SQL editor, or
  -- anything holding the service key. Both are already trusted, and one of
  -- them has to be, or there is no way to appoint the FIRST admin -- the
  -- guard would lock the door with nobody inside.
  if new.role is distinct from old.role
     and auth.uid() is not null
     and coalesce((select role from public.profiles where id = auth.uid()), 'staff') <> 'admin' then
    raise exception 'Only an admin can change a role.' using errcode = 'insufficient_privilege';
  end if;
  return new;
end $$;

drop trigger if exists profiles_role_guard on public.profiles;
create trigger profiles_role_guard
  before update on public.profiles
  for each row execute function public.guard_role_change();

create or replace function public.my_role()
returns text
language sql stable
security definer set search_path = ''
as $$
  select coalesce((select role from public.profiles where id = auth.uid()), 'staff')
$$;

create or replace function public.sees_money()
returns boolean
language sql stable
security definer set search_path = ''
as $$ select public.my_role() in ('admin', 'manager') $$;

-- ---------- what "money" means, in one place ----------
-- Revenue is not only the revenue sheet. The contract value and the advance
-- are what the client agreed to pay; the rebill amounts are what the client is
-- charged for materials and freight; and the target margin states what the
-- company expects to keep. Leave any of them behind and the rest is guessable.
create or replace function public.strip_money(d jsonb)
returns jsonb
language plpgsql
immutable
as $$
declare
  out_d jsonb := coalesce(d, '{}'::jsonb);
begin
  out_d := out_d - 'revenue';
  out_d := out_d #- '{card,contract}';
  out_d := out_d #- '{card,advance}';
  out_d := out_d #- '{settings,targetMargin}';

  if jsonb_typeof(out_d->'materials') = 'array' then
    out_d := jsonb_set(out_d, '{materials}', coalesce((
      select jsonb_agg(row_x - 'rebill' - 'rebillAmt' order by ord)
        from jsonb_array_elements(out_d->'materials') with ordinality as t(row_x, ord)
    ), '[]'::jsonb));
  end if;

  if jsonb_typeof(out_d->'logistics') = 'array' then
    out_d := jsonb_set(out_d, '{logistics}', coalesce((
      select jsonb_agg(row_x - 'rebill' - 'recoverable' order by ord)
        from jsonb_array_elements(out_d->'logistics') with ordinality as t(row_x, ord)
    ), '[]'::jsonb));
  end if;

  return out_d;
end $$;

-- ---------- the app reads a view, never the table ----------
-- Not security_invoker: the view runs as its owner, so a staff member reading
-- it does not need -- and does not have -- any privilege on public.projects.
-- The redaction is therefore not something they can go around.
create or replace view public.projects_v as
select
  p.id,
  case when public.sees_money() then p.data else public.strip_money(p.data) end as data,
  p.project_id, p.client, p.site, p.pm, p.start_date, p.end_date, p.currency, p.locked,
  p.rev, p.created_at, p.created_by, p.updated_at, p.updated_by,
  public.sees_money() as money
from public.projects p;

-- ---------- and writes go through functions ----------
-- A staff member sends the whole document back, as the app always has. What
-- they send for the money keys is ignored: those are taken from the row that
-- is already there. So an employee posting a revenue array of their own
-- invention changes nothing, and does not need to be told so.
create or replace function public.save_project(p_id uuid, p_rev bigint, p_data jsonb)
returns setof public.projects_v
language plpgsql
security definer set search_path = ''
as $$
declare
  cur public.projects%rowtype;
  merged jsonb;
begin
  select * into cur from public.projects where id = p_id;
  if not found then return; end if;
  -- a null revision is the deliberate overwrite the conflict dialog offers
  if p_rev is not null and cur.rev <> p_rev then return; end if;   -- somebody saved first
  if cur.locked and coalesce((p_data->>'locked')::boolean, false) then
    raise exception 'Project % is closed. Reopen it before editing.', cur.project_id
      using errcode = 'check_violation';
  end if;

  if public.sees_money() then
    merged := p_data;
  else
    -- keep every money key exactly as stored, take the rest from the client
    merged := public.strip_money(p_data);
    merged := merged || jsonb_build_object('revenue', coalesce(cur.data->'revenue', '[]'::jsonb));
    merged := jsonb_set(merged, '{card,contract}', coalesce(cur.data->'card'->'contract', 'null'::jsonb), true);
    merged := jsonb_set(merged, '{card,advance}',  coalesce(cur.data->'card'->'advance',  'null'::jsonb), true);
    merged := jsonb_set(merged, '{settings,targetMargin}',
                        coalesce(cur.data->'settings'->'targetMargin', 'null'::jsonb), true);
    -- rebill figures are per row, so they are put back by position
    merged := public.restore_rebills(merged, cur.data, 'materials', array['rebill', 'rebillAmt']);
    merged := public.restore_rebills(merged, cur.data, 'logistics', array['rebill', 'recoverable']);
  end if;

  update public.projects set data = merged where id = p_id;
  return query select * from public.projects_v where id = p_id;
end $$;

-- Restores the hidden per-row fields onto the rows the client sent back.
-- Matched by position, which is what the app itself uses: a sheet is an
-- ordered list and a row's place in it is its identity.
create or replace function public.restore_rebills(incoming jsonb, stored jsonb,
                                                  sheet text, keys text[])
returns jsonb
language plpgsql
immutable
as $$
declare
  merged jsonb;
begin
  if jsonb_typeof(incoming->sheet) <> 'array' then return incoming; end if;
  select jsonb_agg(
           case when jsonb_typeof(stored->sheet->(ord::int - 1)) = 'object'
                then row_x || (select coalesce(jsonb_object_agg(k, stored->sheet->(ord::int - 1)->k), '{}'::jsonb)
                                 from unnest(keys) k
                                where stored->sheet->(ord::int - 1) ? k)
                else row_x end
           order by ord)
    into merged
    from jsonb_array_elements(incoming->sheet) with ordinality as t(row_x, ord);
  return jsonb_set(incoming, array[sheet], coalesce(merged, '[]'::jsonb));
end $$;

-- Creating and deleting a job is not an employee's business.
create or replace function public.create_project(p_data jsonb)
returns setof public.projects_v
language plpgsql
security definer set search_path = ''
as $$
declare new_id uuid;
begin
  if auth.uid() is not null and not public.sees_money() then
    raise exception 'Only a manager can create a project.' using errcode = 'insufficient_privilege';
  end if;
  insert into public.projects (data) values (coalesce(p_data, '{}'::jsonb)) returning id into new_id;
  return query select * from public.projects_v where id = new_id;
end $$;

create or replace function public.delete_project(p_id uuid)
returns void
language plpgsql
security definer set search_path = ''
as $$
begin
  if auth.uid() is not null and not public.sees_money() then
    raise exception 'Only a manager can delete a project.' using errcode = 'insufficient_privilege';
  end if;
  delete from public.projects where id = p_id;
end $$;

-- ---------- privileges ----------
-- The app no longer touches public.projects at all.
revoke all on public.projects from authenticated;
grant select on public.projects_v to authenticated;
grant execute on function public.save_project(uuid, bigint, jsonb) to authenticated;
grant execute on function public.create_project(jsonb) to authenticated;
grant execute on function public.delete_project(uuid) to authenticated;
grant execute on function public.my_role() to authenticated;

-- History carries the same figures, so it follows the same rule.
revoke all on public.project_history from authenticated;
create or replace view public.project_history_v as
select h.id, h.project, h.rev,
       case when public.sees_money() then h.data else public.strip_money(h.data) end as data,
       h.changed_at, h.changed_by
from public.project_history h;
grant select on public.project_history_v to authenticated;

revoke all on public.projects_v        from anon;
revoke all on public.project_history_v from anon;


-- ============================================================
-- ENQUIRIES  (Užklausų registras)
-- ============================================================
-- This register lived in a Power BI report published to the web, reading from
-- a spreadsheet. Two problems with leaving it there: a publish-to-web link is
-- readable by anyone who has the URL -- client names, suppliers and prices for
-- 216 enquiries, 2.6 M EUR of them -- and the spreadsheet behind it was a
-- second place where the truth lived. The register moves here, behind the same
-- login and the same roles as everything else in the calculator.
--
-- Columns are the report's own, kept in Lithuanian order but named in English
-- so the SQL reads like the rest of this file:
--   Numeris        -> number          Užklausos data     -> enquiry_date
--   Klientas       -> client          Užklausa tiekėjams -> sent_to_supplier
--   Aprašymas      -> description     Pasiūlymas klientui-> quoted_to_client
--   Tiekėjas       -> supplier        Užklausos būsena   -> status
--   PO Data        -> po_date         Kaina be PVM       -> price_ex_vat
--   Pristatymas    -> delivered       Atsakingas         -> owner
--
-- `number` is NOT unique: the register already carries 26.2-19.2 twice, which
-- is how they record two lines under one enquiry. A unique index here would
-- have rejected the client's own data on import.
create table if not exists public.enquiries (
  id            uuid primary key default gen_random_uuid(),
  number        text not null,
  client        text,
  description   text,
  enquiry_date  date,
  sent_to_supplier boolean not null default false,
  supplier      text,
  quoted_to_client boolean not null default false,
  status        text not null default 'Vykdoma'
                check (status in ('Vykdoma', 'Gautas PO', 'Atmesta užklausa')),
  po_date       date,
  price_ex_vat  numeric(14,2) not null default 0,
  delivered     boolean not null default false,
  owner         text,
  note          text,
  rev           bigint not null default 1,
  created_at    timestamptz not null default now(),
  created_by    uuid references auth.users(id) default auth.uid(),
  updated_at    timestamptz not null default now(),
  updated_by    uuid references auth.users(id) default auth.uid()
);

create index if not exists enquiries_date_idx     on public.enquiries (enquiry_date desc);
create index if not exists enquiries_status_idx   on public.enquiries (status);
create index if not exists enquiries_client_idx   on public.enquiries (client);
create index if not exists enquiries_supplier_idx on public.enquiries (supplier);

alter table public.enquiries enable row level security;

-- "Neišsiųstas pasiūlymas, dienos" was a calculated column in the report: how
-- long an enquiry has been sitting without a quote going back to the client.
-- It is derived, so it is not stored -- a stored copy goes stale overnight,
-- every night, and the report's own value was only right on the day it ran.
create or replace function public.enquiry_days_unquoted(
  p_quoted boolean, p_date date, p_status text)
returns integer
language sql immutable
as $$
  select case
    when p_quoted or p_date is null then 0
    else greatest(0, (current_date - p_date))::integer
  end
$$;

-- Money is the whole point of this table, so there is no redacted variant of
-- it: an employee who cannot see money does not get this register at all. The
-- view returns nothing rather than returning rows with the prices blanked --
-- a register of who asked for what, with the amounts removed, is still the
-- client list and the supplier list, and neither is theirs to have.
create or replace view public.enquiries_v as
select
  e.id, e.number, e.client, e.description, e.enquiry_date,
  e.sent_to_supplier, e.supplier, e.quoted_to_client,
  public.enquiry_days_unquoted(e.quoted_to_client, e.enquiry_date, e.status) as days_unquoted,
  e.status, e.po_date, e.price_ex_vat, e.delivered, e.owner, e.note,
  e.rev, e.created_at, e.updated_at, e.updated_by
from public.enquiries e
where public.sees_money();

create or replace function public.save_enquiry(p_id uuid, p_rev bigint, p_row jsonb)
returns public.enquiries
language plpgsql security definer set search_path = ''
as $$
declare r public.enquiries;
begin
  if not public.sees_money() then
    raise exception 'not permitted' using errcode = '42501';
  end if;
  update public.enquiries set
    number = coalesce(p_row->>'number', number),
    client = p_row->>'client',
    description = p_row->>'description',
    enquiry_date = nullif(p_row->>'enquiry_date','')::date,
    sent_to_supplier = coalesce((p_row->>'sent_to_supplier')::boolean, false),
    supplier = p_row->>'supplier',
    quoted_to_client = coalesce((p_row->>'quoted_to_client')::boolean, false),
    status = coalesce(p_row->>'status', status),
    po_date = nullif(p_row->>'po_date','')::date,
    price_ex_vat = coalesce((p_row->>'price_ex_vat')::numeric, 0),
    delivered = coalesce((p_row->>'delivered')::boolean, false),
    owner = p_row->>'owner',
    note = p_row->>'note',
    rev = rev + 1,
    updated_at = now(),
    updated_by = auth.uid()
  where id = p_id and rev = p_rev
  returning * into r;
  if not found then
    -- same contract as save_project: a stale rev is a conflict, not a crash
    raise exception 'conflict' using errcode = '40001';
  end if;
  return r;
end $$;

create or replace function public.create_enquiry(p_row jsonb)
returns public.enquiries
language plpgsql security definer set search_path = ''
as $$
declare r public.enquiries;
begin
  if not public.sees_money() then
    raise exception 'not permitted' using errcode = '42501';
  end if;
  insert into public.enquiries (number, client, description, enquiry_date,
      sent_to_supplier, supplier, quoted_to_client, status, po_date,
      price_ex_vat, delivered, owner, note)
  values (coalesce(nullif(p_row->>'number',''), 'NEW'),
      p_row->>'client', p_row->>'description', nullif(p_row->>'enquiry_date','')::date,
      coalesce((p_row->>'sent_to_supplier')::boolean, false), p_row->>'supplier',
      coalesce((p_row->>'quoted_to_client')::boolean, false),
      coalesce(nullif(p_row->>'status',''), 'Vykdoma'), nullif(p_row->>'po_date','')::date,
      coalesce((p_row->>'price_ex_vat')::numeric, 0),
      coalesce((p_row->>'delivered')::boolean, false), p_row->>'owner', p_row->>'note')
  returning * into r;
  return r;
end $$;

create or replace function public.delete_enquiry(p_id uuid)
returns void
language plpgsql security definer set search_path = ''
as $$
begin
  if public.my_role() <> 'admin' then
    raise exception 'not permitted' using errcode = '42501';
  end if;
  delete from public.enquiries where id = p_id;
end $$;

-- The table itself is revoked, exactly as public.projects is: the app can only
-- reach the view and the three functions above.
revoke all on public.enquiries   from anon, authenticated;
revoke all on public.enquiries_v from anon;
grant select on public.enquiries_v to authenticated;
grant execute on function public.save_enquiry(uuid, bigint, jsonb) to authenticated;
grant execute on function public.create_enquiry(jsonb)             to authenticated;
grant execute on function public.delete_enquiry(uuid)              to authenticated;
grant execute on function public.enquiry_days_unquoted(boolean, date, text) to authenticated;
