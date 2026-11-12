SELECT COUNT(*) FROM q25 e JOIN q25cutoff c ON unix_timestamp(CAST(concat(e.ts, '+00:00') AS TIMESTAMP)) >= c.cutoff_epoch;
