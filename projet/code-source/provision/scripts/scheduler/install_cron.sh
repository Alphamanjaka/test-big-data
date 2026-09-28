#!/bin/bash
# =====================================================================
# install_cron.sh — pose l'entrée cron de la planification du pipeline.
#
# Une entrée toutes les minutes vérifie les échéances de schedule.yaml :
#   * * * * * cd $PROJECT_ROOT && $PYTHON -m provision.scripts.scheduler.scheduler --check
# Le déclenchement réel (fréquence/heure) est géré par le planificateur ;
# le cron ne fait qu'une vérification légère chaque minute.
#
# Usage : bash provision/scripts/scheduler/install_cron.sh
# → À exécuter UNE SEULE FOIS sur la VM, après installation du venv.
# =====================================================================
set -e

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
PROJECT_ROOT="${PROJECT_ROOT:-$(cd "$SCRIPT_DIR/../../.." && pwd)}"
LOG_DIR="$PROJECT_ROOT/provision/logs"
mkdir -p "$LOG_DIR"

PYTHON="$HOME/api-venv/bin/python"
if [ ! -x "$PYTHON" ]; then
    PYTHON="$(command -v python3 || command -v python || true)"
fi
if [ -z "$PYTHON" ] || [ ! -x "$PYTHON" ]; then
    echo "python introuvable (cherché $HOME/api-venv/bin/python puis PATH)" >&2
    exit 2
fi

LINE="* * * * * cd $PROJECT_ROOT && $PYTHON -m provision.scripts.scheduler.scheduler --check >> $LOG_DIR/scheduler.log 2>&1"

# Remplace une éventuelle entrée existante du même planificateur.
(crontab -l 2>/dev/null | grep -v 'provision.scripts.scheduler.scheduler' || true) | { cat; echo "$LINE"; } | crontab -

echo "Cron installé pour $USER :"
echo "  $LINE"
echo "Personnalisez la fréquence/heure dans $PROJECT_ROOT/provision/config/schedule.yaml"