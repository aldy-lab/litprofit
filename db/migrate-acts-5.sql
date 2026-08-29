-- ============================================================
-- ACTS, FIFTH PASS: fields the company names for itself
-- ============================================================
-- The act carries what the paper form carried: a number, a date, a customer,
-- an IMO, an object, a project number, and work rows of description / unit /
-- quantity / remarks. Every yard wants one or two more than that, and which
-- two is not something to guess at from here -- port and berth, the
-- customer's order number, hours, who did the work.
--
-- So the list is the company's to write. This adds two things and no fixed
-- fields at all: a place to keep the definition, and a place on each act to
-- keep the values.
--
-- Requires migrate-acts-4.sql. SAFE TO RUN MORE THAN ONCE.
--
-- ------------------------------------------------------------
-- WHY A SIGNED ACT KEEPS ITS OWN COPY OF THE DEFINITION
-- ------------------------------------------------------------
-- Same reason its customer and object are copied rather than joined: it is a
-- signed document. If the definition were read live, renaming a column next
-- March would silently relabel a column on a sheet somebody signed last
-- year -- the paper in the customer's folder would stop matching the record,
-- and the record would be the one that changed.
--
-- So the definition in force is stamped onto the act AT SIGNING. Before that
-- the act follows the live list, because an act still being filled in should
-- pick up a column added this morning.
--
-- ------------------------------------------------------------
-- WHY THE KEY IS NOT THE LABEL
-- ------------------------------------------------------------
-- Values are stored under a key; the label is what gets printed. Storing them
-- under the label would mean that correcting a spelling orphans every value
-- already recorded under the old spelling -- and nothing would report it,
-- because a missing key reads exactly like a field nobody filled in.
--
-- ------------------------------------------------------------
-- WHY THERE IS A LIMIT
-- ------------------------------------------------------------
-- The act is printed on A4 and columns do not fold. Three extra columns is
-- about what fits beside a work description wide enough to describe work;
-- header fields have far more room, so six. The limit is here rather than
-- only in the interface because this is what makes it true of the document.
-- ============================================================

-- ------------------------------------------------------------
-- THE DEFINITION
-- ------------------------------------------------------------
-- One row, and the primary key is what enforces that: `only_row` can only
-- ever be true, so a second insert collides with the first. A settings table
-- that can quietly grow a second row is a settings table that will.
create table if not exists public.act_fields (
  only_row   boolean primary key default true check (only_row),
  defs       jsonb not null default '{"header": [], "columns": []}'::jsonb,
  rev        bigint not null default 1,
  updated_at timestamptz not null default now(),
  updated_by uuid references auth.users(id) default auth.uid()
);
insert into public.act_fields (only_row) values (true) on conflict do nothing;
alter table public.act_fields enable row level security;


-- ------------------------------------------------------------
-- THE VALUES
-- ------------------------------------------------------------
-- Header extras go in `extra`, keyed. Line extras need nothing new: the work
-- rows are already jsonb objects and an extra key on each is just a key.
alter table public.acts add column if not exists extra jsonb not null default '{}'::jsonb;
alter table public.acts add column if not exists field_defs jsonb;


-- ------------------------------------------------------------
-- WHAT A DEFINITION IS ALLOWED TO BE
-- ------------------------------------------------------------
-- Checked here and not only in the browser, because this shapes a document
-- somebody signs and the browser is not the only thing that can call a
-- function.
create or replace function public.check_act_fields(p_defs jsonb)
returns void
language plpgsql immutable set search_path = ''
as $$
declare
  part text;
  arr  jsonb;
  el   jsonb;
  seen text[] := '{}';
  cap  int;
begin
  if p_defs is null or jsonb_typeof(p_defs) <> 'object' then
    raise exception 'the field definition must be an object' using errcode = '22023';
  end if;

  foreach part in array array['header', 'columns'] loop
    arr := coalesce(p_defs -> part, '[]'::jsonb);
    if jsonb_typeof(arr) <> 'array' then
      raise exception '% must be a list', part using errcode = '22023';
    end if;
    cap := case part when 'header' then 6 else 3 end;
    if jsonb_array_length(arr) > cap then
      raise exception 'at most % extra %s (the act is printed on A4)', cap, part
        using errcode = '22023';
    end if;
    for el in select * from jsonb_array_elements(arr) loop
      -- The key is an identifier, not prose: it is a jsonb key and it ends up
      -- in a data attribute in the browser.
      if coalesce(el->>'key','') !~ '^[a-z][a-z0-9_]{0,23}$' then
        raise exception 'bad field key %', coalesce(el->>'key','(none)')
          using errcode = '22023';
      end if;
      if btrim(coalesce(el->>'label','')) = '' then
        raise exception 'field % has no label', el->>'key' using errcode = '22023';
      end if;
      if length(el->>'label') > 40 then
        raise exception 'the label for % is too long to print', el->>'key'
          using errcode = '22023';
      end if;
      if (el->>'key') = any(seen) then
        raise exception 'two fields share the key %', el->>'key' using errcode = '22023';
      end if;
      seen := seen || (el->>'key');
    end loop;
  end loop;
end $$;


drop function if exists public.save_act_fields(bigint, jsonb);
drop view if exists public.act_fields_v;

create view public.act_fields_v as
select f.defs, f.rev, f.updated_at,
       nullif(coalesce(nullif(pr.name,''), nullif(pr.email,'')), '') as updated_by
  from public.act_fields f
  left join public.profiles pr on pr.id = f.updated_by
 where auth.uid() is not null;


