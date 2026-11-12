# Digest — wątek SQL/Spark (190, 210, 220, 230, 260, 280 + scalone 200-270)

Paths are relative to `/home/walidus/ai-based-projects/idle-coordinator/data/`. Every quote carries file:line.

## 190 — evidence collector (2026-10-18)

1. Event logi Sparka niosą już rdzeń dowodu (plan fizyczny, pruned ReadSchema, metryki zadań) — kolektor nie potrzebuje nowej instrumentacji do analizy wstecznej. `"Spark event logs already carry the core evidence"` — `archive/archive-2026-10-19/results/190-sql-spark-evidence-collector/report.md:32`.
2. Prototyp działał end-to-end: `"final collect: 39 records over 9 apps/8 runs"` oraz `"collector: 39 records ({'workflow-definition': 6, 'run': 8, 'metrics': 7, 'plan': 10, 'gap': 2, 'table-schema': 6}), manifests=3 in 2 pages"` — `.../190-sql-spark-evidence-collector/report.md:17,25`.
3. ReadSchema jest column-PRUNED, więc "którą wersją schematu czytał ten run" da się udowodnić tylko dla dotkniętych kolumn; model wydaje werdykty `"NOT CURRENT / POSSIBLY OLDER / UNKNOWN / current"` zamiast zgadywać — `.../190-sql-spark-evidence-collector/report.md:38` (key finding 2).
4. OpenLineage 1.34.0 jako uzupełnienie, nie zamiennik: przechwytuje runId/jobs/dataset paths/columnLineage, ale nie emitował facetów plan/sql i działa tylko w przód — `.../190-sql-spark-evidence-collector/report.md:45`.
5. Ekosystem: Amundsen archived, Marquez/DataHub/OpenMetadata aktywne, Unity Catalog OSS "currently evolving" — `.../190-sql-spark-evidence-collector/report.md:47` + `survey.tsv` (wiersz `amundsen`, `unitycatalog`).

## 210 — wydajność i koszty (2026-10-17)

1. `"Exchange = shuffle boundary"` — każde Exchange to network+sort+ryzyko skew; broadcast usuwa jedno — `archive/archive-2026-10-19/results/210-sql-spark-performance-and-cost/report.md:40`.
2. Pomiar SortMergeJoin vs broadcast: `"SMJ 1.64s / 27.2MB shuffled vs broadcast 0.67s / 7.1MB"` — `.../210-sql-spark-performance-and-cost/report.md:43`.
3. AQE: plan wykonany "flips at runtime" — e04: 200-partycyjny reduce zbiegł do 1 zadania (0.99s → 0.31s); domyślne progi skew (64MB/256MB) nic nie robią w małej skali, dopóki się ich nie obniży — `.../210-sql-spark-performance-and-cost/report.md:48-51`.
4. Skew nie widać w statycznym planie: sygnał to max-vs-median task runtime w UI/event logu (e02: zadanie 4661 ms przy p50 255 ms, 18x straggler) — `.../210-sql-spark-performance-and-cost/report.md:46`.
5. Katalog 44 wierszy: 22 antipattern / 13 lever / 9 antipattern+lever, każda z symptom/detection/fix/measured effect — `.../210-sql-spark-performance-and-cost/report.md` (sekcja Deliverables, wiersz catalogue.tsv); plik: 44 wiersze danych (zweryfikowane: `wc -l catalogue.tsv` = 45).

## 220 — AI reviewer (2026-10-18)

1. Eksperyment czytania 12 case'ów × 4 warunki: `"SQL-only found ~7/10, SQL+plan and compact 9/10 (q05 skew and q08 data-format defects are in NO textual condition; skew showed only in the event log as max/median 17.1)"` — `archive/archive-2026-10-19/results/220-sql-spark-ai-reviewer-design/report.md:26`.
2. Taksonomia 26 failure-modes, ale tylko 14 źródeł fetch-verified — reszta uczciwie oznaczona folklore — `.../220-sql-spark-ai-reviewer-design/report.md:14-16`.
3. 14 mitigations z podziałem deterministic-script vs model-reasoning; M01-M06+M12 jako działające skrypty — `.../220-sql-spark-ai-reviewer-design/report.md:18`.
4. Compact-plan skrypt zwalidowany: `"scripts/test_compact.py = 13/13 PASS"` (q01 4435 → 3456 znaków) — `.../220-sql-spark-ai-reviewer-design/report.md:33-35`.
5. Rekomendacja decision.md: pipeline deterministic-first w kolejności lint → plan → skew → report — `.../220-sql-spark-ai-reviewer-design/report.md:37`.

## 230 — narzędzia Windows+Docker (2026-10-18)

