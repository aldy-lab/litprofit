-- ============================================================
-- ACTS, THIRD PASS: when it was signed, not when it arrived
-- ============================================================
-- sign_act() stamped now(), which is right for a signature drawn on a screen
-- that is talking to this database at that moment. It is wrong for the case
-- the whole feature exists to serve: a vessel has no signal, the act is
-- signed on board at two in the afternoon and reaches here at six when the
-- tablet is back in the office. The paper would say six.
--
-- So the moment comes from the device that held the pen, and the moment it
-- was received is kept beside it in the log. One of those two numbers is what
-- the document says; the other is what the record says; they are not the same
-- fact and they were never going to stay equal.
--
-- Requires migrate-acts-2.sql. SAFE TO RUN MORE THAN ONCE.
--
-- ------------------------------------------------------------
-- A CLIENT CLOCK IS NOT A SOURCE OF TRUTH
-- ------------------------------------------------------------
-- Which is why it is clamped rather than trusted. A tablet whose clock is
-- wrong -- flat battery, wrong time zone, somebody fixing a licence check --
-- would otherwise stamp an act next year, and a signature dated in the future
-- is worse than one dated late.
--
--   later than now      -> now. Nothing is signed in the future.
--   older than 30 days  -> now, and the log says the claim was rejected.
--
-- Thirty days is longer than any tablet stays out of signal and shorter than
-- the window in which a wrong date stops being noticeable.
-- ============================================================

drop function if exists public.sign_act(uuid, bigint, text, text);
drop function if exists public.sign_act(uuid, bigint, text, text, timestamptz);

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

  update public.acts set
    signature = p_signature,
    signed_at = v_at,
    signed_by = auth.uid(),
    rep_name  = coalesce(nullif(p_rep_name,''), rep_name),
    sign_log  = sign_log || jsonb_build_object(
                  'at', to_char(v_at at time zone 'UTC', 'YYYY-MM-DD"T"HH24:MI:SS"Z"'),
                  -- when this database heard about it, which is a different
                  -- fact from when the pen moved and is kept as one
                  'received', to_char(now() at time zone 'UTC', 'YYYY-MM-DD"T"HH24:MI:SS"Z"'),
                  'clock', v_claim,
                  'action', 'signed',
                  'witness', who,
                  'rep', coalesce(nullif(p_rep_name,''), rep_name)),
    rev = rev + 1, updated_at = now(), updated_by = auth.uid()
  where id = p_id;

  return query select * from public.acts_v where id = p_id;
end $$;


-- ------------------------------------------------------------
-- CHECK IT LANDED
-- ------------------------------------------------------------
do $$
declare
  n int;
  args text;
begin
  select count(*), max(pg_get_function_arguments(p.oid)) into n, args
    from pg_proc p join pg_namespace ns on ns.oid = p.pronamespace
   where ns.nspname = 'public' and p.proname = 'sign_act';
  -- exactly one, or PostgREST has two overloads to choose between and picks
  -- by the keys sent, which is a coin toss nobody wants on this call
  if n <> 1 then raise exception 'expected 1 sign_act, found %', n; end if;
  if args not like '%p_signed_at%' then
    raise exception 'sign_act does not take a signing time: %', args;
  end if;
  -- pg_get_function_arguments renders the keyword in upper case; matched
  -- case-insensitively rather than by guessing which way round it comes out
  if args !~* 'p_signed_at[^,]*default' then
    raise exception 'p_signed_at must have a default, or the old four-argument call breaks: %', args;
  end if;

  raise notice 'acts third pass OK: the device says when, the log says when it arrived';
end $$;
