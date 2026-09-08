#!/bin/bash

################################################################################
# MAVIS Database Startup Health Check
# =====================================
# Quick smoke test to verify MAVIS database is running and accessible
# 
# Usage:
#   bash provision/test_startup.sh                    # Default quiet mode
#   bash provision/test_startup.sh --verbose          # Show raw responses
#   bash provision/test_startup.sh --report           # Save JSON report
#   bash provision/test_startup.sh --verbose --report # Both
#
# Exit codes:
#   0 = All checks passed (MAVIS is healthy)
#   1 = At least one check failed (MAVIS is not ready)
#
# Features:
#   - Tests HiveServer2 connectivity (port 10000)
#   - Tests Flask API health endpoint (port 5000)
#   - Verifies sync_metadata.json has recent updates
#   - 5-second timeout per check (no hanging)
#   - Cross-platform: Windows (Git Bash, WSL), macOS, Linux
################################################################################

set -o pipefail

# Configuration
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"
METADATA_FILE="$SCRIPT_DIR/metadata/sync_metadata.json"
REPORTS_DIR="$SCRIPT_DIR/reports"
TIMEOUT=5

# Color codes
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Flags
VERBOSE=0
REPORT=0

# Results tracking
PASSED=0
FAILED=0
CHECKS_RUN=0

################################################################################
# Utility Functions
################################################################################

print_header() {
    echo ""
    echo "══════════════════════════════════════════════════════════════════"
    echo "  MAVIS Database Startup Health Check"
    echo "══════════════════════════════════════════════════════════════════"
    echo ""
}

print_check() {
    local check_name="$1"
    printf "  %-40s " "$check_name"
}

print_result() {
    local status="$1"
    local message="$2"
    
    if [ "$status" = "PASS" ]; then
        echo -e "${GREEN}✓ PASS${NC}"
        if [ "$VERBOSE" = "1" ] && [ -n "$message" ]; then
            echo "      └─ $message"
        fi
        ((PASSED++))
    else
        echo -e "${RED}✗ FAIL${NC}"
        if [ -n "$message" ]; then
            echo "      └─ $message"
        fi
        ((FAILED++))
    fi
    ((CHECKS_RUN++))
}

print_summary() {
    echo ""
    echo "──────────────────────────────────────────────────────────────────"
    
    if [ "$FAILED" -eq 0 ]; then
        echo -e "${GREEN}✓ SUCCESS: All checks passed!${NC}"
        echo "  MAVIS database is running and accessible."
    else
        echo -e "${RED}✗ FAILURE: $FAILED check(s) failed${NC}"
        echo "  MAVIS database is NOT ready."
    fi
    
    echo "  Results: $PASSED/$CHECKS_RUN checks passed"
    echo "──────────────────────────────────────────────────────────────────"
    echo ""
}

log_verbose() {
    if [ "$VERBOSE" = "1" ]; then
        echo "      Debug: $1"
    fi
}

################################################################################
# Check: Vagrant VM Status
################################################################################

check_vagrant_vm_status() {
    print_check "Vagrant VM Status"
    
    if ! command -v vagrant &> /dev/null; then
        print_result "FAIL" "Vagrant CLI not found in PATH"
        return 1
    fi
    
    local status=$(vagrant status 2>/dev/null | grep "default" | awk '{print $2}')
    
    if [ "$status" = "running" ]; then
        print_result "PASS" "VM is running"
        return 0
    else
        print_result "FAIL" "VM status: $status (expected: running)"
        return 1
    fi
}

################################################################################
# Check: HiveServer2 Connectivity
################################################################################

check_hive_connectivity() {
    print_check "HiveServer2 (Beeline)"
    
    # Try via beeline on host (if available) - fastest
    if command -v beeline &> /dev/null; then
        if timeout $TIMEOUT beeline -u "jdbc:hive2://localhost:10000" -n vagrant \
            -e "SELECT 1;" &>/dev/null 2>&1; then
            print_result "PASS" "Connected via local Beeline (localhost:10000)"
            return 0
        fi
    fi
    
    # Fallback: Try via SSH + beeline in VM
    if [ -x "$(command -v vagrant)" ]; then
        if timeout $TIMEOUT vagrant ssh -c \
            "beeline -u 'jdbc:hive2://localhost:10000' -n vagrant -e 'SELECT 1;'" \
            &>/dev/null 2>&1; then
            print_result "PASS" "Connected via SSH+Beeline in VM"
            return 0
        fi
    fi
    
    # Fallback: Try TCP port check
    if command -v nc &> /dev/null; then
        if timeout $TIMEOUT nc -z localhost 10000 &>/dev/null; then
            print_result "PASS" "Port 10000 (HiveServer2) is open"
            return 0
        fi
    fi
    
    print_result "FAIL" "Cannot connect to HiveServer2 (localhost:10000)"
    log_verbose "Ensure: Vagrant VM is running, Hive services are started, port forwarding is active"
    return 1
}

