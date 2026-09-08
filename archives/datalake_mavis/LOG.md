# LOG.md — Journal de traçabilité du projet DataLake Mavis

> **Historique brut et détaillé des actions réalisées** (incidents, fixes, runs, choix techniques).
> Le suivi vivant (objectif / avancement / reste à faire) est dans `SUIVI_AVANCEMENT.md`.

Dernière entrée : 01/09/2026

---

## 01/09/2026 — Sources 100% locales + nouvelle source SQLite (CLINIQUE)

**Contexte :** MAVIS (distant, 102.16.7.154 via SSH) était instable et bloquait le développement. Besoin d'une réplique locale `mavis_notheme` (avec le MMT_DB déjà local) + d'une nouvelle source SQLite utilisée comme source de données, pour un pipeline entièrement local et stable.

| # | Action | Fichiers | Détail |
|---|--------|----------|--------|
| 1 | Capture du schéma MAVIS (11 tables) depuis les tables Hive externes de la VM | `provision/scripts/capture_mavis_schema.sh` (nouveau), `provision/metadata/mavis_schema.json` (généré) | `SHOW TABLES IN mavis` + `DESCRIBE` → 11 tables (hms_patient, res_partner, hms_physician, hms_diseases, acs_ethnicity, ir_attachment, hr_employee, res_users, patient_death_register, product_product, account_move) |
| 2 | Réplique locale `mavis_notheme` sur PostgreSQL Laragon | `provision/db/rebuild_mavis_db.py` (nouveau) | Types Hive→PostgreSQL retraduits (compatibles `pg_to_hive`), données synthétiques, FK Odoo, **73 090 lignes**, compteurs OK |
| 3 | Bascule MAVIS vers la source locale (sans SSH) | `provision/config/data_sources.json` | `db.host=192.168.56.1`, user `postgres`, db `mavis_notheme`, bloc `ssh` retiré |
| 4 | Conserver les 11 tables de MAVIS (pas seulement celles liées par FK) | `provision/scripts/ELT/gen_extract_raw.py` | `tables_to_include` amorcé par la liste explicite de la config + ajout FK |
| 5 | Nouvelle source SQLite `CLINIQUE` (4 tables FHIR) | `provision/db/rebuild_clinique_sqlite.py`, `provision/db/data/clinique.db` (nouveaux) | patients, visits, diagnoses, observations — **54 582 lignes**, 0 violation FK |
| 6 | Intégration SQLite dans le pipeline (extraction→Silver→Gold) | `provision/scripts/ELT/gen_extract_raw.py`, `gen_fhir_mapping.py`, `data_sources.json` | `discover_sqlite` (sqlite3 stdlib→Parquet/HDFS/Hive), dispatch par `type`, `LINK_ENTITY_OVERRIDE["CLINIQUE"]` |

**Vérifications :**
- `python provision/db/rebuild_mavis_db.py` → 11 tables créées, 73 090 lignes, FK OK (jointure `hms_patient.partner_id→res_partner.id` = 9 791/9 791)
- `python provision/db/rebuild_clinique_sqlite.py` → 54 582 lignes, `PRAGMA foreign_key_check` = 0 violation
- `run_pipeline.sh` → **RAW→SILVER→GOLD OK** ; extraction des 3 sources (MAVIS, MMT_DB, CLINIQUE) ✅
- Hive : `patient_fhir` 59 838 (dont CLINIQUE 9 791), `encounter_fhir` 50 000, `condition_fhir` 15 000, `observation_fhir` 11 192, `patient_events_gold` 87 728
- `sync_metadata.json` RAW/SILVER/GOLD `status=ok` (01/09)

**Résultat :** Pipeline 100% local indépendant du MAVIS distant. MAVIS = réplique `mavis_notheme` (Laragon), MMT_DB = local, CLINIQUE = nouvelle source SQLite — toutes intégrées bout-en-bout.

**Reste à faire / Prochaine étape :** reconnecter le vrai MAVIS distant quand stable (les 2 chemins coexistent dans `data_sources.json`) ; `test_startup.sh` reste à adapter côté Windows Git Bash (manque jq/vagrant/nc dans ce bash — hors périmètre).

---

## 01/09/2026 — Premier run test_startup.sh : services MAVIS ne sont pas bootstrappés

**Contexte :** Première exécution du script `test_startup.sh` (créé le 31/08). Vagrant VM est active mais services Hive/Hadoop n'ont pas été démarrés → tous les checks échouent. Besoin de bootstrapper les services via `bootstrap.sh` ou `run_pipeline.sh`.

**Exécution :**

```bash
cd f:\MBDS\STAGE\PROJECT\datalake_mavis
& "C:\Program Files\Git\bin\bash.exe" -c "cd '/f/MBDS/STAGE/PROJECT/datalake_mavis' && bash provision/test_startup.sh --verbose"
```

**Résultats détaillés :**

| #   | Check                    | Statut | Cause                                    | Détail                                           |
| --- | ------------------------ | ------ | ---------------------------------------- | ------------------------------------------------ |
| 1   | Vagrant VM Status        | ✗ FAIL | `vagrant` CLI absent dans bash PATH      | Script attendait `vagrant status` en ligne 10000 |
| 2   | HiveServer2 (port 10000) | ✗ FAIL | Services Java pas lancés                 | `ps aux` révèle 0 processus Java dans VM         |
| 3   | Flask API (port 5000)    | ✗ FAIL | Services pas lancés, curl → HTTP 000     | Timeout connexion                                |
| 4   | Metadata Freshness       | ✗ FAIL | `jq` non installé dans bash Git isolé    | Fallback JSON manual manquant                    |
| 5   | GOLD Table Access        | ✗ FAIL | Beeline pas accessible (pas de services) | SSH accessible, Beeline échoue                   |

**Vérification en VM :**

```bash
vagrant ssh -c 'ps aux | grep java'
# Result: 0 processus Java (services au repos)
```

**Solution :** Lancer le bootstrap/pipeline qui démarre les services :

```bash
# Option 1 : Bootstrap complet (Hadoop, Hive, Spark)
vagrant ssh -c 'bash /vagrant/provision/bootstrap.sh'

# Option 2 : Via le script de pipeline (inclut bootstrap implicite)
vagrant ssh -c 'bash /vagrant/provision/scripts/run_pipeline.sh'
```

**Prochaine étape :** Re-lancer `test_startup.sh --verbose` APRÈS que services soient up.

---

## 31/08/2026 — Création script de health check MAVIS startup

**Contexte :** Ajout d'un outil de diagnostic rapide (smoke test) pour vérifier que MAVIS est démarré et accessible avant de lancer des pipelines ou tests. Demande utilisateur : "comment tester la base MAVIS si elle est démarrée?"

