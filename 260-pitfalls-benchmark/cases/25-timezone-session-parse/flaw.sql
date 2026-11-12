SELECT COUNT(*) FROM q25 e JOIN q25cutoff c ON unix_timestamp(to_timestamp(e.ts, 'yyyy-MM-dd HH:mm:ss')) >= c.cutoff_epoch;
