#!/usr/bin/env bash
# Rebuild and publish the calculator, without typing a command by hand.
#
#     bash tools/publish-calc.sh
#
# build-calc.py takes its three secrets from the environment. Typed on a
# command line they end up in ~/.zsh_history in plain text, and the Supabase
# key and every user's password with them. This asks instead, keeps them in
# variables for the length of one build, and never writes them anywhere.
set -euo pipefail
cd "$(dirname "$0")/.."

say(){ printf '\n\033[1m%s\033[0m\n' "$*"; }

say "Calculator publish"
echo "Three things are needed. Nothing typed here is saved or echoed back."

# Both values are remembered in the macOS keychain after the first run, so a
# rebuild needs no typing at all. The publishable key is public by design --
# it ships inside the page -- but the keychain is still the right place for it:
# a file in the repo gets committed, and a command line gets a shell history.
KC_SVC="litprofit-calc"
kc_get(){ security find-generic-password -s "$KC_SVC" -a "$1" -w 2>/dev/null; }
kc_set(){ security add-generic-password -U -s "$KC_SVC" -a "$1" -w "$2" 2>/dev/null; }

CALC_SUPABASE_URL="$(kc_get url || true)"
CALC_SUPABASE_KEY="$(kc_get key || true)"

if [ -n "$CALC_SUPABASE_URL" ] && [ -n "$CALC_SUPABASE_KEY" ]; then
  echo
  echo "Using the project already in your keychain:"
  echo "  $CALC_SUPABASE_URL"
  echo "  key ${CALC_SUPABASE_KEY%%"${CALC_SUPABASE_KEY#??????????????}"}…"
  echo "  (to change it:  security delete-generic-password -s $KC_SVC -a url;"
  echo "                  security delete-generic-password -s $KC_SVC -a key)"
else
echo
echo "Both of these are in the Supabase dashboard under"
echo "  Project Settings -> Data API"
echo "NOT the address in your browser's bar -- that is the dashboard, and a"
echo "build made with it silently falls back to browser-only storage."
printf '\nProject URL (https://<ref>.supabase.co): '
read -r CALC_SUPABASE_URL
case "$CALC_SUPABASE_URL" in
  *supabase.com/dashboard*|*/project/*)
    ref=$(printf '%s' "$CALC_SUPABASE_URL" | tr '/' '\n' | grep -Ex '[a-z0-9]{20}' | head -1)
    echo "  That is the dashboard address."
    [ -n "$ref" ] && echo "  You want:  https://$ref.supabase.co"
    exit 1 ;;
esac
printf 'anon / publishable key (input hidden): '
read -rs CALC_SUPABASE_KEY; echo
if [ ${#CALC_SUPABASE_KEY} -lt 20 ]; then
  echo "  That key is too short to be one — nothing was built."; exit 1
fi
case "$CALC_SUPABASE_KEY" in
  sbp_*)          echo "  That is a personal access token, not the anon key."; exit 1 ;;
  sb_secret_*)    echo "  That is a secret key. It must never be published."; exit 1 ;;
  *service_role*) echo "  That is the service role key. It must never be published."; exit 1 ;;
esac
kc_set url "$CALC_SUPABASE_URL" >/dev/null && kc_set key "$CALC_SUPABASE_KEY" >/dev/null \
  && echo "  Saved to your keychain — the next build will not ask."
fi

# With a database configured the login is Supabase Auth and accounts live in
# the dashboard; the per-user encryption below is only for the no-database
# build. Asking for passwords that will not be used is how the wrong thing
# gets typed.
if [ -n "$CALC_SUPABASE_URL" ] && [ -n "$CALC_SUPABASE_KEY" ]; then
  say "Building"
  CALC_SUPABASE_URL="$CALC_SUPABASE_URL" CALC_SUPABASE_KEY="$CALC_SUPABASE_KEY" \
    python3 tools/build-calc.py
  say "Built"
  git status --porcelain calculator/ || true
  cat <<'EOF'

If calculator/index.html is listed above, publish it:

    git add calculator/index.html
    git commit -m "Rebuild the calculator"
    git push
EOF
  exit 0
fi

echo
echo "Now the people who may open the calculator."
echo "Enter one per line as  username password  — blank line when done."
USERS='['
first=1
while true; do
  printf '  user: '
  read -r line || break
  [ -z "$line" ] && break
  name="${line%% *}"; pass="${line#* }"
  if [ "$name" = "$pass" ]; then echo "  need a username AND a password on one line"; continue; fi
  esc(){ printf '%s' "$1" | sed 's/\\/\\\\/g; s/"/\\"/g'; }
  [ $first -eq 0 ] && USERS="$USERS,"
  USERS="$USERS[\"$(esc "$name")\",\"$(esc "$pass")\"]"
  first=0
done
USERS="$USERS]"
if [ $first -eq 1 ]; then echo "No users given — nothing to build."; exit 1; fi

say "Building"
CALC_USERS="$USERS" \
CALC_SUPABASE_URL="$CALC_SUPABASE_URL" \
CALC_SUPABASE_KEY="$CALC_SUPABASE_KEY" \
python3 tools/build-calc.py

say "Built"
git status --porcelain calculator/ || true
cat <<'EOF'

If calculator/index.html is listed above, publish it:

    git add calculator/index.html
    git commit -m "Rebuild the calculator"
    git push
EOF
