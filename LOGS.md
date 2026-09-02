# Journal du projet

Journal des événements marquants uniquement. Les exécutions répétitives du pipeline sont condensées en une ligne.

## 2026-09-01 — Fondations

- `INFO | architecture | scope=mvp | python_package_structure_created | success`
- `INFO | data | sources=3_CSV_synthetiques | rows=60 (20/source) | success`
- `INFO | postgres | schema=patient_plateform | tables=4 | idempotent=true | success`
- `INFO | git | branch=main | .gitignore,.gitattributes | initialized`

## 2026-09-01 — Pipeline MVP (exécutions 08:56→10:46)

Pipeline pandas complet : extraction (3 sources) + mapping canonique + nettoyage → déduplication → loader. Résultat stable à chaque run :

- `INFO | deduplication | method=exact_then_probabilistic | master_patients=2 | identity_links=6 | success`
- Validation : `pytest` (2→4 tests), `compileall` OK, `raw=6 → masters=2 → links=6`, `business=purchases=2,consultations=2,exams=2`, rerun sans doublons.
- API : `/health,/metrics,/patients` OK (`health=ok`, `metrics raw=18/masters=2/links=6`).
- Dashboard : Streamlit port 8501, `http_200`, cache `ttl=30s`.

## 2026-09-01 — Gouvernance et contrôle d'accès

- `INFO | governance | schema | tables=api_user,access_audit | added | success`
- `INFO | governance | auth | method=api_key_sha256 | roles=admin,analyst,viewer | success`
- `INFO | governance | consent | endpoints=GET,GET_by_id,POST | purposes=api_access,research,analytics | success`
- `INFO | governance | dashboard | auth=sidebar_api_key | role_aware_views | success`
- `INFO | governance | init | scripts/init_governance.py | demo_users=3 | success`
- `INFO | security | api_keys | storage=hashed_sha256 | plaintext_never_persisted | success`
- Validation : `pytest` → 14 tests OK, `compileall` OK.

## 2026-09-01 — Extension des données (20 lignes/source)

- `INFO | deduplication | method=exact_then_probabilistic | source_rows=60 | master_patients=36 | exact_merges=24 | identity_links=60 | success`
- `INFO | load | fix=postgres_loader | order=masters_before_business | reason=foreign_key_violation | fixed`
- `INFO | postgres | target=patient_plateform | raw=60 | masters=36 | links=60 | purchases=20 | consultations=20 | exams=20 | success`
- `INFO | governance | consents=108 | masters=36 | success`
- Validation : `pytest` → 14 tests OK.

## Exécutions de pipeline complémentaires

| Heure | Lignes/source | Masters | Links |
|---|---|---|---|
| 12:22 | 6 | 11 | 18 |
| 12:26 | 6 | 11 | 18 |

(Exécutions mineures identiques : 11:26→11:46 à 20 lignes/source, master=36/links=60 — non répétées.)

## Notes

- Aucune donnée patient nominative dans les journaux.
- Les décisions de matching sont conservées dans l'identity map produite par le pipeline.
2026-09-02T07:30:44+00:00 | INFO | pipeline | status=started
2026-09-02T07:30:44+00:00 | INFO | extraction | source=pharmacy | rows_read=6 | status=success
2026-09-02T07:30:44+00:00 | INFO | extraction | source=consultation | rows_read=6 | status=success
2026-09-02T07:30:44+00:00 | INFO | extraction | source=imaging | rows_read=6 | status=success
2026-09-02T07:30:44+00:00 | INFO | extraction | source=pharmacy | domain=purchase | rows_read=6 | status=success
2026-09-02T07:30:44+00:00 | INFO | extraction | source=consultation | domain=consultation | rows_read=6 | status=success
2026-09-02T07:30:44+00:00 | INFO | extraction | source=imaging | domain=imaging_exam | rows_read=6 | status=success
2026-09-02T07:30:44+00:00 | INFO | deduplication | method=exact_then_probabilistic | master_patients=11 | identity_links=18 | status=success
2026-09-02T07:30:44+00:00 | INFO | pipeline | status=completed
2026-09-02T10:58:28+00:00 | INFO | pipeline | status=started
2026-09-02T10:58:28+00:00 | INFO | extraction | source=pharmacy | rows_read=6 | status=success
2026-09-02T10:58:28+00:00 | INFO | extraction | source=consultation | rows_read=6 | status=success
2026-09-02T10:58:28+00:00 | INFO | extraction | source=imaging | rows_read=6 | status=success
2026-09-02T10:58:28+00:00 | INFO | extraction | source=pharmacy | domain=purchase | rows_read=6 | status=success
2026-09-02T10:58:28+00:00 | INFO | extraction | source=consultation | domain=consultation | rows_read=6 | status=success
2026-09-02T10:58:28+00:00 | INFO | extraction | source=imaging | domain=imaging_exam | rows_read=6 | status=success
2026-09-02T10:58:28+00:00 | INFO | deduplication | method=exact_then_probabilistic | master_patients=11 | identity_links=18 | status=success
2026-09-02T10:58:28+00:00 | INFO | pipeline | status=completed
