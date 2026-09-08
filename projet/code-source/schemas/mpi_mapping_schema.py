#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Définition du schéma PostgreSQL pour la table Master Patient Index (MPI).

Cette table est le cœur de l'identité patient unique et doit enregistrer toutes les 
sources d'identification connues pour un même individu, avec traçabilité des liens.
Elle remplace/complète simplement la notion de clés étrangères simples dans les scripts sources.
"""
import json

# Définition du schéma (à être intégré aux autres schémas et exécuté au début de l'orchestration)
MPI_TABLE_SCHEMA = {
    "mpi_mapping": [
        {"name": "id", "type": "bigint"}, # Clé primaire globale MPI
        {"name": "source_system", "type": "text", "comment": "Système source (MMT, MAVIS, CLINIQUE)"},
        {"name": "source_record_id", "type": "text", "comment": "L'identifiant de l'enregistrement dans la source"},
        {"name": "source_identifier", "type": "text", "comment": "Identifiant secondaire (e.g., numéro national, nom complet)"},
        {"name": "master_patient_id", "type": "bigint", "comment": "L'ID consolidé et unique du patient au sein de l'hôpital."},
        {"name": "created_at", "type": "timestamp without time zone"},
    ]
}

def generate_mpi_schema(cur):
    """Crée la table MPI si elle n'existe pas."""
    print("--- Création du schéma Master Patient Index (MPI) ---")
    
    # Construction de la définition CREATE TABLE
    defs = ", ".join(f'"{c["name"]}" {c["type"]}' for c in MPI_TABLE_SCHEMA["mpi_mapping"])
    create_table_sql = f'CREATE TABLE IF NOT EXISTS "mpi_mapping" ({defs}, PRIMARY KEY ("id"));'
    
    try:
        cur.execute(create_table_sql)
        print("✅ Table mpi_mapping prête.")
    except Exception as e:
        print(f"❌ ERREUR CRITIQUE lors de la création du schéma MPI : {e}")

# Note: Ce fichier est un module de support et ne doit pas être exécuté directement.
