-- ============================================================
-- ACTS, SECOND PASS: the signature, on the screen
-- ============================================================
-- The act was already the sheet the customer's representative signs. It was
-- signed on PAPER: print it, hand over a pen, scan it, e-mail the scan, file
-- the scan. Five steps, of which four happen after everybody has left the
-- vessel, and the one that matters -- the scan reaching the folder -- is the
-- one nobody notices has not happened.
--
-- This puts the pen on the tablet the fitter is already holding. The
-- signature is a PNG drawn on a canvas, trimmed to the ink, stored on the
-- act, and printed onto the same line the pen used to go on.
--
-- Requires migrate-acts.sql. SAFE TO RUN MORE THAN ONCE.
--
-- ------------------------------------------------------------
-- WHY THE IMAGE IS ON THE ROW AND NOT IN THE BUCKET
-- ------------------------------------------------------------
-- Every other file in this app lives in storage, and this one deliberately
-- does not. A signature is not an attachment to the act; it IS the act. Put
-- it in the bucket and there are two systems with no transaction between
-- them, so the failure mode is an act that says it is signed pointing at an
-- object that was never written -- and the storage bucket is gated on
-- sees_money(), which is exactly the role that must NOT be required here.
--
-- The cost is row size, and it is small: a trimmed signature is a few
-- kilobytes of PNG. What keeps it small in practice is the app never asking
-- for the column when it draws a list -- see the note on the view.
--
-- ------------------------------------------------------------
-- WHY SIGNING LOCKS THE ACT
-- ------------------------------------------------------------
-- A signature is worth exactly as much as the certainty that the words above
-- it have not moved since. save_act() therefore refuses to touch a signed
-- act at all. Changing one means clearing the signature first, in the open,
-- and both the signing and the clearing are recorded on the row.
--
-- Clearing is open to anyone signed in, not restricted to an owner, and that
-- is deliberate: the person who needs it is the fitter who mistyped a
-- quantity and is still standing next to the chief engineer. Locking him out
-- would not protect the document, it would just move the correction onto a
-- second act nobody can reconcile with the first.
-- ============================================================

-- A data URL, and the constraint says so. The column is read back into an
-- <img src>, so "some text" is not good enough: anything that is not a PNG
-- data URL never reaches the table in the first place.
alter table public.acts add column if not exists signature text;
alter table public.acts add column if not exists signed_at  timestamptz;
alter table public.acts add column if not exists signed_by  uuid references auth.users(id);

-- Who signed and who cleared it, in order. Not a table: it is read only when
-- one act is open, never queried across acts, and a child table here would
-- buy a join and nothing else.
alter table public.acts add column if not exists sign_log jsonb not null default '[]'::jsonb;

do $$
begin
  if not exists (select 1 from pg_constraint where conname = 'acts_signature_chk') then
    alter table public.acts add constraint acts_signature_chk
      check (signature is null
             or (signature like 'data:image/png;base64,%'
                 and length(signature) between 100 and 400000));
  end if;
end $$;

-- Finding the unsigned ones is the question this table gets asked: an act
-- that was never signed is work that cannot be invoiced.
create index if not exists acts_unsigned_idx on public.acts (project_id)
  where signature is null;


-- ------------------------------------------------------------
-- THE VIEW
-- ------------------------------------------------------------
-- Dropped with every function that returns `setof public.acts_v` first --
-- they depend on it, and forgetting that is how the last two migrations
-- failed on their second run.
drop function if exists public.create_act(jsonb);
drop function if exists public.save_act(uuid, bigint, jsonb);
drop function if exists public.sign_act(uuid, bigint, text, text);
drop function if exists public.unsign_act(uuid, bigint);
drop view if exists public.acts_v;

