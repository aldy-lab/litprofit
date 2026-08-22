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
