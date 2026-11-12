CREATE OR REPLACE TEMP VIEW q09 AS SELECT * FROM VALUES (1,'old','2026-01-01'),(1,'new','2026-02-01'),(2,'only','2026-03-01') AS t(id,payload,ts);
