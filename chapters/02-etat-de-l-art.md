# Chapitre 2 — État de l'art

> **Portée de l'étude.** Aucun des produits ni aucune des bibliothèques comparés n'a été déployé
> sur la VM ni mesuré : la comparaison s'appuie sur leur **documentation** et sur les métadonnées
> publiques de leurs versions. Les capacités citées sont donc des **capacités annoncées**, jamais
> des résultats obtenus.

## 2.1 Notions de référence et critères de comparaison

Cette section pose les notions du domaine et le droit applicable, puis en déduit les critères
de comparaison.

### 2.1.1 Méthode de la veille

**Protocole de recherche.** Chaque sous-section répond à une **question formulée à
l'avance**, dérivée du cahier des charges, à laquelle on a cherché une réponse sourcée. Les recherches ont combiné des mots-clés anglais et
français : *record linkage*, *entity resolution*, *entity matching*, *master patient index*,
*client registry*, *FHIR Consent*, *lakehouse*, « protection des données à caractère personnel
Madagascar ».

**Tableau 4 — Les questions de veille et les sources retenues.**

| Question de veille | Où c'est traité | Sources retenues |
|---|---|---|
| Quelle théorie fonde l'appariement d'enregistrements, et où en est la recherche ? | § 2.1.2 | [B1], [B2], [B3], [B21], [B22] |
| Quelles similarités, et lesquelles sont utilisables sous Python 3.8 ? | § 2.1.3 | [B3], [B4], [B31] |
| Comment éviter la comparaison quadratique ? | § 2.1.4 | [B1], [B3] |
| Quel standard de santé pour l'identité et l'échange ? | § 2.1.5 | [B5] |
| Quel droit s'applique aux données de santé à Madagascar ? | § 2.1.6 | [B24], [B25] |
| Quelles références de conception pour le consentement ? | § 2.1.6 | [B10] à [B12], [B23], [B26] |
| Quelles briques Big Data, et pour quel usage ? | § 2.1.7, § 2.1.8 | [B6] à [B9], [B27], [B28] |
| Que proposent le marché et l'open source ? | § 2.2.1 | [B13] à [B18], [B29], [B30] |
| Quelles alternatives aux briques retenues ? | § 2.2.2 | [B15], [B21], [B22], [B28], [B31] |

**Règles de sélection retenues.** (1) Une source **primaire** est préférée à une source
secondaire : publication, texte de loi, spécification, documentation officielle. (2) Une source
est **fondatrice** ou **à jour** selon l'axe : les fondations datent de 1969 [B2] et restent la
référence ; la documentation technique est suivie à la version publiée au moment de la
consultation. (3) Une source doit être **exploitable** : chaque référence justifie une décision
de conception ou signale un risque. (4) Le **biais commercial** est signalé : la documentation
d'un éditeur décrit ce que le produit promet, pas ce qu'il fait sur le terrain ; les solutions
propriétaires sont donc citées pour leurs capacités annoncées [B13], [B14], [B17]. (5) Chaque
source en ligne porte sa **date de consultation** dans la bibliographie.

**Période couverte** : des travaux fondateurs (1969) aux versions publiées en septembre 2026.
Ce n'est pas une revue systématique, mais une revue **ciblée sur les décisions du projet** : une
source est retenue parce qu'elle permet de justifier ou de contester un choix.

**Couverture de la grille d'analyse.** La grille d'état de l'art du master compte 20 axes. Le
mémoire en traite 12 directement et 6 partiellement ; un axe est hors périmètre (les personas)
et un axe optionnel n'est pas traité (la sobriété numérique). Le détail, axe par axe, figure en
annexe G.

### 2.1.2 Entity Resolution et Record Linkage

Le problème central du projet consiste à déterminer si des enregistrements issus de sources
différentes désignent la même personne. Il porte un nom générique : **Entity Resolution** (ER),
également appelé *record linkage*, *data matching*, *duplicate detection* ou *fusion de
doublons* selon les communautés [B1], [B3].

Les fondements théoriques datent de 1969 : **Fellegi et Sunter** formalisent la décision
d'appariement de deux enregistrements. On compare leurs champs, puis on conclut à un match, à un
non-match ou à un match indéterminé (*possible match*) [B2]. Chaque champ qui concorde apporte un
**poids** en faveur du match, chaque champ qui diffère un poids contre ; la somme est comparée à
deux seuils. Ce modèle probabiliste reste la référence des systèmes d'ER modernes [B1].

Le processus générique, décrit par Elmagarmid et al. [B1] et détaillé par Christen [B3], se
décompose en cinq étapes. Le **prétraitement** nettoie et standardise les champs (casse, accents,
formats de date). L'**indexation** (*blocking*) réduit le nombre de paires à comparer (§ 2.1.4).
La **comparaison** mesure la similarité champ à champ (§ 2.1.3). La **classification** décide
match ou non-match. L'**évaluation** mesure la qualité sur une vérité terrain, c'est-à-dire un jeu
où l'on sait à l'avance quels enregistrements désignent la même personne. Le chapitre 7 montre
comment chacune de ces étapes a été réalisée.

