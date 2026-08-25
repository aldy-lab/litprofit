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

printf '\nSupabase project URL (https://xxxx.supabase.co): '
read -r CALC_SUPABASE_URL
printf 'Supabase anon key (input hidden): '
read -rs CALC_SUPABASE_KEY; echo

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