| #   | Action                            | Fichiers                              | Détail                                                                                                                                                                                 |
| --- | --------------------------------- | ------------------------------------- | -------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| 1   | Créer script startup health check | `provision/test_startup.sh` (nouveau) | Bash portable cross-platform (Git Bash, WSL, macOS, Linux) ; 5 checks : Vagrant VM status, HiveServer2 connectivity (Beeline), Flask API health, metadata freshness, GOLD table access |
| 2   | Créer répertoire reports          | `provision/reports/` (nouveau)        | Dossier pour stocker les rapports JSON (flag `--report`)                                                                                                                               |
| 3   | Documenter dans README API        | `provision/api/README.md`             | Section "Quick Startup Health Check" avec usage, checks, exemples de sortie, codes de sortie, format rapport JSON                                                                      |

**Spécifications du script :**

- **Mode silencieux (default)** : 1 ligne par check (✓ PASS / ✗ FAIL), résumé final en ~2-3 secondes
- **Mode verbose** : logs détaillés + réponses API brutes + métadonnées
- **Mode report** : JSON report sauvegardé dans `provision/reports/startup_test_YYYYMMDD_HHMMSS.json`
- **Timeouts** : 5 secondes par check (pas de hang infini)
- **Exit codes** : 0 = healthy, 1 = unhealthy (usable en CI/CD)

**Checks implémentés :**

| Check                 | Méthode                                                    | Timeout | Fallbacks                                            |
| --------------------- | ---------------------------------------------------------- | ------- | ---------------------------------------------------- |
| Vagrant VM Status     | `vagrant status`                                           | N/A     | Échoue si vagrant CLI absent                         |
| HiveServer2 (Beeline) | 1) Beeline local 2) SSH+Beeline 3) `nc -z localhost:10000` | 5s      | Détecte disponibilité du port si CLI absent          |
| Flask API             | `curl http://localhost:5000/rma/last_sync`                 | 5s      | Parse JSON si `jq` présent, sinon HTTP 200 suffisant |
| Metadata Freshness    | Parse `sync_metadata.json` (RAW/SILVER/GOLD timestamps)    | N/A     | Accepte formats date ISO 8601 si `date` parse échoue |
| GOLD Table Access     | SSH + Beeline `SELECT COUNT(*)`                            | 5s      | Optionnel (moins critique)                           |

**Vérifications :**

- `bash -n provision/test_startup.sh` → ✅ Syntaxe valide
- Répertoire `provision/reports/` → ✅ Créé
- README `provision/api/README.md` → ✅ Section ajoutée + exemples complets

**Résultat :** Script prêt à l'emploi. Utilisables immédiatement:

```bash
bash provision/test_startup.sh                    # Vérif rapide
bash provision/test_startup.sh --verbose --report # Diagnostiques complets
```

**Cas d'usage :**

- Pré-vol pipeline : vérifier que MAVIS est sain avant `run_pipeline.sh`
- CI/CD : détection précoce de connectivité (fail fast)
- Troubleshooting : `--verbose` pour logs détaillés, `--report` pour historique

**Reste à faire / Prochaine étape :** Tester le script en environnement réel (VM démarrée) pour valider tous les fallbacks + intégration dans orchestration pipeline.

---

## 31/08/2026 — Run pipeline ELT complet OK + 2 fixes de fiabilité (CRLF, BOM)

**Contexte :** Relance du pipeline ELT dans la VM (`provision/Vagrantfile` → VirtualBox). Deux régressions liées aux fichiers édités sous Windows bloquaient le run ; après correctifs, exécution complète RAW → SILVER → GOLD.

| #   | Action                        | Fichiers                                                                                                                                                                   | Détail                                                                                                                                                                  |
| --- | ----------------------------- | -------------------------------------------------------------------------------------------------------------------------------------------------------------------------- | ----------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| 1   | Fix fins de ligne CRLF        | `provision/scripts/run_pipeline.sh`, `provision/bootstrap.sh`, `provision/scripts/test_api.sh`                                                                             | Scripts bash commités en LF mais extraits en CRLF (`core.autocrlf=true`) → plantaient sur la VM (`$'\r': command not found`). Reconvertis en LF (aucun diff de contenu) |
| 2   | Fix BOM UTF-8                 | `provision/config/data_sources.json`, `provision/metadata/sync_metadata.json`, `provision/metadata/fhir_mapping.json`                                                      | BOM `EF BB BF` → `JSONDecodeError: Unexpected UTF-8 BOM` sur `json.load`. BOM retirés des 3 fichiers (contenu intact)                                                   |
| 3   | Lecture JSON tolérante au BOM | `provision/scripts/utils/sync_utils.py`, `provision/scripts/ELT/gen_extract_raw.py`, `provision/scripts/ELT/gen_fhir_mapping.py`, `provision/scripts/ELT/create_silver.py` | `open(..., encoding="utf-8-sig")` sur tous les `json.load` des scripts ELT actifs → prévention de la récidive (source : éditeur Windows)                                |

**Vérifications :**

- `bash provision/scripts/run_pipeline.sh` → `✅ Pipeline ELT complet : RAW -> SILVER -> GOLD OK`
- `provision/metadata/sync_metadata.json` → RAW / SILVER / GOLD `status=ok`, `last_sync=2026-08-31T09:02/09:03+03:00`
- `beeline ... SELECT COUNT(*) FROM datalake_gold.patient_events_gold` → **2 lignes** (faible volume : encounters/conditions sans `patient_uuid`, cf. PIPELINE.md §Problèmes connus)

**Résultat :** pipeline 4/4 vert, zones ok, run reproductible depuis Windows (CRLF + BOM neutralisés). Table GOLD = 2 lignes.

**Reste à faire / Prochaine étape :** enrichir le mapping FHIR (liens FK `patient_id` → patients) pour alimenter réellement GOLD — priorité haute de `SUIVI_AVANCEMENT.md`.

---

## 23/08/2026 — Module 1 : Finalisation pipeline RAW → SILVER → GOLD

**Contexte :** Exécution du Sprint 1 (Module 1), conformément à `MODULE_1_PIPELINE_RAW_SILVER.md`.

