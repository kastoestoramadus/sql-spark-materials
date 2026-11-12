CREATE OR REPLACE TEMP VIEW q34 AS SELECT id, id % 4 AS k, id % 3 AS bucket FROM range(24);
