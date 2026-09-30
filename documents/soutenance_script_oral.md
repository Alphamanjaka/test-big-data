# Script de passage oral — Soutenance M2 MBDS

> **À quoi sert ce fichier.** C'est le **texte à dire**, slide par slide, pour le deck
> `documents/slide_soutenance/Soutenance_M2_MBDS_RANOMENJANAHARY.pptx` (20 slides). Le rapport et
> le mémoire restent sobres ; le récit, la motivation et les nuances se disent ici.
> Débit de référence : **130 à 140 mots par minute**. Repères `[0:00]` = position dans l'exposé.
> `→` = phrase de transition, à dire en passant à la slide suivante.
> **Règle** : aucune affirmation non vérifiable ; ce qui est limité ou en cours se dit comme tel.

---

## Avant de répéter

**Trois choses à ne pas dire**

1. Que le consentement **par type de dossier** fonctionne : il est **en cours de développement** ;
   ce qui est réalisé et testé, c'est le consentement **par finalité**.
2. Que la base centrale contient de vrais consentements : c'est une **base de test**, alimentée
   par le pipeline et par des consentements **de démonstration** (30/09/2026).
3. Que la planification automatique a tourné : le **cron n'a pas été activé**. La reprise et
   l'ingestion incrémentale, elles, ont été validées sur la VM le 30/09.

**Trois phrases à placer quoi qu'il arrive** : « aucune fusion sans justification » (S13),
« zéro fusion à tort, sur les erreurs que j'ai simulées » (S16), « je préfère nommer les
limites » (S18).

**Vidéo** (S17) : 3 min 30, muette, enregistrée à l'avance ; la tester sur le poste de soutenance.

---

## Chronométrage

| Repère | Fin de | Slides |
|---|---|---|
| `[3:30]` | ouverture : qui, où, quel problème | S1 à S6 |
| `[6:00]` | état de l'art et existant | S7 à S10 |
| `[11:00]` | solution, fonctionnalités, résultats | S11 à S16 |
| `[14:30]` | démonstration | S17 |
| `[16:30]` | limites, conclusion, merci | S18 à S20 |

Il reste **environ 3 minutes de marge** sur 20 minutes : elles servent à ralentir, pas à ajouter.

---

## S1. Titre — 0:30 · `[0:00] → [0:30]`

> Bonjour à toutes et à tous. Je suis Ranomenjanahary Manjaka Alpha, en master MBDS. Je vais
> vous présenter mon stage chez Madagascar Medical Technology : une plateforme qui rassemble les
> dossiers d'un même patient dispersés entre plusieurs services, et qui ne laisse lire ces
> dossiers que si le patient l'a accepté. Toutes les données que je vais montrer sont fictives.

→ « Quelques mots d'abord sur l'entreprise qui m'a accueilli. »

---

## S2. L'entreprise — 0:45 · `[0:30] → [1:15]`

> MMT a été créée en 2009. Son métier historique, c'est le matériel biomédical : distribution,
> maintenance, consommables. Elle est Business Partner de Siemens Healthineers. Depuis 2024, elle
> a un département Recherche et Développement, qui gère des systèmes d'information médicale :
> c'est là que j'ai passé quatre mois, de juillet à fin octobre.
>
> J'ai choisi ce sujet parce qu'il réunit les trois volets du master : les bases de données,
> l'intégration de systèmes hétérogènes et le Big Data, que je voulais pratiquer et non plus
> seulement étudier.

**Geste** — ne pas lire les domaines d'activité, ils sont à l'écran.

→ « Voici le problème que j'ai trouvé en arrivant. »

---

## S3. La question — 0:50 · `[1:15] → [2:05]`

> Imaginez un patient. Il passe à la pharmacie, puis en consultation, puis à l'imagerie. À chaque
> étape, on l'enregistre de nouveau. En pharmacie, il s'appelle « Jean Rakoto ». En consultation,
> « Rakoto Jean ». À l'imagerie, « J. RAKOTO ». Le CIN et la date de naissance sont écrits
> autrement à chaque fois.
>
> Aucun de ces services ne sait que c'est la même personne. Et personne ne lui a demandé ce qu'il
> accepte que l'on fasse de ses données. Voilà les deux questions de mon stage : comment savoir
> que c'est lui ? Et qui a le droit de lire son dossier, pour quoi faire ?

**Geste** — laisser 2 secondes de silence sur le point d'interrogation.

→ « Derrière ce cas, il y a trois problèmes. »

---

## S4. Contexte et problématique — 0:45 · `[2:05] → [2:50]`

