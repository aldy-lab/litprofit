#!/usr/bin/env python3
"""
Audits the built site with real device emulation.

    python3 tools/audit.py

Serves the repo root, because the site is served from litprofit.com itself and
every absolute URL now starts at /. It used to serve the PARENT directory to
reproduce the /litprofit/ project path; testing under a prefix the live site
no longer has would make every absolute URL a false 404.

Checks, per page:
  structure   one <h1>, no heading-level jumps, no img without alt, no link
              without an accessible name, no duplicate ids, no JS errors
  links       every internal href resolves to a file that exists
  mobile      at 360/375/390/412/430 x DPR 3 with touch: no horizontal
              overflow, no tap target under 24px (WCAG 2.2), no text field
              under 16px (below that, iOS Safari zooms on focus)
"""
import functools
import http.server
import io
import re
import os
import socket
import socketserver
import sys
import threading

from playwright.sync_api import sync_playwright

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SERVE = ROOT
PREFIX = ""

BASE_PATHS = ["/", "/about/", "/services/", "/services/ship-engine-repair/",
              "/services/refrigeration-systems/", "/services/hull-and-piping/",
              "/services/spare-parts/", "/completed-works/", "/partners/",
              "/certificates/", "/contacts/", "/careers/", "/privacy/"]

# Completed jobs come from the same list the build reads, for the same reason
# the languages do. The list is empty today, so this adds nothing; the first
# job added starts being swept without anyone remembering to come here.
import i18n as _i18n_p
BASE_PATHS += ["/completed-works/%s/" % _pr["slug"] for _pr in _i18n_p.PROJECTS]

# Every page in every language. A translation that only half-renders is still a
# broken page, so they all get the same structural and mobile checks.
#
# The languages come from i18n rather than a list of their own. They were
# written out here as ("", "/lt", "/ru"), and the moment Russian was switched
# off the audit spent its run reporting 404s for pages the site had correctly
# stopped building -- a second copy of a fact is a second thing to forget.
import i18n as _i18n


def _published():
    """Every URL the build actually published, from the sitemap it wrote.

    BASE_PATHS above is a hand-written list, which is the third copy of this
    fact in this file after the languages and the completed jobs -- and this
    file argues against exactly that, twice, in the comments above. It caught
    up with itself: a new page was added, the audit reported the same 27 as
    before, and the number not moving was the only sign that the new page had
    never been opened. A PASS over a list that does not include the page you
    just wrote is worse than no PASS at all.

    The sitemap is written by the same build from the same page table, so
    anything published is swept without anybody remembering to come here. If
    it is missing -- audit run before a build -- fall back to the list, which
    is stale but better than sweeping nothing.
    """
    sm = os.path.join(ROOT, "sitemap.xml")
    if not os.path.exists(sm):
        return None
    xml = io.open(sm, encoding="utf-8").read()
    out, seen = [], set()
    for loc in re.findall(r"<loc>([^<]+)</loc>", xml):
        path = re.sub(r"^https?://[^/]+", "", loc.strip()) or "/"
        if path not in seen:
            seen.add(path)
            out.append(path)
    return out or None


PATHS = _published()
if PATHS is None:
    PATHS = []
    for _lang in [""] + ["/" + lg for lg in _i18n.LANGS if lg != "en"]:
        PATHS += [_lang + p for p in BASE_PATHS]
    print("sitemap.xml not found -- sweeping the hand-written list instead.")
PATHS.append("/404.html")

WIDTHS = [360, 375, 390, 412, 430]

problems = []


def fail(page, msg):
    problems.append("%-38s %s" % (page, msg))


def free_port():
    s = socket.socket()
    s.bind(("127.0.0.1", 0))
    p = s.getsockname()[1]
    s.close()
    return p


class Quiet(http.server.SimpleHTTPRequestHandler):
    def log_message(self, *a):
        pass


STRUCTURE_JS = """() => {
  const out = {h1: 0, headings: [], noAlt: [], noName: [], dupIds: [], hrefs: []};
  out.h1 = document.querySelectorAll('h1').length;
  document.querySelectorAll('h1,h2,h3,h4,h5,h6').forEach(h => {
    out.headings.push({level: +h.tagName[1], text: h.textContent.trim().slice(0, 40)});
  });
  document.querySelectorAll('img').forEach(i => {
    if (!i.hasAttribute('alt')) out.noAlt.push(i.getAttribute('src') || '(no src)');
  });
  document.querySelectorAll('a').forEach(a => {
    const name = (a.textContent || '').trim() ||
                 a.getAttribute('aria-label') ||
                 (a.querySelector('img') || {}).alt || '';
    if (!name.trim()) out.noName.push(a.getAttribute('href') || '(no href)');
    const h = a.getAttribute('href');
    if (h) out.hrefs.push(h);
  });
  const seen = new Set();
  document.querySelectorAll('[id]').forEach(el => {
    if (seen.has(el.id)) out.dupIds.push(el.id);
    seen.add(el.id);
  });
  return out;
}"""

