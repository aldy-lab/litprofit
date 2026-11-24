#!/usr/bin/env bash
# Load a sales-folder manifest into the calculator, without a browser.
#
#     bash tools/import-sales.sh "/Users/aldy/Desktop/LITPROFIT importas 2026/manifest.json"
#
# The project URL and the service_role key come out of the keychain (service
# litprofit-calc, the same entries tools/set-password.sh uses) and go straight
# into the loader's environment: never echoed, never written down.
set -euo pipefail
cd "$(dirname "$0")/.."
DIR="$HOME/Desktop/LITPROFIT importas 2026"
MODE="records"; if [ "${1:-}" = "--costs" ]; then MODE="costs"; shift; fi
MANIFEST="${1:-$DIR/manifest.json}"
kc_get(){ security find-generic-password -s litprofit-calc -a "$1" -w 2>/dev/null; }
URL="$(kc_get url || true)"; KEY="$(kc_get service || true)"
if [ -z "$URL" ] || [ -z "$KEY" ]; then
  echo "The project URL or the service_role key is not in the keychain. Run tools/add-users.sh once first."; exit 1
fi
if [ "$MODE" = "costs" ]; then
  CALC_URL="$URL" CALC_KEY="$KEY" COSTS_JSON="$DIR/costs.json" python3 tools/sales-manifest/6_load_costs.py
else
  CALC_URL="$URL" CALC_KEY="$KEY" python3 tools/sales-manifest/4_load.py "$MANIFEST"
fi
