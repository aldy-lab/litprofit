-- ============================================================
-- PAYMENTS: an invoice paid in parts
-- ============================================================
-- Clients pay in instalments -- an advance, the rest on delivery -- and the
-- register had one tick for "paid" and one amount. A payment is now a row:
-- the day, the share of the invoice in percent, the amount, a note. Either
-- the percent or the amount is typed; the screen works out the other from
-- the order total (the larger of the price and what has been invoiced).
--
-- The enquiry's own paid / paid_ex_vat / paid_date follow the payments, by
-- trigger, so every screen and report that already reads them stays right:
--   paid_ex_vat = the sum of the payments
--   paid        = the sum covers the order total (to the cent)
--   paid_date   = the day of the payment that completed it
--
-- What SharePoint recorded as paid is carried over as one payment per
-- enquiry ("Importuota iš SharePoint"), and an enquiry ticked paid with no
-- amount gets one 100 % payment, so nothing reads as owed that was not.
--
-- Safe to run more than once.
begin;

create table if not exists public.enquiry_payments (
  id          uuid primary key default gen_random_uuid(),
  enquiry_id  uuid not null references public.enquiries(id) on delete cascade,
  paid_on     date not null default current_date,
  pct         numeric(7,3),
  amount      numeric(14,2) not null check (amount >= 0),
  note        text,
  created_at  timestamptz not null default now(),
  created_by  uuid references auth.users(id) default auth.uid()
);
create index if not exists enquiry_payments_enq_idx on public.enquiry_payments (enquiry_id, paid_on);

alter table public.enquiry_payments enable row level security;
drop policy if exists enquiry_payments_read   on public.enquiry_payments;
drop policy if exists enquiry_payments_insert on public.enquiry_payments;
drop policy if exists enquiry_payments_update on public.enquiry_payments;
drop policy if exists enquiry_payments_delete on public.enquiry_payments;
create policy enquiry_payments_read   on public.enquiry_payments for select to authenticated using (public.sees_money());
create policy enquiry_payments_insert on public.enquiry_payments for insert to authenticated with check (public.sees_money());
create policy enquiry_payments_update on public.enquiry_payments for update to authenticated using (public.sees_money()) with check (public.sees_money());
create policy enquiry_payments_delete on public.enquiry_payments for delete to authenticated using (public.sees_money());
revoke all on public.enquiry_payments from anon;
grant select, insert, update, delete on public.enquiry_payments to authenticated;

-- The share is of the whole order: the larger of the price and what has
-- been invoiced. Of the invoice alone, a 50 % advance invoice paid in full
-- read as "paid" while half the order was still to come.
--
-- Enforced BEFORE every update of an enquiry that has payments, so a price
-- or invoice changed later, or a "paid" tick sent by an older screen, cannot
-- leave the row disagreeing with its payments. The payments trigger only
-- touches the row to make that happen.
create or replace function public.enquiry_paid_from_payments()
returns trigger language plpgsql security definer set search_path = '' as $$
declare total numeric; last_day date; n int; base numeric;
begin
  select count(*), coalesce(sum(amount), 0), max(paid_on) into n, total, last_day
    from public.enquiry_payments where enquiry_id = new.id;
  if n = 0 then return new; end if;
  base := greatest(coalesce(new.invoiced_ex_vat, 0), coalesce(new.price_ex_vat, 0));
  new.paid_ex_vat := case when total > 0 then total end;
  new.paid        := base > 0 and total >= base - 0.01;
  new.paid_date   := case when new.paid then last_day end;
  return new;
end $$;
revoke all on function public.enquiry_paid_from_payments() from public, anon;
drop trigger if exists enquiry_paid_from_payments on public.enquiries;
create trigger enquiry_paid_from_payments before update on public.enquiries
  for each row execute function public.enquiry_paid_from_payments();

create or replace function public.enquiry_payments_roll()
returns trigger language plpgsql security definer set search_path = '' as $$
declare eid uuid; left_ int;
begin
  eid := coalesce(new.enquiry_id, old.enquiry_id);
  select count(*) into left_ from public.enquiry_payments where enquiry_id = eid;
  if left_ = 0 then
    -- the last payment removed: nothing paid any more
    update public.enquiries set paid_ex_vat = null, paid = false, paid_date = null,
           updated_at = now(), rev = rev + 1 where id = eid;
  else
    update public.enquiries set updated_at = now(), rev = rev + 1 where id = eid;
  end if;
  return null;
end $$;
revoke all on function public.enquiry_payments_roll() from public, anon;

drop trigger if exists enquiry_payments_roll on public.enquiry_payments;
create trigger enquiry_payments_roll after insert or update or delete on public.enquiry_payments
  for each row execute function public.enquiry_payments_roll();

-- what was already recorded as paid, carried over once
insert into public.enquiry_payments (enquiry_id, paid_on, pct, amount, note)
select e.id, coalesce(e.paid_date, e.po_date, current_date),
       round(100 * e.paid_ex_vat / nullif(greatest(coalesce(e.invoiced_ex_vat, 0), e.price_ex_vat), 0), 3),
       e.paid_ex_vat, 'Importuota iš SharePoint'
  from public.enquiries e
 where e.paid_ex_vat > 0
   and not exists (select 1 from public.enquiry_payments p where p.enquiry_id = e.id);
insert into public.enquiry_payments (enquiry_id, paid_on, pct, amount, note)
select e.id, coalesce(e.paid_date, e.po_date, current_date), 100,
       greatest(coalesce(e.invoiced_ex_vat, 0), e.price_ex_vat), 'Pažymėta kaip apmokėta'
  from public.enquiries e
 where e.paid and coalesce(e.paid_ex_vat, 0) = 0 and greatest(coalesce(e.invoiced_ex_vat, 0), e.price_ex_vat) > 0
   and not exists (select 1 from public.enquiry_payments p where p.enquiry_id = e.id);

commit;
