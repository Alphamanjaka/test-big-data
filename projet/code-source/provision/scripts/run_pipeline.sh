#!/bin/bash

# Pipeline ELT : RAW -> SILVER (FHIR) -> GOLD
# Les scripts utilisent des imports relatifs : exécution en module (-m)
# depuis la racine du projet.
# Chaque étape s'arrête en cas d'erreur (pas de "succès" mensonger).
#
# Usage :
#   ./run_pipeline.sh                     # rechargement complet (historique)
#   ./run_pipeline.sh --resume            # reprend : run échoué -> étapes
#                                         # restantes, sinon nouveau run
#                                         # incrémental (sources inchangées
#                                         # non ré-extraites, cf. watermark)
#   ./run_pipeline.sh --full              # purge + ré-extraction de tout
#   ./run_pipeline.sh --since YYYY-MM-DD  # re-extraction forcée à partir
#                                         # d'une date (INJEST_SINCE)
#   ./run_pipeline.sh --from <étape>      # repart d'une étape nommée
#   ./run_pipeline.sh --dry-run           # affiche le plan sans rien exécuter
#
# L'état de chaque run est persisté dans provision/metadata/pipeline_state.json
# : après un échec, `--resume` repart de la première étape non terminée au lieu
# de tout rejouer. Le run en cours est signalé par status=running : le
# planificateur ne lance pas de doublon tant qu'un run n'est pas fini. Un run
# `running` dont le processus a disparu (arrêt brutal) est orphelin : il est
# traité comme un échec, donc repris par `--resume`.
# Les compteurs de chaque run sont conservés en base (table pipeline_run).

set -u

# PROJECT_ROOT : résolu depuis la position de ce script si non défini
SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
PROJECT_ROOT="${PROJECT_ROOT:-$(cd "$SCRIPT_DIR/../.." && pwd)}"
LOG_DIR="$PROJECT_ROOT/provision/logs"
METADATA_DIR="$PROJECT_ROOT/provision/metadata"
mkdir -p "$LOG_DIR" "$METADATA_DIR"
LOG_FILE="$LOG_DIR/elt.log"
STATE_FILE="$METADATA_DIR/pipeline_state.json"
cd "$PROJECT_ROOT" || exit 1

PYTHON="${PIPELINE_PYTHON:-$HOME/api-venv/bin/python}"
if [ ! -x "$PYTHON" ]; then
    PYTHON="$(command -v python3 || command -v python || true)"
fi
if [ -z "$PYTHON" ] || [ ! -x "$PYTHON" ]; then
    echo "python introuvable (cherché \$HOME/api-venv/bin/python puis PATH)" >&2
    exit 2
fi

STEPS=(
    "ensure_generator_data"
    "gen_extract_raw"
    "gen_fhir_mapping"
    "create_silver"
    "create_gold"
)

state_cli() {
    "$PYTHON" -m provision.scripts.utils.pipeline_state "$@"
}

# Historique chiffré du run (lignes par source, patients maîtres, GOLD) :
# enregistré dans PostgreSQL (pipeline_run) si DATABASE_URL est définie,
# sinon conservé en attente dans provision/metadata/run_metrics.json.
# Ne fait jamais échouer le pipeline.
record_run_history() {
    "$PYTHON" -m provision.scripts.utils.run_metrics flush >> "$LOG_FILE" 2>&1 || true
}

# ---------------------------------------------------------------------
# Arguments
# ---------------------------------------------------------------------
MODE="full"
FROM_STEP=""
SINCE=""
DRY_RUN=0

while [ $# -gt 0 ]; do
    case "$1" in
        --resume) MODE="resume" ;;
        --full)   MODE="full" ;;
        --since)  MODE="since"; SINCE="${2:-}"; shift ;;
        --from)   MODE="from"; FROM_STEP="${2:-}"; shift ;;
        --dry-run) DRY_RUN=1 ;;
        *)
            echo "Argument inconnu : $1" >&2
            echo "Usage : ./run_pipeline.sh [--resume|--full|--since DATE|--from ÉTAPE] [--dry-run]" >&2
            exit 2 ;;
    esac
    shift
done

# ---------------------------------------------------------------------
# Index de début : 0 (full/nouveau run), étape nommée (from), ou première
# étape non terminée (resume après échec).
# ---------------------------------------------------------------------
START_INDEX=0
step_index() {
    local name="$1" i
    for i in "${!STEPS[@]}"; do
        if [ "${STEPS[$i]}" = "$name" ]; then
            echo "$i"
            return 0
        fi
    done
    echo "Étape inconnue : $name" >&2
    echo "Étapes possibles : ${STEPS[*]}" >&2
    return 1
}

