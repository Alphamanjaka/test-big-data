#!/bin/bash
# capture_mavis_schema.sh
# Extrait le schéma (colonnes + types) des 11 tables Hive RAW de la source MAVIS
# et produit provision/metadata/mavis_schema.json au format du rebuild_mmt_db.py.
#
# Usage (dans la VM, depuis /home/vagrant/datalake-final) :
#   bash provision/scripts/capture_mavis_schema.sh

set -e
source /etc/profile.d/bigdata.sh

PROJECT_ROOT="/home/vagrant/datalake-final"
OUT="$PROJECT_ROOT/provision/metadata/mavis_schema.json"

TABLES="hms_patient res_partner hms_physician hms_diseases acs_ethnicity ir_attachment hr_employee res_users patient_death_register product_product account_move"

mkdir -p "$(dirname "$OUT")"

: > "$OUT"
echo "[" > "$OUT"

first=1
for t in $TABLES; do
    echo "=== $t ===" >&2
    desc=$(beeline -u jdbc:hive2://localhost:10000 -n vagrant -e "DESCRIBE mavis.$t;" 2>/dev/null \
        | awk -F'|' '{gsub(/^[ \t]+|[ \t]+$/, "", $2); gsub(/^[ \t]+|[ \t]+$/, "", $3); if ($2 != "" && $3 != "") print $2 ":" $3}')
    # Exclure les pseudo-colonnes Hive (partition/table params ont un type "from deserializer" etc.)
    # On ne garde que les couples col:type simples (type sans espace ni "from deserializer").

    if [ $first -eq 0 ]; then
        echo "," >> "$OUT"
    fi
    echo "  {" >> "$OUT"
    echo "    \"table_name\": \"$t\"," >> "$OUT"
    echo "    \"columns\": [" >> "$OUT"

    n=0
    while IFS= read -r line; do
        col="${line%%:*}"
        typ="${line#*:}"
        # Garde uniquement les types Hive simples
        case "$typ" in
            string|int|bigint|smallint|tinyint|boolean|double|float|date|timestamp|decimal*|varchar*|char*)
                if [ $n -gt 0 ]; then
                    echo "," >> "$OUT"
                fi
                echo "      {\"name\": \"$col\", \"type\": \"$typ\"}" >> "$OUT"
                n=$((n+1))
                ;;
        esac
    done <<< "$desc"

    echo "" >> "$OUT"
    echo "    ]" >> "$OUT"
    echo "  }" >> "$OUT"
    first=0
done

echo "" >> "$OUT"
echo "]" >> "$OUT"

echo "Schéma MAVIS écrit dans $OUT" >&2
cat "$OUT" >&2
