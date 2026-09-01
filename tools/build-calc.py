#!/usr/bin/env python3
"""
Builds the password-protected project calculator.

    CALC_USERS='[["alice","secret"],["bob","other"]]' python3 tools/build-calc.py

WHY ENCRYPTION AND NOT A LOGIN FORM
-----------------------------------
GitHub Pages serves static files; there is no server to check a password
against. A JavaScript gate that compares a typed string and then reveals a
hidden <div> is theatre — the content is already in the file, and "View
source" walks straight past it.

So the calculator is encrypted instead. The published page contains only
ciphertext plus the code to decrypt it. Without the passphrase there is
genuinely nothing to read, not merely nothing displayed.

HOW THE LOGIN WORKS
-------------------
A username field that is merely checked in JavaScript adds nothing — it is
another string comparison to walk past. Here BOTH fields feed the key
derivation, so a wrong username fails exactly as a wrong password does.

The app is encrypted ONCE under a random 256-bit content key. That key is then
wrapped separately for each user, under a key derived from their own username
and password:

  content key   32 random bytes, never derived from anything
  per user      PBKDF2-HMAC-SHA256(username, NUL, password), 310,000 iters,
                own 16-byte salt, wrapping the content key with AES-256-GCM
  payload       AES-256-GCM under the content key
  integrity     GCM's own tag — wrong credentials fail to authenticate rather
                than yielding garbage

That structure buys two things a single passphrase cannot: revoking one person
means rebuilding without their entry, and changing one password does not
re-encrypt the app or disturb anyone else.

USERNAMES ARE NOT STORED. Only the wrapped keys are published, and the browser
tries each in turn — so the file does not disclose who has access.

THE PASSWORD IS NEVER STORED IN THIS REPOSITORY. It comes from the
environment. The repository is public: a password committed here would be
readable by anyone, which would defeat the whole exercise.

The encryption runs in a headless browser through WebCrypto rather than in
Python. That is deliberate — it is the same implementation that will decrypt
it, so the two cannot drift apart in padding, encoding or key derivation.
"""
import functools
import http.server
import io
import json
import os
import socket
import socketserver
import sys
import threading

from playwright.sync_api import sync_playwright

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SERVE = os.path.dirname(ROOT)
PREFIX = "/" + os.path.basename(ROOT)

# Kept in step with tools/build.py by hand, which is how it went stale: the
# site moved to the domain and this file still prefixed /litprofit/, so the
# calculator asked for its logo and its fonts at an address that no longer
# exists. Neither is fatal -- a missing font falls back and a missing logo is
# a gap in the header -- which is exactly why nobody would have noticed.
BASE = ""
OUT_DIR = os.path.join(ROOT, "calculator")
ITERATIONS = 310000

USERS_RAW = os.environ.get("CALC_USERS", "")

# Set these two and the calculator keeps its projects in Postgres instead of
# in one browser, and Supabase Auth becomes the login. See db/schema.sql.
# CALC_SUPABASE_ANON_KEY is still read, because that is what the key was
# called when this was written and shells outlive naming decisions.
SUPA_URL = os.environ.get("CALC_SUPABASE_URL", "").strip()
SUPA_KEY = (os.environ.get("CALC_SUPABASE_KEY")
            or os.environ.get("CALC_SUPABASE_ANON_KEY", "")).strip()

ENCRYPT_JS = """async ([plaintext, users, iterations]) => {
  const enc = new TextEncoder();
  /* Chunked on purpose. String.fromCharCode(...bytes) spreads every byte
     into an argument list, and the engine's argument limit is well under the
     size of this app -- it worked until the file grew, then failed with
     "Maximum call stack size exceeded" rather than anything about size. */
  const b64 = b => {
    const a = new Uint8Array(b);
    let out = '';
    for(let i = 0; i < a.length; i += 0x8000){
      out += String.fromCharCode.apply(null, a.subarray(i, i + 0x8000));
    }
    return btoa(out);
  };

  // one random content key; the app is encrypted under it exactly once
  const rawKey = crypto.getRandomValues(new Uint8Array(32));
  const contentKey = await crypto.subtle.importKey(
    'raw', rawKey, {name:'AES-GCM'}, false, ['encrypt']);
  const iv = crypto.getRandomValues(new Uint8Array(12));
  const ct = await crypto.subtle.encrypt(
    {name:'AES-GCM', iv}, contentKey, enc.encode(plaintext));

  // wrap that content key once per user
  const entries = [];
  for (const [user, pass] of users) {
    const salt = crypto.getRandomValues(new Uint8Array(16));
    const wIv = crypto.getRandomValues(new Uint8Array(12));
    const base = await crypto.subtle.importKey(
      'raw', enc.encode(user + String.fromCharCode(10) + pass), 'PBKDF2', false, ['deriveKey']);
    const kek = await crypto.subtle.deriveKey(
      {name:'PBKDF2', salt, iterations, hash:'SHA-256'},
      base, {name:'AES-GCM', length:256}, false, ['encrypt']);
    const wrapped = await crypto.subtle.encrypt({name:'AES-GCM', iv:wIv}, kek, rawKey);
    entries.push({salt:b64(salt), iv:b64(wIv), key:b64(wrapped)});
  }
  return {iv: b64(iv), data: b64(ct), users: entries};
}"""

