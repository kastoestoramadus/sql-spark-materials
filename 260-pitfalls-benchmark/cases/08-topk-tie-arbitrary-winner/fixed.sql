SELECT collect_list(player) AS tied_top FROM q08 WHERE score = (SELECT MAX(score) FROM q08);
