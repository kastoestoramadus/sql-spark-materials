SELECT id, payload, ts FROM (SELECT id, payload, ts, row_number() OVER (PARTITION BY id ORDER BY ts DESC) rn FROM q09) WHERE rn = 1;