GATE = """<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<meta name="robots" content="noindex, nofollow">
<title>LITPROFIT</title>
<link rel="icon" href="{base}/assets/brand/favicon.svg">
<link rel="stylesheet" href="{base}/css/fonts.css">
<style>
  /* The sign-in screen keeps the brand navy — it is the company's front door.
     The platform behind it is a spreadsheet and stays light. */
  :root{{
    --page:#070824; --surface:#0c0e30;
    --ink-1:#fff; --ink-2:#b0b3c4; --ink-3:#6b6e85;
    --line:rgba(255,255,255,.10); --line-2:rgba(255,255,255,.22);
    --accent:#9ec9ff; --bad:#ff9a9a;
    --font:"Montserrat","Montserrat Fallback",system-ui,-apple-system,sans-serif;
    --mono:ui-monospace,SFMono-Regular,Menlo,monospace;
  }}
  *{{box-sizing:border-box}}
  body{{
    margin:0;min-height:100vh;display:grid;place-items:center;padding:24px;
    background:var(--page);color:var(--ink-1);font-family:var(--font);
  }}
  .gate{{width:100%;max-width:380px}}
  .gate img{{height:26px;width:auto;display:block;margin-bottom:34px}}
  .seam{{
    height:26px;margin-bottom:26px;opacity:.3;
    background-image:url("data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' width='26' height='26'%3E%3Crect x='9.9' y='9.9' width='7' height='7' rx='1.5' fill='%23000000' fill-opacity='0.55'/%3E%3Crect x='9' y='9' width='7' height='7' rx='1.5' fill='%23ffffff'/%3E%3C/svg%3E");
    background-size:26px 26px;background-repeat:repeat-x;
  }}
  h1{{font-size:22px;font-weight:700;letter-spacing:-.02em;margin:0 0 8px}}
  p.sub{{
    font-size:10px;letter-spacing:.2em;text-transform:uppercase;
    color:var(--ink-3);font-family:var(--mono);margin:0 0 26px;
  }}
  label{{
    display:block;font-size:10px;letter-spacing:.18em;text-transform:uppercase;
    color:var(--ink-3);font-family:var(--mono);margin-bottom:8px;
  }}
  input{{
    width:100%;padding:13px 14px;font:inherit;font-size:16px;
    background:var(--surface);border:1px solid var(--line);border-radius:2px;
    color:var(--ink-1);
  }}
  input:focus{{outline:2px solid var(--accent);outline-offset:-1px;border-color:transparent}}
  button{{
    width:100%;margin-top:14px;padding:14px;font:inherit;font-size:11px;
    font-weight:600;letter-spacing:.16em;text-transform:uppercase;
    background:#fff;color:#070824;border:0;border-radius:2px;cursor:pointer;
  }}
  button:disabled{{opacity:.5;cursor:default}}
  .note{{
    margin-top:16px;font-size:12px;color:var(--ink-3);min-height:20px;
    font-family:var(--mono);letter-spacing:.04em;
  }}
  .note.bad{{color:var(--bad)}}
</style>
</head>
<body>
<form class="gate" id="gate" autocomplete="off">
  <img src="{base}/assets/brand/logo-lockup.svg" alt="LITPROFIT">
  <div class="seam" aria-hidden="true"></div>
  <h1>Project Calculator</h1>
  <p class="sub">Restricted <span style="opacity:.5">//</span> internal use</p>
  <label for="user">Username</label>
  <input id="user" type="text" autocomplete="username" autocapitalize="none"
         spellcheck="false" autofocus>
  <label for="pw" style="margin-top:16px">Password</label>
  <input id="pw" type="password" autocomplete="current-password">
  <button id="go" type="submit">Sign in</button>
  <p class="note" id="note" role="status" aria-live="polite"></p>
</form>
<script>
/* The page holds ciphertext only. A wrong passphrase fails AES-GCM's
   authentication tag, so it errors rather than producing plausible rubbish. */
var PAYLOAD = {payload};
var ITER = {iterations};

var f = document.getElementById('gate'),
    user = document.getElementById('user'),
    pw = document.getElementById('pw'),
    go = document.getElementById('go'),
    note = document.getElementById('note');

function b2a(b64) {{
  var s = atob(b64), a = new Uint8Array(s.length);
  for (var i = 0; i < s.length; i++) a[i] = s.charCodeAt(i);
  return a;
}}

f.addEventListener('submit', async function (e) {{
  e.preventDefault();
  if (!user.value || !pw.value) return;
  go.disabled = true;
  note.className = 'note';
  note.textContent = 'Checking\\u2026';

  var enc = new TextEncoder();
  var raw = null;

  /* Both fields feed the derivation, so a wrong username fails exactly as a
     wrong password does. Usernames are not stored anywhere in this file — the
     wrapped keys are simply tried in turn, and the one that authenticates is
     the one that belongs to these credentials. */
  var base = await crypto.subtle.importKey(
    'raw', enc.encode(user.value + String.fromCharCode(10) + pw.value), 'PBKDF2', false, ['deriveKey']);

  for (var i = 0; i < PAYLOAD.users.length; i++) {{
    var u = PAYLOAD.users[i];
    try {{
      var kek = await crypto.subtle.deriveKey(
        {{name:'PBKDF2', salt:b2a(u.salt), iterations:ITER, hash:'SHA-256'}},
        base, {{name:'AES-GCM', length:256}}, false, ['decrypt']);
      raw = await crypto.subtle.decrypt({{name:'AES-GCM', iv:b2a(u.iv)}}, kek, b2a(u.key));
      break;                       /* GCM authenticated — these credentials fit */
    }} catch (err) {{ /* not this entry; try the next */ }}
  }}

  if (!raw) {{
    go.disabled = false;
    note.className = 'note bad';
    note.textContent = 'Wrong username or password.';
    pw.select();
    return;
  }}

  try {{
    var contentKey = await crypto.subtle.importKey(
      'raw', raw, {{name:'AES-GCM'}}, false, ['decrypt']);
    var plain = await crypto.subtle.decrypt(
      {{name:'AES-GCM', iv:b2a(PAYLOAD.iv)}}, contentKey, b2a(PAYLOAD.data));
    var html = new TextDecoder().decode(plain);
    /* document.write, not innerHTML: scripts injected through innerHTML never
       execute, and the calculator is almost entirely script. */
    document.open();
    document.write(html);
    document.close();
  }} catch (err) {{
    go.disabled = false;
    note.className = 'note bad';
    note.textContent = 'Could not open the payload.';
  }}
}});
</script>
</body>
</html>
"""


