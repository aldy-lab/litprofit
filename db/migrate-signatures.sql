-- ============================================================
-- SIGNATURES ON FILE, AND THE EXECUTOR'S SIDE OF THE ACT
-- ============================================================
-- Drawing the same signature on every act is work nobody should do twice, so
-- a signature can be kept and chosen. This is about OUR side of the sheet
-- only, and the distinction is the whole design:
--
--   The customer's representative signs LIVE, every time, and nothing here
--   changes that. A stored signature re-applied to a new document is not a
--   signature, it is a copy of one: what a signature attests to is the exact
--   words above it, and those words are different on every act. There is no
--   version of "remember the chief engineer's signature" that is not forging
--   his assent to a document he has not read.
--
--   The executor's signature is ours. Signing our own document with our own
--   hand, from a copy we keep of it, is what a rubber stamp has always been.
--   Until now the printed act had an empty line there and somebody signed it
--   with a pen afterwards, if they remembered.
--
-- Requires migrate-acts-6.sql. SAFE TO RUN MORE THAN ONCE.
--
-- ------------------------------------------------------------
-- YOU CAN ONLY APPLY YOUR OWN
-- ------------------------------------------------------------
-- signatures_v returns rows where owner = auth.uid(), and nothing else. Not
-- because a colleague is a threat, but because the alternative has no floor:
-- once anybody can stamp anybody's signature, the name under the line stops
-- being evidence of who signed and becomes evidence of who was on the list.
--
-- If a director's signature genuinely has to go on acts a fitter produces,
-- that is a delegation, and a delegation should be a deliberate thing with a
-- record -- not a dropdown that happens to contain everybody.
-- ============================================================

create table if not exists public.signatures (
  id         uuid primary key default gen_random_uuid(),
  owner      uuid not null default auth.uid() references auth.users(id) on delete cascade,
  -- what gets printed under the line. Usually a name, sometimes a name and a
  -- job title, and it is the label that makes a list of two worth choosing
  -- between.
  label      text not null default '',
  image      text not null,
  created_at timestamptz not null default now(),
  updated_at timestamptz not null default now()
);

do $$
begin
  if not exists (select 1 from pg_constraint where conname = 'signatures_image_chk') then
    alter table public.signatures add constraint signatures_image_chk
      check (image like 'data:image/png;base64,%'
             and length(image) between 100 and 400000);
  end if;
end $$;

create index if not exists signatures_owner_idx on public.signatures (owner);
alter table public.signatures enable row level security;


drop function if exists public.create_signature(text, text);
drop function if exists public.delete_signature(uuid);
drop view if exists public.signatures_v;

create view public.signatures_v as
select s.id, s.label, s.image, s.created_at
  from public.signatures s
 where s.owner = auth.uid();


create or replace function public.create_signature(p_label text, p_image text)
returns setof public.signatures_v
language plpgsql security definer set search_path = ''
as $$
declare new_id uuid;
begin
  if auth.uid() is null then
    raise exception 'not permitted' using errcode = '42501';
  end if;
  if p_image is null or p_image !~ '^data:image/png;base64,' then
    raise exception 'not a signature' using errcode = '22023';
  end if;
  if length(p_image) > 400000 then
    raise exception 'signature too large' using errcode = '22023';
  end if;
  if btrim(coalesce(p_label, '')) = '' then
    raise exception 'a signature needs a name under it' using errcode = '22023';
  end if;
  -- Six is more than anybody needs and few enough to pick from at a glance.
  if (select count(*) from public.signatures where owner = auth.uid()) >= 6 then
    raise exception 'six signatures is the limit' using errcode = '22023';
  end if;

  insert into public.signatures (owner, label, image)
  values (auth.uid(), btrim(p_label), p_image)
  returning id into new_id;
  return query select * from public.signatures_v where id = new_id;
end $$;

