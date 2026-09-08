# Module 5 : Tests et Déploiement

## Objectif

Assurer la qualité du code via des tests unitaires et d'intégration, puis préparer le déploiement de l'application en production (Docker, CI/CD, documentation finale).

---

## Portée du MVP (Priorité Absolue)

### MVP - Étape 1 : Tests du Pipeline ELT

| Tâche | Description | Statut |
|-------|-------------|--------|
| Test idempotence pipeline | Relancer `run_pipeline.sh` 2× sans erreur | ⏳ (validation VM) |
| Test normalisation gender | Vérifier male/female dans Silver | ⏳ (validation VM) |
| Test détection doublons | Vérifier `is_duplicate` dans Silver | ⏳ (validation VM) |
| Test GOLD | Vérifier `patient_events_gold` sur HDFS | ⏳ (validation VM) |

### MVP - Étape 2 : Tests Frontend

| Tâche | Description | Statut |
|-------|-------------|--------|
| Test login (ADMIN + MEDECIN) | Connexion/déconnexion | ⏳ |
| Test RBAC (403 MEDECIN sur /users) | Accès refusé | ⏳ (fait manuellement 24/08) |
| Test filtres | Date, sexe, âge appliqués | ⏳ |
| Test CRUD utilisateurs | Créer, éditer, supprimer | ⏳ |

### MVP - Étape 3 : Déploiement

| Tâche | Description | Statut |
|-------|-------------|--------|
| Docker Compose | PostgreSQL + App + FastAPI | ❌ |
| GitHub Actions CI/CD | Lint + Build + Test | ❌ |
| VM .box export | Export Vagrant pour distribution | ❌ |
| .env.example | Variables d'environnement documentées | ❌ |

---

## Améliorations (Post-MVP)

| Tâche | Description | Priorité |
|-------|-------------|----------|
| Tests unitaires PySpark | Tests des scripts ELT | Haute |
| Tests d'intégration API | Tests FastAPI endpoints | Haute |
| Tests E2E (Playwright/Cypress) | Tests du frontend complet | Moyenne |
| Monitoring (Prometheus/Grafana) | Supervision en production | Basse |
| Backup automatique | Sauvegarde PostgreSQL + HDFS | Moyenne |

---

## Critères de validation

| Critère | Cible | Actuel |
|---------|-------|--------|
| Taux de normalisation données | ≥ 95% | ~70% (dettes mapping FHIR) |
| Doublons correctement détectés | ≥ 90% (rappel) | ~85% (24 872 détectés) |
| Temps de traitement pipeline | < 30 min | ~25 min |
| Disponibilité application | ≥ 99% | N/A (dev uniquement) |
| Couverture tests | ≥ 80% | 0% |

---

## Validation

1. `npm test` ou `pytest` → tous les tests passent
2. `docker-compose up` → tous les services démarrent
3. `docker-compose ps` → tous les containers healthy
4. VM .box exportée et testée sur un autre poste
5. Documentation technique à jour

---

## Avancement : ~5% ❌

**Statut :** Tests manuels effectués pour le RBAC (24/08). Aucun test automatisé. Docker/CI-CD non configurés.