-- Everyone signed in READS the definition -- a fitter cannot fill in a column
-- he cannot see. Only an owner writes it: it changes the shape of every act
-- the company will issue, which is not a per-job decision.
create or replace function public.save_act_fields(p_rev bigint, p_defs jsonb)
returns setof public.act_fields_v
language plpgsql security definer set search_path = ''
as $$
declare cur public.act_fields%rowtype;
begin
  if public.my_role() <> 'admin' then
    raise exception 'not permitted' using errcode = '42501';
  end if;
  perform public.check_act_fields(p_defs);

  select * into cur from public.act_fields where only_row;
  if p_rev is not null and cur.rev <> p_rev then return; end if;

  update public.act_fields
     set defs = p_defs, rev = rev + 1, updated_at = now(), updated_by = auth.uid()
   where only_row;

  return query select * from public.act_fields_v;
end $$;


-- ------------------------------------------------------------
-- THE ACT FUNCTIONS, CARRYING THE EXTRAS
-- ------------------------------------------------------------
drop function if exists public.create_act(jsonb);
drop function if exists public.save_act(uuid, bigint, jsonb);
drop function if exists public.sign_act(uuid, bigint, text, text, timestamptz);
drop function if exists public.unsign_act(uuid, bigint);
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
  nullif(coalesce(nullif(pr.name,''), nullif(pr.email,'')), '') as written_by,
  a.rev, a.created_at, a.updated_at
from public.acts a
left join public.profiles pr on pr.id = a.created_by
left join public.profiles sp on sp.id = a.signed_by
where auth.uid() is not null;


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


-- Signing is where the definition stops being live and becomes part of the
-- document.
create or replace function public.sign_act(p_id uuid, p_rev bigint,
                                           p_signature text, p_rep_name text,
                                           p_signed_at timestamptz default null)
returns setof public.acts_v
language plpgsql security definer set search_path = ''
as $$
declare
  cur      public.acts%rowtype;
  who      text;
  v_at     timestamptz;
  v_claim  text := 'device';
  v_defs   jsonb;
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
    signature  = p_signature,
    signed_at  = v_at,
    signed_by  = auth.uid(),
    rep_name   = coalesce(nullif(p_rep_name,''), rep_name),
    field_defs = coalesce(v_defs, '{"header": [], "columns": []}'::jsonb),
    sign_log   = sign_log || jsonb_build_object(
                   'at', to_char(v_at at time zone 'UTC', 'YYYY-MM-DD"T"HH24:MI:SS"Z"'),
                   'received', to_char(now() at time zone 'UTC', 'YYYY-MM-DD"T"HH24:MI:SS"Z"'),
                   'clock', v_claim,
                   'action', 'signed',
                   'witness', who,
                   'rep', coalesce(nullif(p_rep_name,''), rep_name)),
    rev = rev + 1, updated_at = now(), updated_by = auth.uid()
  where id = p_id;

  return query select * from public.acts_v where id = p_id;
end $$;


-- Clearing the signature releases the act back to the live definition, since
-- it is an act being worked on again and not a document any more.
create or replace function public.unsign_act(p_id uuid, p_rev bigint)
returns setof public.acts_v
language plpgsql security definer set search_path = ''
as $$
declare
  cur public.acts%rowtype;
  who text;
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

  update public.acts set
    signature  = null,
    signed_at  = null,
    signed_by  = null,
    field_defs = null,
    sign_log   = sign_log || jsonb_build_object(
                   'at', to_char(now() at time zone 'UTC', 'YYYY-MM-DD"T"HH24:MI:SS"Z"'),
                   'action', 'cleared',
                   'witness', who,
                   'rep', cur.rep_name),
    rev = rev + 1, updated_at = now(), updated_by = auth.uid()
  where id = p_id;

  return query select * from public.acts_v where id = p_id;
end $$;


-- ------------------------------------------------------------
-- CHECK IT LANDED
-- ------------------------------------------------------------
do $$
declare n int;
begin
  select count(*) into n from information_schema.columns
   where table_schema='public' and table_name='acts' and column_name in ('extra','field_defs');
  if n <> 2 then raise exception 'expected 2 new act columns, found %', n; end if;

  select count(*) into n from public.act_fields;
  if n <> 1 then raise exception 'act_fields should hold exactly one row, holds %', n; end if;

  select count(*) into n from information_schema.columns
   where table_schema='public' and table_name='acts_v' and column_name in ('extra','field_defs');
  if n <> 2 then raise exception 'the view is missing the extras'; end if;

  -- the validator actually refuses what it is there to refuse
  begin
    perform public.check_act_fields('{"columns":[{"key":"a"},{"key":"b"},{"key":"c"},{"key":"d"}]}'::jsonb);
    raise exception 'four columns were accepted';
  exception when sqlstate '22023' then null;
  end;
  begin
    perform public.check_act_fields('{"header":[{"key":"Port Berth","label":"x"}]}'::jsonb);
    raise exception 'a key with spaces was accepted';
  exception when sqlstate '22023' then null;
  end;
  begin
    perform public.check_act_fields('{"header":[{"key":"a","label":"A"},{"key":"a","label":"B"}]}'::jsonb);
    raise exception 'a duplicate key was accepted';
  exception when sqlstate '22023' then null;
  end;
  perform public.check_act_fields('{"header":[{"key":"port","label":"Port / berth"}],"columns":[{"key":"hours","label":"Hours","num":true}]}'::jsonb);

  raise notice 'acts fifth pass OK: the company names its own fields, and a signed act keeps the list it was signed under';
end $$;