Le résultat attendu de l'ER est une **réconciliation d'identités** : un patient présent sous
plusieurs formes dans plusieurs systèmes doit être reconnu comme une seule personne, sans fusion
erronée de personnes distinctes. C'est l'équilibre **précision contre rappel** : la précision
mesure la part des fusions qui sont justes, le rappel la part des doublons réels qui ont été
retrouvés.

**L'évolution récente : apprendre la décision.** Depuis Fellegi-Sunter, la recherche a
progressivement remplacé les poids fixés à la main par des décisions **apprises**. L'estimation
des poids par l'algorithme **EM** (*Expectation-Maximisation*, une méthode statistique qui
déduit les poids des données elles-mêmes, sans exemples étiquetés) est aujourd'hui outillée à
grande échelle [B15]. Les approches par **apprentissage profond** vont plus loin : Ditto
reformule l'appariement comme un problème de classification de paires de textes, résolu par un
modèle de langage pré-entraîné (BERT, RoBERTa) ; selon ses auteurs, il améliore le F1 jusqu'à
29 % sur les jeux de référence [B21]. Les travaux les plus récents emploient des **LLM** (grands modèles de langage
génératifs) interrogés directement, sans entraînement spécifique à la tâche [B22].

Ces approches gagnent en qualité ce qu'elles perdent en **lisibilité** et en **sobriété** : elles
exigent des exemples étiquetés, un processeur graphique ou un service externe, et leur décision
ne se résume plus à une somme de poids. Pour des données de santé, où chaque fusion doit pouvoir
être justifiée devant un gestionnaire de données, c'est un coût réel. Le § 2.2.2 en tire les
conséquences pour le projet.

> **Point de vocabulaire.** Entity Resolution = déterminer si deux enregistrements
> désignent la même entité [B1] ; le résultat produit un **golden record** (fiche
> consolidée) et une **identity map** (table de correspondance traçable).

### 2.1.3 Mesures de similarité

Deux chaînes qui désignent la même personne diffèrent rarement d'un seul caractère : les
variantes *Jean Rakoto* / *Rakoto Jean* / *J. RAKOTO* imposent de mesurer une ressemblance, pas
seulement une égalité. Les mesures classiques du domaine se répartissent en trois familles
[B1], [B3] :

**Tableau 5 — Les mesures de similarité classiques.**

| Famille | Mesure | Principe | Usage typique |
|---|---|---|---|
| **Édition** | **Levenshtein** | nombre minimal d'insertions, suppressions ou substitutions pour passer d'une chaîne à l'autre | nom, prénom |
| | **OSA** (*optimal string alignment*) | Levenshtein avec transposition de deux caractères voisins (souvent appelée « Damerau » en pratique) | fautes de frappe |
| | **Jaro–Winkler** | similarité qui favorise un début de chaîne commun | initiales, noms tronqués |
| **Jetons** | `ratio`, `token_sort_ratio` | comparaison des mots, indépendamment de leur ordre | *Rakoto Jean* contre *Jean Rakoto* |
| **Phonétique** | Soundex et ses successeurs | code identique pour des noms qui se prononcent de la même façon | variantes orthographiques d'un même nom |

Les codages phonétiques sont conçus pour une langue donnée : Soundex, par exemple, repose sur
la prononciation anglaise [B3]. Les sources consultées ne décrivent aucun codage adapté aux
noms malgaches ; le projet s'en tient donc aux mesures d'édition et de jetons, qui ne
supposent aucune langue.

Ces mesures sont implémentées par **RapidFuzz**, une bibliothèque Python/C++ sous licence MIT
[B4]. Son intérêt est **opérationnel** : légère, sans dépendance de traitement du langage, elle
fonctionne sous Python 3.8, la version imposée par la VM. Ce point mérite une précision : la
documentation consultée décrit la version 3.14.5, qui exige Python 3.10 ; sous Python 3.8, la
dernière version installable est la **3.9.7** (septembre 2024) [B31]. Le projet dépend donc d'une
version figée, comme toute bibliothèque maintenue sur cette version de Python (§ 2.2.2).

La bibliothèque `sentence_transformers`, qui compare des textes par réseau de neurones, a été
**écartée** : elle plantait sous Python 3.8 dans l'environnement du stage.

### 2.1.4 Blocking et complexité

