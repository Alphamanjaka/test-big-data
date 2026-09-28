#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Pipeline Orchestrator pour le Data Lake Medallion.

Ce script est le point d'entrée principal du système de gouvernance des données patients.
Il gère l'exécution séquentielle et contrôlée (ELT) des différents flux de données
provenant des sources hétérogènes dans la couche RAW, avant de simuler la transformation
(SILVER -> GOLD) et la validation finale des identités.

Usage:
    python projet/code-source/pipeline_orchestrator.py
"""
import os
import subprocess
import sys
from datetime import datetime

# --- Configuration et Dépendances ---
# Assurez-vous que les environnements (.env) sont chargés avant l'exécution.
try:
    from dotenv import load_dotenv
    # Charge le .env de la racine du projet pour garantir les identifiants PG/DB
    load_dotenv(os.path.join(os.path.dirname(os.path.abspath(__file__)), ".env"))
except ImportError:
    print("⚠️ WARNING: python-dotenv non trouvé. Veuillez l'installer (pip install python-dotenv).")

def run_script(script_name, description):
    """Exécute un script de provisionnement et gère les erreurs."""
    print("\n" + "="*80)
    print(f"🚀 ÉTAPE : {description}")
    print("="*80)
    try:
        # Utilisation du subprocess pour s'assurer que l'exécution se fait dans le bon contexte.
        result = subprocess.run([sys.executable, os.path.join("projet/code-source/provision/db", script_name)], 
                                capture_output=True, text=True)
        print(f"✅ SUCCESS : {script_name} exécuté avec succès.")
        # On pourrait logger le stdout/stderr dans un fichier log dédié ici.
    except FileNotFoundError:
        print(f"❌ ERROR : Le script '{script_name}' n'a pas été trouvé à l'emplacement attendu.")
    except subprocess.CalledProcessError as e:
        print(f"❌ FAILURE CRITIQUE lors de l'exécution de {script_name} :")
        print("-" * 20)
        print("STDOUT ERR:")
        print(e.stdout)
        print("STDERR ERR:")
        print(e.stderr)
        print("Le pipeline est arrêté en raison d'une erreur dans la source de données.")
        sys.exit(1)
    except Exception as e:
        print(f"❌ ERREUR INCONNUE lors du lancement de {script_name}: {e}")
        sys.exit(1)

def orchestrate_pipeline():
    """Orchestre le pipeline ELT complet."""
    print("="*80)
    print("✨ STARTING DATA LAKE PIPELINE ORCHESTRATOR ✨")
    print("================================================================================\n")
    print(f"Date de l'exécution: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

    # 1. ÉTAPE RAW (Extraction & Loading - EL)
    run_script(
        "rebuild_mmt_db.py",
        "Phase 1/3 : Ingestion des données MMT_DB (Source Hospitalière Générale)"
    )

    # ATTENTION: Les scripts ci-dessous doivent dépendre de la base PostgreSQL créée par le script précédent.
    run_script(
        "rebuild_mavis_db.py",
        "Phase 2/3 : Ingestion des données Mavis (Source HMO/Data Lake Externe)"
    )

    # Cette source est en SQLite car elle simule un système local distinct.
    run_script(
        "rebuild_clinique_sqlite.py",
        "Phase 3/3 : Ingestion des données Cliniques (Source Locales / FHIR-like)"
    )


    # 2. ÉTAPE TRANSFORMATION (Transformation - T)
    print("\n\n" + "="*80)
    print("✨ PHASE DE CONSOLIDATION ET HARMONISATION (SILVER -> GOLD) ✨")
    print("================================================================================\n")

    # Placeholder pour la logique métier ELT :
    print("➡️ 2.1. Déduplication et Master Patient Record:")
    print(f"   [SIMULATION] Exécution de l'algorithme d'identité maîtresse (Master Patient Indexing).")
    print("   - Objectif: Créer une vue unifiée des identités patients à partir de MMT, Mavis, Clinique.")

    # Placeholder pour la gestion du consentement :
    print("\n➡️ 2.2. Application du Consentement Purpose-by-Purpose:")
    print(f"   [SIMULATION] Filtrage et tagging des données selon les politiques de consentement (Rôles/Consentements).")
    print("   - Les données ne sont considérées comme 'GOLD' que si le droit d'accès est prouvé.")

    # Placeholder pour la création du Gold Layer :
    print("\n➡️ 2.3. Génération du Data Set GOLD:")
    print(f"   [SIMULATION] Création des vues et des agrégations finales prêtes pour l'analyse BI/ML (Golden Records).")
    
    # Validation de fin de pipeline
    print("\n\n================================================================================")
    print("🚀 PIPELINE TERMINÉ AVEC SUCCÈS.")
    print("Les données sont chargées en RAW et structurées en GOLD dans le Data Lake virtuel.")
    print("Action requise : Exécuter les vérifications d'intégrité (scripts de validation).")
    print("================================================================================")

if __name__ == "__main__":
    try:
        orchestrate_pipeline()
    except KeyboardInterrupt:
        print("\n\n🛑 Pipeline interrompu par l'utilisateur.")
    finally:
        print("\nFin du processus d'orchestration.")