> Le premier, c'est la dispersion : le dossier d'un patient est éclaté entre plusieurs bases. Le
> deuxième, l'hétérogénéité : même le genre s'écrit H/F, male/female ou Homme/femme. Et ces
> sources ne sont pas figées : un service peut être séparé en plusieurs bases demain. Le
> troisième, l'absence de gouvernance : rien ne dit qui accède à quoi, ni pourquoi.
>
> Ma problématique est donc la suivante : comment centraliser et dédupliquer ces données, tout en
> gardant la trace des identités et en contrôlant chaque accès par le consentement du patient ?

→ « Le cahier des charges traduit cela en six objectifs. »

---

## S5. Objectifs — 0:25 · `[2:50] → [3:15]`

> Six objectifs : centraliser, nettoyer, dédupliquer de façon explicable, gouverner les accès,
> visualiser et évaluer. Et deux contraintes non négociables : les données ne quittent pas
> l'établissement, et je n'ai travaillé que sur des données synthétiques.

→ (enchaîner directement sur le plan)

---

## S6. Plan — 0:15 · `[3:15] → [3:30]`

> Je commence par l'état de l'art et l'existant, puis la solution et ses résultats, une
> démonstration, et je termine par les limites.

---

## S7. État de l'art : quatre notions — 0:45 · `[3:30] → [4:15]`

> Quatre notions structurent tout le projet. L'ELT : on charge la donnée brute d'abord, on la
> transforme ensuite. Le modèle Medallion : trois zones de qualité croissante, RAW, SILVER et
> GOLD, qu'on peut rejouer. Le Master Patient Index : l'annuaire qui reconnaît un même patient et
> lui donne un identifiant unique. Et le consentement par finalité : le patient autorise un usage
> précis, jamais un accès global. Sans avis de sa part, c'est un refus.

→ « Existe-t-il déjà un produit qui fasse tout cela ? »

---

## S8. Comparatif — 0:50 · `[4:15] → [5:05]`

> J'ai comparé six solutions sur six critères, à partir de leur documentation : je ne les ai pas
> installées. Les plus complètes sur l'identité, comme EMPI ou Talend, sont lourdes et sous
> licence. Azure est un service cloud, donc exclu par l'hébergement interne. Splink est excellent
> sur l'algorithme, mais ses poids sont difficiles à expliquer à un gestionnaire de données.
>
> Aucune ne coche les six critères. J'ai donc construit une chaîne sur mesure, mais adossée aux
> standards : Fellegi-Sunter pour la décision, FHIR pour le format, Medallion pour le lac.

→ « Côté établissement, qu'est-ce qui existait ? »

---

## S9. L'existant — 0:35 · `[5:05] → [5:40]`

> Trois systèmes : MAVIS, sous Odoo, avec 1 260 tables sur le serveur distant ; MMT_DB, sous GNU
> Health ; et une base clinique en SQLite. Chacune est cohérente avec elle-même : la clinique n'a
> aucune violation de clé. Le problème n'est donc pas la qualité de chaque base. C'est l'absence
> de pont entre elles.

→ « Ce pont manquant se décompose en cinq manques. »

---

## S10. Cinq manques — 0:35 · `[5:40] → [6:15]`

> Pas d'identifiant commun : le CIN manque pour environ un quart des patients. Pas de format
> commun. Pas de rapprochement explicable. Pas de gouvernance. Et pas d'espace pour rejouer un
> traitement. Le premier prototype comptait 24 872 marqueurs de doublon, mais sans jamais dire
> pourquoi : on détectait, on n'expliquait pas.

→ « Ma réponse a commencé petit. »

---

## S11. Démarche en trois niveaux — 0:50 · `[6:15] → [7:05]`

> Je n'ai pas commencé par le Big Data. Niveau 1 : un prototype simple, en Pandas et PostgreSQL,
> pour vérifier que le problème métier se résout. Niveau 2 : le même moteur porté en Spark, avec
> des résultats strictement identiques. Niveau 3 : le lac de données sur HDFS, Hive et Spark.
>
> Deux garde-fous : je n'ai changé d'échelle qu'après avoir validé la qualité sur une vérité
> terrain, et je n'ai ouvert les accès qu'une fois la gouvernance en place. Chaque technologie
> arrive parce qu'un besoin l'exige.

→ « Voici le chemin d'une donnée dans l'architecture finale. »

---

## S12. Architecture — 0:50 · `[7:05] → [7:55]`

