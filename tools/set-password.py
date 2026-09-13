#!/usr/bin/env python3
"""
Sets the password on ONE account that already exists.

    CALC_SUPABASE_URL=... CALC_SUPABASE_SERVICE_KEY=... \
        printf '%s' "$NEW" | python3 tools/set-password.py rf@litprofit.com

Use tools/set-password.sh instead. It takes the project URL and the
service_role key out of the keychain, asks for the new password with the
echo off, and hands it over on standard input -- so the one secret that
matters here never appears in a command line, a file or ~/.zsh_history.

WHY THIS IS A SEPARATE TOOL
---------------------------
tools/add-users.py promises, in writing, that it will not touch an account
that is already there: not the password, not the role. That promise is the
reason it is safe to re-run against the whole roster at any time, and it
should not be weakened with a flag. So resetting a password is its own
tool, with its own one-account-at-a-time shape.

Somebody forgetting a password is not an unusual event, and the alternative
-- deleting the account and making it again -- takes their profile row, and
with it whatever the rest of the schema hangs off their id.

IT VERIFIES, RATHER THAN REPORTS
--------------------------------
A 200 from the admin API means the write was accepted. It does not mean
anybody can sign in: a project with email confirmation pending, a banned
user, a password the project's own policy rejects -- all of those can leave
a 200 behind and a person still locked out. So after setting it, this signs
in as that user with the public anon key, exactly the way the calculator
does, and says whether a token came back. That is the only evidence worth
printing.
"""

import getpass
import json
import os
import re
import ssl
import sys
import urllib.error
import urllib.request


def ca_context():
    """The same certificate fallback tools/add-users.py documents: a
    python.org build on macOS whose "Install Certificates.command" was never
    run cannot verify any https host, and says so in a way that reads like a
    wrong key."""
    ctx = ssl.create_default_context()
    if ctx.get_ca_certs():
        return ctx
    try:
        import certifi
        ctx.load_verify_locations(certifi.where())
    except Exception:
        pass
    return ctx


SSL_CTX = ca_context()
URL = (os.environ.get("CALC_SUPABASE_URL") or "").rstrip("/")
KEY = os.environ.get("CALC_SUPABASE_SERVICE_KEY") or ""
ANON = os.environ.get("CALC_SUPABASE_ANON_KEY") or os.environ.get("CALC_SUPABASE_KEY") or ""

if not (URL.startswith("https://")
        or re.match(r"^http://(127\.0\.0\.1|localhost)[:/]", URL)):
    sys.exit("CALC_SUPABASE_URL must be the https project URL.")
if len(KEY) < 20:
    sys.exit("CALC_SUPABASE_SERVICE_KEY is missing.")
if len(sys.argv) != 2 or "@" not in sys.argv[1]:
    sys.exit("usage: set-password.py <email>   (new password on stdin)")

EMAIL = sys.argv[1].strip().lower()


def call(method, path, body=None, key=None, extra=None):
    k = key or KEY
    headers = {"apikey": k, "Authorization": "Bearer " + k,
               "Content-Type": "application/json"}
    headers.update(extra or {})
    req = urllib.request.Request(
        URL + path, method=method,
        data=json.dumps(body).encode() if body is not None else None,
        headers=headers)
    try:
        with urllib.request.urlopen(req, context=SSL_CTX) as r:
            raw = r.read().decode()
            return r.status, (json.loads(raw) if raw else None)
    except urllib.error.HTTPError as e:
        raw = e.read().decode()
        try:
            return e.code, json.loads(raw)
        except ValueError:
            return e.code, {"msg": raw[:200]}
    except urllib.error.URLError as e:
        msg = "Could not reach %s -- %s" % (URL, e.reason)
        if "CERTIFICATE_VERIFY_FAILED" in str(e.reason):
            msg += ("\n\nThis machine's Python cannot verify any certificate at all."
                    "\nThe one-time fix:"
                    "\n    open '/Applications/Python 3.12/Install Certificates.command'")
        sys.exit(msg)


def find(email):
    """The account, by address. The admin listing is paged, and a project
    with more people than one page is the one where guessing goes wrong."""
    page = 1
    while True:
        st, body = call("GET", "/auth/v1/admin/users?per_page=200&page=%d" % page)
        if st != 200:
            sys.exit("Could not list accounts: %s %s" % (st, body))
        users = (body or {}).get("users", [])
        for u in users:
            if (u.get("email") or "").lower() == email:
                return u
        if len(users) < 200:
            return None
        page += 1


user = find(EMAIL)
if not user:
    sys.exit("There is no account for %s. tools/add-users.sh makes new ones."
             % EMAIL)

new = sys.stdin.read().rstrip("\n") if not sys.stdin.isatty() \
    else getpass.getpass("New password for %s (hidden): " % EMAIL)
if len(new) < 6:
    sys.exit("Supabase refuses anything under six characters -- nothing was done.")

print("account   %s" % EMAIL)
print("id        %s" % user["id"])
# The role lives in public.profiles, not in the auth record -- printing it
# is worth one more call, because resetting a password for the wrong person
# and resetting it for the right person look identical otherwise.
st, prof = call("GET", "/rest/v1/profiles?id=eq.%s&select=name,role" % user["id"])
if st == 200 and prof:
    print("name      %s" % (prof[0].get("name") or "-"))
    print("role      %s" % (prof[0].get("role") or "-"))

st, body = call("PUT", "/auth/v1/admin/users/" + user["id"], {"password": new})
if st != 200:
    sys.exit("The password was NOT changed: %s %s" % (st, body))
print("set       accepted by the admin API")

# ---- and now the only evidence worth having ----
if not ANON:
    print("\nNOT VERIFIED: no anon key was given, so this could not try to sign\n"
          "in. Set CALC_SUPABASE_ANON_KEY (it is the public one, the same key\n"
          "the calculator ships with) to have this checked.")
    sys.exit(0)

st, body = call("POST", "/auth/v1/token?grant_type=password",
                {"email": EMAIL, "password": new}, key=ANON)
if st == 200 and (body or {}).get("access_token"):
    print("verified  signed in with the new password, a token came back")
    # Not left signed in: the session this just opened is a real one.
    call("POST", "/auth/v1/logout", {}, key=ANON,
         extra={"Authorization": "Bearer " + body["access_token"]})
else:
    sys.exit("\nThe write was accepted but signing in FAILED: %s %s\n"
             "That is the state worth knowing about -- the account is not\n"
             "usable, whatever the first call said." % (st, body))
