#!/bin/bash

# Pipeline ELT : RAW -> SILVER (FHIR) -> GOLD
# Les scripts utilisent des imports relatifs : exécution en module (-m)
# depuis la racine du projet.
# Chaque étape s'arrête en cas d'erreur (pas de "succès" mensonger).

# PROJECT_ROOT : résolu depuis la position de ce script si non défini
SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
PROJECT_ROOT="${PROJECT_ROOT:-$(cd "$SCRIPT_DIR/../.." && pwd)}"
LOG_DIR="$PROJECT_ROOT/provision/logs"
mkdir -p "$LOG_DIR"
LOG_FILE="$LOG_DIR/elt.log"
cd "$PROJECT_ROOT" || exit 1

DATE=$(date '+%Y-%m-%d %H:%M:%S')

echo "============================================================" >> "$LOG_FILE"
echo "🚀 Lancement du pipeline ELT à $DATE" >> "$LOG_FILE"
echo "============================================================" >> "$LOG_FILE"

run_step() {
    local desc="$1"; shift
    echo "[STEP] $desc" >> "$LOG_FILE"
    "$@" >> "$LOG_FILE" 2>&1
    local rc=$?
    if [ $rc -ne 0 ]; then
        END_DATE=$(date '+%Y-%m-%d %H:%M:%S')
        echo "❌ ÉCHEC (code $rc) à l'étape : $desc — pipeline arrêté à $END_DATE" >> "$LOG_FILE"
        echo "------------------------------------------------------------" >> "$LOG_FILE"
        echo ""
        echo "❌ Pipeline interrompu ($rc) : $desc — voir $LOG_FILE"
        exit $rc
    fi
}

run_step "[0/5] 📦 Garantie des données du générateur (seed 42)" \
    bash "$SCRIPT_DIR/ensure_generator_data.sh"

run_step "[1/5] 🧩 Extraction des données brutes (RAW)" \
    "$HOME/api-venv/bin/python" -m provision.scripts.ELT.gen_extract_raw

run_step "[2/5] Carte de correspondance tables/colonnes -> FHIR" \
    "$HOME/api-venv/bin/python" -m provision.scripts.ELT.gen_fhir_mapping

run_step "[3/5] 🧬 Transformation SILVER (FHIR harmonisé)" \
    "$HOME/api-venv/bin/python" -m provision.scripts.ELT.create_silver

run_step "[4/5] 📊 Création de la couche GOLD (analytique)" \
    "$HOME/api-venv/bin/python" -m provision.scripts.ELT.create_gold

END_DATE=$(date '+%Y-%m-%d %H:%M:%S')
echo "✅ Pipeline ELT FHIR terminé avec succès à $END_DATE" >> "$LOG_FILE"
echo "------------------------------------------------------------" >> "$LOG_FILE"
echo ""
echo "✅ Pipeline ELT complet : RAW -> SILVER -> GOLD OK"
