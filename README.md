# Mon_Memoire — Plateforme de Centralisation et de Gouvernance des Données Patients

Mémoire de stage (Master 2 — Big Data) et **projet unique consolidé** portant sur la conception et la
réalisation d'une plateforme de centralisation et de gouvernance de données **patients synthétiques** :
nettoyage, déduplication multi-sources (exact + probabiliste, Master Patient Index), consentement
purpose-by-purpose, audit d'accès et architecture Big Data.

## Organisation du dépôt unique

```
Mon_Memoire/
├── chapters/             # mémoire — chapitres 01 → 06 (rédigés, statut daté)
├── documents/            # cahier des charges + articles + documentation conceptuelle
├── references/           # bibliographie (B1 → B12) et sources citées
├── projet/
│   ├── code-source/      # code consolidé : Big Data (VM Hive/HDFS/Spark) + moteur engine/
│   └── mvp/              # PoC `test_bigdata` (niveaux 1 et 2 : MVP Pandas + Spark)
├── archives/
│   └── datalake_mavis/   # PoC Big Data d'origine (source seule, sans .git ni artefacts runtime)
├── ai/
│   ├── dev/              # consignes de dev, journal (logs.md), suivi des jalons
│   └── memoire/          # consignes de rédaction (contexte, méthode)
├── AGENTS.md             # consignes projet (traçabilité, interdits)
└── README.md             # ce fichier
```

## Documents clés

- Mémoire : `chapters/01-introduction.md` → `06-tests.md` (consignes : `ai/memoire/`).
- Cahier des charges : `documents/cahier_des_charges.md`.
- Code : `projet/code-source/README.md` (démarrage moteur/tests, démarrage VM Big Data).

## Traçabilité

Toute session, fix ou jalon est journalisé dans `ai/dev/logs.md` et `ai/dev/suivi_avancement.md`
(voir `AGENTS.md`).