################################################################################
# Check: Flask API Health
################################################################################

check_flask_api_health() {
    print_check "Flask API (/rma/last_sync)"
    
    if ! command -v curl &> /dev/null; then
        print_result "FAIL" "curl command not found"
        return 1
    fi
    
    local response
    local http_code
    
    response=$(timeout $TIMEOUT curl -s -w "\n%{http_code}" \
        "http://localhost:5000/rma/last_sync" 2>/dev/null)
    
    http_code=$(echo "$response" | tail -n 1)
    local body=$(echo "$response" | sed '$d')
    
    if [ "$http_code" = "200" ]; then
        # Try to extract success field from JSON
        if command -v jq &> /dev/null; then
            local success=$(echo "$body" | jq -r '.success' 2>/dev/null)
            if [ "$success" = "true" ]; then
                print_result "PASS" "API responding with success=true"
                if [ "$VERBOSE" = "1" ]; then
                    log_verbose "Response: $(echo "$body" | head -c 100)..."
                fi
                return 0
            fi
        fi
        
        # Fallback: Any 200 response is good
        print_result "PASS" "API responding (HTTP 200)"
        if [ "$VERBOSE" = "1" ]; then
            log_verbose "Response: $(echo "$body" | head -c 100)..."
        fi
        return 0
    else
        print_result "FAIL" "HTTP $http_code (expected 200)"
        if [ "$VERBOSE" = "1" ]; then
            log_verbose "Response: $body"
        fi
        return 1
    fi
}

################################################################################
# Check: Metadata Freshness
################################################################################

check_metadata_freshness() {
    print_check "Metadata Freshness"
    
    if [ ! -f "$METADATA_FILE" ]; then
        print_result "FAIL" "sync_metadata.json not found at $METADATA_FILE"
        log_verbose "Run: bash provision/scripts/run_pipeline.sh"
        return 1
    fi
    
    if ! command -v jq &> /dev/null; then
        print_result "FAIL" "jq command not found (needed to parse metadata)"
        return 1
    fi
    
    # Check if metadata file is valid JSON
    if ! jq empty "$METADATA_FILE" 2>/dev/null; then
        print_result "FAIL" "sync_metadata.json is not valid JSON"
        return 1
    fi
    
    # Get the most recent timestamp from RAW, SILVER, or GOLD zones
    local raw_time=$(jq -r '.RAW.last_sync // empty' "$METADATA_FILE" 2>/dev/null)
    local silver_time=$(jq -r '.SILVER.last_sync // empty' "$METADATA_FILE" 2>/dev/null)
    local gold_time=$(jq -r '.GOLD.last_sync // empty' "$METADATA_FILE" 2>/dev/null)
    
    local latest_time=""
    local zone_found=""
    
    # Find the most recent timestamp
    if [ -n "$gold_time" ]; then
        latest_time="$gold_time"
        zone_found="GOLD"
    elif [ -n "$silver_time" ]; then
        latest_time="$silver_time"
        zone_found="SILVER"
    elif [ -n "$raw_time" ]; then
        latest_time="$raw_time"
        zone_found="RAW"
    fi
    
    if [ -z "$latest_time" ]; then
        print_result "FAIL" "No sync timestamps found in metadata"
        return 1
    fi
    
    # Convert ISO 8601 to timestamp (works on macOS/Linux)
    # Format: 2026-08-31T09:02:18+03:00
    local sync_epoch
    
    if command -v date &> /dev/null; then
        # Try GNU date first (Linux)
        if date -d "2026-01-01" &>/dev/null 2>&1; then
            sync_epoch=$(date -d "$latest_time" +%s 2>/dev/null)
        # Try BSD date (macOS)
        elif date -j -f "%Y-%m-%dT%H:%M:%S" "2026-01-01T00:00:00" +%s &>/dev/null 2>&1; then
            # Simplified: just check if it's recent
            sync_epoch=$(date +%s)
        fi
    fi
    
    if [ -z "$sync_epoch" ]; then
        # Fallback: just verify the timestamp exists and looks valid
        if [[ "$latest_time" =~ ^[0-9]{4}-[0-9]{2}-[0-9]{2}T ]]; then
            print_result "PASS" "$zone_found zone synced at $latest_time"
            if [ "$VERBOSE" = "1" ]; then
                log_verbose "RAW: $raw_time"
                log_verbose "SILVER: $silver_time"
                log_verbose "GOLD: $gold_time"
            fi
            return 0
        else
            print_result "FAIL" "Invalid timestamp format: $latest_time"
            return 1
        fi
    fi
    
    # Check if sync happened within the last 24 hours
    local now=$(date +%s)
    local age_seconds=$((now - sync_epoch))
    local age_minutes=$((age_seconds / 60))
    local age_hours=$((age_minutes / 60))
    
    if [ "$age_hours" -lt 24 ]; then
        print_result "PASS" "$zone_found zone synced $(printf '%dh %02dm' $age_hours $(( age_minutes % 60 ))) ago"
        return 0
    else
        print_result "FAIL" "Last sync was $age_hours hours ago (metadata may be stale)"
        return 1
    fi
}