-- Deleting one does NOT touch the acts it has already been applied to: the
-- image is copied onto the act, for the same reason its customer and object
-- are. A document that loses its signature because somebody tidied a list is
-- a document that was never safe.
create or replace function public.delete_signature(p_id uuid)
returns void
language plpgsql security definer set search_path = ''
as $$
begin
  if auth.uid() is null then
    raise exception 'not permitted' using errcode = '42501';
  end if;
  delete from public.signatures where id = p_id and owner = auth.uid();
end $$;


-- ------------------------------------------------------------
-- THE EXECUTOR'S SIDE OF THE ACT
-- ------------------------------------------------------------
alter table public.acts add column if not exists exec_signature text;
alter table public.acts add column if not exists exec_name      text;
alter table public.acts add column if not exists exec_signed_at timestamptz;
alter table public.acts add column if not exists exec_signed_by uuid references auth.users(id);

do $$
begin
  if not exists (select 1 from pg_constraint where conname = 'acts_exec_signature_chk') then
    alter table public.acts add constraint acts_exec_signature_chk
      check (exec_signature is null
             or (exec_signature like 'data:image/png;base64,%'
                 and length(exec_signature) between 100 and 400000));
  end if;
end $$;


drop function if exists public.create_act(jsonb);
drop function if exists public.save_act(uuid, bigint, jsonb);
drop function if exists public.sign_act(uuid, bigint, text, text, timestamptz);
drop function if exists public.unsign_act(uuid, bigint);
drop function if exists public.sign_act_exec(uuid, bigint, uuid);
drop function if exists public.clear_act_exec(uuid, bigint);
drop view if exists public.acts_v;

create view public.acts_v as
select
  a.id, a.project_id, a.number, a.act_date,
  a.customer, a.imo, a.object, a.project_ref,
  a.lines, a.rep_name, a.note, a.extra, a.field_defs,
  (select count(*) from jsonb_array_elements(a.lines) l
    where coalesce(l->>'work','') <> '')::int as line_count,
  a.signature,
  (a.signature is not null) as signed,
  a.signed_at,
  a.sign_log,
  nullif(coalesce(nullif(sp.name,''), nullif(sp.email,'')), '') as witnessed_by,
  a.exec_signature,
  (a.exec_signature is not null) as exec_signed,
  a.exec_name, a.exec_signed_at,
  nullif(coalesce(nullif(xp.name,''), nullif(xp.email,'')), '') as executed_by,
  nullif(coalesce(nullif(pr.name,''), nullif(pr.email,'')), '') as written_by,
  a.rev, a.created_at, a.updated_at
from public.acts a
left join public.profiles pr on pr.id = a.created_by
left join public.profiles sp on sp.id = a.signed_by
left join public.profiles xp on xp.id = a.exec_signed_by
where auth.uid() is not null;


-- The image is COPIED onto the act, not referenced. Same reason the customer
-- and the object are: a signed sheet whose signature can be changed or
-- deleted from somewhere else is not a record of anything.
--
-- Allowed whether or not the customer has signed. Ours is a different line on
-- the paper, and putting it there afterwards does not alter one word the
-- customer accepted -- in practice the fitter gets the customer's signature
-- on board and the office adds the company's when the sheet comes back.
create or replace function public.sign_act_exec(p_id uuid, p_rev bigint, p_signature_id uuid)
returns setof public.acts_v
language plpgsql security definer set search_path = ''
as $$
declare
  cur public.acts%rowtype;
  sig public.signatures%rowtype;
  who text;