def free_port():
    s = socket.socket(); s.bind(("127.0.0.1", 0))
    p = s.getsockname()[1]; s.close(); return p


class Quiet(http.server.SimpleHTTPRequestHandler):
    def log_message(self, *a): pass


def read_app():
    app = io.open(os.path.join(ROOT, "tools", "calc", "app.html"),
                  encoding="utf-8").read()
    return (app.replace("__BASE__", BASE)
               .replace("__SUPABASE_URL__", SUPA_URL)
               .replace("__SUPABASE_ANON_KEY__", SUPA_KEY))


def build_cloud():
    """Database mode: the app itself is the page, Supabase Auth is the gate."""
    # https in production. Loopback is allowed because that is how this gets
    # tested against a local stand-in, and a browser treats 127.0.0.1 as a
    # secure context for the same reason.
    local = SUPA_URL.startswith(("http://127.0.0.1", "http://localhost"))
    if not SUPA_URL.startswith("https://") and not local:
        sys.exit("CALC_SUPABASE_URL must be the https project URL.")
    # The dashboard address is the one in the browser's address bar while you
    # are looking at the project, so it is the one that gets pasted. It is not
    # the API host, and the app cannot tell: it just decides there is no cloud
    # and falls back to browser-local storage. Everything then looks like it
    # works and no data ever arrives. One build shipped that way.
    if "supabase.com/dashboard" in SUPA_URL or "/project/" in SUPA_URL:
        ref = ""
        for part in SUPA_URL.split("/"):
            if len(part) == 20 and part.isalnum() and part.islower():
                ref = part
                break
        sys.exit(
            "CALC_SUPABASE_URL is the dashboard address, not the API host.\n"
            "  you gave : %s\n"
            "  wanted   : https://%s.supabase.co\n"
            "Supabase dashboard -> Project Settings -> Data API -> Project URL."
            % (SUPA_URL, ref or "<project-ref>"))
    if len(SUPA_KEY) < 20:
        sys.exit("CALC_SUPABASE_ANON_KEY does not look like a key.")
    # A personal access token is not the anon key. It is an account credential
    # -- it manages projects, it does not read rows -- and this file is
    # published, so baking one in hands the account to whoever opens the page.
    # One build did exactly that; GitHub's push protection is what stopped it,
    # which is not a control this project should be relying on.
    if SUPA_KEY.startswith("sbp_"):
        sys.exit(
            "That is a Supabase PERSONAL ACCESS TOKEN (sbp_...), not the anon key.\n"
            "It manages your account, and this file is published, so it must never\n"
            "be built in. Revoke it: Supabase -> Account -> Access Tokens.\n"
            "The key you want is in Project Settings -> Data API -> anon public.")
    if SUPA_KEY.startswith("sb_secret_") or "service_role" in SUPA_KEY:
        sys.exit(
            "That is a SERVICE ROLE key. It bypasses row level security, and this\n"
            "file is published. Use the anon / publishable key instead.")
    # The publishable key is public by design -- it names the project, it
    # grants nothing. Anything else here is a real secret and must not ship.
    # Two formats are current: the newer sb_publishable_ / sb_secret_ pair, and
    # the legacy anon / service_role JWTs, which Supabase deprecates at the end
    # of 2026. Both dangerous halves are refused.
    if "service_role" in SUPA_KEY or SUPA_KEY.startswith("sb_secret_"):
        sys.exit("That is a SECRET key (service_role / sb_secret_). It bypasses\n"
                 "row level security and must never be published. Use the\n"
                 "publishable key (sb_publishable_...) instead.")

    app = read_app()
    os.makedirs(OUT_DIR, exist_ok=True)
    dest = os.path.join(OUT_DIR, "index.html")
    io.open(dest, "w", encoding="utf-8").write(app)

    print("mode        database (Supabase Auth is the login)")
    print("project     %s" % SUPA_URL)
    print("written     calculator/index.html  %d bytes" % len(app.encode("utf-8")))
    print()
    print("The page is plain HTML now: the figures are not in it. They live")
    print("behind row level security, and the anon key above grants nothing")
    print("on its own. Accounts are managed in the Supabase dashboard.")
    return


