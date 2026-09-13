#!/usr/bin/env bash
# Set the password on one account that already exists, without typing a
# secret anywhere it can be kept.
#
#     bash tools/set-password.sh rf@litprofit.com
#
# The project URL and the service_role key come out of the keychain, where
# tools/add-users.sh put them. The new password is read with the echo off and
# handed over on standard input, so it is never an argument, never in a file
# and never in ~/.zsh_history.
set -euo pipefail
cd "$(dirname "$0")/.."

EMAIL="${1:-}"
case "$EMAIL" in
  *@*) ;;
  *) echo "usage: bash tools/set-password.sh <email>"; exit 1 ;;
esac

KC_SVC="litprofit-calc"
kc_get(){ security find-generic-password -s "$KC_SVC" -a "$1" -w 2>/dev/null; }
kc_set(){ security add-generic-password -U -s "$KC_SVC" -a "$1" -w "$2" 2>/dev/null; }

URL="$(kc_get url || true)"
SERVICE="$(kc_get service || true)"
if [ -z "$URL" ] || [ -z "$SERVICE" ]; then
  echo "The project URL or the service_role key is not in your keychain yet."
  echo "Run tools/add-users.sh once -- it asks for both and keeps them."
  exit 1
fi

# The anon key is the public one the calculator already ships with, and it is
# here for one reason: to sign in afterwards and prove the new password works.
ANON="$(kc_get anon || true)"
if [ -z "$ANON" ]; then
  cat <<'EOF'

The anon key (Project Settings -> Data API -> anon public).

This is the PUBLIC key -- it is in the calculator's own HTML. It is asked for
so this can sign in afterwards and prove the new password actually works,
rather than trusting that the write was accepted.

EOF
  printf 'anon key: '
  read -r ANON
  [ -n "$ANON" ] && kc_set anon "$ANON" >/dev/null
fi

printf 'New password for %s (hidden): ' "$EMAIL"
read -rs NEW; echo
printf 'Again: '
read -rs AGAIN; echo
if [ "$NEW" != "$AGAIN" ]; then
  echo "Those do not match -- nothing was done."
  exit 1
fi

printf '%s' "$NEW" | CALC_SUPABASE_URL="$URL" \
  CALC_SUPABASE_SERVICE_KEY="$SERVICE" \
  CALC_SUPABASE_ANON_KEY="$ANON" \
  python3 tools/set-password.py "$EMAIL"

cat <<EOF

Hand it over in person or over something that is not email. Nothing here can
force it to be changed on first sign-in -- Supabase has no such flag -- so if
it is meant to be temporary, that is a conversation.
EOF
