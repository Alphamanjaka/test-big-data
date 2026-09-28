# Script de passage oral — Soutenance M2 MBDS (20 min)

> **À quoi sert ce fichier.** C'est le **texte à dire**, pas le support projeté : le support reste
> `slides_soutenance.md`. Débit de référence d'une soutenance : **140 mots/minute**.
> Budget : **16:00 de contenu + 4:00 de marge**. Chaque section donne un objectif de mots ; un
> tableau de contrôle en fin de fichier permet de vérifier l'adéquation.
> Repères `[0:00] → [0:30]` = position dans le budget. `→` = transition, à dire en passant à la
> slide suivante.
> **Règle appliquée** : aucune affirmation non vérifiable ; les nuances d'honnêteté du mémoire
> (précision = plancher, 14/14 = test de fumée, API Flask = reporting) sont **dites à l'oral**.

---

## Avant de répéter

**Les trois commandes de la démonstration** (à exécuter sur la VM, pas à dire) :

```bash
.venv\Scripts\python -m pytest projet/code-source/tests -q
.venv\Scripts\python projet\code-source\evaluation\evaluate_engine.py --level hard
bash projet/code-source/provision/scripts/run_pipeline.sh
```

**Vidéo** : 3:30 maximum, muette de préférence, à enregistrer à la maison avec la VM allumée ; ne
pas filmer le poste actuel. Prévoir une capture d'écran pour chaque commande. Tester la lecture sur
le poste de soutenance avant le jour J.

**Figures** : projetées `fig-1` (S2), `fig-2` (S4), `fig-4` (S5), `fig-8` (S7) ; en réserve `fig-6`,
`fig-3`, `fig-9` ; **jamais projetée** `fig-5` (5,7 pt, illisible en projection).

