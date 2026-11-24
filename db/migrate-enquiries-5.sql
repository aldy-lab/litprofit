-- ============================================================
-- MIGRATION 5: the SharePoint register's own columns
-- ============================================================
-- The register's source of truth is the SharePoint list "Litprofit tiekimo
-- užklausos". Its export carries four columns the Power BI extract did not:
--
--   Išstatyta                  -> invoiced_ex_vat   what was invoiced, which is
--                                 not always the price: SK26-100 and SK26-103
--                                 are invoiced at 50 % as advance payments
--   Apmokėta                   -> paid_ex_vat       what arrived, as a figure
--   Aplanko nuoroda            -> folder_url        the job's SharePoint folder
--   Galutinio pristatymo data  -> final_delivery_date
--
-- `paid` stays the boolean the screen toggles; paid_ex_vat is the amount the
-- list recorded. Both are kept because the list has a line paid MORE than it
-- was invoiced (26.6-25.3), and a boolean cannot say so.
--
-- The view is extended with `create or replace`, appending at the end: replace
-- may add columns but not reorder them, and save_enquiry / create_enquiry
-- return `setof enquiries_v`, so dropping the view would take them with it.
-- save_enquiry does not write these columns, so an edit on screen leaves the
-- imported figures as they were.
--
-- Safe to run more than once. Run after migrate-enquiries-4.sql.
begin;

alter table public.enquiries add column if not exists invoiced_ex_vat     numeric(14,2);
alter table public.enquiries add column if not exists paid_ex_vat         numeric(14,2);
alter table public.enquiries add column if not exists folder_url          text;
alter table public.enquiries add column if not exists final_delivery_date date;

create or replace view public.enquiries_v as
 SELECT id, number, client, description, enquiry_date, sent_to_supplier, supplier,
    quoted_to_client,
    public.enquiry_days_unquoted(quoted_to_client, enquiry_date, status) AS days_unquoted,
    status, po_date, cost_ex_vat, price_ex_vat,
    CASE WHEN cost_ex_vat IS NULL THEN NULL::numeric
         ELSE price_ex_vat - cost_ex_vat END AS margin_eur,
    CASE WHEN cost_ex_vat IS NULL OR price_ex_vat = 0::numeric THEN NULL::numeric
         ELSE round((price_ex_vat - cost_ex_vat) / price_ex_vat, 4) END AS margin_pct,
    delivered, paid, paid_date, invoice_no, owner, note, rev, created_at, updated_at, updated_by,
    invoiced_ex_vat, paid_ex_vat, folder_url, final_delivery_date
   FROM public.enquiries e
  WHERE public.sees_money();

commit;
