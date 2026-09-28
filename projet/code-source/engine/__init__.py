"""
Engine — moteur autonome de résolution d'identité patient.

Adapté du PoC test_bigdata (aujourd'hui dans projet/mvp/) pour être
autonome et compatible Python 3.8 (VM Big Data). Contenu :

- identity/  : modèle canonique + de-duplication exacte/probabiliste
               (Pandas pour l'explication, PySpark pour la montée en charge)
- governance/: consentement, audit, authentification par clés API (FastAPI)
- sql/       : schéma PostgreSQL cible (RAW, master, identity map, consent)
"""

from __future__ import annotations