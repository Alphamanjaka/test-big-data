# Budget du projet

> Source du § 4.4 du mémoire (`chapters/04-demarche-projet.md`). Toute modification se fait
> dans les deux fichiers.

## Hypothèses

- **Durée** : 4 mois, du 6 juillet à fin octobre 2026 (durée du stage).
- **Périmètre** : prototype reproductible sur la VM de développement ; la plateforme **n'est pas
  déployée** chez le commanditaire, donc aucun coût de serveur de production, d'hébergement ni
  d'exploitation.
- **Coûts humains** : **hypothèses de travail** construites sur l'ordre de grandeur des rapports
  de référence, à remplacer par les chiffres réels du commanditaire avant diffusion. Le stage
  n'a pas été rémunéré.
- **Coûts matériels et logiciels** : **réels** — matériel déjà acquis, logiciels libres.

## 1. Coûts humains

| Poste | Base de calcul | Coût mensuel (Ar) | Coût sur 4 mois (Ar) |
|---|---|---:|---:|
| Développeur (stagiaire) | 1 ETP | 1 000 000 | 4 000 000 |
| Encadrement professionnel et pédagogique | 2 × 0,1 ETP | 150 000 | 600 000 |
| **Sous-total** | | **1 150 000** | **4 600 000** |

## 2. Coûts matériels et logiciels

| Poste | Détail | Coût (Ar) |
|---|---|---:|
| Poste de travail | déjà acquis | 0 |
| Machine virtuelle | fournie par le commanditaire, sur le poste existant | 0 |
| Serveur de production | non applicable : plateforme non déployée | 0 |
| Connexion Internet | déjà acquise | 0 |
| Logiciels | Hadoop, Hive, Spark, PostgreSQL, FastAPI, Flask, Next.js, Pandas, PySpark, RapidFuzz, pytest, Vagrant, VirtualBox, Git — open source | 0 |
| Solutions commerciales comparées | EMPI, Talend MDM, Azure HDS — étudiées sur documentation, non acquises | 0 |
| **Sous-total** | | **0** |

## 3. Coût total

| Catégorie | Coût sur 4 mois (Ar) |
|---|---:|
| Coûts humains (hypothèses) | 4 600 000 |
| Coûts matériels et logiciels (réels) | 0 |
| **Total** | **4 600 000** |

Un déploiement en production ajouterait des postes non chiffrés ici : serveur, sauvegarde,
exploitation.
