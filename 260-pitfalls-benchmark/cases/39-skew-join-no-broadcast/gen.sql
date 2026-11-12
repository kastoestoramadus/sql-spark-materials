CREATE OR REPLACE TEMP VIEW q39 AS SELECT id, CASE WHEN id < 18000 THEN 0 ELSE id END AS k FROM range(20000);
CREATE OR REPLACE TEMP VIEW q39dim AS SELECT k, label, lpad(label, 3000000, 'z') AS pad FROM VALUES (0, 'hot'), (1, 'a'), (2, 'b'), (3, 'c'), (4, 'd') AS t(k, label);