if [ "$MODE" = "from" ]; then
    IDX=$(step_index "$FROM_STEP") || exit 2
    START_INDEX="$IDX"
elif [ "$MODE" = "resume" ]; then
    # Statut effectif : un run resté `running` dont le processus a disparu
    # (arrêt brutal de la VM) compte comme un échec, donc comme reprenable.
    STATUS=$(state_cli effective_status 2>/dev/null || echo "")
    if [ "$STATUS" = "failed" ]; then
        RESUME_STEP=$(state_cli resume_start 2>/dev/null || echo "")
        if [ -n "$RESUME_STEP" ]; then
            START_INDEX=$(step_index "$RESUME_STEP") || exit 2
        fi
    fi
fi

# ---------------------------------------------------------------------
# Plan
# ---------------------------------------------------------------------
RUN_ID="$(date '+%Y%m%dT%H%M%S')"
echo "Pipeline ELT — mode: $MODE, run_id: $RUN_ID"
echo "Étapes prévues (à partir de l'index $START_INDEX) : ${STEPS[*]:$START_INDEX}"
if [ "$DRY_RUN" = "1" ]; then
    echo "Mode dry-run — aucune exécution, aucun fichier d'état écrit."
    echo "Env transmis : PIPELINE_MODE=$MODE INGEST_SINCE=${SINCE:-} PIPELINE_RUN_ID=$RUN_ID"
    exit 0
fi

# ---------------------------------------------------------------------
# Lancement
# ---------------------------------------------------------------------
export PIPELINE_MODE="$MODE"
export INGEST_SINCE="${SINCE:-}"
export PIPELINE_RUN_ID="$RUN_ID"

DATE=$(date '+%Y-%m-%d %H:%M:%S')

echo "============================================================" >> "$LOG_FILE"
echo "🚀 Lancement du pipeline ELT à $DATE (run $RUN_ID, mode $MODE)" >> "$LOG_FILE"
echo "============================================================" >> "$LOG_FILE"

# Trace d'un run précédent orphelin avant de le remplacer (message seulement).
state_cli reconcile >> "$LOG_FILE" 2>&1 || true

# $$ : PID de ce shell, qui vit pendant tout le run (détection des runs orphelins).
state_cli begin --mode "$MODE" \
    ${FROM_STEP:+--from "$FROM_STEP"} \
    ${SINCE:+--since "$SINCE"} \
    --start-at "$START_INDEX" \
    --run-id "$RUN_ID" \
    --pid "$$" >/dev/null

run_step_cmd() {
    case "$1" in
        ensure_generator_data) bash "$SCRIPT_DIR/ensure_generator_data.sh" ;;
        gen_extract_raw)       "$PYTHON" -m provision.scripts.ELT.gen_extract_raw ;;
        gen_fhir_mapping)      "$PYTHON" -m provision.scripts.ELT.gen_fhir_mapping ;;
        create_silver)         "$PYTHON" -m provision.scripts.ELT.create_silver ;;
        create_gold)           "$PYTHON" -m provision.scripts.ELT.create_gold ;;
    esac
}

RC=0
for ((i=START_INDEX; i<${#STEPS[@]}; i++)); do
    STEP="${STEPS[$i]}"
    echo "[STEP $((i+1))/${#STEPS[@]}] $STEP" >> "$LOG_FILE"
    state_cli step started "$STEP" >/dev/null
    run_step_cmd "$STEP" >> "$LOG_FILE" 2>&1
    RC=$?
    if [ $RC -ne 0 ]; then
        END_DATE=$(date '+%Y-%m-%d %H:%M:%S')
        echo "❌ ÉCHEC (code $RC) à l'étape : $STEP — pipeline arrêté à $END_DATE" >> "$LOG_FILE"
        echo "------------------------------------------------------------" >> "$LOG_FILE"
        state_cli step failed "$STEP" "code $RC" >/dev/null
        state_cli finish failed >/dev/null
        record_run_history
        echo "" >&2
        echo "❌ Pipeline interrompu ($RC) : $STEP — voir $LOG_FILE" >&2
        echo "  Reprenez avec : bash $SCRIPT_DIR/run_pipeline.sh --resume" >&2
        exit $RC
    fi
    state_cli step ok "$STEP" >/dev/null
done

state_cli finish ok >/dev/null
record_run_history
END_DATE=$(date '+%Y-%m-%d %H:%M:%S')
echo "✅ Pipeline ELT FHIR terminé avec succès à $END_DATE" >> "$LOG_FILE"
echo "------------------------------------------------------------" >> "$LOG_FILE"
echo ""
echo "✅ Pipeline ELT complet : RAW -> SILVER -> GOLD OK"