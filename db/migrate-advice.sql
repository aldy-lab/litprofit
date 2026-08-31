-- ============================================================
-- ADVICE: the facts, computed here, so nothing has to be believed
-- ============================================================
-- The Advice button sends a company's figures to a language model and shows
-- what comes back. The single thing that decides whether that is useful or
-- dangerous is WHO DOES THE ARITHMETIC.
--
-- A model handed rows and asked "how are we doing" will produce a number. It
-- will be plausible, it will be formatted like the real ones, and nothing on
-- the screen will say which of the figures in front of the reader was
-- measured and which was invented. On a screen an owner uses to decide what
-- to charge, that is not a rough edge; it is the whole risk.
--
-- So the database computes every figure and this function is the only source
-- of them. The model receives a finished fact sheet and does the one thing it
-- is genuinely better at: deciding which three of twenty facts matter this
-- week, and saying so in a sentence. It is told, in its own instructions,
-- that it may not compute -- and because every number it is allowed to quote
-- is already in the sheet, that instruction is checkable rather than hopeful.
--
-- WHAT IT REFUSES TO ANSWER
-- -------------------------
-- Every block carries its own `enough` flag and the count behind it. Margin
-- on this database today would be one enquiry out of 217 -- a number with the
-- shape of an answer and none of the meaning. The block reports enough=false
-- and the coverage that would fix it, exactly as the break-even screen
-- already refuses rather than inventing. Advice the data cannot support is
-- the failure mode worth designing against here: it is confident, it is
-- wrong, and it is about somebody's business.
--
-- NO NAMES OF PEOPLE
-- ------------------
-- Salaries and the people attached to them are not in this sheet and will not
-- be. The burn block carries totals -- what the company spends in a month --
-- which is what an owner asks about; who earns what is nobody's business
-- outside this database and certainly not a third party's. `owner` on an
-- enquiry is a person too, so the desk breakdown is by count and share under
-- a label the caller resolves, never by name.
--
-- Client names ARE here, because "your largest client is 34% of turnover" is
-- worth acting on and "one of your clients" is not. They are anonymised one
-- layer up, in the edge function, before anything leaves the building: the
-- model sees CLIENT_1 and the browser puts the real name back. The company's
-- customer list is its own.
--
-- Requires migrate-enquiries.sql, migrate-company.sql. SAFE TO RUN MORE THAN ONCE.
-- ============================================================

create or replace function public.advice_facts()
returns jsonb
language plpgsql
stable
security definer
set search_path = ''
as $$
declare
  j          jsonb;
  n_all      int;
  n_cost     int;
  n_decided  int;
  won_n      int;
  won_eur    numeric;
  lost_n     int;
  lost_eur   numeric;
  open_n     int;
  open_eur   numeric;
  today      date := current_date;
