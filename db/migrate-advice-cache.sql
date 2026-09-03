-- ============================================================
-- ADVICE CACHE: keyed on the figures, not on a clock
-- ============================================================
-- The obvious cache here is "one call per day per user", which needs somebody
-- to decide what a day is and leaves the panel showing this morning's advice
-- after somebody has spent the afternoon filling in costs.
--
-- The key is a hash of the fact sheet itself. Same figures, same advice, no
-- call. Edit one enquiry and the sheet is different, the hash is different,
-- and the next press pays for a fresh answer. Nothing expires by hand and
-- nothing goes stale in a way a reader can notice, because the only thing
-- that could make it stale is the thing the key is made of.
--
-- The cache stores the advice sheet itself, so it is gated the same way it
-- is: sees_company(), not sees_money(). A cache that answers a wider
-- audience than the thing it caches is a hole with a timestamp on it.
--
-- Requires migrate-advice.sql (which defines sees_company()).
-- SAFE TO RUN MORE THAN ONCE.
-- ============================================================

create table if not exists public.advice_cache (
  id         text primary key,
  advice     jsonb not null,
  lang       text  not null default 'en',
  model      text,
  created_at timestamptz not null default now()
);

alter table public.advice_cache enable row level security;

-- No policies, deliberately. Deny-all is the policy here as it is on every
-- other table in this schema: the two functions below are the way in, and the
-- grants are taken away so that adding a policy one day for some unrelated
-- reason cannot quietly wake up a table grant behind it.
revoke all on public.advice_cache from anon, authenticated;

create or replace function public.advice_cache_get(p_id text)
returns jsonb
language plpgsql stable security definer set search_path = ''
as $$
declare a jsonb;
begin
  if not public.sees_company() then
    raise exception 'not allowed' using errcode = 'insufficient_privilege';
  end if;
  -- The age check lives here rather than in the edge function, so the clock
  -- that decides it is the database's and not whichever machine happened to
  -- serve the request.
  select advice into a from public.advice_cache
   where id = p_id and created_at > now() - interval '24 hours';
  return a;
end $$;

create or replace function public.advice_cache_put(p_id text, p_advice jsonb,
                                                   p_lang text, p_model text)
returns void
language plpgsql security definer set search_path = ''
as $$
begin
  if not public.sees_company() then
    raise exception 'not allowed' using errcode = 'insufficient_privilege';
  end if;
  insert into public.advice_cache (id, advice, lang, model, created_at)
  values (p_id, p_advice, coalesce(p_lang, 'en'), p_model, now())
  on conflict (id) do update
    set advice = excluded.advice, lang = excluded.lang,
        model = excluded.model, created_at = now();

  -- Kept small on the way past rather than by a scheduled job nobody
  -- remembers exists. A week of sheets is more history than anything reads.
  delete from public.advice_cache where created_at < now() - interval '7 days';
end $$;

revoke execute on all functions in schema public from public, anon;
grant execute on function public.advice_cache_get(text) to authenticated;
grant execute on function public.advice_cache_put(text, jsonb, text, text) to authenticated;


-- ============================================================
-- CHECK IT LANDED
-- ============================================================
do $$
declare n int; ok boolean := false;
begin
  select count(*) into n from information_schema.role_table_grants
   where table_schema = 'public' and table_name = 'advice_cache'
     and grantee in ('anon', 'authenticated');
  if n > 0 then raise exception 'advice_cache carries table grants'; end if;

  if has_function_privilege('anon', 'public.advice_cache_get(text)', 'EXECUTE') then
    raise exception 'anon can read the advice cache';
  end if;

  -- The gate, asserted by making it fire: this block carries no JWT, so it is
  -- exactly the caller that must be refused.
  begin
    perform public.advice_cache_get('nothing');
  exception when insufficient_privilege then ok := true;
  end;
  if not ok then raise exception 'the cache answered a caller with no role'; end if;

  raise notice 'advice_cache OK: no table grants, both functions gated';
end $$;