1. Docker Desktop daemon leżał ( `"open //./pipe/docker_engine: The system cannot find the file specified"` ) — wszystkie 3 Dockerfiles nietestowane; to największa dziura wątku dla scenariusza bankowego — `archive/archive-2026-10-19/results/230-sql-spark-tools-on-windows-docker/report.md` (tabela Step 0) i `handoff.md:30-32`.
2. pydeequ 1.7.0 nie działa na żadnej macierzy: `"blocked: runs fail on both Spark 3.5.9-py3.11 and 4.2.0 with py4j.Py4JException: Method iterableAsScalaIterable([class java.lang.String]) does not exist"` — `.../230-sql-spark-tools-on-windows-docker/report.md:60`.
3. Event log: 3.5.9 pisze pojedynczy plik (2.1 MB), 4.2.0 katalog `eventlog_v2_local-*` — istotne dla konfiguracji history servera w banku — `.../230-sql-spark-tools-on-windows-docker/report.md:33`.
4. EXPLAIN FORMATTED i COST działają lokalnie; sqlglot transpiluje spark→postgres/databricks i pokazuje błąd parsowania z podświetleniem tokenu — `.../230-sql-spark-tools-on-windows-docker/report.md:35-40`.
5. DataFlint zweryfikowany tylko jako rejestracja zakładki w UI (headless), nie zawartość heat-map/skew — `.../230-sql-spark-tools-on-windows-docker/report.md:54`.

## 260 — pułapki + benchmark (2026-10-18..19)

1. `"35 pitfalls reproduced on Spark 4.2.0 local mode (+ pyspark 3.5.1, DuckDB 1.5.6, sqlite 3.54.0 ...), all 40 benchmark cases built and verified with hidden keys, decoys and run-proven oracles"` — `archive/archive-2026-10-19/results/260-sql-spark-pitfalls-and-benchmark/report.md:18`.
2. Podział lint vs dane: 12 pułapek łapalnych parserem, 23 wymagają danych/statystyk — `.../260-sql-spark-pitfalls-and-benchmark/report.md:37`.
3. TPC-H sf=0.1 lokalnie z oracle różnicowym DuckDB-vs-Spark: suma revenue zgadza się między silnikami — `.../260-sql-spark-pitfalls-and-benchmark/report.md:41` + `repro/tpch/tpch-run.txt`.
4. Benchmark 40 case'ów: correctness 33 / performance 3 / cost 3 / maintainability 1; trudność 15/15/10 — `.../260-sql-spark-pitfalls-and-benchmark/report.md:20`.
5. Słabe punkty uczciwie oznaczone: case 25 (oracle porównania liczby), case 34 (kolejność w ramach remisu), brak TPC-DS, mypy --strict nie przechodził — `.../260-sql-spark-pitfalls-and-benchmark/report.md:22-24` + handoff.md (Not done).

## 280 — playbook doradczy (2026-10-17)

1. Pierwsze pytanie pomiarowe w banku: `"are event logs kept, where, for how long?"` — bez event logów nie ma analizy po fakcie — `archive/archive-2026-10-19/results/280-sql-spark-consulting-playbook/report.md:40`.
2. Klasyczne dźwignie z oficjalnego tuning guide: serializacja `"Often, this will be the first thing you should tune"` (Kryo do 10x), parallelizm 2-3 taski/rdzeń, serialized caching — `.../280-sql-spark-consulting-playbook/report.md:43`.
3. Regulacje ujęte źródłowo (BCBS 239, SR 11-7, AI Act, NIST);privacy AI przez Azure/Foundry, bo OpenAI 403 — `.../280-sql-spark-consulting-playbook/report.md` (sekcja regulacji) + `handoff.md` (Not done).
4. Ceny Databricks tylko strukturalnie (Photon `"DBU emission rate 2.9X"`, `"up to 37% savings ... when you pre-purchase"`); konkretne stawki $ wymagają wyboru regionu — `.../280-sql-spark-consulting-playbook/report.md:62` + handoff.
5. 5 gotowych szablonów (checklist tygodnia, findings, arkusz oszczędności, executive summary, plan 30/90) — `.../280-sql-spark-consulting-playbook/templates/` (5 plików .md, ls zweryfikowane).

## Powiązane (kontekst wątku)

- 1089/1127 (frameless, Scala+Spark OSS): trzy kandydaty PR z testami, c1 wygrany 19/20 (#452 aggMany/SPARK-20346); 1127 potwierdził c3 na Spark 3.4.4 (415/415 + 6/6, GREEN) — `queue/results/1089-oss-frameless-best-of-three/report.md`, `queue/results/1127-frameless-c3-spark34-verify/report.md`.
- 185 (monetyzacja agentów), 330 (rynek pracy), 300 (Metals MCP), 100/140 (skills, narzędzia): tło strategiczne, bez artefaktów Sparkowych — nagłówki w swoich report.md.
