-- ============================================================
--  Ending someone's sessions when they are blocked
-- ============================================================
--  A block (auth ban) stops a NEW sign-in and stops a session being
--  refreshed, but a token already issued keeps working until it expires --
--  up to an hour. Deleting the person's sessions ends the refresh at once,
--  so the most a blocked person keeps is what is left of that one token.
--
--  Called only by the `users` edge function, which runs as service_role
--  after checking that the caller is an admin. Nobody else may execute it.
-- ============================================================

create or replace function public.users_end_sessions(p_user uuid)
returns void
language sql
security definer set search_path = ''
as $$
  delete from auth.sessions where user_id = p_user;
$$;

revoke all on function public.users_end_sessions(uuid) from public, anon, authenticated;
grant execute on function public.users_end_sessions(uuid) to service_role;