> Les sources sont copiées telles quelles dans la zone RAW, sur HDFS. Elles sont ensuite
> harmonisées selon un schéma inspiré de FHIR dans la zone SILVER, où le moteur rattache chaque fiche à son patient
> maître. La zone GOLD porte les agrégats et le consentement. PostgreSQL garde l'état de
> référence : patients maîtres, consentements, journal d'audit. Et l'API de gouvernance est la
> seule porte d'entrée : chaque appel y est journalisé. Le tout tourne sur une machine virtuelle
> de 8 Go, avec des outils libres.

**Geste** — suivre la flèche de gauche à droite avec la main.

→ « Le cœur de cette architecture, c'est le moteur de déduplication. »

---

## S13. Déduplication explicable — 1:00 · `[7:55] → [8:55]`

> Sa règle tient en une phrase : aucune fusion sans identité identique.
>
> Deux fiches sont réunies si, et seulement si, elles ont le même CIN, le même genre, la même date
> et la même ville de naissance. Sans CIN, le nom doit être identique en plus. Il n'y a ni score
> ni seuil : qu'un champ manque, et la fiche reste seule.
>
> J'ai d'abord utilisé un score pondéré. Sur 100 000 patients, il a réuni deux homonymes parfaits,
> aux CIN différents. J'ai donc choisi la règle stricte. Chaque décision porte sa méthode et son
> explication, et l'identifiant du patient, dérivé de sa clé, ne change pas d'un run à l'autre.

→ « Une fois l'identité établie, reste à savoir qui peut la lire. »

---

## S14. Gouvernance — 0:55 · `[8:55] → [9:50]`

> Trois contrôles, dans cet ordre. Qui demande ? La clé d'API donne l'utilisateur et son rôle ;
> une clé inconnue, c'est 401. Pourquoi ? La finalité est obligatoire ; si le patient ne l'a pas
> acceptée, c'est 403, même pour un utilisateur autorisé. Et la trace : chaque appel, accepté ou
> refusé, est journalisé avec son motif.
>
> Aujourd'hui, le patient choisit par finalité : consultation via l'API, recherche, statistiques.
> L'étape suivante,
> en cours de développement, c'est le choix par type de dossier : accepter qu'on lise ses
> consultations, mais refuser l'imagerie.

→ « Qu'est-ce que tout cela donne sur des données ? »

---

## S15. Résultats du run — 0:40 · `[9:50] → [10:30]`

> Sur le jeu difficile, rejoué dans la VM : 1 057 fiches, 942 patients distincts, 115 doublons
> rattachés. La cohérence se vérifie par une soustraction : 1 057 moins 115, 942. Sur 100 000
> patients, le run complet prend moins de trois minutes. Et les 131 tests passent.

→ « Mais ces 942 patients sont-ils les bons ? »

---

## S16. Évaluation — 1:00 · `[10:30] → [11:30]`

> Pour le savoir, il faut connaître la vérité. J'ai donc généré des patients fictifs, puis des
> jeux où 10, 30 ou 50 % des fiches sont abîmées : fautes de frappe, inversions, champs effacés.
>
> Résultat principal : zéro fusion à tort, sur tous les jeux, y compris à 100 000 patients. En
> santé, c'est la propriété qui compte : confondre deux patients est plus grave que de les laisser
> séparés. Sa portée a une limite : mes données ne contiennent pas de CIN partagé par deux
> personnes. C'est donc une estimation optimiste.
>
> Le prix de cette prudence, c'est le rappel : 0,18 sur le jeu difficile, car une fiche dont la
> date ou la ville a été effacée n'est jamais rattachée. Python et Spark donnent exactement les
> mêmes identifiants, fiche par fiche.

→ « Je vous montre maintenant la chaîne en fonctionnement. »

---

## S17. Démonstration — 3:30 (vidéo) · `[11:30] → [15:00]`

**Avant de lancer (10 s)**
> La vidéo suit l'ordre de construction du projet : les tests, l'évaluation, le pipeline, puis le
> tableau de bord.

| Plan | À l'écran | À dire pendant le plan |
|---|---|---|
| 0:45 | tests | « 131 tests, aucun échec : moteur, gouvernance, pipeline. » |
| 0:45 | évaluation, jeu difficile | « Précision 1,000, rappel 0,179, mêmes identifiants en Python et dans Spark. » |
| 1:00 | pipeline RAW → SILVER → GOLD | « Les étapes s'enchaînent jusqu'à la zone GOLD. » |
| 0:30 | tableau de bord | « Les zones, le dernier run et la planification. » |
| 0:30 | repli si la vidéo échoue | « Les mêmes preuves en chiffres : 1 057, 942, 115. » |

