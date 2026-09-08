# Consignes projet — DataLake Mavis

> Archive historique en lecture et référence. Ces consignes ne s'appliquent pas au développement
> consolidé, qui suit `AGENTS.md` et `ai/dev/` à la racine.

- Lire `.ai_context/00_index.md` au début de chaque session (puis `01` → `04` selon la tâche).
- Docs de référence : `PIPELINE.md` (pipeline ELT), `LOG.md` (historique/incidents), `CAHIER_DE_CHARGE.md` (périmètre), `SUIVI_AVANCEMENT.md` (état d'avancement).
- `.ai_context/`, `provision/metadata/` et `provision/config/data_sources.json` ne sont **PAS** commités (voir `.gitignore`). Fichier de config d'exemple : `provision/config/data_sources.example.json`.

## Méthode de travail (traçabilité)

1. **LOG.md après chaque activité** : toute session, fix, incident ou run ajoute une entrée datée dans `LOG.md` et met à jour la ligne « Dernière entrée : ».
2. **Structure d'une entrée LOG.md** :
   - `## JJ/MM/AAAA — <Titre>` ;
   - `**Contexte :**` pour situer l'action ;
   - tableau `| # | Action | Fichiers | Détail |` (fix/feature) ou liste à puces (run/incident) — incident au format `Incident N : cause → fix` ;
   - `**Vérifications :**` commandes + résultats concrets ;
   - `**Résultat :**` état final ; `**Reste à faire / Prochaine étape :**` si nécessaire.
3. **Étape MAJEURE** (jalon par rapport à `CAHIER_DE_CHARGE.md` / `CONCEPTION_GLOBALE.md`) : en plus de LOG.md, mettre à jour `SUIVI_AVANCEMENT.md` (barres %, tableau modules %/statut, fait/réste, « Jalons clés », « Dernière mise à jour ») **et** le(s) `MODULE_*.md` concerné(s).
4. **Seuil** : un simple run, reboot ou fix de robustesse → LOG.md uniquement.
