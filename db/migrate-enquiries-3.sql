-- ============================================================
-- MIGRATION 3: the save that reported a conflict every time it worked
-- ============================================================
-- Editing a cost wrote the value to the database and then told the person it
-- had not been saved. Both halves of that were this file's fault.
--
-- save_enquiry was declared `returns public.enquiries`. PostgREST answers a
-- function returning one composite with a JSON OBJECT; a function returning
-- SETOF answers with an ARRAY. save_project is SETOF, so the client reads
-- rows[0] -- and against an object, rows[0] is undefined, which the client
-- takes to mean nobody's row came back, which it reports as somebody else
-- having saved first. The write had already committed.
--
-- The second half: it returned the TABLE row, which has no margin_eur, no
-- margin_pct and no days_unquoted -- those are computed by the view. So the
-- row written back into the screen had no margin in it, and the cell you had
-- just filled in would have gone blank.
--
-- Both are fixed by returning `setof public.enquiries_v`: an array, and the
-- same shape the register was loaded with.
--
-- Conflict handling changes with it, to the contract save_project already
-- uses: an empty result means somebody saved first. Raising an exception for
-- that is indistinguishable, at the client, from the network failing.
--
-- Safe to run more than once. Run after migrate-enquiries-2.sql.
--   psql "$SUPABASE_DB_URL" -v ON_ERROR_STOP=1 -f db/migrate-enquiries-3.sql

begin;

-- the return type changes, so the old signatures have to go first
drop function if exists public.save_enquiry(uuid, bigint, jsonb);
drop function if exists public.create_enquiry(jsonb);

create function public.save_enquiry(p_id uuid, p_rev bigint, p_row jsonb)
returns setof public.enquiries_v
language plpgsql security definer set search_path = ''
as $$
declare cur public.enquiries%rowtype;
begin
  if not public.sees_money() then
    raise exception 'not permitted' using errcode = '42501';
  end if;
  select * into cur from public.enquiries where id = p_id;
  if not found then return; end if;
  -- a null revision is a deliberate overwrite, as it is for a project
  if p_rev is not null and cur.rev <> p_rev then return; end if;

  update public.enquiries set
    number = coalesce(p_row->>'number', number),
    client = p_row->>'client',
    description = p_row->>'description',
    enquiry_date = nullif(p_row->>'enquiry_date','')::date,
    sent_to_supplier = coalesce((p_row->>'sent_to_supplier')::boolean, false),
    supplier = p_row->>'supplier',
    quoted_to_client = coalesce((p_row->>'quoted_to_client')::boolean, false),
    status = coalesce(p_row->>'status', status),
    po_date = nullif(p_row->>'po_date','')::date,
    -- nullif before the cast: an empty box stays "not known" rather than
    -- becoming a cost of zero and inventing a 100% margin
    cost_ex_vat = nullif(p_row->>'cost_ex_vat','')::numeric,
    price_ex_vat = coalesce((p_row->>'price_ex_vat')::numeric, 0),
    delivered = coalesce((p_row->>'delivered')::boolean, false),
    paid = coalesce((p_row->>'paid')::boolean, false),
    paid_date = nullif(p_row->>'paid_date','')::date,
    invoice_no = p_row->>'invoice_no',
    owner = p_row->>'owner',
    note = p_row->>'note',
    rev = rev + 1,
    updated_at = now(),
    updated_by = auth.uid()
  where id = p_id;

  return query select * from public.enquiries_v where id = p_id;
end $$;

create function public.create_enquiry(p_row jsonb)
returns setof public.enquiries_v
language plpgsql security definer set search_path = ''
as $$
declare new_id uuid;
begin
  if not public.sees_money() then
    raise exception 'not permitted' using errcode = '42501';
  end if;
  insert into public.enquiries (number, client, description, enquiry_date,
      sent_to_supplier, supplier, quoted_to_client, status, po_date,
      cost_ex_vat, price_ex_vat, delivered, paid, paid_date, invoice_no, owner, note)
  values (coalesce(nullif(p_row->>'number',''), 'NEW'),
      p_row->>'client', p_row->>'description', nullif(p_row->>'enquiry_date','')::date,
      coalesce((p_row->>'sent_to_supplier')::boolean, false), p_row->>'supplier',
      coalesce((p_row->>'quoted_to_client')::boolean, false),
      coalesce(nullif(p_row->>'status',''), 'Vykdoma'), nullif(p_row->>'po_date','')::date,
      nullif(p_row->>'cost_ex_vat','')::numeric,
      coalesce((p_row->>'price_ex_vat')::numeric, 0),
      coalesce((p_row->>'delivered')::boolean, false),
      coalesce((p_row->>'paid')::boolean, false),
      nullif(p_row->>'paid_date','')::date, p_row->>'invoice_no',
      p_row->>'owner', p_row->>'note')
  returning id into new_id;
  return query select * from public.enquiries_v where id = new_id;
end $$;

grant execute on function public.save_enquiry(uuid, bigint, jsonb) to authenticated;
grant execute on function public.create_enquiry(jsonb)             to authenticated;

commit;
