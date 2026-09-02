# Avancement Niveau 3 — Architecture Big Data complète

<<<<<<< Updated upstream
=======
Dernière mise à jour : 2026-09-02

>>>>>>> Stashed changes
## Prérequis (Niveaux 1-2 validés)

| # | Critère | État |
|---|---|---|
<<<<<<< Updated upstream
| P1 | MVP complet et fonctionnel | À faire |
=======
| P1 | MVP complet et fonctionnel | Terminé |
>>>>>>> Stashed changes
| P2 | Niveau 2 Spark validé | À faire |
| P3 | Performances Spark documentées | À faire |
| P4 | Scalabilité démontrée | À faire |

<<<<<<< Updated upstream
> Ne pas commencer le Niveau 3 tant que P1-P4 ne sont pas validés.
=======
> P1 validé. P2-P4 dépendent du Niveau 2 — ne pas commencer.
>>>>>>> Stashed changes

## Phase 1 — Environnement

| # | Tâche | État |
|---|---|---|
| D1.1 | Configurer VirtualBox/Docker | À faire |
| D1.2 | Installer Java + Hadoop | À faire |
| D1.3 | Configurer HDFS | À faire |
| D1.4 | Configurer Apache Hive | À faire |
| D1.5 | Valider cluster local (pseudo-distribué) | À faire |

## Phase 2 — Data Lake

| # | Tâche | État |
|---|---|---|
| D2.1 | Structure Data Lake HDFS | À faire |
| D2.2 | Ingestion dans le Data Lake | À faire |
| D2.3 | Zones : /raw /staging /processed /curated | À faire |
| D2.4 | Migrer sources vers /raw | À faire |
| D2.5 | Valider intégrité HDFS | À faire |

## Phase 3 — Apache Hive

| # | Tâche | État |
|---|---|---|
| D3.1 | Créer bases Hive | À faire |
| D3.2 | Tables externes sur HDFS | À faire |
| D3.3 | Requêtes analytiques | À faire |
| D3.4 | Valider SQL sur Data Lake | À faire |

## Phase 4 — Pipeline Big Data

| # | Tâche | État |
|---|---|---|
| D4.1 | Adapter pipeline Spark distribué | À faire |
| D4.2 | Extraction depuis HDFS | À faire |
| D4.3 | Traitement distribué (cleaning, mapping) | À faire |
| D4.4 | Déduplication distribuée | À faire |
| D4.5 | Écrire résultats dans /curated | À faire |
| D4.6 | Valider pipeline complet | À faire |

## Phase 5 — Dashboard et démonstration

| # | Tâche | État |
|---|---|---|
| D5.1 | Adapter dashboard Big Data | À faire |
| D5.2 | Métriques performance Spark | À faire |
| D5.3 | Métriques Data Lake | À faire |
| D5.4 | Préparer démonstration complète | À faire |
| D5.5 | Documenter architecture finale | À faire |

## État global

```
<<<<<<< Updated upstream
P1 ░░░░0%   P2 ░░░░0%   P3 ░░░░0%   P4 ░░░░0%   P5 ░░░░0%   TOTAL ░░░░0%
=======
P1 ░░░░25%   P2 ░░░░0%   P3 ░░░░0%   P4 ░░░░0%   TOTAL ░░░░ 5%
>>>>>>> Stashed changes
```

## Critères de succès

| Critère | Cible |
|---|---|
| Architecture | HDFS + Hive + Spark opérationnels |
| Pipeline | Exécution distribuée bout en bout |
| Cohérence | Résultats identiques Niveaux 1-2 |
| Scalabilité | Volumes > MVP |
| Démonstration | Présentation claire des 3 niveaux |

## Décisions techniques

| Technologie | Rôle |
|---|---|
| VirtualBox/Docker | Virtualisation |
| Java | Runtime Hadoop |
| Hadoop | Stockage distribué |
| Hive | SQL analytique |
| Spark | Traitement distribué |
| PostgreSQL | Master Patient |
| Streamlit | Dashboard |

## Hypothèses / Blocages / Journal
<<<<<<< Updated upstream
- Hypothèses : HD1-HD4
- Blocages : BD1 (vide)
- Journal : (date | phase | action | résultat)
=======

- **Hypothèses** :
  - HD1 : VirtualBox/Docker disponible pour virtualisation
  - HD2 : Cluster pseudo-distribué suffisant pour la démo
  - HD3 : Mêmes données sources que le MVP
  - HD4 : Résultats Niveaux 1-2 comme baseline
- **Blocages** : Aucun
- **Journal** :
  - 2026-09-02 | Prérequis | MVP validé | P1 terminé, Niveau 3 partially débloqué (P2-P4 en attente Niveau 2)
>>>>>>> Stashed changes
