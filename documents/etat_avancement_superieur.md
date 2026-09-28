# État d'avancement du projet — synthèse pour le supérieur

Source : cahier des charges, suivi d'avancement (`ai/dev/suivi_avancement.md`) et journal des
sessions (`ai/dev/logs.md`). Données d'état : 28/09/2026.

---

## Approche générale

On résout d'abord le problème métier avec un prototype simple (MVP), puis on ajoute la technologie
Big Data uniquement quand le besoin de passage à l'échelle le justifie. Chaque étape est validée par
des tests avant d'aller plus loin.

---

## 1. Les 6 objectifs du cahier des charges — où en est-on ?

| Objectif attendu | État | Ce que c'est concrètement |
|---|---|---|
| Centraliser les données médicales | **Réalisé** | Le pipeline complet fonctionne sur les vraies données des 3 systèmes de MMT (MAVIS, MMT_DB, CLINIQUE). 4 étapes passent toutes au vert en environnement VM. |
| Nettoyer et standardiser | **Réalisé** | Les formats divergents (genre, dates, numéro CIN, orthographes) sont harmonisés vers un modèle unique. |
| Dédupliquer (éviter qu'un même patient soit enregistré plusieurs fois) | **Réalisé** | 214 fiches entrées → **145 dossiers patients uniques**, **69 doublons** détectés (taux 32 %). Chaque rapprochement est **documenté** (pourquoi on juge que c'est le même patient). |
| Gouverner les accès (consentement + traçabilité) | **Réalisé côté mécanique**, une vérification réelle en base reste à faire | Consentement du patient par finalité (ex. consultation / recherche / statistiques), refus bloquant, historique de qui a accédé à quoi, mots de passe jamais stockés en clair. |
| Visualiser (optionnel) | **Réalisé, reste optionnel** | Tableau de bord recentré sur l'essentiel : synthèse, doublons, gouvernance. |
| Évaluer la qualité de la déduplication | **Réalisé** | Test sur un jeu de données de référence : **aucun faux rapprochement** (tout ce qui est fusionné l'est à juste titre) ; sur le cas le plus difficile (volontairement dégradé), 42 % des doublons sont retrouvés — chiffre connu et assumé. |

## 2. Fiabilité (tests)

- Moteur de déduplication + consentement + API : **54 tests, tous passent**.
- API de gouvernance sur données réelles : **3 sur 3**.
- Générateur de données de test : **44 sur 44**.
- Un même patient est retrouvé à l'identique quelle que soit la technologie utilisée (simple ou
  distribuée) → résultats déterministes, garantie de reproductibilité.

## 3. Les livrables attendus

| Livrable | État |
|---|---|
| Code source complet en un seul dépôt | ✅ Fait |
| Pipeline Big Data | ✅ Fait et exécuté |
| Moteur de déduplication + évaluation | ✅ Fait |
| Base centrale (patients, consentement, audit) | ✅ Scripts et schéma prêts ; **exécution sur une base réelle à faire** (la VM n'était pas disponible) |
| API données + API gouvernance | ✅ Fait et testées |
| Documentation technique + manuel conceptuel | ✅ Fait |
| Tableau de bord (optionnel) | ✅ Fait |
| Rapport de stage + slides de soutenance | ✅ Fait (rapport, slides, script d'oral, diaporama 21 slides) ; relecture humaine restante |

## 4. Mémoire de soutenance

- 9 chapitres rédigés + glossaire expliquant les termes techniques en français courant.
- Document Word finalisé (A4, sommaire, figures, 37 tableaux).
- Soutenance préparée : exposé de 20 min minuté, démonstration **filmée à l'avance** (pour ne pas
  dépendre de la machine le jour J — il reste à la filmer).

## 5. Points d'attention restants (transparence)

1. **Vérification finale en base** : le dispositif de consentement et d'audit est prouvé par les
   tests, mais pas encore rejoué sur une base fraîchement créée.
2. **Démo vidéo à filmer** (3 min 30) et relecture humaine du document Word et du diaporama.
3. **Cas difficiles** : sur des patients quasi identiques (homophones), le rappel est faible — cas
   exclu du générateur de test, documenté comme limite.
4. **Sécurité** : un détail documenté (hachage des clés API sans « sel ») est une dette à corriger
   à terme ; les identifiants du serveur distant restent à renouveler côté MMT.

---

## Verdict global

Le cœur du projet (centraliser, nettoyer, dédupliquer, gouverner, évaluer) est **terminé et prouvé
par des tests** (54/54, API 3/3, zéro accès non autorisé). Il reste de la **finalisation** (base
réelle à rejouer, vidéo de démo, relectures) et des **dettes assumées**, toutes documentées.

## Ordre de priorité des actions restantes

1. Rejouer la base centrale (schéma + données de démonstration) sur l'environnement réel.
2. Filmer la démonstration vidéo de la soutenance (3 min 30).
3. Relecture humaine : document Word, diaporama, rapport de stage.
4. Dettés documentées (sécurité, enrichissement du croisement des données) — planifiables après la
   soutenance.