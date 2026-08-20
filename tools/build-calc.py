#!/usr/bin/env python3
"""
Builds the password-protected project calculator.

    CALC_PASSWORD='...' python3 tools/build-calc.py

WHY ENCRYPTION AND NOT A LOGIN FORM
-----------------------------------
GitHub Pages serves static files; there is no server to check a password
against. A JavaScript gate that compares a typed string and then reveals a
hidden <div> is theatre — the content is already in the file, and "View
source" walks straight past it.

So the calculator is encrypted instead. The published page contains only
ciphertext plus the code to decrypt it. Without the passphrase there is
genuinely nothing to read, not merely nothing displayed.

  key         PBKDF2-HMAC-SHA256, 310,000 iterations, 16-byte random salt
  cipher      AES-256-GCM, 12-byte random IV
  integrity   GCM's own tag — a wrong password fails to authenticate rather
              than yielding garbage

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

BASE = "/litprofit"          # keep in step with tools/build.py
OUT_DIR = os.path.join(ROOT, "calculator")
ITERATIONS = 310000

PASSWORD = os.environ.get("CALC_PASSWORD", "")

ENCRYPT_JS = """async ([plaintext, password, iterations]) => {
  const enc = new TextEncoder();
  const salt = crypto.getRandomValues(new Uint8Array(16));
  const iv = crypto.getRandomValues(new Uint8Array(12));
  const base = await crypto.subtle.importKey(
    'raw', enc.encode(password), 'PBKDF2', false, ['deriveKey']);
  const key = await crypto.subtle.deriveKey(
    {name:'PBKDF2', salt, iterations, hash:'SHA-256'},
    base, {name:'AES-GCM', length:256}, false, ['encrypt']);
  const ct = await crypto.subtle.encrypt(
    {name:'AES-GCM', iv}, key, enc.encode(plaintext));
  const b64 = b => btoa(String.fromCharCode(...new Uint8Array(b)));
  return {salt: b64(salt), iv: b64(iv), data: b64(ct)};
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
  :root{{
    --navy-900:#070824; --surface:#0c0e30;
    --ink-1:#fff; --ink-2:#b0b3c4; --ink-3:#6b6e85;
    --line:rgba(255,255,255,.10); --line-2:rgba(255,255,255,.22);
    --accent:#9ec9ff; --bad:#ff9a9a;
    --font:"Montserrat","Montserrat Fallback",system-ui,-apple-system,sans-serif;
    --mono:ui-monospace,SFMono-Regular,Menlo,monospace;
  }}
  *{{box-sizing:border-box}}
  body{{
    margin:0;min-height:100vh;display:grid;place-items:center;padding:24px;
    background:var(--navy-900);color:var(--ink-1);font-family:var(--font);
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
    background:#fff;color:var(--navy-900);border:0;border-radius:2px;cursor:pointer;
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
  <label for="pw">Passphrase</label>
  <input id="pw" type="password" autocomplete="current-password" autofocus>
  <button id="go" type="submit">Unlock</button>
  <p class="note" id="note" role="status" aria-live="polite"></p>
</form>
<script>
/* The page holds ciphertext only. A wrong passphrase fails AES-GCM's
   authentication tag, so it errors rather than producing plausible rubbish. */
var PAYLOAD = {payload};
var ITER = {iterations};

var f = document.getElementById('gate'),
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
  if (!pw.value) return;
  go.disabled = true;
  note.className = 'note';
  note.textContent = 'Deriving key\\u2026';
  try {{
    var enc = new TextEncoder();
    var base = await crypto.subtle.importKey(
      'raw', enc.encode(pw.value), 'PBKDF2', false, ['deriveKey']);
    var key = await crypto.subtle.deriveKey(
      {{name:'PBKDF2', salt:b2a(PAYLOAD.salt), iterations:ITER, hash:'SHA-256'}},
      base, {{name:'AES-GCM', length:256}}, false, ['decrypt']);
    var plain = await crypto.subtle.decrypt(
      {{name:'AES-GCM', iv:b2a(PAYLOAD.iv)}}, key, b2a(PAYLOAD.data));
    var html = new TextDecoder().decode(plain);
    /* document.write, not innerHTML: scripts injected through innerHTML never
       execute, and the calculator is almost entirely script. */
    document.open();
    document.write(html);
    document.close();
  }} catch (err) {{
    go.disabled = false;
    note.className = 'note bad';
    note.textContent = 'Wrong passphrase.';
    pw.select();
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


def main():
    if not PASSWORD:
        sys.exit("CALC_PASSWORD is not set.\n"
                 "The passphrase is deliberately not stored in this repository —\n"
                 "it is public, so a committed password would protect nothing.\n\n"
                 "  CALC_PASSWORD='your passphrase' python3 tools/build-calc.py")

    app = io.open(os.path.join(ROOT, "tools", "calc", "app.html"),
                  encoding="utf-8").read().replace("__BASE__", BASE)

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
            payload = page.evaluate(ENCRYPT_JS, [app, PASSWORD, ITERATIONS])
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
    print("written     calculator/index.html  %d bytes" % len(out))
    print("\nThe passphrase is not stored anywhere in this repo. Keep it safe —")
    print("without it the published page cannot be decrypted, by anyone.")


if __name__ == "__main__":
    main()