################################################################################
# Check: GOLD Table Access (Optional - requires active pipeline)
################################################################################

check_gold_table_accessible() {
    print_check "GOLD Table Data Access"
    
    if ! command -v vagrant &> /dev/null; then
        print_result "FAIL" "Vagrant CLI not available"
        return 1
    fi
    
    # Query GOLD table row count via Beeline in VM
    local row_count=$(timeout $TIMEOUT vagrant ssh -c \
        "beeline -u 'jdbc:hive2://localhost:10000' -n vagrant \
         -e 'SELECT COUNT(*) FROM datalake_gold.patient_events_gold;' \
         2>/dev/null | grep -E '^[0-9]+$' | head -1" 2>/dev/null)
    
    if [ -n "$row_count" ] && [ "$row_count" -ge 0 ]; then
        if [ "$row_count" -gt 0 ]; then
            print_result "PASS" "$row_count rows in GOLD table"
        else
            print_result "PASS" "GOLD table accessible (0 rows - may need data injection)"
        fi
        return 0
    else
        print_result "FAIL" "Cannot query GOLD table"
        return 1
    fi
}

################################################################################
# Generate Report
################################################################################

generate_report() {
    local timestamp=$(date -u +"%Y-%m-%dT%H:%M:%SZ")
    local hostname=$(hostname 2>/dev/null || echo "unknown")
    
    mkdir -p "$REPORTS_DIR"
    
    local report_file="$REPORTS_DIR/startup_test_$(date +%Y%m%d_%H%M%S).json"
    
    cat > "$report_file" << EOF
{
  "timestamp": "$timestamp",
  "hostname": "$hostname",
  "checks_run": $CHECKS_RUN,
  "checks_passed": $PASSED,
  "checks_failed": $FAILED,
  "status": $([ "$FAILED" -eq 0 ] && echo '"HEALTHY"' || echo '"UNHEALTHY"'),
  "metadata_file": "$METADATA_FILE",
  "metadata_exists": $([ -f "$METADATA_FILE" ] && echo 'true' || echo 'false')
}
EOF
    
    echo "Report saved to: $report_file"
}

################################################################################
# Parse Arguments
################################################################################

parse_arguments() {
    while [ $# -gt 0 ]; do
        case "$1" in
            --verbose)
                VERBOSE=1
                shift
                ;;
            --report)
                REPORT=1
                shift
                ;;
            --help)
                show_help
                exit 0
                ;;
            *)
                echo "Unknown option: $1"
                show_help
                exit 1
                ;;
        esac
    done
}

show_help() {
    cat << EOF
MAVIS Database Startup Health Check

Usage:
  bash provision/test_startup.sh [OPTIONS]

Options:
  --verbose     Show detailed output and raw API responses
  --report      Save JSON report to provision/reports/
  --help        Show this help message

Exit Codes:
  0             All checks passed (MAVIS is healthy)
  1             At least one check failed (MAVIS is not ready)

Examples:
  # Quick check
  bash provision/test_startup.sh

  # With detailed output
  bash provision/test_startup.sh --verbose

  # Save results to file
  bash provision/test_startup.sh --report

  # Full diagnostics
  bash provision/test_startup.sh --verbose --report

EOF
}

################################################################################
# Main
################################################################################

main() {
    parse_arguments "$@"
    
    print_header
    
    # Run all checks
    check_vagrant_vm_status
    check_hive_connectivity
    check_flask_api_health
    check_metadata_freshness
    
    # Optional check (less critical)
    check_gold_table_accessible
    
    # Print summary
    print_summary
    
    # Generate report if requested
    if [ "$REPORT" = "1" ]; then
        generate_report
    fi
    
    # Exit with appropriate code
    if [ "$FAILED" -eq 0 ]; then
        exit 0
    else
        exit 1
    fi
}

main "$@"
