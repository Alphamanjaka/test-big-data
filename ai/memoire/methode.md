# Méthode de rédaction du mémoire

## Principes

- Le mémoire raconte une **démarche progressive et honnête** : problème métier → MVP → validation des
  algorithmes → passage à l'échelle → architecture Big Data.
- **Preuves avant affirmations** : chaque chiffre doit être vérifiable dans le dépôt
  (`documents/`, `projet/code-source/`, `archives/`) — pas d'invention de résultat.
- Conserver un ton pédagogique : expliquer **pourquoi** chaque technologie (voir
  `documents/documentation/bigdata_concepts.md`).

## Structure des chapitres (`Mon_Memoire/chapters/01..06`)

Rédiger en remplaçant le squelette « Objectif + Notes/TODO » existant :

1. **01-introduction** : contexte organisme, problématique (données dispersées, doublons, identité),
   objectifs, démarche 3 niveaux, plan du mémoire.
2. **02-etat-de-l-art** : FHIR (interopérabilité), Medallion, Entity Resolution / MPI, RapidFuzz,
   consentement (RGPD, données de santé), Hadoop/Hive/Spark, ELT vs ETL.
3. **03-analyse** : besoin, sources, contraintes (VM 8 Go, MAVIS distant, hétérogénéité), choix
   (RapidFuzz sans NLP, SPH pivot FHIR, PostgreSQL central).
4. **04-conception** : architecture 3 niveaux, modèle canonique `CanonicalPatient`, pipeline ETL,
   scoring/blocking/seuil, schéma SQL, gouvernance (consent, api_user, access_audit).
5. **05-realisation** : générateur de données + ground-truth, extraction/mapping, déduplication,
   chargement PG (idempotence), gouvernance + API + dashboard, Spark (parité), Data Lake Medallion.
6. **06-tests** : tests unitaires et d'intégration, **évaluation ground-truth** (P/R/F1, breakdown
   exact/probabilistic, par source), difficultés rencontrées, limites (recall hard, GOLD sparse).

## Style

- Phrases courtes, français soutenu mais simple.
- Tableaux pour synthétiser (concepts, scripts, résultats).
- Un schéma **par chapitre technique** (Mermaid) représentant l'architecture à chaque niveau.
- Réutiliser les cartes de vocabulaire (Medallion, MPI, blocking, purpose-by-purpose, golden record).

## Traçabilité

- Toute étape MAJEURE de rédaction (chapitre rédigé, figures ajoutées) est journalisée dans
  `ai/dev/logs.md` et le jalon dans `ai/dev/suivi_avancement.md`.
- Les sources à citer vivent dans `references/` et `documents/articles/`.

## Alphabet de checklist par chapitre

- [ ] Objectif posé en ouverture
- [ ] Au moins un fait vérifiable (chiffre/fichier) par affirmation majeure
- [ ] Vocabulaire du thème défini
- [ ] Lien vers le document conceptuel correspondant
- [ ] Conclusion + transition vers le chapitre suivant