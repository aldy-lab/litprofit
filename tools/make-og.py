#!/usr/bin/env python3
"""
Renders the Open Graph share cards.

    python3 tools/make-og.py

Cards are screenshotted from a real page in a real browser, using the site's
own stylesheet and its own self-hosted Montserrat — so a card cannot drift
away from the site's typography, and the brand navy comes from the same
custom property everything else uses. Generating them with an image library
would mean re-specifying the design in a second place.

Output: assets/og/*.jpg at 1200x630, the size LinkedIn, Facebook, X, Slack
and WhatsApp all crop from.
"""
import functools
import http.server
import io
import os
import socket
import socketserver
import threading

from playwright.sync_api import sync_playwright

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SERVE = os.path.dirname(ROOT)
PREFIX = "/" + os.path.basename(ROOT)
OUT = os.path.join(ROOT, "assets", "og")

# (slug, eyebrow, headline)
CARDS = [
    ("home", "Klaipeda, Lithuania // since 2010",
     "Ship repair and maintenance all over the world"),
    ("about", "About us", "A Klaipeda ship repair company, working worldwide"),
    ("services", "Services", "What we repair, supply and install"),
    ("refrigeration-systems", "Service 01", "Refrigeration systems and equipment"),
    ("ship-engine-repair", "Service 02", "Ship equipment and engine repair"),
    ("hull-and-piping", "Service 03", "Hull and piping works"),
    ("spare-parts", "Service 04", "Supply of spare parts"),
    ("completed-works", "Completed works", "Where the work has been done"),
    ("partners", "Partners", "We represent BITZER and DANFOSS"),
    ("certificates", "Certificates", "Certification and cover"),
    ("contacts", "Contacts", "Talk to us"),
]

CARD = """<!DOCTYPE html>
<html lang="en"><head>
<meta charset="utf-8">
<link rel="stylesheet" href="{prefix}/css/fonts.css">
<link rel="stylesheet" href="{prefix}/css/style.css">
<style>
  html, body {{ margin: 0; padding: 0; }}
  body {{ width: 1200px; height: 630px; overflow: hidden; }}
  .card {{
    position: relative;
    width: 1200px; height: 630px;
    background:
      radial-gradient(80% 100% at 88% 8%, rgba(45,53,190,0.42), transparent 62%),
      var(--navy-900);
    display: flex; flex-direction: column; justify-content: space-between;
    padding: 62px 68px 56px;
    box-sizing: border-box;
  }}
  /* the same rivet seam the site uses at its section boundaries */
  .card::before {{
    content: ""; position: absolute; top: 0; left: 0; right: 0;
    height: var(--rivet-pitch);
    background-image: var(--rivet);
    background-size: var(--rivet-pitch) var(--rivet-pitch);
    background-repeat: repeat-x;
    opacity: 0.45;
  }}
  .card::after {{
    content: ""; position: absolute; right: -4%; top: 50%;
    transform: translateY(-50%);
    width: 520px; aspect-ratio: 272/200;
    background: var(--mark-img) right center / contain no-repeat;
    opacity: 0.08;
  }}
  .row {{ position: relative; }}
  .lockup {{ height: 42px; width: auto; display: block; }}
  .eyebrow-og {{
    font-size: 15px; font-weight: 500; letter-spacing: 0.26em;
    text-transform: uppercase; color: var(--grey-400); margin: 0 0 26px;
  }}
  h1 {{
    font-size: 74px; line-height: 1.02; letter-spacing: -0.035em;
    font-weight: 700; color: #fff; margin: 0; max-width: 17ch;
    text-wrap: balance;
  }}
  .foot {{
    display: flex; justify-content: space-between; align-items: flex-end;
    font-size: 17px; letter-spacing: 0.16em; text-transform: uppercase;
    color: var(--grey-400);
  }}
  .foot b {{ color: #fff; font-weight: 600; }}
</style></head>
<body><div class="card">
  <div class="row"><img class="lockup" src="{prefix}/assets/brand/logo-lockup.svg" alt=""></div>
  <div class="row">
    <p class="eyebrow-og">{eyebrow}</p>
    <h1>{headline}</h1>
  </div>
  <div class="row foot">
    <span><b>litprofit.com</b></span>
    <span>Klaipeda <span style="opacity:.4">//</span> Lithuania</span>
  </div>
</div></body></html>
"""


def free_port():
    s = socket.socket(); s.bind(("127.0.0.1", 0))
    port = s.getsockname()[1]; s.close(); return port


class Quiet(http.server.SimpleHTTPRequestHandler):
    def log_message(self, *a): pass


def main():
    os.makedirs(OUT, exist_ok=True)
    port = free_port()
    handler = functools.partial(Quiet, directory=SERVE)
    socketserver.TCPServer.allow_reuse_address = True
    httpd = socketserver.TCPServer(("127.0.0.1", port), handler)
    threading.Thread(target=httpd.serve_forever, daemon=True).start()

    tmp = os.path.join(ROOT, "_og-card.html")
    try:
        with sync_playwright() as pw:
            browser = pw.chromium.launch()
            page = browser.new_context(
                viewport={"width": 1200, "height": 630},
                device_scale_factor=1).new_page()

            for i, (slug, eyebrow, headline) in enumerate(CARDS):
                io.open(tmp, "w", encoding="utf-8").write(
                    CARD.format(prefix=PREFIX, eyebrow=eyebrow, headline=headline))
                # cache-bust: the template path never changes, so without a
                # unique query the browser re-serves the previous card and every
                # image comes out identical
                page.goto("http://127.0.0.1:%d%s/_og-card.html?c=%d" % (port, PREFIX, i),
                          wait_until="networkidle")
                page.wait_for_timeout(220)   # let the webfont settle
                dest = os.path.join(OUT, slug + ".jpg")
                page.screenshot(path=dest, type="jpeg", quality=88)
                print("%-26s %6d bytes" % (slug + ".jpg", os.path.getsize(dest)))
            browser.close()
    finally:
        if os.path.exists(tmp):
            os.remove(tmp)
        httpd.shutdown()


if __name__ == "__main__":
    main()
