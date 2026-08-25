-- ============================================================
-- MIGRATION 4: a history for the register
-- ============================================================
-- Projects keep public.project_history. Enquiries kept nothing, so a price
-- changed from 28,295.49 to something else left no trace of what it had been
-- or who changed it -- on a register several people edit, in a table where a
-- single click now toggles "paid".
--
-- One row per change, written by a trigger rather than by the application:
-- anything that reaches the table is recorded, including a correction made
-- straight from the SQL editor, which is exactly when somebody later wants to
-- know what happened.
--
-- Safe to run more than once. Run after migrate-enquiries-3.sql.
--   psql "$SUPABASE_DB_URL" -v ON_ERROR_STOP=1 -f db/migrate-enquiries-4.sql

begin;

create table if not exists public.enquiry_history (
  id           bigserial primary key,
  enquiry_id   uuid not null references public.enquiries(id) on delete cascade,
  at           timestamptz not null default now(),
  by_user      uuid,
  -- what changed, old and new, one row per change rather than a whole copy of
  -- the record: the question asked afterwards is always "what moved"
  field        text not null,
  was          text,
  now_is       text
);

create index if not exists enquiry_history_idx on public.enquiry_history (enquiry_id, at desc);

alter table public.enquiry_history enable row level security;

create or replace function public.enquiry_track()
returns trigger
language plpgsql security definer set search_path = ''
as $$
declare
  f text;
  o text;
  n text;
begin
  -- the fields worth a line in a log: money, status, and the two flags that a
  -- single click can flip
  foreach f in array array['number','client','description','enquiry_date','supplier',
                           'sent_to_supplier','quoted_to_client','status','po_date',
                           'cost_ex_vat','price_ex_vat','delivered','paid','paid_date',
                           'invoice_no','owner']
  loop
    execute format('select ($1).%I::text, ($2).%I::text', f, f)
      into o, n using old, new;
    if o is distinct from n then
      insert into public.enquiry_history (enquiry_id, by_user, field, was, now_is)
      values (new.id, auth.uid(), f, o, n);
    end if;
  end loop;
  return new;
end $$;

drop trigger if exists enquiries_history on public.enquiries;
create trigger enquiries_history
  after update on public.enquiries
  for each row execute function public.enquiry_track();

-- Same rule as the register itself: no money, no history. The history holds
-- prices, so it is not a way around the view.
create or replace view public.enquiry_history_v as
select h.id, h.enquiry_id, h.at, h.by_user, h.field, h.was, h.now_is
from public.enquiry_history h
where public.sees_money();

revoke all on public.enquiry_history   from anon, authenticated;
revoke all on public.enquiry_history_v from anon;
grant select on public.enquiry_history_v to authenticated;

commit;
