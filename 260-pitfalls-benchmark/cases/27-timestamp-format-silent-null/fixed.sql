SELECT to_timestamp(ts, 'dd/MM/yyyy HH:mm') AS parsed, try_to_timestamp(ts, 'yyyy-MM-dd HH:mm') IS NULL AS parse_failed FROM q27;