Comparer chaque enregistrement à tous les autres est **quadratique** : pour n patients, il faut
de l'ordre de n² comparaisons. La pratique standard du domaine, le **blocking** (ou
indexation), regroupe les enregistrements en blocs de candidats qui partagent une clé grossière
(préfixe du nom, date de naissance, numéro d'identité). La comparaison fine n'est exécutée
**qu'à l'intérieur de chaque bloc** [B1], [B3].

Le choix des clés est un compromis. Une clé trop fine laisse échapper des doublons (deux
graphies du même nom tombent dans deux blocs différents) ; une clé trop large ramène vers le
coût quadratique. La littérature recommande donc plusieurs clés combinées, chacune rattrapant les
erreurs des autres [B3]. Sans blocking, un volume de l'ordre du million de patients imposerait
environ 10¹² comparaisons. Le projet combine trois clés (préfixe du nom, date de naissance, CIN) ;
leur mise en œuvre est décrite au § 7.2.3.

### 2.1.5 Master Patient Index et interopérabilité FHIR

En santé, l'ER aboutit à un référentiel d'identités : le **Master Patient Index (MPI)**. Chaque
fiche des bases sources y est rattachée à un identifiant unique, celui du **patient maître**
(*master patient*), par une **identity map**, une table de correspondance qui conserve la trace
de chaque rattachement :

**Tableau 6 — Exemple d'identity map : trois fiches rattachées au même patient maître.**

| Source | Identifiant source | Patient maître | Score | Méthode |
|---|---|---|---|---|
| pharmacy | 15 | 102 | 1,000 | exacte |
| consultation | 88 | 102 | 0,950 | probabiliste |
| imaging | IMG-20 | 102 | 0,920 | probabiliste |

Cette démarche rejoint le standard d'interopérabilité **FHIR** (*Fast Healthcare
Interoperability Resources*, publié par l'organisme HL7), qui définit pour la ressource Patient
une opération dédiée, `$match` : elle reçoit les champs d'un patient et retourne les
correspondances candidates, chacune avec un score explicite [B5]. Le projet reprend cette philosophie, rechercher puis apparier par
score, sans déployer de serveur FHIR.

Côté format, FHIR sert de **schéma pivot** : un format commun vers lequel chaque source est
traduite. Quatre ressources FHIR (`Patient`, `Encounter`, `Condition`, `Observation`) suffisent à
harmoniser des sources structurées différemment.

### 2.1.6 Consentement et cadre juridique des données de santé

**Le droit applicable : la loi malgache n° 2014-038.** L'établissement commanditaire est à
Madagascar. Le texte applicable est donc la loi n° 2014-038 du 9 janvier 2015 sur la protection
des données à caractère personnel [B24]. Elle classe les données de santé parmi les **données
sensibles**, dont le traitement est **interdit par principe** (art. 18). Des dérogations existent :
le **consentement exprès** de la personne ; les traitements nécessaires aux soins, mis en œuvre
par un professionnel de santé ou par une personne soumise au secret professionnel ; la recherche
d'intérêt public en santé, si la personne ne s'y est pas opposée (art. 18).

Trois autres articles pèsent directement sur la conception. L'article 14 impose des **finalités
déterminées** et interdit de réutiliser les données pour une autre finalité **sans consentement**.
L'article 15 impose une **obligation de sécurité** contre l'accès non autorisé. L'article 20
n'autorise le **transfert à l'étranger** que vers un pays offrant une protection équivalente, ou
avec une autorisation de l'autorité de contrôle. La loi institue cette autorité : la **CMIL**
(Commission Malagasy de l'Informatique et des Libertés, art. 28). Elle soumet en outre les
traitements présentant des risques particuliers à son **autorisation préalable** (art. 46).
Selon l'observatoire Law Lab Africa, consulté en septembre 2026, la CMIL n'était pas encore
opérationnelle et aucune décision de contrôle n'avait été publiée [B25].

**La référence de conception : le RGPD et la CNIL.** Le règlement européen (RGPD) et les
recommandations de la CNIL française ont servi de cadre de conception, pour deux raisons. La loi
malgache en partage les principes (finalité, consentement, sécurité, autorité indépendante), et
la doctrine européenne est abondante et détaillée. Le RGPD pose la même interdiction de principe
des données de santé et la même dérogation par consentement explicite (art. 9.2.a) [B10]. La CNIL
précise deux distinctions utiles : la base légale (art. 6) et la dérogation propre aux données
sensibles (art. 9) se cumulent, et le consentement au **traitement** des données diffère du
consentement aux **soins** [B11], [B12].

**Tableau 7 — Exigences des deux textes et principe de conception retenu.**

| Exigence | Loi 2014-038 (Madagascar) | RGPD (référence de conception) | Principe de conception retenu |
|---|---|---|---|
| Données de santé = données sensibles | art. 18 | art. 9.1 | aucun accès par défaut |
| Dérogation par consentement | consentement exprès (art. 18) | consentement explicite (art. 9.2.a) | consentement enregistré, **refus par défaut** |
| Finalité déterminée, pas de réutilisation | art. 14 | art. 5.1.b | la finalité est **déclarée à chaque accès** et contrôlée |
| Sécurité, accès non autorisé | art. 15 | art. 32 | rôles, clés d'accès, refus explicite |
| Traçabilité | registre des traitements (art. 43) | registre (art. 30) | **journal de chaque accès**, refus compris |
| Transfert hors du pays | encadré (art. 20) | encadré (chapitre V) | **hébergement interne** |

Ce tableau appelle une nuance. Pour les soins eux-mêmes, le consentement n'est pas la seule base
possible : le traitement par un professionnel de santé soumis au secret est une dérogation
distincte (art. 18). En revanche, dès qu'une donnée collectée pour les soins est réutilisée pour
une autre finalité (analyse, recherche), l'article 14 exige un consentement. C'est exactement le
cas d'usage visé par le contrôle **par finalité** (*purpose-by-purpose*) : un consentement est
enregistré pour chaque finalité, et une finalité non consentie est refusée. La mécanique
correspondante (rôles, finalité obligatoire, table de consentement, journal d'audit) est décrite
au § 7.2.3.

**Le standard FHIR pour le consentement.** FHIR définit une ressource **Consent** [B26]. Elle
exprime une décision par défaut (*permit* ou *deny*) et des exceptions (*provisions*). Chaque
exception peut être limitée à une **finalité d'usage** (`provision.purpose`, codée dans le
vocabulaire HL7 *PurposeOfUse*), à une période, à un acteur ou à un type de données. La
spécification laisse volontairement l'**application** du consentement hors de son périmètre : elle
la délègue aux mécanismes de contrôle d'accès (OAuth, XACML). Dans la version 5.0.0 consultée, la
ressource est au niveau de maturité 2 (*Trial Use*), et seul le cas d'usage « vie privée » est
entièrement modélisé [B26]. Le modèle du projet en est une version simplifiée : une décision par finalité,
refus par défaut, sans périmètre de données ni période. L'application du consentement relève de
l'API, conformément à la répartition des rôles prévue par la norme.

**L'appariement respectueux de la vie privée.** Lorsque deux établissements veulent rapprocher
leurs patients sans s'échanger les identités en clair, la littérature propose le *privacy-preserving
record linkage* (PPRL). Chaque nom est d'abord transformé en empreinte, par exemple un filtre de
Bloom, un tableau de bits dérivé des fragments du nom, puis les empreintes sont comparées sans
jamais révéler le nom [B23]. Dans le projet, toutes les sources appartiennent au même
établissement et restent sur ses machines : l'appariement en clair y est légitime. La technique
deviendrait nécessaire pour un rapprochement **entre** établissements ; c'est une perspective.

Toutes les données manipulées sont **synthétiques**. La conformité est ici un **cadre de
conception**, pas une certification : aucune déclaration ni demande d'autorisation n'a été
adressée à la CMIL, puisque le prototype n'est pas déployé (§ 4.2).

### 2.1.7 Big Data : HDFS, MapReduce, Spark, Hive

**HDFS** (*Hadoop Distributed File System*) est le socle de stockage distribué de l'écosystème
Hadoop. Un **NameNode** tient les métadonnées (quel fichier, quels blocs, sur quelle machine) ; des
**DataNodes** stockent les blocs. Chaque bloc est **répliqué** sur plusieurs machines, et le calcul
est envoyé là où se trouvent les données (*data locality*) plutôt que l'inverse [B6].

Le premier modèle de calcul distribué, **MapReduce**, écrit ses résultats intermédiaires sur
disque entre chaque étape. **Apache Spark** l'a supplanté en pratique : il garde les données **en
mémoire** entre les étapes et offre une interface de haut niveau (DataFrame), utilisable depuis
Python avec **PySpark** [B7]. **Hive** apporte la couche SQL sur le lac de données. Son
**metastore** est le catalogue qui décrit les tables et leurs colonnes ; **HiveServer2** est le
service qui reçoit et exécute les requêtes SQL [B8].

Ces briques sont conçues pour le volume. Sur de petits jeux, leur coût de démarrage domine : le
projet a mesuré environ 1 à 2 ms en Pandas contre 0,4 à 4 s en Spark pour quelques dizaines de
lignes, l'essentiel du temps Spark étant le lancement de la machine virtuelle Java. Spark se justifie donc par le **volume visé**, pas par le volume de
démonstration. Le § 2.2.2 discute les alternatives à ce socle, et le § 7.1 décrit la plate-forme
retenue.

### 2.1.8 Data Lake Medallion et ELT

Le **modèle Medallion**, formalisé par Databricks, organise le lac en **zones de qualité
croissante** [B9]. La zone **RAW** conserve la donnée brute, telle qu'elle a été reçue. La zone
**SILVER** porte la donnée nettoyée, standardisée, avec les doublons identifiés. La zone **GOLD**
contient les données agrégées, prêtes à l'analyse.

Chaque zone est un **état distinct de la donnée**, ce qui apporte trois choses : la
**traçabilité** (on sait d'où vient chaque valeur), le **rejeu** (on relance un traitement depuis
une zone propre, sans tout recommencer) et la **séparation** des responsabilités exigée par la
gouvernance.

Le modèle Medallion est né dans le monde du ***lakehouse***, une architecture qui ajoute aux
fichiers d'un lac de données les garanties d'un entrepôt [B27]. Ces garanties sont les
transactions **ACID** (une écriture est entière ou n'a pas lieu, et deux écritures simultanées
ne se corrompent pas) et l'historique des versions d'une table. Elles sont portées par des
**formats de table** comme Delta Lake [B28]. Medallion est donc habituellement mis en œuvre sur
un tel format ; le projet l'applique sur de simples fichiers Parquet exposés par des tables
Hive, sans ces garanties. Le § 2.2.2 examine ce choix.

Le pipeline suit la logique **ELT** (*Extract, Load, Transform*) : l'ingestion charge la donnée
**telle quelle** dans RAW, et la transformation s'applique *a posteriori* dans les zones suivantes.
C'est le **schema-on-read** : on décide du format au moment de lire, et non au moment d'écrire,
ce qui caractérise le lac de données.

### 2.1.9 Critères de comparaison retenus

Sept critères sont déduits de ces notions, du problème posé au § 1.2.1 (données dispersées, à
dédupliquer et à gouverner) et des contraintes du stage (§ 4.2). Deux sont **éliminatoires** :
une solution qui ne les satisfait pas est écartée, quelles que soient ses qualités. Cinq sont des
critères de **qualité**, qui départagent les solutions restantes.

**Critères éliminatoires :**

- **E1 — Hébergement interne** (*on-premise*) : les données restent sur les machines de
  l'établissement. C'est une contrainte du commanditaire, et la voie la plus simple face à
  l'encadrement des transferts à l'étranger (art. 20 de la loi 2014-038, § 2.1.6).
- **E2 — Exploitable dans l'environnement du stage** : licence libre ou gratuite, VM de 8 Go
  déjà occupée par Hadoop, Hive et Spark, Python 3.8 (§ 4.2).

**Critères de qualité :**

- **Q1 — Déduplication explicable** : chaque fusion porte un score, une méthode et une
  justification (§ 2.1.2 à 2.1.4).
- **Q2 — Interopérabilité FHIR** : la solution sait lire ou produire le format pivot de santé
  (§ 2.1.5).
- **Q3 — Gouvernance par rôle, consentement et audit** : l'accès est contrôlé par le rôle, la
  finalité consentie et une trace (§ 2.1.6).
- **Q4 — Montée en charge** : la solution s'appuie sur un stockage et un calcul répartis
  (§ 2.1.7, § 2.1.8).
- **Q5 — Coût et indépendance** : pas de licence ni d'abonnement récurrent, et aucune fonction
  essentielle suspendue à la feuille de route d'un éditeur (§ 2.2.1).

## 2.2 Étude des solutions existantes

### 2.2.1 Produits et plateformes

Quatre familles de produits couvrent, partiellement, le besoin. Deux sigles reviennent souvent. Le
**MPI**, défini au § 2.1.5, est l'annuaire qui attribue un identifiant unique à chaque patient ;
dans les programmes de santé publique, on parle aussi de **registre de clients** (*client
registry*). Le **MDM** (*Master Data Management*) applique la même idée à toutes les données de
référence d'une organisation, patients ou non.

**Tableau 8 — Les sept solutions étudiées : apport et obstacle à l'adoption.**

| Solution | Famille | Apport pour le besoin | Ce qui bloque l'adoption ici |
|---|---|---|---|
| **InterSystems EMPI** [B13] | MPI commercial | Moteur d'identité déterministe **et** probabiliste, rapprochement avec un référentiel externe de population (LexisNexis LexID), fiche composite par personne, services d'échange IHE **PIX** et **PDQ** | Produit **propriétaire, sous licence** ; son atout, le référentiel externe, suppose de confronter les identités à des données tierces, ce qui contredit l'hébergement interne ; ne couvre ni le lac Medallion ni le consentement par finalité |
| **Talend MDM** [B14] | MDM commercial | Rapprochement et règles de **survie** (*survivorship* : quelle valeur garder lors d'une fusion), **golden record**, fusions validées par des gestionnaires de données (*data stewards*), seuils de confiance paramétrables | Suite **commerciale**, dont l'édition gratuite a été retirée (voir ci-dessous) ; suppose une équipe de gestionnaires de données ; pas d'interopérabilité **FHIR** native ; ne traite pas la gouvernance des accès aux données patients |
| **Azure Health Data Services** [B17] | Plateforme cloud santé | Services **FHIR** et **DICOM** gérés par Microsoft, export massif `$export` vers un stockage de lac, service de **dé-identification** (marquage, masquage ou substitution des données identifiantes) | Service **cloud**, facturé à l'usage : incompatible avec l'hébergement interne et soumis à l'encadrement des transferts (§ 2.1.6) ; ne fournit **ni MPI ni déduplication** |
| **HAPI FHIR** [B16] | Open source (Java, Apache 2.0) | Implémentation de référence d'un serveur FHIR : validation, stockage, opérations REST, recherche, `$match` | Fournit l'**interopérabilité** et un **cadre** d'intercepteurs d'autorisation et de consentement, que le développeur doit programmer lui-même (aucune politique fournie) ; **ni rapprochement d'identité maîtrisé, ni zones de qualité** : à lui seul, il ne résout aucun des trois problèmes du § 1.2.1 |
| **OpenCR** [B29] | Open source (registre de clients, OpenHIE) | Registre de patients libre, conçu pour les systèmes de santé publics de pays à ressources limitées : règles de décision **déterministes et probabilistes configurables**, **revue humaine** des correspondances douteuses, échanges en **FHIR R4** | Le plus proche du besoin d'identité. Mais il repose sur un service Node.js, un serveur HAPI FHIR et Elasticsearch : trois services de plus sur une VM déjà occupée par Hadoop, Hive et Spark ; il n'offre ni lac Medallion ni consentement par finalité |
| **Splink** [B15] | Open source (Python, MIT) | Appariement probabiliste à grande échelle : modèle **Fellegi-Sunter**, poids estimés par **EM**, exécution sur Spark ou DuckDB, environ un million d'enregistrements en une minute selon sa documentation ; graphique « en cascade » qui détaille la contribution de chaque champ au score | Excellent sur le **cœur** algorithmique, et explicable. Mais les poids sont **appris sur les données** et changent à chaque réestimation, là où le projet veut des poids **fixés et validés par le métier** ; ni gouvernance, ni Medallion, ni journal d'accès (§ 2.2.2) |
| **Apache Atlas** [B18] | Open source (gouvernance Hadoop) | Catalogue de métadonnées, **lignage** de bout en bout (d'où vient chaque donnée), étiquettes `PII` / `SENSITIVE` propagées le long des traitements | Gouvernance des **métadonnées**, pas des accès : Atlas ne filtre aucune requête à l'exécution et n'implémente ni consentement par finalité ni journal d'accès |

**Coût et dépendance à l'éditeur.** Deux produits du tableau (EMPI, Azure) imposent une licence
ou un abonnement récurrent, payé en devises. Ce coût se répète chaque année, bien au-delà du
stage. Il crée aussi une **dépendance** : l'établissement ne décide plus seul de l'évolution de
son outil. Le cas de Talend montre que ce risque n'est pas théorique. Après le rachat de Talend
par Qlik, l'édition libre Talend Open Studio a été retirée le 31 janvier 2024 ; elle n'est plus ni
distribuée ni mise à jour, et ses utilisateurs ont dû passer à l'offre payante ou migrer [B30].
Une fonction essentielle confiée à un produit peut ainsi disparaître par une décision
commerciale extérieure.

L'open source réduit ce risque sans le supprimer. Les bibliothèques abandonnent aussi les
anciennes versions de Python, et une installation limitée à Python 3.8 se retrouve sur une
version figée (§ 2.2.2). La différence est ailleurs : avec du code ouvert, l'établissement garde
le **contrôle de la logique de décision** et peut figer une version qui fonctionne, là où un
service commercial peut être retiré ou changer de tarif.

### 2.2.2 Briques technologiques alternatives

La comparaison des produits ne suffit pas : il faut aussi vérifier, brique par brique, que les
composants retenus ne sont pas dépassés par une alternative disponible. Le tableau ci-dessous
confronte chaque brique du projet à ses alternatives, en vérifiant leur compatibilité avec
Python 3.8 dans les métadonnées officielles des versions publiées [B31].

**Tableau 9 — Les briques du projet face à leurs alternatives.**

| Besoin | Brique retenue | Alternative | Ce que l'alternative apporte | Compatibilité Python 3.8 | Raison du choix |
|---|---|---|---|---|---|
| Calcul sur le lac | Spark 3.4.2 (PySpark) | DuckDB, Polars (moteurs sur une seule machine) | Nettement plus rapides sur petits et moyens volumes, sans machine virtuelle Java | versions figées : DuckDB 1.2.2, Polars 1.9.0 ; les versions actuelles exigent Python 3.10 | le sujet est une **plateforme Big Data** et le lac hérite du PoC Hadoop ; alternative **crédible** si le volume réel de l'établissement se révèle modeste |
| Format des tables | fichiers Parquet exposés par des tables externes Hive | Delta Lake 2.4 [B28] | transactions ACID, historique des versions, évolution du schéma | Delta 2.4 est compatible avec Spark 3.4 | le pipeline réécrit chaque zone en entier à chaque exécution : pas de mise à jour concurrente à protéger. **Perspective** : migration possible sans changer de moteur |
| Appariement probabiliste | moteur propre sur RapidFuzz, poids fixés | Splink [B15] | Fellegi-Sunter complet, poids estimés par EM, exécution Spark | jusqu'à Splink 4.0.11 (novembre 2025) ; la 5.0 exige Python 3.10 | poids **validés par le métier** et stables d'une exécution à l'autre, plutôt qu'estimés ; version figée |
| | | *recordlinkage* (Python Record Linkage Toolkit) | indexation, comparaisons, classification (dont EM) prêtes à l'emploi | oui (0.16, juillet 2023) | limité à Pandas, sans exécution distribuée ; peu d'activité depuis 2023 |
| | | *dedupe* | apprentissage actif : l'outil choisit les paires douteuses et les fait étiqueter par un humain | oui (3.0.3, août 2024) | exige une campagne d'étiquetage par du personnel de l'établissement ; poids appris, moins lisibles |
| Appariement par apprentissage | aucun | Ditto [B21], LLM [B22] | meilleure qualité mesurée sur les jeux de référence | non (modèles de langage, mêmes limites que `sentence_transformers`) | exige des données étiquetées et un GPU, ou l'envoi des identités à un service externe, contraire à l'hébergement interne |

Deux constats se dégagent. D'abord, la brique Big Data n'est pas imposée par le volume de
démonstration, mais par le sujet et par le volume visé ; le tableau le dit, et désigne DuckDB ou
Polars comme alternatives crédibles si ce volume se révèle faible. Ensuite, l'alternative la plus
sérieuse au moteur d'appariement est **Splink**. Le choix d'un moteur propre ne repose pas sur une
supériorité technique, mais sur une exigence du cahier des charges : des poids lisibles, fixés et
modifiables par le métier. Les options sont notées sur des critères pondérés au § 7.1.

## 2.3 Tableau comparatif et synthèse

Les sept critères du § 2.1.9 sont appliqués à chaque solution : « oui » signifie capacité
annoncée par la documentation, « partiel » capacité partielle, « non » capacité absente. Il s'agit
d'une **lecture documentaire, sans mesure**.

**Tableau 10 — Comparaison des solutions sur les sept critères.**

| Critère | EMPI | Talend MDM | Azure HDS | HAPI FHIR | OpenCR | Splink | Atlas | Solution du stage |
|---|:---:|:---:|:---:|:---:|:---:|:---:|:---:|:---:|
| **E1** Hébergement interne | partiel | oui | non | oui | oui | oui | oui | **oui, testé** |
| **E2** Exploitable dans l'environnement du stage | non | non | non | partiel | partiel | partiel | partiel | **oui, testé** |
| **Q1** Déduplication explicable | oui | oui | non | non | oui | oui | non | **oui, testé** |
| **Q2** Interopérabilité FHIR | partiel | non | oui | oui | oui | non | non | **oui, testé** |
| **Q3** Gouvernance rôle + consentement + audit | partiel | partiel | partiel | partiel | non | non | partiel | **oui, conçu** |
| **Q4** Montée en charge (stockage et calcul répartis) | partiel | oui | oui | non | partiel | oui | oui | **partiel, architecturé** |
| **Q5** Coût et indépendance | non | non | non | oui | oui | oui | oui | **oui** (dépendance reportée sur la maintenance, § 2.4) |

**Lecture.** Les critères éliminatoires écartent d'emblée EMPI, Talend et Azure : le premier
repose sur un référentiel externe et une licence, le deuxième n'a plus d'édition gratuite, le
troisième est un service cloud. Parmi les solutions libres restantes, **aucune ne couvre à la fois
l'identité, la gouvernance et le lac de données**. OpenCR est la plus proche sur l'identité, mais
n'offre ni lac ni consentement par finalité. Splink est la plus forte sur l'algorithme, mais ne
fournit que cet algorithme. HAPI FHIR et Atlas ne traitent qu'une partie du problème. Le
cahier des charges fixe en outre un délai de **4 mois** et un environnement **entièrement
interne** (cahier des charges, § 1 et § 3).

Deux précautions de lecture. D'abord, la colonne du projet n'est **pas soumise au même régime de
preuve** que les autres : les produits sont jugés sur des capacités *annoncées*, alors que la
solution du stage est notée « oui, testé » lorsqu'une mesure existe et « oui, conçu » lorsqu'elle
n'existe pas encore. C'est le cas de la ligne gouvernance, vérifiée mécaniquement par la suite de tests
(§ 8.4), mais dont les données PostgreSQL n'étaient pas peuplées au moment de l'exécution
(chapitre 8). De même, la montée en charge est **architecturée** et reproductible, mais n'a été
démontrée que sur 212 523 fiches synthétiques au plus. Ensuite, « partiel » signifie « partiel selon la
documentation » : il signale une capacité réelle mais incomplète dans le contexte du stage, et non
un doute sur l'existence de la fonction. En gouvernance, le « partiel » de HAPI FHIR signale un cadre à
programmer, pas une politique prête à l'emploi. Pour HAPI FHIR, OpenCR et Atlas, le « partiel » en E2 traduit
le poids de services Java ou Node.js supplémentaires sur une VM déjà chargée ; pour Splink, une
version figée par Python 3.8.

## 2.4 Pertinence entre le projet et l'état de l'art

**Décision.** Le projet ne réinvente pas les concepts. Il **réutilise les standards et les
algorithmes de l'existant** et n'écrit que la chaîne d'exécution et de gouvernance, qu'aucune
solution ne fournit dans le contexte imposé.

**Tableau 11 — Ce que le projet reprend de l'état de l'art.**

| Élément repris de l'existant | Provenance | Implémentation retenue |
|---|---|---|
| Décision *match / non-match* par somme de poids | Fellegi-Sunter [B2] | score pondéré et seuil fixés par le métier (§ 7.2.3) |
| Service de correspondance par score | FHIR `$match` [B5] | même philosophie, sans serveur FHIR (§ 7.2.3) |
| Interopérabilité par schéma pivot | FHIR [B5] | 4 ressources `Patient / Encounter / Condition / Observation` |
| Consentement par finalité, refus par défaut | FHIR Consent [B26], loi 2014-038 art. 14 et 18 [B24] | une décision par finalité, contrôlée à chaque accès (§ 7.2.3) |
| Stockage en zones de qualité croissante | Medallion [B9] | RAW / SILVER / GOLD sur HDFS et Hive |
| Rapprochement multi-sources | MPI, identity map, registre de clients [B13], [B29] | patient maître et table de correspondance en PostgreSQL |
| Gouvernance et traçabilité | catalogue de métadonnées [B18] | **l'inverse** : le contrôle est exercé *à l'exécution* (rôles, consentement, audit), pas seulement sur les métadonnées |

Cinq arbitrages structurent le positionnement du projet. **RapidFuzz** plutôt qu'un modèle de
langage : la bibliothèque `sentence_transformers` plantait sous Python 3.8, et un modèle appris
exigerait des données étiquetées. Un **MPI local avec
pivot FHIR** plutôt qu'un MPI commercial ou un registre complet comme OpenCR, trop lourds pour
l'environnement du stage. Un **score pondéré à seuil unique** plutôt que des poids estimés par EM,
pour que la décision reste lisible par un gestionnaire de données. Une montée en complexité **par
paliers** (MVP, puis Spark, puis Big Data) plutôt qu'un Big Data direct, pour introduire chaque
technologie par un besoin. Enfin, une **parité Pandas = Spark vérifiée** plutôt que deux logiques
divergentes, pour montrer que le passage à l'échelle ne change pas le résultat. L'inventaire
complet des arbitrages, avec pour chacun la preuve et le risque résiduel assumé, est donné dans la
conclusion générale.

Quatre écarts à l'existant sont assumés, justifiés par le besoin et non par la commodité :

- **Pas d'estimation EM** (à la différence de Splink) : les poids restent **fixés, lisibles et
  modifiables** par un gestionnaire de données, condition posée par l'exigence « jamais fusionner
  sans logique explicable ».
- **Pas de référentiel externe** (à la différence d'EMPI) : aucune donnée de tiers n'entre dans
  la plateforme, conformément à l'hébergement interne.
- **Pas de service géré dans le cloud** (à la différence d'Azure) : le lac de données est interne
  à la VM, ce qui évite la question du transfert à l'étranger (art. 20 de la loi 2014-038).
- **Pas de format de table transactionnel** (à la différence du *lakehouse*) : le rejeu complet
  suffit tant qu'aucune écriture concurrente n'existe ; Delta Lake reste une évolution compatible.

**Le risque déplacé : la maintenance.** Construire plutôt qu'acheter supprime la licence et la
dépendance à un éditeur ; cela ne supprime pas toute dépendance. Le risque se déplace vers la
**maintenabilité** du code écrit, qui devra être repris par l'équipe de MMT. Il a été réduit en
rendant les décisions paramétrables plutôt qu'écrites dans la logique : poids, seuil et stratégie
de blocking sont déclarés dans un seul fichier de configuration, lu par toutes les étapes
(§ 7.2.3). Une évolution du comportement se fait donc par **une** modification de configuration.
Cette centralisation a un contrepoids assumé : le même fichier alimente l'évaluation, si bien que
modifier un poids **invalide les métriques publiées** tant que l'évaluation n'a pas été rejouée
(chapitre 8).

> **Limite de l'étude.** Les produits et bibliothèques cités sont décrits **d'après leur
> documentation** et n'ont **pas été installés ni exécutés** : la grille compare des capacités
> annoncées, non des performances mesurées. Une évaluation comparative réelle, par exemple de
> Splink et du moteur du projet sur la même vérité terrain, demanderait un banc d'essai hors du
> périmètre du stage ; c'est la première perspective de cette étude.

## Conclusion et transition

L'état de l'art établit le vocabulaire et les références du mémoire : l'Entity Resolution fondée
sur Fellegi-Sunter [B2] et ses évolutions apprises [B15], [B21], [B22] ; les similarités de
RapidFuzz [B4] ; le MPI et FHIR, y compris pour le consentement [B5], [B26] ; le cadre juridique
malgache [B24], appuyé sur la doctrine européenne [B10] ; le lac Medallion [B9] porté par HDFS,
Hive et Spark. Le marché, comparé sur sept critères, ne les couvre jamais tous à la fois dans les
contraintes du stage. Les produits les plus complets imposent une licence, un abonnement ou un
hébergement externe, et donc une dépendance durable à un éditeur. La décision qui en découle est
une **chaîne sur mesure, adossée aux standards**, plutôt qu'un produit. Le chapitre 3 examine
maintenant **l'existant propre à MMT** (les systèmes de l'établissement, vus par l'utilisateur et
par le développeur), puis la solution envisagée.
