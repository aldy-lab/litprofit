-- ============================================================
-- ACTS, SIXTH PASS: six columns, and the paper turns sideways
-- ============================================================
-- The cap on work-table columns was three, and the reason given was that the
-- act is printed on A4 and columns do not fold. That reason was sound and the
-- conclusion was lazy: A4 has another orientation.
--
-- So the cap is six, and the printed sheet turns landscape once there are
-- more than three. Under that it stays portrait, because a portrait act is
-- what the form has always looked like and turning every sheet sideways to
-- accommodate a yard that added one column would be the wrong default.
--
-- Requires migrate-acts-5.sql. SAFE TO RUN MORE THAN ONCE.
-- ============================================================

create or replace function public.check_act_fields(p_defs jsonb)
returns void
language plpgsql immutable set search_path = ''
as $$
declare
  part text;
  arr  jsonb;
  el   jsonb;
  seen text[] := '{}';
  cap  int;
begin
  if p_defs is null or jsonb_typeof(p_defs) <> 'object' then
    raise exception 'the field definition must be an object' using errcode = '22023';
  end if;

  foreach part in array array['header', 'columns'] loop
    arr := coalesce(p_defs -> part, '[]'::jsonb);
    if jsonb_typeof(arr) <> 'array' then
      raise exception '% must be a list', part using errcode = '22023';
    end if;

    -- Six either way now. Header fields print in a block with room to spare;
    -- columns past three turn the sheet landscape, and past six even
    -- landscape stops holding a description wide enough to describe work.
    cap := 6;
    if jsonb_array_length(arr) > cap then
      raise exception 'at most % extra %s -- more will not print', cap, part
        using errcode = '22023';
    end if;

    for el in select * from jsonb_array_elements(arr) loop
      if coalesce(el->>'key','') !~ '^[a-z][a-z0-9_]{0,23}$' then
        raise exception 'bad field key %', coalesce(el->>'key','(none)')
          using errcode = '22023';
      end if;
      if btrim(coalesce(el->>'label','')) = '' then
        raise exception 'field % has no label', el->>'key' using errcode = '22023';
      end if;
      if length(el->>'label') > 40 then
        raise exception 'the label for % is too long to print', el->>'key'
          using errcode = '22023';
      end if;
      if (el->>'key') = any(seen) then
        raise exception 'two fields share the key %', el->>'key' using errcode = '22023';
      end if;
      seen := seen || (el->>'key');
    end loop;
  end loop;
end $$;


-- ------------------------------------------------------------
-- CHECK IT LANDED
-- ------------------------------------------------------------
do $$
begin
  -- six is allowed
  perform public.check_act_fields(
    '{"header":[],"columns":[{"key":"a","label":"A"},{"key":"b","label":"B"},
      {"key":"c","label":"C"},{"key":"d","label":"D"},{"key":"e","label":"E"},
      {"key":"f","label":"F"}]}'::jsonb);

  -- seven is not
  begin
    perform public.check_act_fields(
      '{"header":[],"columns":[{"key":"a","label":"A"},{"key":"b","label":"B"},
        {"key":"c","label":"C"},{"key":"d","label":"D"},{"key":"e","label":"E"},
        {"key":"f","label":"F"},{"key":"g","label":"G"}]}'::jsonb);
    raise exception 'seven columns were accepted';
  exception when sqlstate '22023' then null;
  end;

  -- and everything the fifth pass refused is still refused
  begin
    perform public.check_act_fields('{"header":[{"key":"Port Berth","label":"x"}]}'::jsonb);
    raise exception 'a key with spaces was accepted';
  exception when sqlstate '22023' then null;
  end;
  begin
    perform public.check_act_fields('{"header":[{"key":"a","label":"A"},{"key":"a","label":"B"}]}'::jsonb);
    raise exception 'a duplicate key was accepted';
  exception when sqlstate '22023' then null;
  end;
  begin
    perform public.check_act_fields('{"header":[{"key":"a","label":""}]}'::jsonb);
    raise exception 'a field with no label was accepted';
  exception when sqlstate '22023' then null;
  end;

  raise notice 'acts sixth pass OK: six columns, and the sheet turns landscape past three';
end $$;
