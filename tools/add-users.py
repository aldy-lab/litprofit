#!/usr/bin/env python3
"""
Creates calculator accounts from a roster, and sets what each one may see.

    CALC_SUPABASE_URL=... CALC_SUPABASE_SERVICE_KEY=... \
        python3 tools/add-users.py /path/to/roster.tsv

Use tools/add-users.sh instead, which takes both values from the keychain and
never puts them on a command line.

WHY A SCRIPT AND NOT A MIGRATION
--------------------------------
An account is not application data. Supabase Auth (GoTrue) owns auth.users,
and rows written into it by hand are rows GoTrue did not make: the password
has to be hashed the way it expects, the identity row has to match, and half
a dozen token columns have conventions that are not written down anywhere and
change between versions. It works until an upgrade, and then it does not, and
what breaks is everybody's ability to sign in.

The Admin API is the supported way in. It needs the service_role key, which
is the key that bypasses every row level security policy in the project --
so it is asked for once, kept in the keychain, and never written down.

WHAT THIS DOES NOT DO
---------------------
It does not delete anybody, it does not change a password that already
exists, and it does not touch an account it did not create. Run it twice and
the second run reports what was already there and stops.

THE ROSTER
----------
Tab-separated, one person per line, blank lines and #comments ignored:

    email <TAB> full name <TAB> role <TAB> password

role is `admin` or `staff`. Nothing else is accepted -- `manager` exists in
the schema but is a middle tier nobody asked for here, and a typo silently
becoming 'staff' is how somebody ends up unable to do their job.
"""

import json, os, ssl, sys, urllib.error, urllib.request


def ca_context():
    """An SSL context that can actually verify a certificate.

    A python.org build on macOS does not use the system keychain. It looks for
    a cert.pem that the installer's "Install Certificates.command" is supposed
    to link to certifi -- and when nobody has run it, that file is simply not
    there. Verification then fails against every https host on the machine,
    with an error that reads like a wrong key or a wrong address:

        [SSL: CERTIFICATE_VERIFY_FAILED] unable to get local issuer certificate

    certifi ships with that same Python and holds Mozilla's CA list, which is
    exactly what the installer would have pointed at. Falling back to it is
    not a workaround around verification, it is verification with the roots
    the machine failed to hand over.
    """
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

# Loopback allowed so this can be driven against a local stand-in, the same
# concession the calculator's own CLOUD block makes and for the same reason:
# a script that provisions accounts should be runnable before it is run for
# real. Nothing else may be plain http.
import re as _re
if not (URL.startswith("https://") or
        _re.match(r"^http://(127\.0\.0\.1|localhost)[:/]", URL)):
    sys.exit("CALC_SUPABASE_URL must be the https project URL.")
if len(KEY) < 20:
    sys.exit("CALC_SUPABASE_SERVICE_KEY is missing.")
if len(sys.argv) < 2:
    sys.exit("usage: add-users.py <roster.tsv>")

ROLES = ("admin", "staff")


def call(method, path, body=None):
    req = urllib.request.Request(
        URL + path, method=method,
        data=json.dumps(body).encode() if body is not None else None,
        headers={"apikey": KEY, "Authorization": "Bearer " + KEY,
                 "Content-Type": "application/json"})
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
        # No network, wrong host, DNS gone. A stack trace here tells the
        # person running this nothing they can act on.
        msg = "Could not reach %s -- %s" % (URL, e.reason)
        if "CERTIFICATE_VERIFY_FAILED" in str(e.reason):
            msg += ("\n\nThis machine's Python cannot verify any certificate at all."
                    "\nThe one-time fix, which also mends every other Python tool here:"
                    "\n    open '/Applications/Python 3.12/Install Certificates.command'")
        sys.exit(msg)


def existing():
    """Everyone already there, by email. Paged, because the admin listing is."""
    by = {}
    page = 1
    while True:
        st, body = call("GET", "/auth/v1/admin/users?per_page=200&page=%d" % page)
        if st != 200:
            sys.exit("Could not list accounts: %s %s" % (st, body))
        users = (body or {}).get("users", [])
        for u in users:
            if u.get("email"):
                by[u["email"].lower()] = u["id"]
        if len(users) < 200:
            return by
        page += 1


def roster(path):
    people = []
    seen = set()
    for n, line in enumerate(open(path, encoding="utf-8"), 1):
        line = line.rstrip("\n")
        if not line.strip() or line.lstrip().startswith("#"):
            continue
        parts = [p.strip() for p in line.split("\t")]
        if len(parts) != 4:
            sys.exit("line %d: expected 4 tab-separated fields, found %d" % (n, len(parts)))
        email, name, role, password = parts
        if "@" not in email:
            sys.exit("line %d: %r is not an email" % (n, email))
        if role not in ROLES:
            sys.exit("line %d: role must be one of %s, not %r" % (n, "/".join(ROLES), role))
        if len(password) < 6:
            # Supabase refuses anything shorter, and it refuses it per-user in
            # the middle of the run, which is a worse place to find out.
            sys.exit("line %d: the password for %s is under six characters" % (n, email))
        if email.lower() in seen:
            sys.exit("line %d: %s appears twice in the roster" % (n, email))
        seen.add(email.lower())
        people.append({"email": email, "name": name, "role": role, "password": password})
    if not people:
        sys.exit("the roster is empty")
    return people


people = roster(sys.argv[1])
have = existing()
print("%d in the roster, %d accounts already exist\n" % (len(people), len(have)))

made, kept, failed = [], [], []

for p in people:
    uid = have.get(p["email"].lower())
    if uid:
        # Deliberately not touching the password or the role of an account
        # that is already there. Somebody may have changed either on purpose.
        kept.append(p["email"])
        print("  = %-34s already there, left alone" % p["email"])
        continue

    st, body = call("POST", "/auth/v1/admin/users", {
        "email": p["email"],
        "password": p["password"],
        # Confirmed on creation: there is no mailbox to click a link in for a
        # shared address like info@, and these accounts are handed out in
        # person rather than invited.
        "email_confirm": True,
        "user_metadata": {"name": p["name"]},
    })
    if st not in (200, 201) or not (body or {}).get("id"):
        failed.append((p["email"], st, body))
        print("  ! %-34s NOT created: %s %s" % (p["email"], st, body))
        continue
    uid = body["id"]

    # The profile is made by the on_auth_user_created trigger and lands as
    # 'staff'. Only a role that is not the default needs a second call.
    if p["role"] != "staff":
        st2, body2 = call("PATCH", "/rest/v1/profiles?id=eq." + uid, {"role": p["role"]})
        if st2 not in (200, 204):
            failed.append((p["email"], st2, body2))
            print("  ! %-34s made, but the role did NOT stick: %s %s"
                  % (p["email"], st2, body2))
            continue
    made.append((p["email"], p["role"]))
    print("  + %-34s created, %s" % (p["email"], p["role"]))

print("\n%d created, %d left alone, %d failed" % (len(made), len(kept), len(failed)))
if failed:
    sys.exit(1)
print("""
Passwords were set to what the roster said. Nothing here can make somebody
change one, so if they are meant to be temporary, that is a conversation and
not a setting.""")