begin
  -- Same gate as every other figure on this screen. An employee cannot see
  -- revenue anywhere else in the application and must not receive it wrapped
  -- in a paragraph of advice either.
  if not public.sees_money() then
    raise exception 'not allowed' using errcode = 'insufficient_privilege';
  end if;

  select count(*), count(cost_ex_vat) into n_all, n_cost from public.enquiries;

  select
    count(*) filter (where status = 'Gautas PO'),
    coalesce(sum(price_ex_vat) filter (where status = 'Gautas PO'), 0),
    count(*) filter (where status = 'Atmesta užklausa'),
    coalesce(sum(price_ex_vat) filter (where status = 'Atmesta užklausa'), 0),
    count(*) filter (where status = 'Vykdoma'),
    coalesce(sum(price_ex_vat) filter (where status = 'Vykdoma'), 0)
  into won_n, won_eur, lost_n, lost_eur, open_n, open_eur
  from public.enquiries;

  n_decided := won_n + lost_n;

  j := jsonb_build_object(
    'generated_at', to_char(now(), 'YYYY-MM-DD'),
    'currency', 'EUR'
  );

  -- ---------- period ----------
  j := j || jsonb_build_object('period', (
    select jsonb_build_object(
             'from', min(enquiry_date), 'to', max(enquiry_date),
             'months', greatest(1, (extract(year from age(max(enquiry_date), min(enquiry_date))) * 12
                                  + extract(month from age(max(enquiry_date), min(enquiry_date))))::int))
      from public.enquiries));

  -- ---------- the funnel ----------
  -- Two win rates on purpose. By count answers "how often do we win"; by
  -- value answers "do we win the ones worth winning", and they can disagree
  -- sharply -- a desk that wins nine small jobs and loses one large one looks
  -- excellent by count and is not. Only decided rows are counted either way:
  -- treating everything still open as a loss reports a collapsing hit rate
  -- every time the desk gets busy, which is exactly backwards.
  j := j || jsonb_build_object('funnel', jsonb_build_object(
    'enquiries', n_all,
    'won', won_n, 'won_eur', round(won_eur),
    'lost', lost_n, 'lost_eur', round(lost_eur),
    'open', open_n, 'open_eur', round(open_eur),
    'decided', n_decided,
    'win_rate_count', case when n_decided > 0
                      then round(won_n::numeric / n_decided, 4) end,
    'win_rate_value', case when (won_eur + lost_eur) > 0
                      then round(won_eur / (won_eur + lost_eur), 4) end,
    'enough', n_decided >= 20));

  -- ---------- who buys ----------
  j := j || jsonb_build_object('clients', (
    select coalesce(jsonb_agg(x order by (x->>'won_eur')::numeric desc), '[]'::jsonb) from (
      select jsonb_build_object(
               'client', client,
               'won', count(*) filter (where status = 'Gautas PO'),
               'won_eur', round(coalesce(sum(price_ex_vat)
                                 filter (where status = 'Gautas PO'), 0)),
               'asked', count(*),
               'share', case when won_eur > 0
                        then round(coalesce(sum(price_ex_vat)
                             filter (where status = 'Gautas PO'), 0) / won_eur, 4) end) as x
        from public.enquiries
       where coalesce(client, '') <> ''
       group by client
      having count(*) filter (where status = 'Gautas PO') > 0) s));

  -- ---------- how long it takes ----------
  -- Median, not mean. In a register kept by hand there is always one enquiry
  -- that sat for two years, and it drags an average far enough to be useless.
  j := j || jsonb_build_object('cycle', (
    select jsonb_build_object(
             'days_to_po', percentile_cont(0.5) within group (order by (po_date - enquiry_date)),
             'n', count(*),
             'enough', count(*) >= 10)
      from public.enquiries
     where po_date is not null and enquiry_date is not null
       and po_date >= enquiry_date and po_date - enquiry_date < 3650));

  -- ---------- what is going stale ----------
  -- The register's own overdue list, in the two shapes it actually takes: a
  -- price never sent, and a price sent that nobody ever answered.
  -- An enquiry with no quote sent has no price yet, so the value of that pile
  -- is not zero -- it is unknown, and those are not the same sentence. The
  -- euro figure here reported 0 against 23 rows on the live register, which
  -- reads as a broken sum rather than as "nobody has priced these". Count
  -- them, and say how many carry a price at all.
  j := j || jsonb_build_object('stale', jsonb_build_object(
    'no_quote_over_14d', (select count(*) from public.enquiries
       where not coalesce(quoted_to_client, false) and status = 'Vykdoma'
         and enquiry_date < today - 14),
    'no_quote_over_14d_priced', (select count(*) from public.enquiries
       where not coalesce(quoted_to_client, false) and status = 'Vykdoma'
         and enquiry_date < today - 14 and coalesce(price_ex_vat, 0) > 0),
    'quoted_undecided_over_30d', (select count(*) from public.enquiries
       where coalesce(quoted_to_client, false) and status = 'Vykdoma'
         and enquiry_date < today - 30),
    'quoted_undecided_over_30d_eur', (select round(coalesce(sum(price_ex_vat), 0))
       from public.enquiries
       where coalesce(quoted_to_client, false) and status = 'Vykdoma'
         and enquiry_date < today - 30),
    'quoted_undecided_over_90d', (select count(*) from public.enquiries
       where coalesce(quoted_to_client, false) and status = 'Vykdoma'
         and enquiry_date < today - 90)));

  -- ---------- the season ----------
  j := j || jsonb_build_object('by_month', (
    select coalesce(jsonb_agg(jsonb_build_object(
             'month', m, 'enquiries', n, 'won', w, 'won_eur', e) order by m), '[]'::jsonb)
      from (select to_char(enquiry_date, 'YYYY-MM') as m,
                   count(*) as n,
                   count(*) filter (where status = 'Gautas PO') as w,
                   round(coalesce(sum(price_ex_vat)
                         filter (where status = 'Gautas PO'), 0)) as e
              from public.enquiries
             where enquiry_date is not null
             group by 1) s));

  -- ---------- margin, if it can be answered at all ----------
  -- One priced row out of two hundred is not a margin, it is an anecdote.
  -- The threshold is deliberately blunt: below it the block says so and says
  -- what would fix it, and the model is told it may not reason about
  -- profitability from a block whose `enough` is false.
  j := j || jsonb_build_object('margin', (
    select jsonb_build_object(
             'rows_with_cost', n_cost,
             'rows_total', n_all,
             'coverage', case when n_all > 0 then round(n_cost::numeric / n_all, 4) end,
             'won_with_cost', count(*),
             'sold_eur', round(coalesce(sum(price_ex_vat), 0)),
             'cost_eur', round(coalesce(sum(cost_ex_vat), 0)),
             'margin_pct', case when coalesce(sum(price_ex_vat), 0) > 0
                           then round((sum(price_ex_vat) - sum(cost_ex_vat))
                                      / sum(price_ex_vat), 4) end,
             'enough', count(*) >= 15)
      from public.enquiries
     where status = 'Gautas PO' and cost_ex_vat is not null and price_ex_vat is not null));

  -- ---------- what is not filled in ----------
  -- The block that earns its place on a register this young. Everything the
  -- model cannot say is downstream of these three columns, so the sheet names
  -- them rather than leaving the reader to wonder why the advice is thin.
  j := j || jsonb_build_object('coverage', jsonb_build_object(
    'rows', n_all,
    'missing_cost', n_all - n_cost,
    'missing_owner', (select count(*) from public.enquiries where coalesce(owner, '') = ''),
    'delivered_unpaid', (select count(*) from public.enquiries
                          where coalesce(delivered, false) and not coalesce(paid, false)),
    'delivered_unpaid_eur', (select round(coalesce(sum(price_ex_vat), 0))
                               from public.enquiries
                              where coalesce(delivered, false) and not coalesce(paid, false)),
    'people', (select count(*) from public.people),
    'overheads', (select count(*) from public.overheads),
    'projects', (select count(*) from public.projects)));

  -- ---------- what it costs to open the doors ----------
  -- Totals only, and only to an owner. sees_payroll() rather than
  -- sees_money(): this is the payroll gate everywhere else in the schema and
  -- a sum is still a payroll figure.
  if public.sees_payroll() then
    j := j || jsonb_build_object('burn', (
      select jsonb_build_object(
               'headcount', b.headcount,
               'payroll_month', round(b.payroll),
               'overheads_month', round(b.overheads),
               'burn_month', round(b.burn),
               -- one person and one overhead row is a database somebody has
               -- started filling in, not a company's cost base
               'enough', b.headcount >= 3)
        from public.company_burn() b));
  end if;

  -- ---------- the jobs themselves ----------
  j := j || jsonb_build_object('projects', (
    select jsonb_build_object('n', count(*), 'enough', count(*) >= 3)
      from public.projects));

  return j;
end $$;

revoke execute on all functions in schema public from public, anon;
grant execute on function public.advice_facts() to authenticated;


-- ============================================================
-- CHECK IT LANDED
-- ============================================================
do $$
declare
  j   jsonb;
  ok  boolean := false;
begin
  if has_function_privilege('anon', 'public.advice_facts()', 'EXECUTE') then
    raise exception 'anon can call advice_facts';
  end if;
  if not has_function_privilege('authenticated', 'public.advice_facts()', 'EXECUTE') then
    raise exception 'the app cannot call advice_facts';
  end if;

  -- The gate, asserted by making it fire. This block runs as the migration
  -- role, which carries no JWT and therefore no my_role(), so a caller with
  -- no business seeing revenue is exactly what is standing here -- and the
  -- function must refuse it. Checking that the gate REFUSES is worth more
  -- than checking that it permits: a gate that never fires is the one that
  -- gets deleted by accident and nothing notices.
  begin
    perform public.advice_facts();
  exception when insufficient_privilege then ok := true;
  end;
  if not ok then
    raise exception 'advice_facts answered a caller with no role';
  end if;

  raise notice 'advice OK: granted to authenticated, refused without a role';
end $$;
