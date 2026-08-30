#!/usr/bin/env bash
# Create calculator accounts from a roster, without typing a secret.
#
#     bash tools/add-users.sh ~/Desktop/litprofit-accounts.tsv
#
# The project URL is already in the keychain from the calculator build. The
# service_role key is asked for once and kept beside it. Typed on a command
# line it would end up in ~/.zsh_history, and this is the key that bypasses
# every row level security policy in the project -- it reads payroll.
set -euo pipefail
cd "$(dirname "$0")/.."

ROSTER="${1:-}"
if [ -z "$ROSTER" ] || [ ! -f "$ROSTER" ]; then
  echo "usage: bash tools/add-users.sh <roster.tsv>"
  echo
  echo "Tab-separated, one person per line:"
  echo "    email <TAB> full name <TAB> admin|staff <TAB> password"
  exit 1
fi

KC_SVC="litprofit-calc"
kc_get(){ security find-generic-password -s "$KC_SVC" -a "$1" -w 2>/dev/null; }
kc_set(){ security add-generic-password -U -s "$KC_SVC" -a "$1" -w "$2" 2>/dev/null; }

CALC_SUPABASE_URL="$(kc_get url || true)"
if [ -z "$CALC_SUPABASE_URL" ]; then
  printf 'Project URL (https://<ref>.supabase.co): '
  read -r CALC_SUPABASE_URL
  kc_set url "$CALC_SUPABASE_URL" >/dev/null
fi

CALC_SUPABASE_SERVICE_KEY="$(kc_get service || true)"
if [ -z "$CALC_SUPABASE_SERVICE_KEY" ]; then
  cat <<'EOF'

The service_role key. Supabase dashboard -> Project Settings -> API keys.

It is NOT the anon key the calculator ships with. This one ignores every
policy in the database, so it never goes in a file, a repository or a
command line. It is used here, kept in your keychain, and nowhere else.

EOF
  printf 'service_role key (input hidden): '
  read -rs CALC_SUPABASE_SERVICE_KEY; echo
  case "$CALC_SUPABASE_SERVICE_KEY" in
    sbp_*) echo "  That is a personal access token, not the service key."; exit 1 ;;
  esac
  if [ ${#CALC_SUPABASE_SERVICE_KEY} -lt 20 ]; then
    echo "  That key is too short to be one -- nothing was done."; exit 1
  fi
  kc_set service "$CALC_SUPABASE_SERVICE_KEY" >/dev/null \
    && echo "  Saved to your keychain -- the next run will not ask."
fi

echo
CALC_SUPABASE_URL="$CALC_SUPABASE_URL" \
CALC_SUPABASE_SERVICE_KEY="$CALC_SUPABASE_SERVICE_KEY" \
  python3 tools/add-users.py "$ROSTER"

cat <<EOF

The roster still holds everybody's password in plain text. Delete it when the
accounts have been handed out:

    rm "$ROSTER"
EOF