MOBILE_JS = """() => {
  const out = {scrollW: document.documentElement.scrollWidth,
               clientW: document.documentElement.clientWidth,
               wide: [], small: [], tiny: []};
  const cw = document.documentElement.clientWidth;
  document.querySelectorAll('*').forEach(el => {
    const r = el.getBoundingClientRect();
    if (r.width === 0 && r.height === 0) return;
    if (r.right > cw + 1) {
      const cs = getComputedStyle(el);
      if (cs.visibility !== 'hidden' && cs.display !== 'none' && cs.opacity !== '0') {
        out.wide.push(el.tagName.toLowerCase() +
          (el.className && typeof el.className === 'string'
            ? '.' + el.className.trim().split(/\\s+/).join('.') : '') +
          ' right=' + Math.round(r.right));
      }
    }
  });
  document.querySelectorAll('a, button, input, select, textarea').forEach(el => {
    const cs = getComputedStyle(el);
    if (cs.display === 'none' || cs.visibility === 'hidden') return;
    const r = el.getBoundingClientRect();
    if (r.width === 0 && r.height === 0) return;
    const label = el.tagName.toLowerCase() +
      ((el.textContent || '').trim().slice(0, 22) || el.type || '');
    if (r.height < 24 || r.width < 24) {
      out.small.push(label + ' ' + Math.round(r.width) + 'x' + Math.round(r.height));
    }
    if (/^(INPUT|TEXTAREA|SELECT)$/.test(el.tagName) && parseFloat(cs.fontSize) < 16) {
      out.tiny.push(label + ' ' + cs.fontSize);
    }
  });
  return out;
}"""