**Trois choses à ne pas dire** : que PostgreSQL a été validé en conditions réelles (le `.env` n'a
pas été fourni) ; que les 14 tests API prouvent le contrôle d'accès (ils prouvent la joignabilité) ;
que le pipeline a été exécuté sur ce poste (il ne l'est pas).

---

## Chronométrage

| Repère | Fin de | Contenu |
|---|---|---|
| `[4:00]` | partie A | le problème, la promesse, la démarche |
| `[10:00]` | partie B | architecture, déduplication, résultats, évaluation, limites |
| `[14:00]` | partie C | démonstration |
| `[16:00]` | partie D | réponse, perspectives, remerciements |
| `[20:00]` | — | **arrêt impératif** (créneau questions distinct) |

---

## S1. Titre — 0:30 · `[0:00] → [0:30]` · 72 mots mesurés

**À dire**
> Bonjour à toutes et à tous. Je suis Ranomenjanahary Manjaka Alpha, en deuxième année de master
> Big Data. Mon stage chez Madagascar Medical Technology a porté sur une plateforme de
> centralisation et de gouvernance de données patients. Elle répond à deux besoins qu'on oppose
> souvent : garantir la qualité de la donnée, et maîtriser qui peut y accéder. Vingt minutes : le
> problème métier, la réalisation technique, une démonstration, puis mes limites assumées.

**À montrer** — page de garde du rapport.

→ « Commençons par le problème que j'ai rencontré en entrant dans l'établissement. »

---

## S2. Le problème — 1:15 · `[0:30] → [1:45]` · 146 mots mesurés

**À dire**
> Voici un même patient, tel qu'il apparaît dans les trois systèmes de l'établissement. En
> pharmacie : « Jean Rakoto », CIN 101 02404 5. En consultation : « Rakoto Jean », 101024045. En
> imagerie : « J. RAKOTO ». Trois systèmes, trois formats, et même pas le même nom de colonne pour
> le genre — la pharmacie écrit `sexe`, la consultation `genre`, l'imagerie `sex`.
>
> Le point important, c'est que **chaque base est intègre avec elle-même** : dans MAVIS, j'ai vérifié
> une jointure sur 9 791 lignes sur 9 791. Ce n'est donc pas un problème de qualité. C'est un problème
> d'absence d'équivalent **entre** les bases.
>
> La conséquence est directe : un dossier éclaté, des agrégats faux — un patient compté trois fois,
> jamais compté une seule — et des accès que personne ne maîtrise. Sur la figure, vous voyez les
> trois systèmes isolés, les cinq manques que j'ai identifiés, et les quatre réponses que le projet
> apporte.

**À montrer** — `figures/fig-1.png` : pointer successivement les 3 systèmes, les 5 manques, les
4 réponses.

→ « Ces cinq manques, ce sont exactement les trois engagements de la plateforme. »

---

## S3. La promesse — 1:00 · `[1:45] → [2:45]` · 120 mots mesurés

**À dire**
> La plateforme tient donc trois engagements.
>
> Un : **centraliser**. Les trois sources convergent vers un Data Lake Medallion, trois zones de qualité
> croissante, RAW, SILVER, GOLD.
>
> Deux : **dédupliquer de façon explicable**. Je n'ai pas écrit « on regroupe les doublons » ; j'ai
> écrit : chaque fusion porte une méthode, un score et une justification, et elle est consultable
> dans le lac de données.
>
> Trois : **gouverner**. Un accès n'est pas accordé parce qu'on est autorisé à entrer, mais parce
> qu'une finalité a été déclarée et acceptée, et chaque accès est journalisé.
>
> Un mot sur les données : elles sont **exclusivement synthétiques**, générées pour cette étude.
> C'est ce qui permet de démontrer la confidentialité sur des cas réels sans exposer personne.

**À montrer** — les 3 puces, une par une. *Support : `documents/cahier_des_charges.md` §3.*

→ « Pour atteindre cet objectif, j'ai choisi une démarche, et elle est visible sur la figure suivante. »

---

## S4. Démarche — 1:15 · `[2:45] → [4:00]` · 154 mots mesurés

**À dire**
> La figure montre six étapes, et je voudrais insister sur leur ordre : chaque technologie est
> introduite par un besoin, jamais l'inverse.
>
> J'ai commencé par un MVP en Pandas avec PostgreSQL, parce qu'il fallait une réponse rapide à la
> question « est-ce qu'une déduplication de patients est même possible ici ? ». Ensuite seulement,
> j'ai validé avec une **vérité terrain** : un fichier qui dit, pour chaque enregistrement, quel
> patient réel il désigne. Ce fichier n'est jamais donné à l'algorithme — il sert uniquement à le
> noter.
>
> Spark est arrivé après, pour une seule raison : le MVP tenait dans un seul nœud, la cible ne le
> pouvait pas. Le Data Lake Medallion est donc venu avec Spark, et non avant. La gouvernance, enfin,
> arrive en dernier mais conditionne l'accès : pas de contrôle, pas de plateforme.
>
> J'ai aussi fusionné deux proofs of concept préexistants en un dépôt unique et autonome.

**À montrer** — `figures/fig-2.png`, suivre la chaîne de gauche à droite.

→ « Voyons maintenant l'architecture qui organise ces six étapes. »

Another garbled fragment. Must rewrite cleanly.

---

## S5. Architecture cible — 1:30 · `[4:00] → [5:30]` · 168 mots mesurés

**À dire**
> L'architecture tient en trois plans, comme la figure le montre.
>
> Le plan machine : un Data Lake Medallion sur HDFS, Hive et Spark. Le générateur écrit en RAW, les
> tables FHIR se construisent en SILVER, les vues de consommation en GOLD.
>
> Le plan identité : c'est là que se trouve le cœur du projet. Un moteur de déduplication, écrit une
> fois, décliné en deux implantations — Pandas pour le MVP, PySpark pour le lac. Les deux
> implantations partagent le même code de normalisation, les mêmes poids et le même seuil, lus dans
> un fichier de configuration. Elles ne diffèrent que par la façon de regrouper les enregistrements.
>
> Le plan gouvernance : un PostgreSQL central qui porte la table des patients maîtres, les
> consentements, le journal d'accès et les clés d'API, plus une API par finalité.
>
> Je souligne un point : les poids et le seuil sont **déclarés en YAML, pas écrits dans le code**.
> Modifier le comportement de la déduplication se fait par une seule édition de fichier.

**À montrer** — `figures/fig-4.png` : les trois niveaux. *Réserve : `fig-5.png` pour les questions.*

→ « Le cœur du projet, c'est la déduplication. »

---

## S6. Déduplication explicable (MPI) — 1:30 · `[5:30] → [7:00]` · 219 mots mesurés

**À dire**
> Le principe tient en une phrase : **aucune fusion sans justification lisible**. C'est ce qu'on
> appelle une MPI, une identification de master patient, et c'est le cœur du projet.
>
> Le moteur travaille en deux temps. D'abord un **blocage** : trois index bornés — préfixe de nom,
> date de naissance, CIN — qui évitent de comparer toutes les paires possibles. Le volume passe de
> « tout contre tout » à un sous-ensemble, ce qui est la condition pour tenir sur une VM de 4 cœurs
> et 8 gigaoctets.
>
> Ensuite la décision. D'abord une voie **exacte**, par clé composite : date de naissance, CIN et nom
> normalisé. Si elle échoue, une voie **probabiliste** : un score pondéré — 0,5 sur le nom, 0,3 sur
> la naissance, 0,1 sur le CIN, 0,1 sur la ville — au-dessus de 0,80.
>
> Un point de conception que je tiens à signaler : **aucune valeur n'est devinée**. Un genre qui
> n'est pas dans la liste fermée, un CIN dont la longueur est incohérente, une date illisible : le
> champ reste vide. L'enregistrement bascule alors vers la voie probabiliste. Un champ douteux ne
> peut donc pas corrompre une clé de rapprochement exact.
>
> Chaque décision sort avec quatre éléments : l'identifiant du patient maître, la méthode, le score
> et l'explication. C'est ce qui permet à un gestionnaire de données de contester une fusion.

**À montrer** — les 3 critères de blocage et les poids. *Réserve : `fig-6.png`.*

→ « Sur cette base, voici ce que le pipeline a réellement produit. »

---

## S7. Résultats du run — 1:00 · `[7:00] → [8:00]` · 112 mots mesurés

**À dire**
> Ce sont des chiffres de run, pas des chiffres de présentation. Sur la VM, le pipeline Medallion
> s'est exécuté de bout en bout : quatre étapes sur quatre.
>
> La zone SILVER compte 214 lignes patients : 76 en pharmacie, 76 en consultation, 62 en imagerie.
> Après déduplication, cela donne 145 patients maîtres et 69 doublons liens, soit un taux de
> duplication de 32,24 %.
>
> Le contrôle de cohérence est la soustraction : 214 moins 69 égale bien 145, et je peux le vérifier
> par un simple comptage sur le lac, sans consulter la logique de fusion. C'est la correspondance
> « un patient maître = un enregistrement non dupliqué » qui est vérifiée, pas la décision.
>
> L'API répond sur 14 tests sur données réelles, sans données de secours.

**À montrer** — `figures/fig-8.png` : les 4 étapes, puis le tableau de compteurs.

→ « Est-ce que ces 145 patients maîtres sont les bons ? C'est la question suivante. »

---

## S8. Évaluation ground-truth — 1:15 · `[8:00] → [9:15]` · 169 mots mesurés

**À dire**
> Pour le vérifier, j'ai construit une **vérité terrain** : trois jeux synthétiques, easy, medium et
> hard, tous issus des **mêmes 500 patients maîtres** avec la même graine aléatoire ; seul le taux de
> variation change — 10, 30 puis 50 %.
>
> Le résultat le plus important : **zéro faux positif sur les trois jeux**. Le moteur n'a jamais
> fusionné à tort. En santé, c'est la propriété critique : une fusion erronée mélange deux personnes
> et contamine tous les agrégats.
>
> Mais je dois être précis sur sa portée. C'est un **plancher, pas une borne**. Mon générateur dégrade
> des enregistrements existants — casse, espaces, faute de frappe, changement de format — mais il ne
> crée jamais deux personnes distinctes qui se ressemblent. Le cas adversariaire des faux positifs
> n'est donc pas sollicité par la vérité terrain. Le dire fait partie du résultat.
>
> Côté rappel, l'ajout du CIN comme clé exacte a fait passer le jeu dur de 0,287 à **0,422**, toujours
> sans faux positif. Et les deux implantations, Pandas et Spark, prennent des **décisions
> identiques** sur les jeux testés.

**À montrer** — le tableau de métriques. *Réserve : `fig-9.png`.*

→ « Venons-en aux points que je n'ai pas résolus. »

---

## S9. Difficultés et honnêteté — 0:45 · `[9:15] → [10:00]` · 112 mots mesurés

**À dire**
> Quatre points, volontairement.
>
> Un incident réel : la zone SILVER explosait à 11 614 lignes, parce qu'une colonne d'identifiant
> était capturée par le mapping dynamique. Corrigé, et documenté comme piège anti-régression.
>
> Deux dettes assumées : `patient_events_gold` est **vide**, et la table de consentement n'était pas
> peuplée au moment du run. La **mécanique** est prouvée par les tests, pas la **donnée**.
>
> Enfin une distinction : l'API de données est un *reporting*, elle ne filtre rien ; le contrôle par
> rôle et consentement s'applique à l'API de gouvernance. Et les 14 sur 14 sont des tests de fumée :
> ils prouvent la joignabilité, pas le contrôle d'accès, qui est vérifié par 13 cas dédiés.

**À montrer** — le tableau des dettes.

→ « Pour montrer que ce n'est pas qu'une affirmation, voici la démonstration. »

---

## S10. Démonstration vidéo — 4:00 · `[10:00] → [14:00]` · 76 mots de narration + vidéo 3:30

**Vidéo muette de 3:30 + narration à voix haute.** Si la vidéo est sonore, couper la narration et
commenter au moment des plans 2 et 3.

| Plan | Ce qu'on voit | **À dire pendant le plan** |
|---|---|---|
| 1 · 1:00 | 54 tests qui passent | « Le moteur de déduplication et l'API de gouvernance, 54 tests, aucun échec. » |
| 2 · 1:00 | métriques du jeu hard | « Le même moteur, sur le jeu à 50 % de variation : zéro faux positif, rappel 0,422, et les mêmes décisions en Pandas et en Spark. » |
| 3 · 1:30 | pipeline Medallion 4/4 | « Et voici le pipeline complet, de l'extraction au chargement : quatre étapes sur quatre. » |
| 4 · 0:30 | repli (captures figées) | « Si la vidéo ne s'est pas lancée, les mêmes preuves sont ici : 214 lignes, 145 maîtres, 69 doublons, 32,24 %. » |

**À dire en introduction, avant de lancer la vidéo (15 s)**
> Trois démonstrations, dans l'ordre où le projet a été construit : les tests, l'évaluation, puis le
> lac de données.

→ « Après la démonstration, la synthèse. »

---

## S11. Réponse à la problématique — 1:00 · `[14:00] → [15:00]` · 138 mots mesurés

**À dire**
> Je reviens à la problématique. Sur des données synthétiques et une architecture Big Data, la
> plateforme **centralise** trois systèmes hétérogènes dans un Data Lake Medallion, **normalise** par
> un contrat explicite où aucune valeur n'est devinée, **déduplique** de façon explicable — chaque
> fusion porte une méthode, un score et une justification, et toutes les décisions sont identiques
> entre Pandas et Spark — et **gouverne** par consentement par finalité, avec authentification par
> clé, rôles, et journalisation des accès y compris les refus.
>
> Le résultat mesuré : zéro faux positif sur les trois jeux évalués, un rappel dur de 0,422, et une
> parité de décision vérifiée entre les deux implantations.
>
> Et je revendique la limite : le produit de ces trois engagement n'est pas un système de production,
> c'est une chaîne complète, testée et honnête sur ce qu'elle ne fait pas encore.

**À montrer** — les 4 verbes, dans l'ordre.

→ « Ce que je ferais ensuite. »

---

## S12. Perspectives — 0:45 · `[15:00] → [15:45]` · 104 mots mesurés

**À dire**
> Quatre chantiers, par ordre de valeur.
>
> Le premier est un correctif, pas une amélioration : rattacher les encounters, conditions et
> observations aux patients, pour que la zone GOLD contienne enfin des événements de soin et pas
> seulement des identités.
>
> Le deuxième est d'alimenter la base centrale de consentements, ce qui rendrait la preuve de
> gouvernance complète sur le jeu de données lui-même.
>
> Le troisième est méthodologique : ajouter au générateur des homophones quasi identiques, pour
> solliciter enfin le cas adversariaire des faux positifs.
>
> Le quatrième est l'échelle : conteneurisation, intégration continue, export de la VM. Aucun n'est
> dans le périmètre de ce stage.

**À montrer** — les 4 puces. *Support : `chapters/09-conclusion.md`.*

→ « Je vous remercie. »

---

## S13. Merci — 0:15 · `[15:45] → [16:00]` · 34 mots mesurés

**À dire**
> Je vous remercie. Le dépôt unique et le rapport de stage sont disponibles. Je reste à votre
> disposition pour vos questions, notamment sur les poids, le seuil, ou l'absence d'estimation par
> EM.

**À montrer** — contact / référence du dépôt.

---

## Gestion du temps : que sacrifier si vous débordrez

| Situation | Geste |
|---|---|
| `[4:00]` dépassé | raccourcir S5 et S6 : les figures portent déjà l'information, ralentir sur S9 |
| `[10:00]` dépassé | réduire le plan 3 de la vidéo (couper le pipeline) plutôt que l'évaluation |
| `[14:00]` dépassé | ne PAS toucher à S11 et S12 : ce ne sont que 2 minutes de synthèse |
| Question du jury en cours d'exposé | noter, répondre, reprendre le fil au point suivant |
| **Toujours** | ne jamais couper S2 (problème), S8 (évaluation), S9 (honnêteté) |

## Contrôle du débit (mesuré, pas estimé)

Comptage automatique des sections « À dire » : la colonne *mots* ne compte que ce qui est réellement
prononcé, hors gestes et hors annotations.

| Slide | Durée | Mots | Débit | Verdict |
|---|---|---|---|---|
| S1 | 0:30 | 72 | 144 /min | tenu |
| S2 | 1:15 | 146 | 117 /min | large |
| S3 | 1:00 | 120 | 120 /min | large |
| S4 | 1:15 | 154 | 123 /min | large |
| S5 | 1:30 | 168 | 112 /min | large |
| S6 | 1:30 | 219 | 146 /min | tenu |
| S7 | 1:00 | 112 | 112 /min | large |
| S8 | 1:15 | 169 | 135 /min | tenu |
| S9 | 0:45 | 112 | 149 /min | à la limite |
| S10 | 4:00 | 76 + vidéo 3:30 | — | narration seulement |
| S11 | 1:00 | 138 | 138 /min | tenu |
| S12 | 0:45 | 104 | 139 /min | tenu |
| S13 | 0:15 | 34 | 136 /min | tenu |
| **Parole** | **12:00** | **1 548** | **129 /min** | — |

**Conclusion mesurée.** Les 12 slides de parole contiennent 1 548 mots, soit **11:03 à 140 mots/min**,
auxquels s'ajoutent 12 transitions (121 mots, 0:52). Avec la vidéo de 3:30, l'exposé court
**15:25 sur 16:00 planifiées** — 35 secondes de filet à l'intérieur du plan, plus les 4:00 de marge
déclarée, soit environ **19:25 sur 20:00**.

Conséquence pratique : il ne faut **pas** ajouter de texte avant la première répétition. Le temps
disponible se dépense en **ralentir** sur S2, S8 et S9, et en laissant le temps de montrer les
figures. Trois slides sont volontairement au-dessus du débit de comfortable parce que la figure ou le
tableau projeté porte déjà le détail : S6 (146 /min), S9 (149 /min) et S1 (144 /min).