begin
  if auth.uid() is null then
    raise exception 'not permitted' using errcode = '42501';
  end if;

  -- owner = auth.uid() in the WHERE is the whole access rule: you cannot
  -- apply a signature that is not yours because you cannot find one.
  select * into sig from public.signatures
   where id = p_signature_id and owner = auth.uid();
  if not found then
    raise exception 'that signature is not yours' using errcode = '42501';
  end if;

  select * into cur from public.acts where id = p_id;
  if not found then return; end if;
  if p_rev is not null and cur.rev <> p_rev then return; end if;

  select coalesce(nullif(name,''), nullif(email,'')) into who
    from public.profiles where id = auth.uid();

  update public.acts set
    exec_signature = sig.image,
    exec_name      = sig.label,
    exec_signed_at = now(),
    exec_signed_by = auth.uid(),
    sign_log = sign_log || jsonb_build_object(
                 'at', to_char(now() at time zone 'UTC', 'YYYY-MM-DD"T"HH24:MI:SS"Z"'),
                 'action', 'executor signed',
                 'witness', who,
                 'rep', sig.label),
    rev = rev + 1, updated_at = now(), updated_by = auth.uid()
  where id = p_id;

  return query select * from public.acts_v where id = p_id;
end $$;


create or replace function public.clear_act_exec(p_id uuid, p_rev bigint)
returns setof public.acts_v
language plpgsql security definer set search_path = ''
as $$
declare cur public.acts%rowtype; who text;
begin
  if auth.uid() is null then
    raise exception 'not permitted' using errcode = '42501';
  end if;
  select * into cur from public.acts where id = p_id;
  if not found then return; end if;
  if p_rev is not null and cur.rev <> p_rev then return; end if;
  if cur.exec_signature is null then
    return query select * from public.acts_v where id = p_id; return;
  end if;

  select coalesce(nullif(name,''), nullif(email,'')) into who
    from public.profiles where id = auth.uid();

  update public.acts set
    exec_signature = null, exec_name = null,
    exec_signed_at = null, exec_signed_by = null,
    sign_log = sign_log || jsonb_build_object(
                 'at', to_char(now() at time zone 'UTC', 'YYYY-MM-DD"T"HH24:MI:SS"Z"'),
                 'action', 'executor cleared',
                 'witness', who,
                 'rep', cur.exec_name),
    rev = rev + 1, updated_at = now(), updated_by = auth.uid()
  where id = p_id;

  return query select * from public.acts_v where id = p_id;
end $$;


-- ------------------------------------------------------------
-- THE FOUR THAT ONLY CHANGE BECAUSE THE VIEW DID
-- ------------------------------------------------------------
create or replace function public.create_act(p_row jsonb)
returns setof public.acts_v
language plpgsql security definer set search_path = ''
as $$
declare
  new_id uuid; v_pid uuid := nullif(p_row->>'project_id','')::uuid;
  v_num text; i int;
begin
  if auth.uid() is null then
    raise exception 'not permitted' using errcode = '42501';
  end if;
  v_num := public.next_act_number(v_pid, coalesce(p_row->>'number',''));
  for i in 1..5 loop
    begin
      insert into public.acts (project_id, number, act_date, customer, imo, object,
                               project_ref, lines, rep_name, note, extra)
      values (v_pid, v_num,
              coalesce(nullif(p_row->>'act_date','')::date, current_date),
              coalesce(p_row->>'customer',''), coalesce(p_row->>'imo',''),
              coalesce(p_row->>'object',''), coalesce(p_row->>'project_ref',''),
              coalesce(p_row->'lines', '[]'::jsonb),
              coalesce(p_row->>'rep_name',''), p_row->>'note',
              coalesce(p_row->'extra', '{}'::jsonb))
      returning id into new_id;
      exit;
    exception when unique_violation then
      v_num := public.next_act_number(v_pid, v_num);
      if i = 5 then raise; end if;
    end;
  end loop;
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
      extra       = coalesce(p_row->'extra', extra),
      rev = rev + 1, updated_at = now(), updated_by = auth.uid()
    where id = p_id;
  exception when unique_violation then
    raise exception 'act number already used on this job' using errcode = '23505';
  end;
  return query select * from public.acts_v where id = p_id;
end $$;

create or replace function public.sign_act(p_id uuid, p_rev bigint,
                                           p_signature text, p_rep_name text,
                                           p_signed_at timestamptz default null)
returns setof public.acts_v
language plpgsql security definer set search_path = ''
as $$
declare
  cur public.acts%rowtype; who text; v_at timestamptz;
  v_claim text := 'device'; v_defs jsonb;