create view public.acts_v as
select
  a.id, a.project_id, a.number, a.act_date,
  a.customer, a.imo, a.object, a.project_ref,
  a.lines, a.rep_name, a.note,
  (select count(*) from jsonb_array_elements(a.lines) l
    where coalesce(l->>'work','') <> '')::int as line_count,

  -- The image itself, and a boolean that answers "is it signed" WITHOUT it.
  -- The app selects columns by name and leaves `signature` out of the list
  -- query: a screen showing forty acts has no use for forty signatures, and
  -- the list is also what gets written to localStorage.
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


-- ------------------------------------------------------------
-- WRITES
-- ------------------------------------------------------------
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

-- Unchanged except for the lock. Note the signature is not in the accepted
-- keys and never was: it has its own entry point, because signing is an event
-- with a time and a witness and not a field somebody types.
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

  -- Raised, not silently ignored. A save that returns the row unchanged looks
  -- to the caller exactly like a save that worked.
  if cur.signature is not null then
    raise exception 'act is signed' using errcode = '42501';
  end if;

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


-- The signature arrives with the representative's name, because the two are
-- one act by one person at one moment. Signing an act that is already signed
-- is refused rather than overwritten -- the second signature would replace
-- the first with no trace of it.
create or replace function public.sign_act(p_id uuid, p_rev bigint,
                                           p_signature text, p_rep_name text)
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

  select coalesce(nullif(name,''), nullif(email,'')) into who
    from public.profiles where id = auth.uid();

  update public.acts set
    signature = p_signature,
    signed_at = now(),
    signed_by = auth.uid(),
    rep_name  = coalesce(nullif(p_rep_name,''), rep_name),
    sign_log  = sign_log || jsonb_build_object(
                  'at', to_char(now() at time zone 'UTC', 'YYYY-MM-DD"T"HH24:MI:SS"Z"'),
                  'action', 'signed',
                  'witness', who,
                  'rep', coalesce(nullif(p_rep_name,''), rep_name)),
    rev = rev + 1, updated_at = now(), updated_by = auth.uid()
  where id = p_id;

  return query select * from public.acts_v where id = p_id;
end $$;


-- Clearing keeps the log entry. The point of the log is that a signature
-- having been there once is not something the app can quietly undo.
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
    signature = null,
    signed_at = null,
    signed_by = null,
    sign_log  = sign_log || jsonb_build_object(
                  'at', to_char(now() at time zone 'UTC', 'YYYY-MM-DD"T"HH24:MI:SS"Z"'),
                  'action', 'cleared',
                  'witness', who,
                  'rep', cur.rep_name),
    rev = rev + 1, updated_at = now(), updated_by = auth.uid()
  where id = p_id;

  return query select * from public.acts_v where id = p_id;
end $$;


-- Deleting a signed act is still possible and still the same call. It is a
-- deliberate act with a confirmation in front of it, and an act signed by
-- mistake for the wrong vessel has to be removable.
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
  select count(*) into n from information_schema.columns
   where table_schema='public' and table_name='acts'
     and column_name in ('signature','signed_at','signed_by','sign_log');
  if n <> 4 then raise exception 'expected 4 new columns, found %', n; end if;

  select count(*) into n from information_schema.columns
   where table_schema='public' and table_name='acts_v'
     and column_name in ('signature','signed','signed_at','sign_log','witnessed_by');
  if n <> 5 then raise exception 'the view is missing the signature columns'; end if;

  select count(*) into n from pg_proc p join pg_namespace ns on ns.oid=p.pronamespace
   where ns.nspname='public'
     and p.proname in ('create_act','save_act','delete_act','sign_act','unsign_act');
  if n < 5 then raise exception 'expected 5 functions, found %', n; end if;

  -- the constraint actually rejects what it is there to reject
  begin
    insert into public.acts (number, signature) values ('__probe__', 'javascript:alert(1)');
    raise exception 'the signature constraint let a non-PNG through';
  exception when check_violation then null;
  end;
  delete from public.acts where number = '__probe__';

  raise notice 'acts second pass OK: signature, lock, and a log of both';
end $$;
