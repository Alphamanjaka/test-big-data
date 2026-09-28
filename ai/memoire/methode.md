# Méthode de rédaction du mémoire

## Principes

- Le mémoire raconte une **démarche progressive et honnête** : problème métier → MVP → validation des
  algorithmes → passage à l'échelle → architecture Big Data.
- **Preuves avant affirmations** : chaque chiffre doit être vérifiable dans le dépôt
  (`documents/`, `projet/code-source/`, `archives/`) — pas d'invention de résultat.
- Conserver un ton pédagogique : expliquer **pourquoi** chaque technologie (voir
  `documents/documentation/bigdata_concepts.md`).

## Structure des chapitres (plan MBDS, `Mon_Memoire/chapters/00..09`)

La structure détaillée (fichier → sections) est dans `ai/memoire/README.md`. Règles propres au plan :

1. **Introduction et conclusion générales ne sont pas numérotées** ; les chapitres 1 à 8 le sont,
   et leurs sections suivent la numérotation MBDS (1.1, 1.2, 2.1…). Un renvoi vers la conclusion
   s'écrit « conclusion générale », pas « § 9.x ».
2. **État de l'art (ch. 2)** : notions de référence → critères → étude de chaque solution →
   tableau comparatif → pertinence du projet. **Étude documentaire** : aucune solution citée n'est
   installée ni exécutée — le dire explicitement.
3. **Exigences (ch. 5)** : organisées par **étapes du pipeline** (intégration, déduplication,
   gouvernance, exploitation), chaque étape illustrée par ses cas d'utilisation.
4. **Planning (§ 4.3)** : ne dater que ce que les journaux datent ; une période sans trace est
   figurée comme telle, jamais reconstituée.
5. **Budget (§ 4.4)** : coûts humains (hypothèses étiquetées), coûts matériels et logiciels
   (réels), total ; source détaillée `documents/budget.md`.
6. Titres limités à trois niveaux (`#`, `##`, `###`) : l'exporteur ne rend pas `####`.

## Style

- Phrases courtes, français soutenu mais simple.
- **Chaque terme technique est expliqué en français courant à sa première apparition en prose** :
  on garde le mot du métier, on ajoute l'explication à côté (« le *metastore*, c'est-à-dire le
  catalogue qui décrit les tables »). Un terme employé sans définition est un défaut de rédaction.
- Les définitions détaillées sont dans les chapitres, leur liste dans `chapters/glossaire.md`.
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