def main():
    port = free_port()
    handler = functools.partial(Quiet, directory=SERVE)
    # Threading, not TCPServer. A browser opens several connections to one
    # page and a single-threaded server serves them one at a time; with
    # keep-alive holding a socket, the next request waits behind it and
    # `networkidle` never arrives. The audit then fails as a 30-second
    # timeout on whichever page happened to be next, which reads as a broken
    # page rather than as a broken harness -- it hung on /contacts/ first,
    # and /contacts/ was fine.
    http.server.ThreadingHTTPServer.allow_reuse_address = True
    httpd = http.server.ThreadingHTTPServer(("127.0.0.1", port), handler)
    threading.Thread(target=httpd.serve_forever, daemon=True).start()
    base = "http://127.0.0.1:%d%s" % (port, PREFIX)
    print("serving %s at %s\n" % (SERVE, base))

    with sync_playwright() as pw:
        browser = pw.chromium.launch()

        # ---------- structure, desktop ----------
        ctx = browser.new_context(viewport={"width": 1440, "height": 900})
        page = ctx.new_page()
        errors = []
        page.on("pageerror", lambda e: errors.append(str(e)))
        page.on("console", lambda m: errors.append(m.text) if m.type == "error" else None)

        for p in PATHS:
            del errors[:]
            url = base + p
            resp = page.goto(url, wait_until="networkidle")
            if resp and resp.status >= 400:
                fail(p, "HTTP %d" % resp.status)
                continue

            r = page.evaluate(STRUCTURE_JS)

            if r["h1"] != 1:
                fail(p, "expected exactly one <h1>, found %d" % r["h1"])

            prev = 0
            for h in r["headings"]:
                if prev and h["level"] > prev + 1:
                    fail(p, "heading jumps h%d -> h%d at %r"
                         % (prev, h["level"], h["text"]))
                prev = h["level"]

            for s in r["noAlt"]:
                fail(p, "img without alt: %s" % s)
            for s in r["noName"]:
                fail(p, "link without accessible name: %s" % s)
            for s in set(r["dupIds"]):
                fail(p, "duplicate id: %s" % s)
            for e in errors:
                fail(p, "JS error: %s" % e[:100])

            # internal links must resolve on disk
            for h in set(r["hrefs"]):
                if h.startswith(("http", "mailto:", "tel:", "#")):
                    continue
                if not h.startswith(PREFIX + "/"):
                    fail(p, "link missing base prefix: %s" % h)
                    continue
                rel = h[len(PREFIX) + 1:].split("#")[0].split("?")[0]
                target = os.path.join(ROOT, rel)
                if rel.endswith("/") or rel == "":
                    target = os.path.join(target, "index.html")
                if not os.path.exists(target):
                    fail(p, "dead link: %s" % h)

        ctx.close()

        # ---------- mobile ----------
        # Chrome's headless window clamps around 500px, so these widths cannot
        # be tested by resizing a desktop window — they need a device context.
        for w in WIDTHS:
            ctx = browser.new_context(
                viewport={"width": w, "height": 800},
                device_scale_factor=3, is_mobile=True, has_touch=True)
            page = ctx.new_page()
            for p in PATHS:
                page.goto(base + p, wait_until="networkidle")
                r = page.evaluate(MOBILE_JS)
                if r["scrollW"] > r["clientW"] + 1:
                    fail("%s @%d" % (p, w), "horizontal overflow: scrollW=%d clientW=%d"
                         % (r["scrollW"], r["clientW"]))
                    for el in r["wide"][:5]:
                        fail("%s @%d" % (p, w), "  overflowing: %s" % el)
                for s in r["small"][:6]:
                    fail("%s @%d" % (p, w), "tap target under 24px: %s" % s)
                for s in r["tiny"][:6]:
                    fail("%s @%d" % (p, w), "field under 16px (iOS zooms): %s" % s)
            ctx.close()

        # ---------- the interactive pieces actually respond ----------
        # These fail silently: the markup renders, nothing throws, the controls
        # simply stop doing anything. The drawing's handler was lost once to an
        # unrelated edit and no existing check noticed, so behaviour is asserted
        # here rather than assumed.
        ctx = browser.new_context(viewport={"width": 1440, "height": 980})
        page = ctx.new_page()
        page.goto(base + "/", wait_until="networkidle")
        page.wait_for_timeout(300)

        part = page.locator('.part[data-prt="screw"]')
        if part.count() == 0:
            fail("drawing", "no parts list on the general arrangement")
        else:
            part.hover()
            page.wait_for_timeout(350)
            if page.locator("#drawing").get_attribute("data-active") != "screw":
                fail("drawing", "hovering a part does not light it in the drawing")
            if part.get_attribute("aria-expanded") != "true":
                fail("drawing", "hovering a part does not open its description")

        # The work light. Back to the top first: hovering a part above scrolled
        # the page to the drawing, and bounding_box() is in VIEWPORT
        # coordinates — from down there the hero's box is off-screen and the
        # click lands nowhere near it. This check reported a broken lamp for
        # that reason alone.
        page.evaluate("() => window.scrollTo(0, 0)")
        page.wait_for_timeout(400)
        hero = page.locator(".hero")
        box = hero.bounding_box()
        page.mouse.dblclick(box["x"] + box["width"] * 0.8, box["y"] + box["height"] * 0.4)
        page.wait_for_timeout(400)
        if not hero.evaluate("el => el.classList.contains('is-lamp')"):
            fail("work light", "double-clicking the hero does not switch the lamp on")
        if page.evaluate("() => String(getSelection())").strip():
            fail("work light", "double-click leaves a text selection behind")
        ctx.close()

        # ---------- the mobile menu actually works ----------
        ctx = browser.new_context(viewport={"width": 390, "height": 800},
                                  device_scale_factor=3, is_mobile=True, has_touch=True)
        page = ctx.new_page()
        page.goto(base + "/", wait_until="networkidle")
        burger = page.locator(".burger")
        if burger.count() == 0:
            fail("menu", "no burger at 390px")
        else:
            burger.tap()
            page.wait_for_timeout(400)
            if burger.get_attribute("aria-expanded") != "true":
                fail("menu", "aria-expanded did not become true")
            if not page.locator(".nav-links").evaluate(
                    "el => el.classList.contains('is-open')"):
                fail("menu", "menu did not open")
            if page.evaluate("() => document.body.style.overflow") != "hidden":
                fail("menu", "body scroll not locked while menu is open")
            burger.tap()
            page.wait_for_timeout(400)
            if page.evaluate("() => document.body.style.overflow") == "hidden":
                fail("menu", "body scroll not restored after closing")
        ctx.close()

        browser.close()

    httpd.shutdown()

    print("=" * 74)
    if problems:
        print("%d PROBLEM(S)\n" % len(problems))
        for p in problems:
            print("  " + p)
        sys.exit(1)
    print("PASS — %d pages x %d widths, no problems found."
          % (len(PATHS), len(WIDTHS)))


if __name__ == "__main__":
    main()