def main():
    # ONE LOGIN, NEVER TWO.
    #
    # The encryption below exists because a static host has no server to check
    # a password against. A database changes that: Supabase Auth is a real
    # login, checked somewhere the visitor does not control, and it brings
    # per-person accounts, password reset and revoking one person without
    # re-encrypting for everybody.
    #
    # Keeping both would mean the team types two passwords to reach one tool,
    # and the weaker of the two would set the pace. So when the database is
    # configured the page ships as plain HTML and the gate moves to the login
    # form. It stays noindex, nofollow and unlinked; hiding it was never what
    # protected it, and now the figures are not in the file at all -- they are
    # behind row level security on the server.
    if SUPA_URL and SUPA_KEY:
        return build_cloud()

    if not USERS_RAW:
        sys.exit("CALC_USERS is not set.\n"
                 "Credentials are deliberately not stored in this repository —\n"
                 "it is public, so committed passwords would protect nothing.\n\n"
                 "  CALC_USERS='[[\"alice\",\"secret\"],[\"bob\",\"other\"]]' \\\n"
                 "      python3 tools/build-calc.py")
    try:
        users = json.loads(USERS_RAW)
        assert users and all(len(u) == 2 and all(u) for u in users)
    except Exception:
        sys.exit("CALC_USERS must be JSON: [[\"username\",\"password\"], ...]")

    app = read_app()

    port = free_port()
    handler = functools.partial(Quiet, directory=SERVE)
    socketserver.TCPServer.allow_reuse_address = True
    httpd = socketserver.TCPServer(("127.0.0.1", port), handler)
    threading.Thread(target=httpd.serve_forever, daemon=True).start()

    try:
        with sync_playwright() as pw_:
            browser = pw_.chromium.launch()
            page = browser.new_page()
            # WebCrypto needs a secure context; 127.0.0.1 counts as one.
            page.goto("http://127.0.0.1:%d%s/" % (port, PREFIX))
            payload = page.evaluate(ENCRYPT_JS, [app, users, ITERATIONS])
            browser.close()
    finally:
        httpd.shutdown()

    os.makedirs(OUT_DIR, exist_ok=True)
    out = GATE.format(base=BASE, payload=json.dumps(payload),
                      iterations=ITERATIONS)
    dest = os.path.join(OUT_DIR, "index.html")
    io.open(dest, "w", encoding="utf-8").write(out)

    print("plaintext   %7d bytes" % len(app.encode("utf-8")))
    print("ciphertext  %7d bytes (base64)" % len(payload["data"]))
    print("accounts    %7d  (usernames are NOT stored in the output)"
          % len(payload["users"]))
    print("written     calculator/index.html  %d bytes" % len(out))
    print("\nCredentials are not stored anywhere in this repo. Keep them safe —")
    print("without them the published page cannot be decrypted, by anyone.")


if __name__ == "__main__":
    main()
