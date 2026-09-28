#!/bin/bash

# Étape 0 (optionnelle) du pipeline : garantit que les CSV du générateur
# synthétique existent. Si un fichier source manque, la source concernée
# est régénérée avec le seed fixe 42 (sortie déterministe).
# Variables d'environnement :
#   GENERATOR_PATIENTS : nombre de patients maîtres (défaut 500)

set -e

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
PROJECT_ROOT="${PROJECT_ROOT:-$(cd "$SCRIPT_DIR/../.." && pwd)}"
GENERATOR_DIR="$PROJECT_ROOT/evaluation/synthetic-patient-generator"
GENERATOR_PATIENTS="${GENERATOR_PATIENTS:-500}"

# Interpréteur : venv dédié > venv API > python3 système
if [ -x "$HOME/generator-venv/bin/python" ]; then
    PYTHON="$HOME/generator-venv/bin/python"
elif [ -x "$HOME/api-venv/bin/python" ]; then
    PYTHON="$HOME/api-venv/bin/python"
else
    PYTHON="$(command -v python3 || echo python)"
fi

# source -> fichiers requis
declare -A FILES
FILES[pharmacy]="patients.csv achats.csv"
FILES[consultation]="patients.csv consultations.csv"
FILES[imaging]="patients.csv examens.csv"

run_source() {
    local src="$1" seed=42
    echo "🔄 Régénération de la source '$src' (seed $seed, $GENERATOR_PATIENTS patients)"
    ( cd "$GENERATOR_DIR" && "$PYTHON" -m "generator.${src}_generator" \
        --patients "$GENERATOR_PATIENTS" --seed "$seed" )
}

cd "$PROJECT_ROOT"
for src in "${!FILES[@]}"; do
    dir="$GENERATOR_DIR/data/raw/$src"
    missing=""
    for f in ${FILES[$src]}; do
        if [ ! -f "$dir/$f" ]; then
            missing="$missing $f"
        fi
    done
    if [ -n "$missing" ]; then
        echo "⚠️  Source '$src' : fichiers manquants :$missing"
        run_source "$src"
    else
        echo "✓ Source '$src' : fichiers présents ($dir)"
    fi
done

echo "✅ Données du générateur : OK"