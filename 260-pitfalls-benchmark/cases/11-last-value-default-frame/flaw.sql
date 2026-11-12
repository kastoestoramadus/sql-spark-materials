SELECT evt, amt, LAST_VALUE(amt) OVER (ORDER BY evt) AS last_amt FROM q11 ORDER BY evt;
