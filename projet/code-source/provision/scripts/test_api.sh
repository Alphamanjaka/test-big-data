#!/bin/bash
# test_api.sh — Lancer les tests de l'API Flask
# Usage: bash provision/scripts/test_api.sh

echo "================================================="
echo "  Lancement des tests API Flask"
echo "================================================="
echo ""
echo "Prérequis : l'API Flask doit tourner sur localhost:5000"
echo "  cd ~/datalake-final && python -m provision.api.hive_api &"
echo ""

cd ~/datalake-final
source ~/api-venv/bin/activate
python -m provision.api.test_api
