# Méthode de rédaction du mémoire

## Principes

- Le mémoire raconte une **démarche progressive et honnête** : problème métier → MVP → validation des
  algorithmes → passage à l'échelle → architecture Big Data.
- **Preuves avant affirmations** : chaque chiffre doit être vérifiable dans le dépôt
  (`documents/`, `projet/code-source/`, `archives/`) — pas d'invention de résultat.
- Conserver un ton pédagogique : expliquer **pourquoi** chaque technologie (voir
  `documents/documentation/bigdata_concepts.md`).

## Structure des chapitres (`Mon_Memoire/chapters/01..09`)

Rédiger en remplaçant le squelette « Objectif + Notes/TODO » existant :

1. **01-introduction** : contexte organisme, problématique (données dispersées, doublons, identité),
   objectifs, démarche 3 niveaux, plan du mémoire.
2. **02-etat-de-l-art** : FHIR (interopérabilité), Medallion, Entity Resolution / MPI, RapidFuzz,
   consentement (RGPD, données de santé), Hadoop/Hive/Spark, ELT vs ETL.
3. **03-etude-existant** : systèmes d'information en place (MAVIS, MMT_DB, CLINIQUE) et leurs
   limites ; solutions du domaine (MPI/DMP, MDM/ETL, Data Lake santé, open source) ; grille de
   comparaison sur 6 critères ; verdict et espace de manœuvre. **Étude documentaire** : aucune
   solution citée n'est installée ni exécutée — le dire explicitement.
4. **04-analyse** : besoin, sources, contraintes (VM 8 Go, MAVIS distant, hétérogénéité), choix
   (RapidFuzz sans NLP, pivot FHIR, PostgreSQL central).
5. **05-conception** : architecture 3 niveaux + chaîne de bout-en-bout (composants, ports), modèle
   canonique `CanonicalPatient`, pipeline ETL, scoring/blocking/seuil, schéma SQL, gouvernance
   (consent, api_user, access_audit).
6. **06-realisation** : générateur + ground-truth, extraction/mapping, déduplication, chargement PG
   (idempotence), gouvernance + API + dashboard, Spark (parité), Data Lake Medallion, difficultés.
7. **07-tests** : tests unitaires et d'intégration, **évaluation ground-truth** (P/R/F1, breakdown
   exact/probabilistic, par source), limites (recall hard, GOLD sparse).
8. **08-conclusion** : conclusion générale autonome — réponse à la problématique (tableau
   volet → réalisation → preuve), acquis démontrés, limites assumées, perspectives, bilan.
9. **09-glossaire** : un mot = une explication en français courant + le renvoi au chapitre qui
   le détaille ; une table des objets du dépôt (tables, scripts, couches) et leur rôle.

## Style

- Phrases courtes, français soutenu mais simple.
- **Chaque terme technique est expliqué en français courant à sa première apparition en prose** :
  on garde le mot du métier, on ajoute l'explication à côté (« le *metastore*, c'est-à-dire le
  catalogue qui décrit les tables »). Un terme employé sans définition est un défaut de rédaction.
- Les définitions détaillées sont dans les chapitres, leur liste dans `chapters/09-glossaire.md`.
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
- [ ] Vocabulaire du thème défini (glossaire à jour si un terme est ajouté)
- [ ] Lien vers le document conceptuel correspondant
- [ ] Conclusion + transition vers le chapitre suivant

## Communication et soutenance

- Construire un scénario reproductible avec prérequis, commande, données synthétiques, résultat attendu
  et preuve capturée.
- Séparer le message métier du message technique : gouvernance des usages d'un côté, pipeline,
  déduplication explicable, MPI et audit de l'autre.
- Étiqueter chaque affirmation comme réalisée, simulée, prévue ou limitée au PoC. Les performances et
  les résultats doivent toujours renvoyer à une commande, un rapport ou un fichier vérifiable.
- Les figures et captures indiquent leur source, date, périmètre et unité ; elles ne contiennent jamais
  de secret ni de donnée patient réelle.