begin
  if auth.uid() is null then
    raise exception 'not permitted' using errcode = '42501';
  end if;
  if p_signature is null or p_signature !~ '^data:image/png;base64,' then
    raise exception 'not a signature' using errcode = '22023';
  end if;
  if length(p_signature) > 400000 then
    raise exception 'signature too large' using errcode = '22023';
  end if;
  select * into cur from public.acts where id = p_id;
  if not found then return; end if;
  if p_rev is not null and cur.rev <> p_rev then return; end if;
  if cur.signature is not null then
    raise exception 'act is already signed' using errcode = '42501';
  end if;

  v_at := coalesce(p_signed_at, now());
  if v_at > now() then v_at := now(); v_claim := 'clamped-future'; end if;
  if v_at < now() - interval '30 days' then v_at := now(); v_claim := 'clamped-old'; end if;
  if p_signed_at is null then v_claim := 'server'; end if;

  select coalesce(nullif(name,''), nullif(email,'')) into who
    from public.profiles where id = auth.uid();
  select defs into v_defs from public.act_fields where only_row;

  update public.acts set
    signature = p_signature, signed_at = v_at, signed_by = auth.uid(),
    rep_name  = coalesce(nullif(p_rep_name,''), rep_name),
    field_defs = coalesce(v_defs, '{"header": [], "columns": []}'::jsonb),
    sign_log = sign_log || jsonb_build_object(
                 'at', to_char(v_at at time zone 'UTC', 'YYYY-MM-DD"T"HH24:MI:SS"Z"'),
                 'received', to_char(now() at time zone 'UTC', 'YYYY-MM-DD"T"HH24:MI:SS"Z"'),
                 'clock', v_claim, 'action', 'signed', 'witness', who,
                 'rep', coalesce(nullif(p_rep_name,''), rep_name)),
    rev = rev + 1, updated_at = now(), updated_by = auth.uid()
  where id = p_id;

  return query select * from public.acts_v where id = p_id;
end $$;

create or replace function public.unsign_act(p_id uuid, p_rev bigint)
returns setof public.acts_v
language plpgsql security definer set search_path = ''
as $$
declare cur public.acts%rowtype; who text;
begin
  if auth.uid() is null then
    raise exception 'not permitted' using errcode = '42501';
  end if;
  select * into cur from public.acts where id = p_id;
  if not found then return; end if;
  if p_rev is not null and cur.rev <> p_rev then return; end if;
  if cur.signature is null then return query select * from public.acts_v where id = p_id; return; end if;

  select coalesce(nullif(name,''), nullif(email,'')) into who
    from public.profiles where id = auth.uid();

  -- The executor's signature is NOT cleared here. It is a different line and
  -- a different person's assent; clearing the customer's is about reopening
  -- the sheet for editing, not about withdrawing ours.
  update public.acts set
    signature = null, signed_at = null, signed_by = null, field_defs = null,
    sign_log = sign_log || jsonb_build_object(
                 'at', to_char(now() at time zone 'UTC', 'YYYY-MM-DD"T"HH24:MI:SS"Z"'),
                 'action', 'cleared', 'witness', who, 'rep', cur.rep_name),
    rev = rev + 1, updated_at = now(), updated_by = auth.uid()
  where id = p_id;

  return query select * from public.acts_v where id = p_id;
end $$;


-- ------------------------------------------------------------
-- PRIVILEGES, AND A DEFAULT THAT DOES NOT HOLD
-- ------------------------------------------------------------
-- migrate-harden.sql set ALTER DEFAULT PRIVILEGES to stop granting EXECUTE
-- to PUBLIC on new functions, and that was supposed to be the end of it.
-- It is not. Measured rather than assumed: with the default ACL recorded as
-- `authenticated=X | service_role=X` and no PUBLIC entry in it, a brand-new
-- function still comes out as
--
--     =X/postgres | postgres=X/postgres | authenticated=X | service_role=X
--
-- -- the leading `=X` being PUBLIC, and PUBLIC being how anon gets in. So
-- every migration after the hardening would have quietly handed the whole
-- new API surface back to anybody who never signed in.
--
-- Which makes these two lines a standing step at the end of any migration
-- that creates a function here, not a flourish on this one.
revoke all on public.signatures from anon, authenticated;

