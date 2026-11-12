SELECT o.id, s.status FROM q05o o LEFT JOIN q05s s ON o.sid = s.sid WHERE s.status = 'OPEN';