→ « Ce que je n'ai pas résolu. »

---

## S18. Limites et perspectives — 0:50 · `[15:00] → [15:50]`

> Je préfère nommer les limites. Le rappel sur le jeu difficile est de 0,18. La planification
> automatique n'a pas encore été activée. La base centrale est une base de test, avec des
> consentements de démonstration. Et la plateforme n'est pas déployée : c'est un prototype
> reproductible.
>
> La suite : terminer le consentement par type de dossier, valider à la main les fiches
> incomplètes, activer la planification. Et avant toute mise en production, vérifier le droit malgache des données de
> santé.

→ « Pour conclure. »

---

## S19. Conclusion — 0:30 · `[15:50] → [16:20]`

> La plateforme centralise, normalise, déduplique sans fusion à tort sur nos jeux de référence, et contrôle chaque
> accès par le consentement. Changer d'échelle n'a pas changé la logique. Et derrière chaque
> chiffre, il y a ce patient du début : reconnu comme une seule personne, et maître de l'usage de
> ses données.

---

## S20. Merci — 0:10 · `[16:20] → [16:30]`

> Merci pour votre attention. Je suis à votre disposition pour vos questions.

---

## Si le temps presse

| Situation | Geste |
|---|---|
| `[6:15]` dépassé | raccourcir S8 (garder la conclusion : aucune solution ne coche tout) et S9 |
| `[11:30]` dépassé | couper le plan « tableau de bord » de la vidéo |
| Question pendant l'exposé | noter, répondre brièvement, reprendre au point suivant |
| **Jamais** | couper S3 (le patient), S16 (l'évaluation) ou S18 (les limites) |

## Questions probables du jury

| Question | Réponse courte |
|---|---|
| Pourquoi une entreprise de matériel biomédical gère-t-elle des données patients ? | son département R&D gère depuis 2024 des systèmes d'information médicale (GNU Health, MAVIS, base clinique) |
| Pourquoi une règle stricte plutôt qu'un score ? | le score de la première version a réuni deux homonymes aux CIN différents, sur 100 000 patients ; la règle stricte ne fusionne jamais à tort, au prix du rappel |
| Pourquoi ne pas estimer des poids automatiquement, comme Splink ? | pour qu'un gestionnaire de données puisse lire la règle ; il n'y a d'ailleurs plus de poids du tout |
| Pourquoi Spark, si Pandas est plus rapide sur vos volumes ? | Spark porte l'extraction, le lac, GOLD et désormais la déduplication : tout se répartit en ajoutant des nœuds |
| Que se passe-t-il si la VM s'arrête pendant un run ? | le run est reconnu orphelin (processus disparu) : il est marqué en échec et repris à l'étape interrompue, sans bloquer la planification |
| Et avec des millions de lignes ? La VM est-elle assez puissante ? | la VM limite la démonstration (8 Go, gels observés). La règle stricte s'exécute dans Spark sans tout rapatrier : 212 523 fiches en moins de trois minutes. Pour des millions, il faut extraire les seules lignes nouvelles et ajouter des nœuds |
| Votre précision est-elle vraiment de 1 ? | sur tous nos jeux, oui, 100 000 patients compris ; la première version à score y réunissait deux homonymes. Reste le cas d'un CIN partagé par erreur, que nos données ne contiennent pas |
| Le consentement par type de dossier est-il fait ? | non, il est en cours ; le consentement par finalité est réalisé et testé (401, 403, 422) |
| Et le RGPD à Madagascar ? | le RGPD sert de cadre de conception ; le droit malgache reste à étudier avant toute production |

## Contrôle du débit

Mots réellement prononcés par slide (texte « à dire » et transitions), recomptés par script le
30/09/2026 après le passage à la règle stricte. La vidéo (S17) n'est comptée que pour sa narration.

| Slides | Durée prévue | Mots | Débit |
|---|---|---|---|
| S1 à S6 (ouverture) | 3:30 | 421 | 120 /min |
| S7 à S10 (état de l'art, existant) | 2:45 | 285 | 104 /min |
| S11 à S16 (solution, résultats) | 5:15 | 580 | 110 /min |
| S17 (vidéo 3:30) | 3:30 | 68 | narration seule |
| S18 à S20 (limites, conclusion) | 1:30 | 147 | 98 /min |
| **Total** | **16:30** | **1 501** | — |

Les slides S1 à S4 sont les plus denses (environ 130 mots par minute) : ce sont celles du récit,
à dire posément. Les slides techniques laissent le temps de montrer l'écran. Avec la marge, l'exposé
tient dans 20 minutes.
