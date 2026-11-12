SELECT /*+ BROADCAST(q39dim) */ q39dim.label, count(*) AS n FROM q39 JOIN q39dim ON q39.k = q39dim.k GROUP BY q39dim.label;
