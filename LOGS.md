# Journal du projet

## 2026-09-01

```text
INFO | architecture | scope=mvp | status=success | python_package_structure_created
INFO | extraction | sources=3_csv_synthetiques | status=success | rows_read=6
INFO | transformation | target=canonical_patient | status=success | date_and_phone_standardized
INFO | deduplication | method=exact_then_probabilistic | status=success | master_patients=2 | identity_links=6
INFO | validation | test_suite=pytest | status=success | tests_passed=2
INFO | validation | compile=python_compileall | status=success
```

Les journaux ne contiennent aucune donnée patient nominative. Les décisions de matching sont conservées dans l’identity map produite par le pipeline.
2026-09-01T08:56:49+00:00 | INFO | pipeline | status=started
2026-09-01T08:56:49+00:00 | INFO | extraction | source=pharmacy | rows_read=2 | status=success
2026-09-01T08:56:49+00:00 | INFO | extraction | source=consultation | rows_read=2 | status=success
2026-09-01T08:56:49+00:00 | INFO | extraction | source=imaging | rows_read=2 | status=success
2026-09-01T08:56:49+00:00 | INFO | deduplication | method=exact_then_probabilistic | master_patients=2 | identity_links=6 | status=success
2026-09-01T08:56:49+00:00 | INFO | pipeline | status=completed
INFO | git | branch=main | status=initialized | author_configured
INFO | git | configuration=.gitignore,.gitattributes | status=success
INFO | validation | test_suite=pytest | status=success | tests_passed=3
INFO | postgres | component=raw_load | target=raw_patient_record | status=success | rows=6
INFO | validation | traceability=raw_to_master | status=success | raw=6 | masters=2 | identity_links=6
INFO | postgres | component=business_load | target=patient_plateform | status=success | purchases=2 | consultations=2 | exams=2
INFO | validation | business_rerun=true | status=success | duplicate_business_rows=0
INFO | api | endpoints=health,metrics,patients | target=patient_plateform | status=success
INFO | api | health=ok | database=connected | status=success
INFO | api | metrics=available | raw_records=18 | master_patients=2 | identity_links=6 | status=success
INFO | dashboard | framework=streamlit | port=8501 | status=started
INFO | dashboard | smoke_test=http_200 | status=success
INFO | validation | test_suite=pytest | status=success | tests_passed=4
INFO | postgres | component=connection | host=localhost | port=5432 | status=server_reachable | database=missing
INFO | postgres | component=connection | host=localhost | port=5432 | status=success | database=patient_plateform
INFO | postgres | component=schema | target=patient_plateform | status=success | tables=4
INFO | postgres | component=load | target=patient_plateform | status=success | master_patients=2 | identity_links=6
2026-09-01T10:35:34+00:00 | INFO | pipeline | status=started
2026-09-01T10:35:34+00:00 | INFO | extraction | source=pharmacy | rows_read=2 | status=success
2026-09-01T10:35:34+00:00 | INFO | extraction | source=consultation | rows_read=2 | status=success
2026-09-01T10:35:34+00:00 | INFO | extraction | source=imaging | rows_read=2 | status=success
2026-09-01T10:35:34+00:00 | INFO | deduplication | method=exact_then_probabilistic | master_patients=2 | identity_links=6 | status=success
2026-09-01T10:35:34+00:00 | INFO | pipeline | status=completed
2026-09-01T10:39:11+00:00 | INFO | pipeline | status=started
2026-09-01T10:39:11+00:00 | INFO | extraction | source=pharmacy | rows_read=2 | status=success
2026-09-01T10:39:11+00:00 | INFO | extraction | source=consultation | rows_read=2 | status=success
2026-09-01T10:39:11+00:00 | INFO | extraction | source=imaging | rows_read=2 | status=success
2026-09-01T10:39:11+00:00 | INFO | deduplication | method=exact_then_probabilistic | master_patients=2 | identity_links=6 | status=success
2026-09-01T10:39:11+00:00 | INFO | pipeline | status=completed
INFO | postgres | component=schema | target=patient_plateform | status=success | idempotent=true
INFO | postgres | component=load | target=patient_plateform | status=success | rerun=true | master_patients=2 | identity_links=6
INFO | validation | test_suite=pytest | status=success | tests_passed=3
2026-09-01T10:42:48+00:00 | INFO | pipeline | status=started
2026-09-01T10:42:48+00:00 | INFO | extraction | source=pharmacy | rows_read=2 | status=success
2026-09-01T10:42:48+00:00 | INFO | extraction | source=consultation | rows_read=2 | status=success
2026-09-01T10:42:48+00:00 | INFO | extraction | source=imaging | rows_read=2 | status=success
2026-09-01T10:42:48+00:00 | INFO | deduplication | method=exact_then_probabilistic | master_patients=2 | identity_links=6 | status=success
2026-09-01T10:42:48+00:00 | INFO | pipeline | status=completed
2026-09-01T10:46:25+00:00 | INFO | pipeline | status=started
2026-09-01T10:46:25+00:00 | INFO | extraction | source=pharmacy | rows_read=2 | status=success
2026-09-01T10:46:25+00:00 | INFO | extraction | source=consultation | rows_read=2 | status=success
2026-09-01T10:46:25+00:00 | INFO | extraction | source=imaging | rows_read=2 | status=success
2026-09-01T10:46:25+00:00 | INFO | extraction | source=pharmacy | domain=purchase | rows_read=2 | status=success
2026-09-01T10:46:25+00:00 | INFO | extraction | source=consultation | domain=consultation | rows_read=2 | status=success
2026-09-01T10:46:25+00:00 | INFO | extraction | source=imaging | domain=imaging_exam | rows_read=2 | status=success
2026-09-01T10:46:25+00:00 | INFO | deduplication | method=exact_then_probabilistic | master_patients=2 | identity_links=6 | status=success
2026-09-01T10:46:25+00:00 | INFO | pipeline | status=completed
2026-09-01T10:46:27+00:00 | INFO | pipeline | status=started
2026-09-01T10:46:27+00:00 | INFO | extraction | source=pharmacy | rows_read=2 | status=success
2026-09-01T10:46:27+00:00 | INFO | extraction | source=consultation | rows_read=2 | status=success
2026-09-01T10:46:27+00:00 | INFO | extraction | source=imaging | rows_read=2 | status=success
2026-09-01T10:46:27+00:00 | INFO | extraction | source=pharmacy | domain=purchase | rows_read=2 | status=success
2026-09-01T10:46:27+00:00 | INFO | extraction | source=consultation | domain=consultation | rows_read=2 | status=success
2026-09-01T10:46:27+00:00 | INFO | extraction | source=imaging | domain=imaging_exam | rows_read=2 | status=success
2026-09-01T10:46:27+00:00 | INFO | deduplication | method=exact_then_probabilistic | master_patients=2 | identity_links=6 | status=success
2026-09-01T10:46:27+00:00 | INFO | pipeline | status=completed
