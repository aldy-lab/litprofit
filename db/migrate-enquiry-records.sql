-- ============================================================
-- ENQUIRY RECORDS: what the sales folder says, without the files
-- ============================================================
-- The year's sales folder is a folder per enquiry: quotes, invoices, payment
-- orders, e-mails, photographs -- 9,000 files, 4.6 GB. What the register
-- needs from it is the information, not the files: one row per document with
-- its type, date, number, amount, the other party, the e-mail's subject, and
-- where the file sits on the office disk. ~8,700 rows, a few MB.
--
-- Written only through import_enquiry_records(), which the calculator calls
-- in batches from Documents -> "Import a sales folder" with the manifest made
-- by tools/sales-manifest/. Idempotent: (enquiry_id, sha256) is unique and a
-- row already there is left alone, so the import can be run again.
--
-- Safe to run more than once.
begin;

create table if not exists public.enquiry_records (
  id           bigserial primary key,
  enquiry_id   uuid not null references public.enquiries(id) on delete cascade,
  sha256       text not null,
  kind         text not null default 'other',
  doc_date     date,
  ref          text,
  amount       numeric(14,2),
  counterparty text,
  title        text,
  detail       text,
  source       text,
  copies       int not null default 1,
  created_at   timestamptz not null default now(),
  unique (enquiry_id, sha256)
);
create index if not exists enquiry_records_enq_idx on public.enquiry_records (enquiry_id, doc_date);

alter table public.enquiry_records enable row level security;
drop policy if exists enquiry_records_read on public.enquiry_records;
create policy enquiry_records_read on public.enquiry_records
  for select to authenticated using (public.sees_money());
revoke all on public.enquiry_records from anon;
grant select on public.enquiry_records to authenticated;

create or replace function public.import_enquiry_records(p_rows jsonb)
returns int language plpgsql security definer set search_path = '' as $$
declare n int;
begin
  if not public.sees_money() then
    raise exception 'not permitted' using errcode = '42501';
  end if;
  insert into public.enquiry_records (enquiry_id, sha256, kind, doc_date, ref, amount,
                                      counterparty, title, detail, source, copies)
  select (r->>'enquiry_id')::uuid, r->>'sha256', coalesce(r->>'kind', 'other'),
         nullif(r->>'doc_date', '')::date, nullif(r->>'ref', ''),
         nullif(r->>'amount', '')::numeric, nullif(r->>'counterparty', ''),
         left(r->>'title', 500), left(r->>'detail', 2000), left(r->>'source', 600),
         coalesce(nullif(r->>'copies', '')::int, 1)
    from jsonb_array_elements(p_rows) r
   where nullif(r->>'enquiry_id', '') is not null
  on conflict (enquiry_id, sha256) do nothing;
  get diagnostics n = row_count;
  return n;
end $$;
revoke all on function public.import_enquiry_records(jsonb) from public, anon;
grant execute on function public.import_enquiry_records(jsonb) to authenticated;

-- the files are not uploaded after all: the bucket goes back to 25 MB
update storage.buckets set file_size_limit = 26214400 where id = 'documents';

commit;