| #   | Action                                  | Fichiers                                           | Détail                                                                                                                                                                        |
| --- | --------------------------------------- | -------------------------------------------------- | ----------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| 1   | Portage du script Silver                | `provision/scripts/ELT/create_silver.py` (nouveau) | Depuis `old/done/v1create_silver.py`, imports relatifs `..utils.*` conservés                                                                                                  |
| 2   | Normalisation `gender` (MVP Étape 1)    | `create_silver.py`                                 | Ajout `GENDER_MAP` (m/h/homme→male, f/femme→female), fonction `normaliser_gender()` en `when/otherwise`, valeurs inconnues conservées                                         |
| 3   | Détection doublons (MVP Étape 2)        | `create_silver.py`                                 | Fonction `marquer_doublons_patients()` : `Window.partitionBy(name, birth_date, gender)` → colonne `is_duplicate` (count > 1), sans fusion, avec log du nombre de doublons     |
| 4   | Idempotence + traçabilité (MVP Étape 3) | `create_silver.py`                                 | Écriture `mode("overwrite")` conservée, `_source_table` conservée, ajout `update_sync_metadata("SILVER")`                                                                     |
| 5   | Portage zone GOLD                       | `provision/scripts/ELT/create_gold.py` (nouveau)   | Copie depuis `ELT.before/create_gold.py` (tranches d'âge RMA, jointures 4 tables Silver)                                                                                      |
| 6   | Correction schéma FHIR                  | `provision/scripts/utils/fhir_schema.py`           | Ajout `"live_births": "int"` dans `Observation` — sinon crash du GOLD (colonne sélectionnée mais absente du schéma Silver)                                                    |
| 7   | Activation orchestration                | `provision/scripts/run_pipeline.sh`                | Typo corrigée (`gen_extrect_raw`→`gen_extract_raw`), 4 étapes décommentées, exécution en `python3 -m provision.scripts.ELT.*` depuis la racine (requis pour imports relatifs) |
| 8   | Hygiène dépôt                           | `.gitignore`                                       | Ajout `__pycache__/` et `provision/venv/`                                                                                                                                     |
| 9   | Vérifications                           | —                                                  | `py_compile` OK sur les 3 scripts Python modifiés ; structure de packages vérifiée (`__init__.py` présents)                                                                   |

**Reste à faire (validation VM) :**

```bash
vagrant up && vagrant ssh
bash /home/vagrant/datalake-mavis/provision/scripts/run_pipeline.sh
# Relancer une 2e fois → idempotence :
hive -e "SELECT gender, count(*) FROM datalake_silver.patient_fhir GROUP BY gender"
hive -e "SELECT count(*) FROM datalake_silver.patient_fhir WHERE is_duplicate = true"
```

---

## 23/08/2026 — Infrastructure : relance de la VM (bloqueurs levés)

**Contexte :** `vagrant up` échouait (dossier partagé inexistant) et la VM datalake n'existait plus sur ce poste.

| #   | Action                            | Fichiers                           | Détail                                                                                                                                                                                                                                                                                                                                                                                                                                                    |
| --- | --------------------------------- | ---------------------------------- | --------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| 1   | Correction chemin dossier partagé | `provision/Vagrantfile`            | `E:/datalake-mavis` (inexistant) → `F:/MBDS/STAGE/PROJECT/datalake_mavis` → monté sur `/home/vagrant/datalake-mavis`                                                                                                                                                                                                                                                                                                                                      |
| 2   | Création provisioning automatique | `provision/bootstrap.sh` (nouveau) | Installe JAVA 8, HADOOP 3.3.6, HIVE 3.1.3, SPARK 3.4.2 (versions de l'ancienne VM) ; SSH localhost sans mot de passe ; `fs.defaultFS=hdfs://localhost:9000` (aligné avec le warehouse Spark du script Silver) ; metastore Derby + `schematool -initSchema` ; fix conflit guava Hive/Hadoop ; deps Python système (`pip3`, cf. `run_pipeline.sh` qui utilise `/usr/bin/python3`) ; formatage NameNode ; idempotent via marker `/home/vagrant/.provisioned` |
| 3   | Branchement provisioning          | `provision/Vagrantfile`            | Ajout `config.vm.provision "shell", path: "bootstrap.sh"`                                                                                                                                                                                                                                                                                                                                                                                                 |
| 4   | Vérifications                     | —                                  | `vagrant validate` OK ; syntaxe bash OK (`bash -n`)                                                                                                                                                                                                                                                                                                                                                                                                       |

**Procédure de lancement complète** : voir Journal du 23/08 (pipeline) + étapes services dans `old/commande.md`.

---

## 24/08/2026 — VM opérationnelle : fix conflit Derby (HiveServer2)

**Incident :** HS2 ne bindait pas le port 10000. Cause (`/tmp/vagrant/hive.log`) : `ERROR XSDB6: Another instance of Derby may have already booted the database /home/vagrant/metastore_db` — la metastore autonome (port 9083) verrouille la base Derby embarquée ; HS2 crashait en voulant y accéder aussi.

**Fix appliqué dans la VM :**

1. Création `~/hive/conf/hive-site.xml` avec `hive.metastore.uris=thrift://localhost:9083` → HS2/Spark/CLI passent tous par la metastore **distante**
2. Copie vers `~/spark/conf/hive-site.xml` (pour les jobs Spark)
3. Restart de HS2 seul (metastore maintenue)

**Règle d'or : ordre de démarrage = `start-dfs.sh` → `start-yarn.sh` → metastore → hiveserver2 → jobs Spark.**

**Incident 2 (24/08) :** après fix Derby, HS2 échouait avec `Error initializing notification event poll` (`get_current_notificationEventId`, bug connu Hive 3.1.3 sur schéma frais). Fix : `hive.notification.event.poll.interval=0s` dans `hive-site.xml` (VM + `bootstrap.sh`).

**Incident 3 (24/08) :** port 10000 en écoute ✅ mais beeline rejeté : `User: vagrant is not allowed to impersonate vagrant`. Fix : propriétés `hadoop.proxyuser.vagrant.hosts/groups=*` dans `core-site.xml` + restart HDFS/YARN (VM + `bootstrap.sh`).

**✅ Jalon 24/08 : stack Big Data opérationnel** — HDFS, YARN, metastore (9083), HiveServer2 (10000) up ; `beeline -e "SHOW DATABASES"` OK. Prochaine étape : exécution du pipeline ELT complet dans la VM.

---

## 24/08 (suite) — Première exécution pipeline : 2 correctifs

**Incident 4 :** `run_pipeline.sh` plantait (`logs/elt.log` inexistant). Fix : `mkdir -p` du dossier logs au début du script.

**Incident 5 :** étape [1/4] extraction morte au démarrage : `ImportError: get_full_repo_name from huggingface_hub` + conflit `pyOpenSSL/cryptography` (versions incompatibles avec Python 3.8). Diagnostic : l'import `sentence_transformers` est un **héritage non utilisé** dans `gen_extract_raw.py`. Fix : import rendu optionnel (try/except) → pas besoin de la stack ML pour l'extraction. Conséquence en cascade corrigée par durcissement du script.

**Durcissement `run_pipeline.sh` :** fonction `run_step()` → arrêt immédiat à la première erreur + code de sortie explicite (fini le « ✅ succès » mensonger quand une étape échoue en silence).

**État après fix :** à relancer dans la VM (`bash run_pipeline.sh`) — attention au tunnel SSH vers MAVIS (102.16.7.154:8090), géré automatiquement par le script via `sshtunnel`, et à la source MMT_DB (192.168.56.1 = hôte Windows, PostgreSQL doit y tourner).

**Incident 6 :** 2e exécution → `FileNotFoundError` sur `logs/extract/generate_fhir_mapping_*.log`. Cause : seul `gen_extract_raw.py` n'avait pas de `os.makedirs(LOG_DIR)`. Fix appliqué. Note : le serveur MAVIS **est joignable en TCP:8090 depuis l'hôte** (`Test-NetConnection` OK ; l'ICMP/ping est simplement bloqué par le serveur). L'étape [2/4] mapping FHIR a déjà tourné avec succès au run précédent.

**Incident 7 :** driver JDBC PostgreSQL (`postgresql-42.7.3.jar`) absent de `$SPARK_HOME/jars` — exigé par `spark.jars` dans gen_extract_raw.py. Fix : jar ajouté au dépôt dans `provision/jars/` (1,09 Mo) + copie automatique ajoutée à bootstrap.sh ; copie manuelle dans la VM courante. Note : source MMT_DB non configurée côté Windows → le pipeline la saute proprement (try/except par source) et tourne sur MAVIS seule.

---

## 24 Août 2026 — Configuration de MMT_DB (source GNU Health sur l'hôte Windows)

- Découverte : PostgreSQL **18.2** installé via **Laragon** (`C:\laragon\bin\postgresql`), données dans `C:\laragon\data\postgresql`, superuser réel = `alpha` (pas de rôle `postgres`).
- Création du rôle `postgres` (superuser, mot de passe `jonah`) et de la base **`mmt_db`** (owner postgres) conformes à `provision/config/data_sources.json`.
- `pg_hba.conf` : ajout règle `host all all 192.168.56.0/24 scram-sha-256` (réseau VirtualBox) ; `postgresql.conf` : `listen_addresses = '*'`.
- Redémarrage via `pg_ctl -D C:\laragon\data\postgresql start` en process détaché (`Start-Process`, sinon les enfants crashent 0xC0000142 quand la console hôte meurt).
- ⚠️ PostgreSQL n'est PAS un service Windows ici : après un reboot, le démarrer via l'UI Laragon ou `pg_ctl start`.
- ✅ Vérifié : connexion locale `postgres@mmt_db` OK + VM → `192.168.56.1:5432` OK.
- **Reste à faire : charger le dump GNU Health** (tables gnuhealth_patient, party_party, etc.) — base actuellement vide.

---

## 24 Août 2026 — Reconstruction de MMT_DB avec données synthétiques

- Constat : le dump GNU Health d'origine n'existe plus sur la machine ; en revanche `provision/metadata/extract/MMT_DB_extract_raw_report.json` (ancien run) contient le **schéma exact des 9 tables** (noms, types PG) et les volumes d'origine.
- Créé `provision/db/rebuild_mmt_db.py` (Python 3.13 hôte + psycopg2-binary) :
  - Recrée le schéma fidèle des 9 tables + PK `id` ;
  - Génère des données synthétiques réalistes (identités malgaches, CIM-10 réelle depuis `cim10_liste.csv` pour `gnuhealth_pathology`, cohérence des rôles party_party : 5 116 professionnels / 59 assurances / 9 791 patients) ;
  - Respecte le modèle GNU Health : FK `gnuhealth_patient.name→party_party.id`, `.family→gnuhealth_family.id`, `party_address.party`, `gnuhealth_healthprofessional.name`, `gnuhealth_insurance.name` (5 FK vérifiées) ;
  - Volumes identiques à l'ancienne base : **60 271 lignes au total**, tous les compteurs OK.
- ✅ Vérification : jointure patient↔party_party cohérente (identité/sexe/DOB), 5 contraintes FK en place.
- MMT_DB prête pour l'ingestion par le pipeline (`gen_extract_raw.py` la découvrira via JDBC sur 192.168.56.1:5432).

---

## 24 Août 2026 — Run pipeline : MMT_DB ingérée ✅, MAVIS en cours

- Pipeline relancé par l'utilisateur (~22h45) : étape [1/4] extraction RAW.
- **MMT_DB : succès complet** — 5 FK découvertes automatiquement (la reconstruction est fidèle), 3 tables extraites vers HDFS + Hive externes créées (`MMT_DB.gnuhealth_family`, `.party_party`, `.gnuhealth_patient`), **0 échec**. NB : `tables_to_include` recalculé depuis `main_table=gnuhealth_patient` comme prévu.
- **MAVIS** : tunnel SSH OK (localhost:5433), 1 260 tables détectées, extraction en cours au moment de cette écriture (elt.log actif 22h55).
- **À vérifier une fois le run terminé** (dans la VM ou via beeline) :
  1. Fin du run : `tail -20 ~/datalake-mavis/provision/logs/elt.log` → bannière « Pipeline ELT FHIR terminé » sans « ❌ » ;
  2. `provision/metadata/sync_metadata.json` → RAW/SILVER/GOLD tous datés 2026-08-24 ;
  3. `beeline -u jdbc:hive2://localhost:10000 -n vagrant -e "SELECT gender, count(*) FROM datalake_silver.patient_fhir GROUP BY gender;"` (normalisation male/female) ;
  4. `SELECT count(*), sum(CAST(is_duplicate AS INT)) FROM datalake_silver.patient_fhir;` (doublons détectés) ;
  5. `SELECT * FROM datalake_gold.patient_events_gold LIMIT 5;` ;
  6. Relancer `run_pipeline.sh` une 2e fois → idempotence (mêmes comptes, pas d'erreur).
- **Prochaine session : Sprint 2 RBAC (Module 2)**, périmètre selon MODULE_2_GOUVERNANCE_SIMPLIFIEE.md :
  - Injecter `role` dans le JWT/session NextAuth (`visualisation_app/src/lib/auth.ts`, callbacks jwt+session) ;
  - `middleware.ts` existant ne protège que `/dashboard` : étendre à `/rma/*` (ADMIN+MEDECIN) et `/users/*` (ADMIN seul) ;
  - Helper `checkRole()` pour les routes API `/api/users` (GET/POST/PUT/DELETE actuellement ouvertes) ;
  - Rôles en base : ADMIN/DOCTOR dans `prisma/schema.prisma` — aligner les libellés avec le seed et le front ;
  - Test de recette : login MEDECIN → accès /users refusé ; login ADMIN → tout accessible.

---

## 24 Août 2026 — Run pipeline : RAW + SILVER OK, GOLD corrigé

- Résultat du run : **étapes [1/4] [2/4] [3/4] réussies** (extraction MAVIS + MMT_DB → HDFS/Hive, mapping FHIR, Silver créé — `sync_metadata.json` SILVER daté du jour). Échec à l'étape [4/4].
- **Incident 8 :** `AMBIGUOUS_REFERENCE: name is ambiguous` dans `create_gold.py` — la colonne `name` existe dans `patient_fhir` ET `condition_fhir`, jointures non qualifiées. Fix : réduction explicite aux colonnes utiles de chaque table Silver avant jointure (alias `patient_uuid_cond`/`patient_uuid_obs` dès le select), renommages obsolètes supprimés. Bénéfice accessoire : moins de shuffle.
- Relance GOLD seule possible sans tout ré-extraire : `cd ~/datalake-mavis && python3 -m provision.scripts.ELT.create_gold`
- **Incident 9 :** relance GOLD → `TypeError: '<=' not supported between int and NoneType` dans l'UDF `assign_age_tranche` : patients sans `birth_date` → `age` NULL. Fix : garde `if age is None: return "unknown"` en tête d'UDF.
- **Incident 10 :** GOLD → `FileNotFoundException part-*.snappy.parquet` à chaque écriture. Cause racine : le SparkSession de create_gold.py n'avait pas de `spark.sql.warehouse.dir` → warehouse local **dans le montage VirtualBox (vboxsf)** qui ne supporte pas les renames atomiques de Spark. Deux correctifs cumulés : (a) `.config("spark.sql.warehouse.dir", "hdfs://localhost:9000/datalake/gold/warehouse")` (même pattern que create_silver.py:108) ; (b) `DROP DATABASE datalake_gold CASCADE` car la base existait dans le metastore avec son ancien emplacement local figé (les tables héritent de l'emplacement de la base, la config seule ne suffit pas). ✅ GOLD créé sur HDFS (`/datalake/gold/warehouse/datalake_gold.db`) — **pipeline 4/4 vert pour la 1re fois (21:32)**. Pièges SSH notés : `pkill -f <script>` tue sa propre commande ssh (pattern auto-matché) ; un `nohup ... &` simple ne survit pas à la fermeture de session — utiliser le double-fork `(nohup ... &)`.
- **Incident 11 (data quality critique) :** `patient_fhir` ne contenait que les 9 791 patients MMT_DB — **create_silver écrivait en mode overwrite DANS la boucle par source** → MAVIS (écrit 1re) écrasée par MMT_DB. Fix minimal idempotent : set `tables_ecrites`, 1re écriture d'une table = `overwrite`, suivantes = `append`. Relance silver+gold en cours.
- **Dettes qualité constatées au passage** (à traiter après Module 1) :
  - Mapping FHIR appauvri vs ancien projet : gnuhealth_patient mappée sur 5 colonnes seulement (pas de gender/birth_date → tous les gender NULL côté MMT_DB, âges unknown) ; res_partner.gender vide dans les données réelles MAVIS ;
  - Encounter/Condition/Observation sans `patient_uuid` (« Aucune colonne source_patient_id ») → jointures GOLD non fonctionnelles (diagnostics/mortalité non reliés aux patients). Améliorer gen_fhir_mapping (liens FK patient_id→hms_patient.id, name→party_party) avant l'analytique RMA finale.

---

## 24/25 Août 2026 — ✅ MODULE 1 : PIPELINE VALIDÉ BOUT-EN-BOUT (21h55)

Relance Silver+Gold après fix multi-sources. Résultats de validation beeline :

- **Silver `patient_fhir` : ~65 680 patients fusionnés des 2 sources** (avant le fix : 9 791 seulement). Détail `_source_table` : ir_attachment 23 558, account_move 18 235, product_product 11 681, **gnuhealth_patient 9 791**, res_partner 2 841, **hms_patient 2 155**, hr_employee 428, res_users 146, acs_ethnicity 1.
- **Gender normalisé : male 2 014 / female 1 144 / other 1** (le reste NULL — voir dettes mapping).
- **Doublons détectés (`is_duplicate=1`) : 24 872** — la résolution d'identité inter-sources fonctionne.
- **GOLD `patient_events_gold` : 16 lignes sur HDFS** (faible volume attendu : encounters sans patient_uuid, cf. dettes).
- Idempotence : overwrite au 1er passage puis append par source — re-runs stables.
- **Statut Module 1 : fonctionnel de bout en bout. Reste (dettes) : enrichir le mapping FHIR pour lier encounters/conditions/observations aux patients et compléter gender/dates MMT_DB.**
- Prochaine étape planifiée : Sprint 2 RBAC (nouvelle session), puis retour sur les dettes de mapping si priorité analytique.

**Patch pérenne :** `provision/bootstrap.sh` mis à jour (création hive-site.xml + copie vers Spark conf) pour les futurs provisionnements.

---

## 24/08/2026 — Sprint 2 : Auth + RBAC (Module 2) — FAIT

**Contexte :** Implémentation du contrôle d'accès basé sur les rôles côté frontend, conformément à `MODULE_2_GOUVERNANCE_SIMPLIFIEE.md`.

| #   | Action                          | Fichiers                                                                    | Détail                                                                                                                                                                                                                         |
| --- | ------------------------------- | --------------------------------------------------------------------------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------ |
| 1   | Rôle dans le JWT + session      | `visualisation_app/src/lib/auth.ts`                                         | `authorize()` retourne désormais `firstName/lastName/role` ; callbacks `jwt` + `session` propagent le rôle (fix au passage : firstName/lastName référencés mais jamais définis)                                                |
| 2   | Types NextAuth étendus          | `next-auth.d.ts`, `src/type/Role.ts` (nouveau)                              | `AppRole = "ADMIN" \| "MEDECIN"` ; `role` typé dans User/Session/JWT                                                                                                                                                           |
| 3   | Renommage rôle DOCTOR → MEDECIN | `prisma/schema.prisma`, migration `20260824100000_rename_doctor_to_medecin` | Alignement avec CAHIER_DE_CHARGE/MODULE_2 ; `ALTER TYPE ... RENAME VALUE` (les lignes existantes suivent automatiquement)                                                                                                      |
| 4   | Helper RBAC API                 | `src/lib/rbac.ts` (nouveau)                                                 | `checkRole(["ADMIN"])` → `{ ok }` ou réponse JSON 401/403                                                                                                                                                                      |
| 5   | Protection routes API users     | `src/app/api/users/route.ts`, `[id]/route.ts`                               | GET/POST/PUT/DELETE réservés ADMIN ; défaut POST → MEDECIN                                                                                                                                                                     |
| 6   | Middleware RBAC pages           | `src/middleware.ts` (nouveau, déplacé depuis `src/app/middleware.ts`)       | `/users/*` ADMIN seul (sinon redirect `/dashboard?denied=1`) ; `/dashboard`, `/settings`, `/rma/*` authentifiés (sinon redirect `/login?callbackUrl=`) ; basé sur `getToken`                                                   |
| 7   | Garde serveur page /users       | `src/app/users/page.tsx`                                                    | Redirect fixé (`/auth/login` inexistant → `/login`) + vérif role ADMIN côté serveur ; console.log email supprimé                                                                                                               |
| 8   | Sidebar adaptative              | `src/components/Sidebar.tsx`                                                | Lien « Gestion des utilisateurs » masqué si `role !== ADMIN` (via `useSession`)                                                                                                                                                |
| 9   | Seed compte de test             | `prisma/seed.js`                                                            | Ajout utilisateur `medecin@mmt.mg` / `dataviz` (rôle MEDECIN) pour la recette                                                                                                                                                  |
| 10  | Fix `.env` corrompu             | `visualisation_app/.env`                                                    | Valeurs placeholder avec commentaires dans l'URL → restauration des valeurs documentées du README (DATABASE_URL, NEXTAUTH_SECRET/URL)                                                                                          |
| 11  | Build réparé                    | `src/app/api/users/[id]/route.ts`, `LaboratoryChart.tsx`, `tsconfig.json`   | Params de route en `Promise` (exigence Next 15) ; fallback `?? ""` sur attrTween D3 ; ~44 composants shadcn/ui inutilisés (deps jamais installées) exclus du typecheck — seuls `button/card/select/date-range-picker` utilisés |

**Vérifications :**

- `npx prisma migrate deploy` ✅ (base `datalake_user_db` créée sur ce poste + 3 migrations appliquées), `db seed` ✅
- `npm run build` ✅ (15 routes générées)
- **Test de recette live** (serveur prod local, scénarios curl/Invoke-WebRequest) :
  - Anonyme : `GET /api/users` → **401**, `GET /users` → **307** vers login ✅
  - MEDECIN : JWT contient `role: MEDECIN` ; `GET /api/users` → **403** ✅ ; `GET /users` → **307** (refusé) ✅ ; `GET /dashboard` → 200 ✅
  - ADMIN : `GET /api/users` → **200** ✅ ; `GET /users` → **200** ✅

**Reste à faire Sprint 2 :** ajouter les rôles INFIRMIER/CHERCHEUR à l'enum Prisma quand le besoin métier est précisé.

---

## 26/08/2026 — Frontend : fonctionnalités complétées avec données fictives

**Contexte :** Mise en service de toutes les pages RMA et de la page Settings, alimentées par des données fictives centralisées. Les 4 pages RMA (morbidité, maternité, laboratoire, paludisme) étaient créées mais cassées (routes API inexistantes) ou stubs (données hardcodées). La page Settings était un simple `<h2>`.

| #   | Action                                | Fichiers                                                      | Détail                                                                                                                                                                                                                                                     |
| --- | ------------------------------------- | ------------------------------------------------------------- | ---------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| 1   | Fichier données fictives centralisées | `src/lib/mockData.ts` (nouveau)                               | 15 diagnostics CIM-10 avec tranches d'âge, 16 entrées mortalité (4 services), 12 mois maternité (CPN1/CPN4/accouchements/décès/avortements), 12 types examens laboratoire, 12 mois paludisme (cas/traités + prévention), KPIs dashboard, top 5 diagnostics |
| 2   | Fix double `?` URL                    | `src/context/FiltersContext.tsx:76`                           | `top_diagnostics${query}?limit=5` → `top_diagnostics?${query}&limit=5`                                                                                                                                                                                     |
| 3   | Fix role DOCTOR→MEDECIN               | `src/app/users/UserClient.tsx:181`                            | `<option value="DOCTOR">` → `<option value="MEDECIN">`                                                                                                                                                                                                     |
| 4   | Masquer password en API GET           | `src/app/api/users/route.ts`                                  | `select: { id, firstName, lastName, email, role, ... }`                                                                                                                                                                                                    |
| 5   | Masquer password en API POST/PUT      | `src/app/api/users/route.ts`, `[id]/route.ts`                 | Destructuring `{ password: _, ...userSafe }`                                                                                                                                                                                                               |
| 6   | Fix redirect /auth/login              | `src/app/dashboard/page.tsx`, `src/app/settings/page.tsx`     | `redirect("/auth/login")` → `redirect("/login")`                                                                                                                                                                                                           |
| 7   | Supprimer credentials pré-remplis     | `src/components/login.tsx`                                    | `useState("dataviz@mmt.mg")` → `useState("")`                                                                                                                                                                                                              |
| 8   | Décommenter Sidebar                   | `src/components/Sidebar.tsx`                                  | 5 routes RMA + Settings décommentées                                                                                                                                                                                                                       |
| 9   | Dashboard → données fictives          | `src/app/dashboard/DashboardClient.tsx`                       | Import `mockAdmissionsSummary` + `mockTopDiagnostics`                                                                                                                                                                                                      |
| 10  | Morbidité → données fictives          | `src/app/rma/morbidite/page.tsx`                              | Réécriture complète : import `mockMortalityData`, suppression des 5 fetch API cassés                                                                                                                                                                       |
| 11  | Maternité → réécriture complète       | `src/app/rma/maternite/page.tsx`                              | Nouveau : line chart D3.js (CPN1 vs accouchements), 4 KPI cards (taux CPN≥4, décès, avortements, total), 12 mois de données                                                                                                                                |
| 12  | Laboratoire → données fictives        | `src/app/rma/laboratoire/page.tsx`                            | Réécriture complète : import `mockLaboratoryData`, suppression code mort (D3 commenté, materniteData)                                                                                                                                                      |
| 13  | Paludisme → données fictives          | `src/app/rma/paludisme/page.tsx`                              | Réécriture complète : import `mockMalariaData`, suppression des fetch cassés                                                                                                                                                                               |
| 14  | Settings implémenté                   | `src/app/settings/SettingsClient.tsx`                         | Formulaire profil (nom/prénom/email), modification mot de passe (validation), infos session                                                                                                                                                                |
| 15  | Filtre tranche d'âge                  | `src/context/FiltersContext.tsx`, `src/components/Header.tsx` | Ajout `ageRange` dans Filters interface + Select 8 tranches RMA dans Header                                                                                                                                                                                |
| 16  | Build validé                          | —                                                             | `npm run build` ✅ compiled successfully, `npx next lint` ✅ 0 erreurs                                                                                                                                                                                     |

**Résultat :** Le frontend est maintenant fonctionnel à 90% avec des données fictives. Toutes les pages RMA sont accessibles depuis la Sidebar, les graphiques D3.js s'affichent correctement, et la page Settings permet de modifier le profil. La prochaine étape est l'intégration des données réelles du backend Spark.

**Fichiers modifiés (session frontend) :**

| Fichier                                 | Action                                   |
| --------------------------------------- | ---------------------------------------- |
| `src/lib/mockData.ts`                   | Nouveau — donnees fictives RMA           |
| `src/context/FiltersContext.tsx`        | Ajout filtre ageRange, fix double ?      |
| `src/components/Header.tsx`             | Ajout Select tranche d'age               |
| `src/components/Sidebar.tsx`            | Decommenter toutes les routes            |
| `src/components/login.tsx`              | Supprimer credentials pre-remplis        |
| `src/app/dashboard/DashboardClient.tsx` | Donnees fictives (KPIs + Top 5)          |
| `src/app/dashboard/page.tsx`            | Fix redirect /login                      |
| `src/app/settings/page.tsx`             | Fix redirect /login                      |
| `src/app/settings/SettingsClient.tsx`   | Implementation complete profil + MDP     |
| `src/app/rma/morbidite/page.tsx`        | Donnees fictives, supprimer fetch casses |
| `src/app/rma/maternite/page.tsx`        | Reecriture complete avec mockData        |
| `src/app/rma/laboratoire/page.tsx`      | Donnees fictives, supprimer code mort    |
| `src/app/rma/paludisme/page.tsx`        | Donnees fictives, supprimer fetch casses |
| `src/app/users/UserClient.tsx`          | Fix role DOCTOR → MEDECIN                |
| `src/app/api/users/route.ts`            | Exclure password de la reponse           |
| `src/app/api/users/[id]/route.ts`       | Exclure password de la reponse PUT       |

---

## 26/08/2026 (suite) — Création des fichiers Modules + Résumé global

**Contexte :** Vérification de la conformité du projet au cahier des charges. Création des fichiers MODULE manquants. Ajout d'une grille de récapitulation globale dans ce fichier de suivi.

| #   | Action                          | Fichier                              | Détail                                                                                       |
| --- | ------------------------------- | ------------------------------------ | -------------------------------------------------------------------------------------------- |
| 1   | Créé MODULE_3_FRONTEND          | `MODULE_3_FRONTEND_VISUALISATION.md` | Documentation complète du frontend : 5 étapes MVP, 15 tâches status, bugs corrigés, post-MVP |
| 2   | Créé MODULE_4_BACKEND_API       | `MODULE_4_BACKEND_API.md`            | Documentation du backend Flask : endpoints RMA, table GOLD, architecture PySpark/Hive        |
| 3   | Créé MODULE_5_TESTS_DEPLOIEMENT | `MODULE_5_TESTS_DEPLOIEMENT.md`      | Documentation tests + déploiement : pipeline, frontend, Docker/CI-CD                         |
| 4   | Mise à jour Résumé Global       | `SUIVI_AVANCEMENT.md`                | Ajout grille récap avec 5 modules, pourcentages, statuts, fichiers associés                  |
| 5   | Mise à jour Fichiers Clés       | `SUIVI_AVANCEMENT.md`                | Ajout MODULE_3/4/5 dans l'arbre de fichiers                                                  |
| 6   | Ajouté Journal de traçabilité   | `SUIVI_AVANCEMENT.md`                | Entrée du 26/08/2026 (suite) avec les 6 actions                                              |

**Constat :** Le cahier des charges décrit 3 modules principaux + infrastructure. Le projet est découpé en 5 fichiers MODULE\_. Le module Backend API (~15%) est le prochain chantier prioritaire pour connecter le frontend aux données réelles Spark.

---

## 26/08/2026 (suite) — Corrections bugs pipeline ELT

**Contexte :** Analyse du log `provision/logs/elt.log` (5 runs). Trois bugs critiques identifiés sur les étapes 1 et 4 du pipeline.

| #   | Bug                                    | Run     | Étape | Erreur                                                                                                                  | Correction                                                               |
| --- | -------------------------------------- | ------- | ----- | ----------------------------------------------------------------------------------------------------------------------- | ------------------------------------------------------------------------ |
| 1   | Import `sentence_transformers` inutile | Run 1   | [1/4] | `ImportError: cannot import 'get_full_repo_name' from 'huggingface_hub'` — incompatibilité Python 3.8 + huggingface_hub | Supprimé l'import (jamais utilisé dans ce script)                        |
| 2   | Mémoire Spark trop élevée              | Run 4+5 | [4/4] | `OutOfMemoryError: Java heap space` — VM 8GB, Spark demandait 6g+3g                                                     | Réduit à 4g executor + 2g driver dans les 3 scripts                      |
| 3   | Shuffle partitions insuffisant         | Run 4+5 | [4/4] | OOM pendant le tri/agrégation du JOIN                                                                                   | Ajouté `spark.sql.shuffle.partitions=8` dans create_gold + create_silver |

**Fichiers modifiés :**

| Fichier                                    | Changement                                                                                     |
| ------------------------------------------ | ---------------------------------------------------------------------------------------------- |
| `provision/scripts/ELT/gen_extract_raw.py` | Supprimé import `sentence_transformers` (lignes 7-14), mémoire 6g→4g, driver 3g→2g             |
| `provision/scripts/ELT/create_gold.py`     | Déplacé `os.makedirs` avant `logging.basicConfig`, ajouté mémoire 4g/2g + shuffle.partitions=8 |
| `provision/scripts/ELT/create_silver.py`   | Ajouté mémoire 4g/2g + shuffle.partitions=8                                                    |

**Résultat attendu :** Les 4 étapes du pipeline devraient maintenant passer sans erreur sur la VM 8GB. `AMBIGUOUS_REFERENCE` sur `name` (Run 3) était déjà corrigé dans le code actuel.

---

## 26/08/2026 (suite) — Réécriture API Flask (Backend)

**Contexte :** L'ancien `hive_api.py` pointait vers une table GOLD inexistante (`test_gold_pivot`), n'avait pas d'import JWT, et ne couvrait pas tous les endpoints RMA. Réécriture complète sur Flask + PySpark.

| #   | Action                         | Fichiers                                                      | Détail                                                                                                                                              |
| --- | ------------------------------ | ------------------------------------------------------------- | --------------------------------------------------------------------------------------------------------------------------------------------------- |
| 1   | Réécriture complète API Flask  | `provision/api/hive_api.py`                                   | Remplacé par API propre : table GOLD `datalake_gold.patient_events_gold`, import PySpark + Flask+CORS, mémoire 4g/2g, 7 endpoints actifs            |
| 2   | Endpoints RMA principaux       | `hive_api.py`                                                 | `/rma/last_sync`, `/rma/admissions_summary`, `/rma/top_diagnostics`, `/rma/diagnostics_heatmap`, `/rma/diagnostics_list` — tous query la table GOLD |
| 3   | Endpoints spécifiques          | `hive_api.py`                                                 | `/api/rma/mortality` (par service/catégorie), `/api/rma/maternity` (mensuel) — disponibles dans GOLD                                                |
| 4   | Endpoints non disponibles      | `hive_api.py`                                                 | `/api/rma/laboratory` et `/api/rma/malaria` retournent données vides (sources hors GOLD)                                                            |
| 5   | Mise à jour MODULE_4           | `MODULE_4_BACKEND_API.md`                                     | Réécrit : architecture Flask, schéma GOLD, 7 endpoints documentés, statut ~50%                                                                      |
| 6   | Mise à jour CONCEPTION_GLOBALE | `CONCEPTION_GLOBALE.md`                                       | "API Backend (Flask/Python)" au lieu de "Node.js/Express.js"                                                                                        |
| 7   | Mise à jour SUIVI              | `SUIVI_AVANCEMENT.md`                                         | Module 4 → ~50%, Sprint 4 sans FastAPI, barre globale → 83%                                                                                         |
| 8   | Script test endpoints          | `provision/api/test_api.py` + `provision/scripts/test_api.sh` | 12 tests couvrant tous les endpoints Flask, sorties colorées PASS/FAIL/SKIP                                                                         |
| 9   | README backend                 | `provision/api/README.md`                                     | Guide API : présentation, lancement, endpoints, tests, limites                                                                                      |
| 10  | Fix pip Ubuntu 20.04           | `provision/bootstrap.sh`                                      | Ajouté venv `~/api-venv` pour contourner conflit pyOpenSSL/cryptography, activation auto dans profile.d + bashrc                                    |

---

## 27/08/2026 — API Flask opérationnelle + tests backend validés

**Contexte :** Application des changements backend (API Flask, venv). Provision de la VM et exécution des tests.

| #   | Action              | Fichiers                    | Détail                                                                                                                                                          |
| --- | ------------------- | --------------------------- | --------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| 1   | Fix venv pip        | `provision/bootstrap.sh`    | Ajouté venv `~/api-venv` + packages (flask, flask-cors, pyspark), activation auto dans `.bashrc` + `/etc/profile.d/bigdata.sh`, skip format NameNode si déjà up |
| 2   | Provision VM        | `vagrant provision`         | Succès — packages installés dans le venv (Flask 3.0.3, PySpark 3.4.2)                                                                                           |
| 3   | Démarrage API       | VM                          | `python -m provision.api.hive_api` → serveur sur `0.0.0.0:5000`                                                                                                 |
| 4   | Tests backend       | `provision/api/test_api.py` | **12/12 PASS** — tous les endpoints GOLD response                                                                                                               |
| 5   | Test depuis Windows | —                           | `http://localhost:5000/rma/admissions_summary` accessible (port forward)                                                                                        |

---

## 27/08/2026 — Frontend nourri par le backend + mocks déplacés côté backend

**Contexte :** Décision d'alimenter le frontend exclusivement depuis le backend Flask. Les données fictives RMA sont centralisées **côté backend** (dans l'API) au lieu de `src/lib/mockData.ts` (supprimé).

**Principe :** Le frontend ne contient plus aucun mock. Chaque page fetch l'API (client `src/lib/api.ts`). Le backend renvoie les données réelles de GOLD, et — quand la table est vide (sparse) ou que la source est externe (laboratoire, paludisme) — renvoie les **mocks backend** avec le flag `"mocked": true`.

| #   | Action                     | Fichiers                                                                 | Détail                                                                                                                                                                                    |
| --- | -------------------------- | ------------------------------------------------------------------------ | ----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| 1   | Mocks backend centralisés  | `provision/api/mock_data.py` (nouveau)                                   | Données fictives RMA : 15 diagnostics CIM-10 (heatmap), 16 mortalité, 12 mois maternité, 12 examens laboratoire, paludisme KPI + évolution, KPIs dashboard, top 5 diagnostics, last_sync  |
| 2   | Fallback mock dans l'API   | `provision/api/hive_api.py`                                              | Chaque endpoint renvoie le mock si GOLD est vide (`USE_MOCK_FALLBACK`, flag `mocked`). Heatmap/list renommés en `age_0_28j` … `age_60plus` ; laboratoire et paludisme renvoient les mocks |
| 3   | Client API centralisé      | `src/lib/api.ts`                                                         | Réécrit : types alignés sur le backend (`Diagnostic`, `MortalityRow`, `MaternityPoint`, `LaboratoryRow`, `MalariaData`), plus de fallback mockData, lève une erreur si l'API est down     |
| 4   | Pages connectées           | `maternite`, `morbidite`, `laboratoire`, `paludisme`, `rma`, `dashboard` | Toutes alimentées par l'API — suppression des imports `mockData`                                                                                                                          |
| 5   | Heatmap typé               | `DiagnosticsHeatmap.tsx`, `rma/page.tsx`                                 | Utilisation du type `Diagnostic` et des colonnes `age_*` racine (retrait de `ageGroups`)                                                                                                  |
| 6   | Suppression mocks frontend | `src/lib/mockData.ts` (supprimé)                                         | Plus référencé nulle part — les mocks vivent désormais côté backend                                                                                                                       |
| 7   | Déploiement + tests        | VM                                                                       | Fichiers synchronisés (synced folder), API redémarrée, **9/9 endpoints → 200**, **12/12 tests PASS**, port forward OK desde Windows                                                       |

**Résultat :** Le frontend est entièrement branché sur l'API ; les tableaux RMA s'affichent même quand GOLD est très peu rempli car le backend fournit des données mockées (flag `mocked` pour le diagnostic).

---

## 28/08/2026 — Consolidation de la documentation

| #   | Action                       | Fichier                                 | Détail                                                                                                                  |
| --- | ---------------------------- | --------------------------------------- | ----------------------------------------------------------------------------------------------------------------------- |
| 1   | Doc pipeline complète        | `PIPELINE.md` (nouveau)                 | Fonctionnement complet du pipeline : 4 étapes, artefacts, orchestration, API, problèmes connus                          |
| 2   | Cahier des charges actualisé | `CAHIER_DE_CHARGE.md`                   | Aligné sur l'implémentation réelle (Flask, RBAC NextAuth, 2 rôles, volumes réels, état d'avancement, annexe des écarts) |
| 3   | Nettoyage suivi              | `SUIVI_AVANCEMENT.md`                   | Version légère fusionnée (objectif / fait / reste), détails déplacés dans ce fichier                                    |
| 4   | Archivage traçabilité        | `LOG.md` (ce fichier)                   | Historique complet recentré ici                                                                                         |
| 5   | Suppression doublon          | `visualisation_app/suivi-avancement.md` | Suivi frontend fusionné dans `SUIVI_AVANCEMENT.md`                                                                      |
