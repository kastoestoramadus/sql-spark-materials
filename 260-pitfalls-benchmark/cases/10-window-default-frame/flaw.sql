SELECT evt, amt, SUM(amt) OVER (PARTITION BY acct ORDER BY evt) AS running FROM q10 ORDER BY evt, amt;