revoke execute on all functions in schema public from public, anon;

-- Handed back BY NAME, and this is the second half of the lesson. The first
-- version of this block ended with
--
--     grant execute on all functions in schema public to authenticated;
--
-- and that one line put eleven internal helpers and trigger functions back
-- on the API -- handle_new_user, guard_role_change, next_act_number and the
-- rest -- undoing the allow-list migrate-harden.sql had established. anon
-- stayed shut, so nothing was open to the world, but it was undone SILENTLY,
-- because a grant that grants too much reports nothing at all.
--
-- Revoking from PUBLIC has to be blanket, because PUBLIC is granted blanket.
-- Granting is a list, and a list has names in it.
grant execute on function public.create_signature(text, text)     to authenticated, service_role;
grant execute on function public.delete_signature(uuid)           to authenticated, service_role;
grant execute on function public.sign_act_exec(uuid, bigint, uuid) to authenticated, service_role;
grant execute on function public.clear_act_exec(uuid, bigint)     to authenticated, service_role;
grant execute on function public.create_act(jsonb)                to authenticated, service_role;
grant execute on function public.save_act(uuid, bigint, jsonb)    to authenticated, service_role;
grant execute on function public.sign_act(uuid, bigint, text, text, timestamptz)
                                                                   to authenticated, service_role;
grant execute on function public.unsign_act(uuid, bigint)         to authenticated, service_role;


-- ============================================================
-- CHECK IT LANDED
-- ============================================================
do $$
declare n int;
begin
  select count(*) into n from information_schema.tables
   where table_schema='public' and table_name='signatures';
  if n <> 1 then raise exception 'the signatures table is missing'; end if;

  select count(*) into n from information_schema.columns
   where table_schema='public' and table_name='acts'
     and column_name in ('exec_signature','exec_name','exec_signed_at','exec_signed_by');
  if n <> 4 then raise exception 'expected 4 executor columns, found %', n; end if;

  select count(*) into n from information_schema.columns
   where table_schema='public' and table_name='acts_v'
     and column_name in ('exec_signature','exec_signed','exec_name','exec_signed_at','executed_by');
  if n <> 5 then raise exception 'the view is missing the executor columns'; end if;

  select count(*) into n from pg_proc p join pg_namespace ns on ns.oid=p.pronamespace
   where ns.nspname='public'
     and p.proname in ('create_signature','delete_signature','sign_act_exec','clear_act_exec');
  if n <> 4 then raise exception 'expected 4 new functions, found %', n; end if;

  -- the constraint refuses what it is there to refuse
  begin
    insert into public.signatures (owner, label, image)
    values (null, 'x', 'javascript:alert(1)');
    raise exception 'the signature constraint let a non-PNG through';
  exception when check_violation then null;
       when not_null_violation then null;
  end;

  select count(*) into n from pg_proc p join pg_namespace ns on ns.oid=p.pronamespace
   where ns.nspname='public' and p.proname in ('create_signature','sign_act_exec')
     and has_function_privilege('anon', p.oid, 'EXECUTE');
  if n > 0 then raise exception 'anon can execute the new functions'; end if;

  select count(*) into n from pg_proc p join pg_namespace ns on ns.oid=p.pronamespace
   where ns.nspname='public'
     and p.proname in ('create_signature','delete_signature','sign_act_exec','clear_act_exec')
     and has_function_privilege('authenticated', p.oid, 'EXECUTE');
  if n <> 4 then raise exception 'the app cannot call the new functions'; end if;

  raise notice 'signatures OK: kept, chosen, copied onto the act, and yours only';
end $$;
