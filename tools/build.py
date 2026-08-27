#!/usr/bin/env python3
"""
Builds the whole LITPROFIT site: every page, the sitemap and robots.txt.

    python3 tools/build.py

Unlike the ALPROJECTS site — where the sub-pages were generated from the
chrome in a hand-written index.html — everything here is generated, index
included. That is what makes BASE (below) work: the site has to be able to
serve both from a GitHub project URL (/litprofit/...) and from the bare
domain, and a half-generated site cannot switch between the two.

The output is committed, so nothing has to run to serve the site.
"""
import datetime
import html as _html
import io
import json
import hashlib
import os
import re

import i18n

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

# ============================================================
# SITE CONFIG
# ============================================================

# GitHub Pages serves this repo at aldy-lab.github.io/litprofit/, so every
# absolute path needs that prefix. When the real domain is pointed at the
# repo, set BASE = "" and ORIGIN to the domain, add the CNAME file, and
# rebuild — that is the whole migration.
BASE = "/litprofit"
ORIGIN = "https://aldy-lab.github.io"

NAME = "LITPROFIT"
LEGAL = 'UAB "Litprofit"'
TAGLINE = "Ship Repair and Maintenance All Over the World"

PHONE = "+370 670 20 357"
PHONE_HREF = "+37067020357"
EMAIL = "info@litprofit.com"
# The postal address lives in i18n.py now, one entry per language: a Lithuanian
# company writing its own street as "Svajones str." on its Lithuanian page --
# English abbreviation, no diacritics -- reads careless to exactly the people it
# is meant to convince. STREET/CITY/COUNTRY remain for the machine-readable
# JSON-LD and the OG cards, which are language-neutral and take the register's
# own spelling.
#
# The number is 30, not 3. The client's own site says 30 in English and 3 in
# Lithuanian and Russian; the register settles it -- see the README.
STREET = "Svajonės g. 30"
CITY = "LT-94101 Klaipėda"
COUNTRY = "Lithuania"
COMPANY_ID = "302568798"
VAT = "LT100005766815"
FOUNDED = "2010"

# The company presentation. Drop the file in assets/docs/ and put its filename
# here; leave it "" and nothing renders -- no block on the about page, no
# footer link, no empty container. Same rule as every other pending value on
# this site: the worst case is a missing link, never a broken one. The file is
# also checked for on disk, so a filename typed here that is not there behaves
# exactly like a blank.
PRESENTATION = "litprofit-presentation.pdf"

# The lockup is the supplied monogram plus the supplied wordmark, both as
# outlined paths — so no font is loaded, no web licence is needed, and the
# lettering is pixel-identical everywhere. Set LOGO_LOCKUP to "" to fall back
# to mark + the name set in the site typeface.
LOGO_MARK = "/assets/brand/logo-mark-white.svg"
LOGO_LOCKUP = "/assets/brand/logo-lockup.svg"

# Header call-to-action. Set this to the company's Calendly link and the
# button points at it; while it is empty the button falls back to the
# contacts page, so nothing dead ever ships.
BOOKING_URL = "https://calendly.com/rf-litprofit/30min"
# The label is translated per language in tools/i18n.py ("book").
# Only the URL is configured here.

# The studio credit in the footer. Leave ALDY_URL empty and the credit is
# rendered as plain text plus the mark, with no dead link.
ALDY_URL = "https://aldystudio.com"

LASTMOD = datetime.date.today().isoformat()

# The language currently being generated. Set once per pass in the build loop;
# u() and every page builder read it. A module global rather than a parameter
# threaded through forty call sites.
LANG = "en"


def T(key, **kw):
    """A UI string in the current language, with optional interpolation."""
    v = i18n.S[LANG][key]
    return v % kw if kw else v


def PT(key, **kw):
    """A page string in the current language."""
    v = i18n.P[LANG][key]
    return v % kw if kw else v


def lang_prefix(lang=None):
    lang = lang or LANG
    return "" if lang == "en" else "/" + lang


# Paths that are the same file whatever the language. Everything else is a page
# and gets the language prefix, so no call site has to know the difference.
#
# /calculator/ is built once by tools/build-calc.py and translates itself at
# runtime from its own language picker -- there is no /lt/calculator/ to point
# at, and the footer link went straight to one until this line existed.
SHARED = ("/assets/", "/css/", "/js/", "/sitemap.xml", "/robots.txt", "/404.html",
          "/calculator/")


def asset(path):
    """A site-absolute asset URL with the file's own content stamped into it.

    GitHub Pages serves css and js with max-age=600, and the browser caches
    them independently of the HTML. Ship markup that needs new rules and for
    the next ten minutes a returning visitor gets the new page with the old
    stylesheet: on this site that put the compressor canvas back to its
    default 300x150 in the corner and dropped every caption to unstyled text.
    It looked exactly like a build that had gone wrong, and nothing was wrong
    with the build. The hash changes when the file does, so the URL changes
    when the file does, and a stale copy can no longer be found.
    """
    full = os.path.join(ROOT, path.lstrip("/"))
    try:
        with open(full, "rb") as f:
            h = hashlib.sha1(f.read()).hexdigest()[:10]
    except OSError:
        return u(path)
    return "%s?v=%s" % (u(path), h)


def u(path):
    """Site-absolute URL, honouring BASE and the current language.

    Assets are shared between languages; pages are not. Deciding that here
    rather than at each call site is what kept the language switch from
    touching every template."""
    if path.startswith(SHARED):
        return (BASE + path) if BASE else path
    pre = BASE + lang_prefix()
    if path == "/":
        return (pre + "/") if pre else "/"
    return pre + path


def img_size(rel):
    """(width, height) read out of the file itself.

    The certificate thumbnails carried hand-written heights in the CERTIFICATES
    table, and the moment the generator changed width those numbers described
    files that no longer existed -- the browser would have reserved the wrong
    box and the page would have shifted as they loaded. Numbers that describe a
    file belong to the file.

    Parses the WebP header rather than importing Pillow, so the site build
    keeps its only dependency being Python itself; the image tools that need
    Pillow are run by hand and separately."""
    path = os.path.join(ROOT, rel.lstrip("/"))
    with open(path, "rb") as fh:
        d = fh.read(32)
    if d[:4] != b"RIFF" or d[8:12] != b"WEBP":
        raise ValueError("not a WebP: %s" % rel)
    fmt = d[12:16]
    if fmt == b"VP8X":
        w = int.from_bytes(d[24:27], "little") + 1
        h = int.from_bytes(d[27:30], "little") + 1
    elif fmt == b"VP8L":
        b0, b1, b2, b3 = d[21], d[22], d[23], d[24]
        w = ((b1 & 0x3F) << 8 | b0) + 1
        h = ((b3 & 0x0F) << 10 | b2 << 2 | (b1 & 0xC0) >> 6) + 1
    elif fmt == b"VP8 ":
        w = int.from_bytes(d[26:28], "little") & 0x3FFF
        h = int.from_bytes(d[28:30], "little") & 0x3FFF
    else:
        raise ValueError("unknown WebP chunk %r in %s" % (fmt, rel))
    return w, h


def canonical(path):
    return ORIGIN + u(path)


def lang_url(lang, path):
    # 404.html exists once, at the root — GitHub Pages serves it for any
    # unmatched path on the host. Pointing the switcher or hreflang at
    # /lt/404.html would be pointing at a file that does not exist.
    if path == "/404.html":
        path = "/"
    pre = BASE + lang_prefix(lang)
    if path == "/":
        return ORIGIN + ((pre + "/") if pre else "/")
    return ORIGIN + pre + path


def alternates(path):
    """hreflang for every language, plus x-default pointing at English.

    Without these three languages of the same page compete with each other in
    search results instead of being understood as translations."""
    out = []
    for lg in i18n.LANGS:
        out.append('  <link rel="alternate" hreflang="%s" href="%s">'
                   % (i18n.LOCALE[lg][0], lang_url(lg, path)))
    out.append('  <link rel="alternate" hreflang="x-default" href="%s">'
               % lang_url("en", path))
    return "\n".join(out) + "\n"




def lockup():
    """The brand lockup: monogram + name."""
    if LOGO_LOCKUP:
        return '<img class="brand-lockup" src="%s" alt="%s" width="637" height="100">' % (
            u(LOGO_LOCKUP), NAME)
    # alt="" on the mark: the adjacent text already names the company, and a
    # second "LITPROFIT" would be read out twice by a screen reader.
    return ('<img class="brand-mark" src="%s" alt="" width="272" height="200">'
            '<span class="brand-word">%s</span>' % (u(LOGO_MARK), NAME))


def attr(v):
    """Escape a value going into an HTML attribute.

    LEGAL is 'UAB "Litprofit"' — raw double quotes, which silently terminate a
    content="..." attribute. Unescaped, the homepage shipped a meta description
    four characters long ("UAB ") and five pages were affected. Anything
    interpolated into an attribute goes through here."""
    return _html.escape(str(v), quote=True)


def text(v):
    """Escape a value going into element text (no quote escaping needed)."""
    return _html.escape(str(v), quote=False)


# ============================================================
# NAVIGATION
# ============================================================


def nav_items():
    return i18n.NAV[LANG]


def lang_switch(path):
    """The language switcher. Each link goes to the SAME page in the other
    language, not to its homepage — dumping a reader back at the top is the
    usual way these get it wrong."""
    out = []
    for lg in i18n.LANGS:
        cur = ' aria-current="true"' if lg == LANG else ""
        href = lang_url(lg, path).replace(ORIGIN, "") or "/"
        out.append('<a href="%s" hreflang="%s" lang="%s"%s>%s</a>'
                   % (href, i18n.LOCALE[lg][0], i18n.LOCALE[lg][0], cur, i18n.LABEL[lg]))
    # --n so the sliding indicator's width and travel are arithmetic on the
    # number of languages rather than a hard-coded half. Switch Russian back on
    # and the pill becomes a third the width and moves in thirds; nothing in the
    # stylesheet has to be found and changed.
    idx = list(i18n.LANGS).index(LANG)
    return ('<div class="langs" role="group" aria-label="%s" style="--n:%d;--i:%d">%s</div>'
            % (attr(T("lang_label")), len(i18n.LANGS), idx, "".join(out)))


def header(active, path="/"):
    items = "\n".join(
        '        <a href="%s"%s>%s</a>' % (
            u(href), ' aria-current="page"' if href == active else "", label)
        for label, href in nav_items())
    return """  <a class="skip-link" href="#main">{skip}</a>

  <header class="site-header">
    <nav class="nav" aria-label="Main">
      <a class="brand" href="{home}" aria-label="{name} — home">{logo}</a>

      <div class="nav-links" id="navLinks">
{items}
        <a class="nav-cta-mobile" href="{book}"{book_attrs}>{book_label}</a>
        {langs}
      </div>

      <div class="nav-actions">
        {langs_desktop}
        <a class="btn btn-book" href="{book}"{book_attrs}>{book_label}</a>
        <button class="burger" type="button" aria-label="{menu}"
                aria-expanded="false" aria-controls="navLinks">
          <span></span><span></span><span></span>
        </button>
      </div>
      <span class="progress" aria-hidden="true"></span>
    </nav>
  </header>""".format(home=u("/"), logo=lockup(),
                      name=NAME, items=items,
                      book=BOOKING_URL or u("/contacts/"),
                      book_attrs=(' target="_blank" rel="noopener" data-book'
                                  if BOOKING_URL else ""),
                      book_label=attr(T("book")), skip=T("skip"), menu=attr(T("menu")),
                      langs=lang_switch(path), langs_desktop=lang_switch(path))


# The staff calculator. Followed the same rule as the booking link: blank and
# the link is not rendered at all, so it can be taken back off the site without
# leaving a dead entry in the footer.
#
# rel="nofollow" alongside the page's own noindex. Linking it publicly makes it
# findable, which is the point of asking for it -- what keeps the figures safe
# is the sign-in and row level security, never the fact that nobody had the
# address.
CALCULATOR_URL = "/calculator/"


def pres_link():
    """The presentation in the footer nav, or nothing. Same rule as calc_link."""
    pr = presentation()
    if not pr:
        return ""
    return ('            <li><a href="%s" download>%s</a></li>\n'
            % (attr(pr[0]), text(T("pres_title"))))


def calc_link():
    if not CALCULATOR_URL:
        return ""
    href = u(CALCULATOR_URL) if CALCULATOR_URL.startswith("/") else CALCULATOR_URL
    return ('<a href="%s" rel="nofollow" class="foot-calc">%s</a>'
            % (attr(href), text(T("f_calc"))))


def aldy_credit():
    mark = ('<img src="%s" alt="" width="709" height="709">'
            % u("/assets/brand/aldy.svg"))
    inner = '%s<span>Made by <b>ALDY</b></span>' % mark
    if ALDY_URL:
        return ('<a class="aldy" href="%s" target="_blank" rel="noopener">%s</a>'
                % (ALDY_URL, inner))
    return '<span class="aldy">%s</span>' % inner


FOOTER_TPL = """  <footer class="site-footer">
    <div class="container">
      <div class="footer-top">
        <div class="footer-col footer-brand">
          <div class="brand">{logo}</div>
          <p>{tagline}</p>
        </div>

        <div class="footer-col">
          <h2 class="col-title">{f_address}</h2>
          <p>{street}<br>{city}<br>{country}</p>
        </div>

        <div class="footer-col">
          <h2 class="col-title">{f_contacts}</h2>
          <ul>
            <li><a href="tel:{phone_href}">{phone}</a></li>
            <li><a href="mailto:{email}">{email}</a></li>
          </ul>
        </div>

        <div class="footer-col">
          <h2 class="col-title">{f_details}</h2>
          <p>{legal}<br>{l_cid}: {cid}<br>{l_vat}: {vat}</p>
        </div>

        <div class="footer-col">
          <h2 class="col-title">{f_site}</h2>
          <ul>
{navlinks}
{preslink}          </ul>
        </div>
      </div>

      <div class="footer-bottom">
        <span>&copy; {founded}&ndash;<span data-year>2026</span> {legal}</span>
        <span class="spacer"><a href="{privacy}">{l_privacy}</a>{calc}</span>
        <span class="made">{made}</span>
      </div>
    </div>
  </footer>"""


def footer():
    return FOOTER_TPL.format(
    logo=lockup(), name=NAME, tagline=T("tagline"),
    street=T("addr_street"), city=T("addr_city"), country=T("addr_country"),
    phone=PHONE, phone_href=PHONE_HREF,
    email=EMAIL, legal=LEGAL, cid=COMPANY_ID, vat=VAT, founded=FOUNDED,
    privacy=u("/privacy/"), calc=calc_link(), made=aldy_credit(),
    f_address=T("f_address"), f_contacts=T("f_contacts"), f_details=T("f_details"),
    f_site=T("f_site"), l_privacy=T("f_privacy"), l_cid=T("company_no"), l_vat=T("vat"),
    preslink=pres_link(),
    navlinks="\n".join('            <li><a href="%s">%s</a></li>' % (u(h), l)
                        for l, h in nav_items()))


# The site read as a set of sheets, after the drawing's own title block
# (DWG 04 // 06). Gives every interior page a position in a sequence and
# somewhere obvious to go next, instead of dead-ending at the footer.
def sheets():
    """Home plus the six nav entries, in the language being built."""
    return [("/", T("home"))] + [(h, l) for l, h in nav_items()]


def sheet_index(path):
    for i, (href, _) in enumerate(sheets()):
        if href == path:
            return i
    return None


def sheet_tag(path):
    i = sheet_index(path)
    if i is None:
        return ""
    return ('<span class="eyebrow-num">%02d</span><span class="sep">//</span>'
            % (i + 1))


def pager(path):
    """Previous / next across the sheet set. A dead end at the bottom of a
    page is a navigation failure, not a styling one."""
    i = sheet_index(path)
    if i is None:
        return ""
    sh = sheets()
    prev = sh[i - 1] if i > 0 else None
    nxt = sh[i + 1] if i < len(sh) - 1 else None
    if not prev and not nxt:
        return ""

    def cell(item, rel, label):
        if not item:
            return '<span class="pg-cell pg-empty"></span>'
        href, name = item
        return ("""<a class="pg-cell pg-{rel}" href="{href}" rel="{rel}">
          <span class="pg-dir">{label}</span>
          <span class="pg-name">{name}</span>
        </a>""").format(rel=rel, href=u(href), label=label, name=name)

    return """
    <nav class="pager" aria-label="{aria}">
      <div class="container pg-grid">
        {prev}
        <span class="pg-of">{n} // {total}</span>
        {next}
      </div>
    </nav>
""".format(prev=cell(prev, "prev", T("prev")), next=cell(nxt, "next", T("next")),
           aria=attr(T("sheets")), n="%02d" % (i + 1), total="%02d" % len(sh))


# Share card per page. Anything unmapped falls back to the home card rather
# than to nothing — a summary_large_image declaration with no image renders as
# a blank card on LinkedIn and WhatsApp, which is worse than not declaring one.
OG_SLUGS = {
    "/": "home",
    "/about/": "about",
    "/services/": "services",
    "/services/refrigeration-systems/": "refrigeration-systems",
    "/services/ship-engine-repair/": "ship-engine-repair",
    "/services/hull-and-piping/": "hull-and-piping",
    "/services/spare-parts/": "spare-parts",
    "/completed-works/": "completed-works",
    "/partners/": "partners",
    "/certificates/": "certificates",
    "/contacts/": "contacts",
}


def og_image(path):
    return ORIGIN + u("/assets/og/%s.jpg" % OG_SLUGS.get(path, "home"))


# ============================================================
# PAGE SHELL
# ============================================================
def page(path, title, description, body, head_extra="", noindex=False, active=None):
    full_title = title if title.startswith(NAME) else "%s — %s" % (title, NAME)
    robots = "noindex, follow" if noindex else "index, follow"
    return """<!DOCTYPE html>
<html lang="{htmllang}">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>{full_title_text}</title>
  <meta name="description" content="{description}">
  <link rel="canonical" href="{canon}">
  <meta name="robots" content="{robots}">
  <meta name="theme-color" content="#070824">
  <meta property="og:site_name" content="{name}">
  <meta property="og:title" content="{full_title}">
  <meta property="og:description" content="{description}">
  <meta property="og:type" content="website">
  <meta property="og:url" content="{canon}">
  <meta property="og:locale" content="{oglocale}">
{alts}
  <meta property="og:image" content="{og}">
  <meta property="og:image:width" content="1200">
  <meta property="og:image:height" content="630">
  <meta property="og:image:alt" content="{full_title}">
  <meta name="twitter:card" content="summary_large_image">
  <meta name="twitter:image" content="{og}">
  <link rel="icon" href="{icon}">
  <link rel="preload" as="font" type="font/woff2" href="{font}" crossorigin>
  <link rel="stylesheet" href="{fonts_css}">
  <link rel="stylesheet" href="{style_css}">
  <!-- Marks the document as scripted BEFORE the stylesheet paints, so the
       scroll-reveal rules only ever hide content that JS can bring back.
       Inline and synchronous on purpose: an external file would race. -->
  <script>document.documentElement.className += " js";</script>
{head_extra}</head>
<body>

{header}

  <main id="main">
{body}
{pager}  </main>

{footer}

  <script src="{js}"></script>
</body>
</html>
""".format(full_title=attr(full_title), full_title_text=text(full_title),
           description=attr(description), canon=canonical(path),
           robots=robots, name=NAME, icon=u("/assets/brand/favicon.svg"),
           htmllang=i18n.LOCALE[LANG][0], oglocale=i18n.LOCALE[LANG][1],
           alts=alternates(path),
           font=u("/assets/fonts/montserrat-latin.woff2"),
           fonts_css=asset("/css/fonts.css"), style_css=asset("/css/style.css"),
           js=asset("/js/main.js"), head_extra=head_extra,
           header=header(active if active is not None else path, path), body=body,
           pager=pager(path), footer=footer(), og=og_image(path))


def write(path, html):
    full = os.path.join(ROOT, path)
    d = os.path.dirname(full)
    if d:
        os.makedirs(d, exist_ok=True)
    io.open(full, "w", encoding="utf-8").write(html)
    print("wrote %-44s %6d bytes" % (path, len(html)))


def outfile(url_path):
    """/services/ -> services/index.html, under the language directory."""
    pre = lang_prefix().strip("/")
    rel = "index.html" if url_path == "/" else url_path.strip("/") + "/index.html"
    return os.path.join(pre, rel) if pre else rel


# ============================================================
# SHARED FRAGMENTS
# ============================================================
def cta(heading, text, primary=None, secondary=None):
    primary = primary or (T("cta_enquiry"), "/contacts/")
    secondary = secondary if secondary is not None else (
        T("cta_call") + " " + PHONE, "tel:" + PHONE_HREF)
    sec = ""
    if secondary:
        href = secondary[1] if secondary[1].startswith("tel:") else u(secondary[1])
        sec = '<a class="btn btn-outline" href="%s">%s</a>' % (href, secondary[0])
    return """
    <section class="cta seam-top">
      <div class="container reveal">
        <h2>{heading}</h2>
        <p>{text}</p>
        <div class="btn-row">
          <a class="btn btn-solid" href="{phref}">{ptext}</a>
          {sec}
        </div>
      </div>
    </section>
""".format(heading=heading, text=text, phref=u(primary[1]), ptext=primary[0], sec=sec)


def crumb(trail):
    """trail: [(label, path|None)] — the last item is the current page."""
    parts = []
    for label, href in trail:
        if href:
            parts.append('<a href="%s">%s</a>' % (u(href), label))
        else:
            parts.append("<span>%s</span>" % label)
    return '<p class="crumb">%s</p>' % '<span class="sep">//</span>'.join(parts)


def strip_tags(v):
    """Plain text for JSON-LD. A crumb label is usually a bare string, but some
    come from the same i18n entries the page renders as markup, and a stray
    <span> inside a schema name is invisible until a validator refuses it."""
    return _html.unescape(re.sub(r"<[^>]+>", "", str(v))).strip()


def crumb_ld(trail, path=None):
    """BreadcrumbList for the trail the page already shows.

    Emitted from page_head, off the same `trail` the visible breadcrumb is
    built from, so the two cannot drift apart -- a marked-up trail that
    disagrees with the one on screen is worse than none, and that is exactly
    what happens when the two are maintained separately.

    The last crumb is the current page and carries no href in the trail; Google
    allows the final item to omit `item`, but giving it the canonical is more
    use and costs nothing."""
    if not trail:
        return ""
    items = []
    for i, (label, href) in enumerate(trail, 1):
        node = {"@type": "ListItem", "position": i, "name": strip_tags(label)}
        target = href or path
        if target:
            node["item"] = canonical(target)
        items.append(node)
    return ('  <script type="application/ld+json">\n  %s\n  </script>\n'
            % json.dumps({"@context": "https://schema.org",
                          "@type": "BreadcrumbList",
                          "itemListElement": items}, ensure_ascii=False))


def page_head(eyebrow, h1, lead, trail=None, path=None, wrap=None, aside=None):
    """wrap opens a div the caller closes itself; aside adds a second column.

    Only About uses either, and only so the page title and the compressor can
    be one first screen rather than two. The head measured 610px and the stage
    began at 945, so on desktop, laptop and phone alike not one pixel of the
    machine was above the fold: the page opened on a paragraph about a machine
    and you had to take its word for it.

    Trimming paddings would only have fitted the viewport I measured. What
    actually costs the height is that the page and the section each brought a
    full head -- an 81px h1 and a 58px h2, 388px of type before anything is
    drawn. So the machine's own lead moves up here into a second column beside
    the page lead, where there was empty space anyway, and the section keeps
    its heading at caption scale. Then the head and the stage are one flex
    column of exactly one screen, and the stage takes whatever is left over at
    any height rather than a guess that happens to add up.
    """
    body = """
      {crumb}
      <p class="eyebrow">{sheet}{eyebrow}</p>
      <h1>{h1}</h1>
      <p class="lead">{lead}</p>"""
    if aside:
        body = """
      <div class="page-head-main">
        {crumb}
        <p class="eyebrow">{sheet}{eyebrow}</p>
        <h1>{h1}</h1>
      </div>
      <div class="page-head-aside">
        <p class="lead">{lead}</p>
        <p class="lead lead--sub">%s</p>
      </div>""" % aside
    return ("""
    %s<section class="container page-head%s">""" % (
        '<div class="%s">\n    ' % wrap if wrap else "",
        " page-head--split" if aside else "") + body + """
    </section>
{ld}""").format(crumb=crumb(trail) if trail else "", eyebrow=eyebrow, h1=h1, lead=lead,
           sheet=sheet_tag(path) if path else "", ld=crumb_ld(trail, path))


def tags(items):
    return '<ul class="tags">\n%s\n      </ul>' % "\n".join(
        "        <li>%s</li>" % i for i in items)


# ============================================================
# SERVICES — the content model
# Every equipment name, manufacturer and standard here is carried over
# from litprofit.com verbatim. The prose around them is rewritten; the
# lists are not, because they are the part a customer checks.
# ============================================================
def tags_of(items):
    return tags(items)


def services():
    """The four services in the current language, in display order.

    Numbers are derived from position, so the label on a card cannot disagree
    with where the card actually sits."""
    out = []
    for i, slug in enumerate(i18n.ORDER):
        d = dict(i18n.SVC[LANG][slug])
        f, w, h = i18n.IMG[slug]
        d.update(slug=slug, num="%02d" % (i + 1),
                 img=(f, w, h, i18n.ALT[LANG][slug]))
        d["blocks"] = SERVICE_BLOCKS[slug](d)
        out.append(d)
    return out


def _refrig_blocks(d):
    comps = ["%s &mdash; %s" % (c, n) for c, n in
             zip(i18n.COMPRESSORS, i18n.COUNTRIES[LANG])]
    return [
        (d["h_works"],
         ["<ul>%s</ul>" % "".join("<li>%s</li>" % w for w in d["works"]),
          "<p>%s</p>" % d["note"]]),
        (d["h_compressors"], [tags(comps)]),
        (d["h_systems"], ["<p>%s</p>" % d["sys_note"], tags(i18n.SYSTEMS)]),
    ]


def _engine_blocks(d):
    return [
        (d["h_engines"], ["<p>%s</p>" % d["engines"],
                          "<p>%s</p>" % d["engines_note"], tags(i18n.ENGINES)]),
        (d["h_machinery"], ["<p>%s</p>" % d["machinery"]]),
        (d["h_deck"], ["<p>%s</p>" % d["deck"]]),
        (d["h_how"], ["<p>%s</p>" % d["how"]]),
    ]


def _hull_blocks(d):
    return [
        (d["h_pipes"], ["<p>%s</p>" % d["pipes"], "<p>%s</p>" % d["pipes2"]]),
        (d["h_scope"], ["<p>%s</p>" % d["scope"], "<p>%s</p>" % d["scope2"]]),
    ]


def _parts_blocks(d):
    return [
        (d["h_source"],
         ["<p>%s</p>" % d["intro"],
          "<h3>%s</h3>" % d["h_c"], tags(i18n.PART_COMPRESSORS),
          "<h3>%s</h3>" % d["h_e"], tags(i18n.PART_ENGINES),
          "<h3>%s</h3>" % d["h_p"], tags(i18n.PUMPS),
          "<h3>%s</h3>" % d["h_t"], tags(i18n.TURBO),
          "<h3>%s</h3>" % d["h_o"],
          "<ul>%s</ul>" % "".join("<li>%s</li>" % o for o in d["other"])]),
        (d["h_delivery"], ["<p>%s</p>" % d["delivery"]]),
    ]


SERVICE_BLOCKS = {
    "refrigeration-systems": _refrig_blocks,
    "ship-engine-repair": _engine_blocks,
    "hull-and-piping": _hull_blocks,
    "spare-parts": _parts_blocks,
}

FEATURE_SLUG = i18n.ORDER[0]

# (name, file, intrinsic w, intrinsic h, url, sector key)
# The sector is a claim about someone else's business, so it is only filled in
# where their own site says it. Six are blank until the client confirms them —
# an invented line under a customer's logo is their problem, not ours.
CLIENTS = [
    ("Sealord", "logo-sealord-paua.png", 140, 60, "https://sealord.com", "seafood"),
    ("Limarko Group", "limarko-group.png", 400, 120, "", ""),
    # Reverse artwork, generated by tools/make-reverse-logo.py. The supplied
    # file has a white disc baked in behind the whale, so the CSS knockout
    # flattens it to a blank circle; this one has the plate removed.
    ("Ocean Whale Company", "ocean-whale-company-rev.png", 393, 108, "", ""),
    ("Baltreids", "logo-baltreids.png", 66, 82, "", ""),
    ("Alliance Marine", "logo-alliance-marine.png", 248, 155, "", ""),
    ("Seafish Trade", "logo-seafish-trade.png", 282, 179, "https://seafishtrade.com", "frozenfish"),
    ("Santavilte", "santavilte.png", 400, 89, "https://santavilte.lt", "engineering"),
    ("LZK", "logo-lzk.png", 208, 208, "", ""),
    ("OWH", "logo-owh.png", 246, 161, "", ""),
]

# Read off the documents themselves. Both entries previously carried the date
# 2025-10-21, which is neither certificate's date -- it was the file's. On a
# page whose whole purpose is to make an accreditation checkable, a date that
# does not appear anywhere on the certificate is worse than no date.
CERTIFICATES = [
    dict(name="RINA", file="rina-certificate-2025.pdf", size="329 KB",
         no="REC037725XF", issued="2025-05-08", valid="2028-05-12",
         note="Italian classification society"),
    dict(name="PRS", file="prs-certificate.pdf", size="961 KB",
         no="TM/1703/842502/25", issued="2025-10-15", valid="2028-10-14",
         note="Polish Register of Shipping"),
]



def card(s, level="h3", variant=""):
    """A service card. `level` keeps the document outline continuous: h2 where
    the cards are the page's top-level content, h3 where a section heading
    already sits above them. `variant` is "feature" or "compact"; the grid
    only rearranges itself when one card is marked as the feature."""
    f, w, h, alt = s["img"]
    cls = "card reveal" + (" card--" + variant if variant else "")

    # One file was serving two very different slots: a 1325px banner on the
    # service page and a 148px thumbnail in the compact card here. The card was
    # being handed 1313px of valve photograph to draw 148px of it. A card-width
    # copy goes in the srcset and the browser picks -- which also means a phone,
    # where these cards go full width at 348px, still gets the large file,
    # because there it genuinely needs it.
    card_rel = "assets/photos/%s-card.webp" % f.rsplit(".", 1)[0]
    srcset = ""
    if os.path.exists(os.path.join(ROOT, card_rel)):
        cw, _ = img_size(card_rel)
        # one row of four in a 1392px container
        slot = "330px"
        srcset = (' srcset="%s %dw, %s %dw" sizes="(min-width: 900px) %s, 100vw"'
                  % (u("/" + card_rel), cw, u("/assets/photos/" + f), w, slot))

    return """          <a class="{cls}" href="{href}">
            <span class="card-media">
              <img src="{img}" alt="{alt}" width="{w}" height="{h}" loading="lazy"{srcset}>
            </span>
            <span class="card-body">
              <span class="card-num">{num}</span>
              <{lv}>{title}</{lv}>
              <p>{short}</p>
              <span class="card-more">{more}</span>
            </span>
          </a>""".format(cls=cls, srcset=srcset, href=u("/services/%s/" % s["slug"]),
                         img=u("/assets/photos/" + f),
                         alt=alt, w=w, h=h, lv=level, num=s["num"],
                         title=s["title"], short=s["short"], more=T("read_more"))


# Refrigeration leads: it is the company's original discipline and the one it
# has the deepest bench in, so it gets the feature card rather than being one
# of four equal boxes — and, being first, it is 01.
FEATURE_SLUG = "refrigeration-systems"





def presentation():
    """(url, size in MB) for the company presentation, or None."""
    if not PRESENTATION:
        return None
    rel = "assets/docs/" + PRESENTATION
    full = os.path.join(ROOT, rel)
    if not os.path.exists(full):
        return None
    return u("/" + rel), os.path.getsize(full) / 1e6


def presentation_block():
    """A download row for the presentation, or nothing at all."""
    pr = presentation()
    if not pr:
        return ""
    href, mb = pr
    return """
    <section class="section section-tight">
      <div class="container">
        <a class="doc-row reveal" href="{href}" download>
          <span class="doc-row-num">PDF</span>
          <span class="doc-row-body">
            <span class="doc-row-title">{title}</span>
            <span class="doc-row-note">{note}</span>
          </span>
          <span class="doc-row-size">{mb} MB</span>
        </a>
      </div>
    </section>""".format(href=href, mb=("%.1f" % mb).rstrip("0").rstrip("."),
                         title=text(T("pres_title")), note=text(T("pres_note")))


def service_cards(level="h3"):
    """Four cards, all the same.

    This was one feature card beside a stack of compact ones, on the argument
    that refrigeration is the deepest discipline and the page should say so.
    The page does say so -- it has a whole live compressor two sections down.
    What the mixed sizes actually produced was three thumbnails beside three
    paragraphs, which is a directory listing, and the heading over it says
    "four disciplines, one contractor". Four equal cards is what that sentence
    looks like.
    """
    return "\n".join(card(x, level) for x in services())


def client_tile(c):
    """One client card. Linked where the company's own site was verified.

    The logo sits on a white plate inside the card: these are other companies'
    trademarks, in their own colours, and recolouring them to fit our palette
    is not ours to do."""
    name, f, w, h, url, sector = c
    img = ('<img src="%s" alt="%s" width="%d" height="%d" loading="lazy">'
           % (u("/assets/clients/" + f), name, w, h))
    desc = i18n.SECTORS[LANG].get(sector, "") if sector else ""
    body = ('<span class="cc-plate">%s</span>'
            '<span class="cc-name">%s</span>'
            '<span class="cc-desc">%s</span>' % (img, name, desc or "&nbsp;"))
    if url:
        return ('          <li class="cc"><a href="%s" target="_blank" rel="noopener noreferrer">'
                '%s<span class="cc-go">&#8599;</span></a></li>' % (url, body))
    return '          <li class="cc"><span class="cc-inner">%s</span></li>' % body


# ============================================================
# HERO — MARINE PROVISION REFRIGERATION, P&ID
# A full plant diagram in the style a chief engineer would recognise: two
# compressor sets each with accumulator, oil separator and gauges, two
# seawater-cooled condensers, and three refrigerated spaces at their working
# temperatures, joined by discharge, liquid and suction lines carrying the
# usual run of gate valves, check valves, solenoids, filter driers, sight
# glasses and thermostatic expansion valves.
#
# Repetition is generated, not typed: two identical compressor sets and three
# room coils come from one function each, so the drawing stays editable.
# ============================================================
def hero_drawing(lit=False):
    P = []          # geometry
    add = P.append

    def gate(x, y, vert=False):
        """Gate valve: two triangles meeting at the stem."""
        if vert:
            return ('<g class="rp-sym"><path d="M%d %d L%d %d L%d %d L%d %d Z"/>'
                    '<line x1="%d" y1="%d" x2="%d" y2="%d"/></g>'
                    % (x-8, y-10, x+8, y-10, x-8, y+10, x+8, y+10, x-14, y, x+14, y))
        return ('<g class="rp-sym"><path d="M%d %d L%d %d L%d %d L%d %d Z"/>'
                '<line x1="%d" y1="%d" x2="%d" y2="%d"/></g>'
                % (x-10, y-8, x-10, y+8, x+10, y-8, x+10, y+8, x, y-8, x, y-17))

    def check(x, y):
        """Check valve: seat plus disc."""
        return ('<g class="rp-sym"><path d="M%d %d L%d %d L%d %d Z"/>'
                '<line x1="%d" y1="%d" x2="%d" y2="%d"/></g>'
                % (x-9, y-9, x-9, y+9, x+8, y, x+9, y-10, x+9, y+10))

    def solenoid(x, y):
        return ('<g class="rp-sym"><rect x="%d" y="%d" width="18" height="14"/>'
                '<line x1="%d" y1="%d" x2="%d" y2="%d"/>'
                '<rect x="%d" y="%d" width="12" height="9"/></g>'
                % (x-9, y-7, x, y-7, x, y-20, x-6, y-29))

    def txv(x, y):
        """Thermostatic expansion valve: gate body with a bulb on a capillary."""
        return ('<g class="rp-sym"><path d="M%d %d L%d %d L%d %d L%d %d Z"/>'
                '<line x1="%d" y1="%d" x2="%d" y2="%d"/>'
                '<circle cx="%d" cy="%d" r="5"/></g>'
                % (x-10, y-8, x-10, y+8, x+10, y-8, x+10, y+8,
                   x, y-8, x, y-22, x, y-27))

    def drier(x, y):
        return ('<g class="rp-sym"><rect x="%d" y="%d" width="30" height="14"/>'
                '<line x1="%d" y1="%d" x2="%d" y2="%d"/></g>'
                % (x-15, y-7, x-8, y-7, x+8, y+7))

    def sight(x, y):
        return ('<g class="rp-sym"><circle cx="%d" cy="%d" r="9"/>'
                '<line x1="%d" y1="%d" x2="%d" y2="%d"/></g>'
                % (x, y, x-6, y, x+6, y))

    def gauge(x, y, tag):
        return ('<g class="rp-sym"><circle cx="%d" cy="%d" r="14"/>'
                '<line x1="%d" y1="%d" x2="%d" y2="%d"/></g>'
                '<text class="rp-tag" x="%d" y="%d" text-anchor="middle">%s</text>'
                % (x, y, x, y, x+8, y-9, x, y-22, tag))

    # ---------- compressor set ----------
    def comp_set(x, y, n):
        g = []
        # accumulator
        g.append('<g class="rp-body"><rect x="%d" y="%d" width="52" height="104" rx="24"/></g>' % (x, y+34))
        g.append('<g class="rp-thin"><rect x="%d" y="%d" width="20" height="52" rx="8"/></g>' % (x+16, y+58))
        # compressor block and motor
        g.append('<g class="rp-body"><rect x="%d" y="%d" width="126" height="86" rx="6"/>'
                 '<circle cx="%d" cy="%d" r="26"/></g>' % (x+86, y+50, x+149, y+93))
        g.append('<g class="rp-thin"><circle cx="%d" cy="%d" r="12"/>'
                 '<line x1="%d" y1="%d" x2="%d" y2="%d"/></g>'
                 % (x+149, y+93, x+86, y+72, x+212, y+72))
        # oil separator with level
        g.append('<g class="rp-body"><rect x="%d" y="%d" width="46" height="96" rx="6"/></g>' % (x+232, y+42))
        g.append('<g class="rp-thin"><line x1="%d" y1="%d" x2="%d" y2="%d"/>'
                 '<line x1="%d" y1="%d" x2="%d" y2="%d"/></g>'
                 % (x+232, y+108, x+278, y+108, x+232, y+120, x+278, y+120))
        g.append(gauge(x+110, y+18, "P%d" % (n * 2 - 1)))
        g.append(gauge(x+178, y+18, "P%d" % (n * 2)))
        g.append(sight(x+255, y+156))
        g.append('<text class="rp-lbl" x="%d" y="%d">COMP #%d</text>' % (x+92, y+156, n))
        g.append('<text class="rp-tag" x="%d" y="%d">ACC.%d</text>' % (x, y+156, n))
        g.append('<text class="rp-tag" x="%d" y="%d">O/S%d</text>' % (x+232, y+156, n))
        return "".join(g)

    # ---------- seawater condenser ----------
    def condenser(x, y, n):
        tubes = "".join('<line x1="%d" y1="%d" x2="%d" y2="%d"/>'
                        % (x+18, y+14+i*11, x+338, y+14+i*11) for i in range(5))
        return ('<g class="rp-body"><rect x="%d" y="%d" width="356" height="76" rx="26"/>'
                '<rect x="%d" y="%d" width="22" height="20"/>'
                '<rect x="%d" y="%d" width="22" height="20"/></g>'
                '<g class="rp-thin">%s</g>'
                '<text class="rp-tag" x="%d" y="%d">SEA-WATER COOLED CONDENSER #%d</text>'
                % (x, y, x+54, y-20, x+280, y+76, tubes, x, y+100, n))

    # ---------- refrigerated space ----------
    def room(x, y, w, h, name, temp):
        g = ['<g class="rp-room"><rect x="%d" y="%d" width="%d" height="%d"/></g>' % (x, y, w, h)]
        cx, cy = x + w / 2, y + 74
        # evaporator: finned coil plus fan
        g.append('<g class="rp-body"><rect x="%d" y="%d" width="132" height="40" rx="6"/></g>'
                 % (cx-66, cy-20))
        g.append('<g class="rp-thin">%s</g>' % "".join(
            '<line x1="%d" y1="%d" x2="%d" y2="%d"/>' % (cx-58+i*13, cy-20, cx-58+i*13, cy+20)
            for i in range(11)))
        g.append('<g class="rp-sym"><circle cx="%d" cy="%d" r="15"/>'
                 '<path d="M%d %d L%d %d M%d %d L%d %d"/></g>'
                 % (cx+92, cy, cx+81, cy-11, cx+103, cy+11, cx+81, cy+11, cx+103, cy-11))
        g.append('<text class="rp-room-t" x="%d" y="%d" text-anchor="middle">%s</text>'
                 % (cx, y + h - 46, name))
        g.append('<text class="rp-room-c" x="%d" y="%d" text-anchor="middle">%s</text>'
                 % (cx, y + h - 14, temp))
        return "".join(g)

    # ================= assembly =================
    add(comp_set(70, 96, 1))
    add(comp_set(70, 470, 2))
    add(condenser(70, 320, 1))
    add(condenser(70, 694, 2))

    add(room(760, 96, 340, 300, i18n.ROOMS[LANG][0], "+2 &#176;C"))
    add(room(1150, 96, 380, 300, i18n.ROOMS[LANG][1], "&minus;20 &#176;C"))
    add(room(1150, 470, 380, 300, i18n.ROOMS[LANG][2], "+17 &#176;C"))

    def pipe(kind, d, i):
        """The run, plus a twin that carries a travelling pip along it.

        Two paths rather than dashing the pipe itself: on a P&ID a dashed line
        is not decoration, it means a different service or a future run, so
        making the live pipes dashed would be saying something untrue about the
        plant. The pipe stays solid and the pip rides over it.

        Every `d` here is written from source to destination -- discharge
        leaves the compressors, liquid leaves the condensers, suction returns
        to the accumulators -- so one animation carries all three circuits in
        the direction the refrigerant actually travels. The delay staggers them
        so the pips do not march in lockstep."""
        add('<path class="rp-pipe %s" d="%s"/>' % (kind, d))
        add('<path class="rp-pipe rp-flow %s" d="%s" style="animation-delay:%.1fs"/>'
            % (kind, d, -1.7 * i))

    # discharge: compressors -> condensers (high pressure)
    pipe('rp-hp', 'M348 138 L420 138 L420 300 L248 300 L248 320', 0)
    pipe('rp-hp', 'M348 512 L420 512 L420 674 L248 674 L248 694', 1)
    # liquid line: condensers -> receiver header -> rooms
    pipe('rp-lq', 'M426 358 L640 358 L640 620 L700 620', 2)
    pipe('rp-lq', 'M426 732 L640 732', 3)
    pipe('rp-lq', 'M700 620 L700 170 L790 170', 4)
    pipe('rp-lq', 'M700 200 L1190 200', 5)
    pipe('rp-lq', 'M700 574 L1190 574', 6)
    # suction: rooms -> accumulators (low pressure)
    pipe('rp-lp', 'M930 396 L930 440 L560 440 L560 200 L96 200', 7)
    pipe('rp-lp', 'M1340 396 L1340 452 L590 452 L590 574', 8)
    pipe('rp-lp', 'M1340 770 L1340 812 L560 812 L560 574 L96 574', 9)

    # valves and fittings along the runs
    add(check(420, 220)); add(check(420, 594))
    add(gate(530, 358)); add(drier(590, 358)); add(sight(640, 400))
    add(gate(530, 732))
    for rx in (790, 1190, 1190):
        pass
    add(solenoid(838, 200)); add(txv(880, 200))
    add(solenoid(1238, 200)); add(txv(1280, 200))
    add(solenoid(1238, 574)); add(txv(1280, 574))
    add(gate(300, 200, vert=True)); add(gate(300, 574, vert=True))

    # flow arrows
    add('<g class="rp-arr">'
        '<path d="M414 250 L420 236 L426 250 Z"/>'
        '<path d="M694 300 L700 286 L706 300 Z"/>'
        '<path d="M986 194 L1000 200 L986 206 Z"/>'
        '<path d="M700 434 L686 440 L700 446 Z"/>'
        '<path d="M266 194 L252 200 L266 206 Z"/>'
        '</g>')

    # legend
    add('<g class="rp-leg">'
        '<line class="rp-pipe rp-hp" x1="70" y1="900" x2="128" y2="900"/>'
        '<text x="138" y="905">DISCHARGE</text>'
        '<line class="rp-pipe rp-lq" x1="300" y1="900" x2="358" y2="900"/>'
        '<text x="368" y="905">LIQUID</text>'
        '<line class="rp-pipe rp-lp" x1="500" y1="900" x2="558" y2="900"/>'
        '<text x="568" y="905">SUCTION</text>'
        '</g>')

    # title block
    add('<g class="rp-tb">'
        '<rect x="1150" y="856" width="380" height="48"/>'
        '<line x1="1150" y1="880" x2="1530" y2="880"/>'
        '<line x1="1390" y1="856" x2="1390" y2="904"/>'
        '<text x="1164" y="874">%s</text>'
        '<text x="1164" y="898">R404A / R717</text>'
        '<text class="rp-tb-b" x="1404" y="874">LITPROFIT</text>'
        '<text x="1404" y="898">DWG 01</text>'
        '</g>' % i18n.VESSEL_TB[LANG])

    cls = "hero-drawing hero-drawing--lit" if lit else "hero-drawing"
    return ('      <svg class="%s" viewBox="0 0 1600 940" aria-hidden="true"\n'
            '           preserveAspectRatio="xMidYMid meet">%s</svg>'
            % (cls, "".join(P)))


# ============================================================
# HOME
# ============================================================
def home():
    cards = service_cards("h3")

    logos = "\n".join(client_tile(c) for c in CLIENTS)

    return """
    <section class="hero">
      <div class="hero-media">
{hero_drawing}
        <span class="hero-lamp" aria-hidden="true">
{hero_drawing_lit}
        </span>
      </div>
      <!-- Both controls, icon only, above the drawing they act on. They were a
           pair of labelled chips at the end of the trust rule, which turned a
           line of proof -- BITZER, DANFOSS, RINA, PRS -- into a toolbar. Here
           they are instruments beside the instrument diagram, and the strip is
           only what the company can show. -->
      <div class="hero-tools">
        <button type="button" class="hero-tool" id="lampToggle"
                aria-pressed="false" data-on="{lha}" data-off="{lho}" title="{lha}">
          <svg viewBox="0 0 20 20" aria-hidden="true">
            <g stroke="currentColor" stroke-width="1.2" stroke-linecap="round" fill="none">
              <circle cx="10" cy="10" r="3.2"/>
              <path d="M10 1.8v2.4M10 15.8v2.4M1.8 10h2.4M15.8 10h2.4"/>
              <path d="M4.2 4.2l1.7 1.7M14.1 14.1l1.7 1.7M15.8 4.2l-1.7 1.7M5.9 14.1l-1.7 1.7"/>
            </g>
          </svg>
          <span class="visually-hidden">{lha}</span>
        </button>
        <button type="button" class="hero-tool" id="frostToggle"
                aria-pressed="false" data-on="{fha}" data-off="{fho}" title="{fha}">
          <svg viewBox="0 0 20 20" aria-hidden="true">
            <g stroke="currentColor" stroke-width="1.2" stroke-linecap="round" fill="none">
              <path d="M10 2v16M3.1 6l13.8 8M3.1 14l13.8-8"/>
              <path d="M7.4 3.9 10 5.6l2.6-1.7M7.4 16.1 10 14.4l2.6 1.7"/>
              <path d="M4.6 8.7 4.2 5.7l-2.6-.6M15.4 11.3l.4 3 2.6.6"/>
              <path d="M4.6 11.3 4.2 14.3l-2.6.6M15.4 8.7l.4-3 2.6-.6"/>
            </g>
          </svg>
          <span class="visually-hidden">{fha}</span>
        </button>
      </div>

      <div class="container hero-inner">
        <p class="eyebrow eyebrow-plain">{he} <span class="sep">//</span> {hs} {founded}</p>
        <h1>{h1}</h1>
        <p class="lead">{hlead}</p>
        <!-- The three steps used to sit here. They are gone because section 04
             is those same three words with a paragraph under each -- the hero
             was announcing a heading that arrives in full two screens later,
             and it was the least specific thing on the busiest screen. The
             promise strip and its links go with them. -->
        <div class="btn-row">
          <a class="btn btn-solid" href="{book}"{book_attrs}>{book_label}</a>
          <a class="btn btn-outline" href="{services}">{hsvc}</a>
        </div>
        <!-- The four figures used to be a glass panel of their own, a screen
             further down. They are the first things a shipowner checks, and
             they belong on the first screen -- but not as a second panel under
             the buttons. Here they are a measurement rule along the foot of
             the hero: hairline ticks, figures on the baseline, units under
             them. The trust strip that was removed from this hero was claims;
             this is numbers, which is the difference. -->
        <ul class="facts reveal">
          <li class="fact">
            <p class="fact-value">{years}+</p>
            <p class="fact-label">{f1}</p>
          </li>
          <li class="fact">
            <p class="fact-value">24/7</p>
            <p class="fact-label">{f2}</p>
          </li>
          <li class="fact">
            <p class="fact-value">2</p>
            <p class="fact-label">{f3}</p>
          </li>
          <li class="fact">
            <p class="fact-value">&euro;250k</p>
            <p class="fact-label">{f4}</p>
          </li>
        </ul>
        <span class="scroll-cue" aria-hidden="true"></span>
      </div>
    </section>


    <section class="section section-tight partners-band seam-top seam-bottom">
      <div class="container">
        <div class="section-head reveal">
          <p class="eyebrow"><span class="eyebrow-num">01</span><span class="sep">//</span>{rep_e}</p>
          <h2>{rep_h}</h2>
          <p class="lead">{rep_l}</p>
        </div>
        <div class="partner-grid reveal">
          <div class="partner">
            <p class="partner-role">{tp}</p>
            <h3 class="partner-logo"><img src="{bitzer}" alt="BITZER" width="454" height="163"></h3>
            <p>{rep_b}</p>
          </div>
          <div class="partner">
            <p class="partner-role">{tr}</p>
            <h3 class="partner-logo"><img src="{danfoss}" alt="Danfoss" width="126" height="55"></h3>
            <p>{rep_d}</p>
          </div>
        </div>
      </div>
    </section>

    <section class="section section-alt" id="services">
      <div class="container">
        <div class="section-head reveal">
          <p class="eyebrow"><span class="eyebrow-num">02</span><span class="sep">//</span>{svc_e}</p>
          <h2>{svc_h}</h2>
          <p class="lead">{svc_l}</p>
        </div>
        <div class="card-grid">
{cards}
        </div>
      </div>
    </section>
{vessel}

    <section class="section">
      <div class="container split">
        <div class="reveal">
          <p class="eyebrow"><span class="eyebrow-num">04</span><span class="sep">//</span>{how_e}</p>
          <h2>{how_h}</h2>
          <p class="lead">{how_l}</p>
        </div>
        <div class="pillars reveal">
          <!-- ids stay in English across all three languages: they are the
               target of a same-page link, not something a reader sees. -->
          <div class="pillar" id="consult">
            <h3>{s1}</h3>
            <p>{how1}</p>
          </div>
          <div class="pillar" id="organise">
            <h3>{s2}</h3>
            <p>{how2}</p>
          </div>
          <div class="pillar" id="ensure">
            <h3>{s3}</h3>
            <p>{how3}</p>
          </div>
        </div>
      </div>
    </section>

{machine}
{cycle}
    <section class="section section-alt">
      <div class="container">
        <div class="split" style="align-items: center">
          <div class="reveal">
            <p class="eyebrow"><span class="eyebrow-num">07</span><span class="sep">//</span>{cap_e}</p>
            <h2 class="lightwords">{cap_h}</h2>
            <p class="lead">{cap_l}</p>
            <div class="btn-row">
              <a class="btn btn-outline" href="{refrig}">{refrig_label}</a>
            </div>
          </div>
          <!-- A link, not a div. It brightens under the cursor like the service
               cards do, and something that answers the pointer has to go
               somewhere -- the destination is the one already named in the
               button beside it.

               Which is exactly why it is hidden from assistive tech and taken
               out of the tab order. Announced, it made four links to the
               refrigeration page on one screen, two of them adjacent and
               carrying the identical name -- the button, then the photograph
               of the same thing, read out twice in a row. This is a
               mouse-and-touch shortcut over a link that is already there;
               tabindex="-1" is what makes aria-hidden legitimate here rather
               than a focusable element hidden from the people focusing it. -->
          <a class="media-panel cornered reveal" href="{refrig}"
             aria-hidden="true" tabindex="-1">
            <img src="{plant_img}" alt="Industrial refrigeration compressor plant"
                 width="800" height="555" loading="lazy">
          </a>
        </div>
      </div>
    </section>

    <!-- The clients were the second half of the section above: a statement
         with a photograph, then a rail of logos, 1162px of one screenful. Two
         statements, so two sections. -->
    <section class="section">
      <div class="container">
        <div class="section-head reveal">
          <p class="eyebrow"><span class="eyebrow-num">08</span><span class="sep">//</span>{cl_e}</p>
          <h2>{cl_h}</h2>
        </div>
        <div class="client-rail-wrap reveal">
          <ul class="client-rail" id="clientRail">
{logos}
          </ul>
          <button class="rail-btn rail-prev" type="button" aria-label="{rail_prev}"
                  data-rail="-1">&#8592;</button>
          <button class="rail-btn rail-next" type="button" aria-label="{rail_next}"
                  data-rail="1">&#8594;</button>
        </div>
      </div>
    </section>
{cta}""".format(founded=FOUNDED, legal=LEGAL, services=u("/services/"),
                hero_drawing=hero_drawing(), vessel=vessel_drawing(),
                rail_prev=attr(T("rail_prev")), rail_next=attr(T("rail_next")),
                hero_drawing_lit=hero_drawing(lit=True),
                he=T("hero_eyebrow"), hs=T("hero_since"), h1=T("hero_h1"),
                hlead=T("hero_lead", legal=LEGAL), s1=T("step1"), s2=T("step2"),
                s3=T("step3"), hsvc=T("hero_services"),
                # role_bitzer and role_danfoss still feed the partner cards further
                # down this page. trust_cert is gone with the hero strip -- the
                # certificates page is where RINA and PRS are stated now.
                tp=T("role_bitzer"), tr=T("role_danfoss"),
                # frost_hint is no longer rendered -- icon only, like the lamp.
                fha=attr(T("frost_hint_a11y")),
                fho=attr(T("frost_hint_off")),
                # lamp_hint is no longer rendered -- the control is icon-only.
                # The string stays in i18n in case it ever carries a label again.
                lha=attr(T("lamp_hint_a11y")),
                lho=attr(T("lamp_hint_off")),
                rep_e=T("rep_eyebrow"),
                rep_h=T("rep_h2"), rep_l=T("rep_lead"), rep_b=T("rep_bitzer"),
                rep_d=T("rep_danfoss"), f1=T("fact_years"), f2=T("fact_service"),
                f3=T("fact_certs"), f4=T("fact_insured"), svc_e=T("svc_eyebrow"),
                svc_h=T("svc_h2"), svc_l=T("svc_lead"), how_e=T("how_eyebrow"),
                how_h=T("how_h2"), how_l=T("how_lead"), how1=T("how1"),
                how2=T("how2"), how3=T("how3"), cap_e=T("cap_eyebrow"),
                cap_h=T("cap_h2"), cap_l=T("cap_lead"), cl_e=T("clients_eyebrow"),
                cl_h=T("clients_h2"),
                refrig_label=i18n.SVC[LANG]["refrigeration-systems"]["title"],
                cards=cards, logos=logos, cycle=compressor_drawing(),
                machine=recip_3d(),
                bitzer=u("/assets/partners/bitzer.webp"),
                danfoss=u("/assets/partners/danfoss.svg"),
                plant_img=u("/assets/photos/plant-room.webp"),
                refrig=u("/services/refrigeration-systems/"),
                book=BOOKING_URL or u("/contacts/"),
                book_attrs=(' target="_blank" rel="noopener" data-book'
                            if BOOKING_URL else ""),
                book_label=T("book"),
                years=datetime.date.today().year - int(FOUNDED),
                cta=cta(T("cta_h2"), T("cta_p")))


# ============================================================
# GENERAL ARRANGEMENT DRAWING
# A side elevation of a skid-mounted marine screw compressor package —
# the machine this company overhauls more than any other. Drawn to the
# conventions of a real workshop drawing: centre lines, dimension lines
# with ticks, hatched skid, leader lines to numbered balloons, and a
# title block. The point is the drawing; the labels come second.
# ============================================================
_UNUSED_PARTS = [
    dict(n="01", key="motor", title="Electric motor",
         text="Drives the compressor through the coupling. Bearings, insulation "
              "resistance and alignment are checked before anything is reassembled."),
    dict(n="02", key="coupling", title="Coupling",
         text="Where misalignment turns into vibration and a wrecked bearing. "
              "Set cold, then checked again once the package has run up to temperature."),
    dict(n="03", key="screw", title="Screw compressor",
         text="Rotors, slide valve, shaft seal and bearings. This is the overhaul "
              "itself &mdash; SABROE, BITZER, HOWDEN, KUHLAUTOMAT, STAL, GRASSO, MYCOM."),
    dict(n="04", key="separator", title="Oil separator",
         text="Takes the oil back out of the discharge gas and returns it. Carry-over "
              "here shows up much later as poor heat transfer in the condenser."),
    dict(n="05", key="lines", title="Suction &amp; discharge",
         text="Refrigerant piping to class requirements, then pressure testing and "
              "commissioning before the plant is handed over."),
]


def compressor_drawing():
    def balloon(x, y, n, key, lx, ly):
        """A numbered balloon with a leader line, drawing-office style."""
        return ('      <g class="ball" data-prt="{k}">'
                '<line x1="{x}" y1="{y}" x2="{lx}" y2="{ly}"/>'
                '<circle cx="{x}" cy="{y}" r="15"/>'
                '<text x="{x}" y="{ty}">{n}</text></g>').format(
                    k=key, x=x, y=y, lx=lx, ly=ly, ty=y + 5, n=n)

    fins = "".join('<line x1="%d" y1="318" x2="%d" y2="432"/>' % (fx, fx)
                   for fx in range(140, 305, 15))
    hatch = "".join('<line x1="%d" y1="500" x2="%d" y2="512"/>' % (hx, hx - 12)
                    for hx in range(82, 846, 16))
    # bolt circles on the two flanges
    sbolts = "".join('<circle cx="374" cy="%d" r="2.5"/>' % by for by in (346, 358, 370, 382))
    dbolts = "".join('<circle cx="606" cy="%d" r="2.5"/>' % by for by in (406, 418, 430))

    buttons = "\n".join("""          <button type="button" class="part" data-prt="{key}">
            <span class="part-n">{n}</span>
            <span class="part-body">
              <span class="part-title">{title}</span>
              <span class="part-text"><span>{text}</span></span>
            </span>
          </button>""".format(key=k, n="%02d" % (j + 1),
                              title=i18n.PARTS[LANG][k][0],
                              text=i18n.PARTS[LANG][k][1])
                        for j, k in enumerate(i18n.PARTS_ORDER))

    return """
    <section class="section section-alt drawing-section seam-top">
      <div class="container">
        <div class="section-head reveal">
          <p class="eyebrow"><span class="eyebrow-num">06</span><span class="sep">//</span>{ga_e}</p>
          <h2>{ga_h}</h2>
          <p class="lead">{ga_l}</p>
        </div>

        <div class="drawing bleed reveal" id="drawing">
          <!-- The viewBox is cropped to the drawing itself. It used to be
               0 0 900 660 while the content occupied 70,105 to 886,646 -- 105
               units of empty above it and 70 to the left, so a sixth of the
               box was margin and the drawing rendered a fifth smaller than the
               space it was given. Balloon 04 and the dimension arrow overhang,
               hence overflow:visible and the few units of air here. -->
          <svg class="ga" viewBox="62 97 842 557" aria-hidden="true"
               preserveAspectRatio="xMidYMid meet">

            <!-- shaft centre line, dash-dot, the way a drawing marks an axis -->
            <line class="cl" x1="92" y1="375" x2="640" y2="375"/>

            <!-- 01 motor -->
            <g class="prt" data-prt="motor">
              <rect class="body" x="122" y="305" width="196" height="140" rx="10"/>
              <g class="thin">{fins}</g>
              <rect class="body" x="196" y="278" width="56" height="27" rx="2"/>
              <rect class="body" x="142" y="445" width="26" height="41"/>
              <rect class="body" x="272" y="445" width="26" height="41"/>
            </g>

            <!-- 02 coupling guard -->
            <g class="prt" data-prt="coupling">
              <rect class="body" x="318" y="336" width="62" height="78" rx="3"/>
              <g class="thin"><line x1="334" y1="346" x2="334" y2="404"/>
                <line x1="349" y1="346" x2="349" y2="404"/>
                <line x1="364" y1="346" x2="364" y2="404"/></g>
            </g>

            <!-- 03 screw compressor -->
            <g class="prt" data-prt="screw">
              <rect class="body" x="380" y="318" width="222" height="128" rx="8"/>
              <circle class="body" cx="404" cy="375" r="17"/>
              <g class="thin"><circle cx="404" cy="375" r="7"/></g>
              <rect class="body" x="400" y="446" width="26" height="40"/>
              <rect class="body" x="556" y="446" width="26" height="40"/>
              <!-- gauges -->
              <g class="thin">
                <line x1="446" y1="318" x2="446" y2="296"/>
                <line x1="506" y1="318" x2="506" y2="296"/>
              </g>
              <circle class="body" cx="446" cy="284" r="13"/>
              <circle class="body" cx="506" cy="284" r="13"/>
              <g class="thin"><line x1="446" y1="284" x2="452" y2="276"/>
                <line x1="506" y1="284" x2="500" y2="276"/></g>
            </g>

            <!-- 04 oil separator -->
            <g class="prt" data-prt="separator">
              <rect class="body" x="662" y="186" width="128" height="272" rx="30"/>
              <rect class="body" x="712" y="162" width="28" height="24"/>
              <g class="thin">
                <line x1="662" y1="228" x2="790" y2="228"/>
                <line x1="662" y1="416" x2="790" y2="416"/>
                <rect x="714" y="308" width="24" height="72" rx="2"/>
                <line x1="714" y1="344" x2="738" y2="344"/>
              </g>
              <rect class="body" x="678" y="458" width="22" height="28"/>
              <rect class="body" x="752" y="458" width="22" height="28"/>
            </g>

            <!-- 05 suction and discharge lines -->
            <g class="prt" data-prt="lines">
              <path class="pipe" d="M74 256 L352 256 L352 362 L380 362"/>
              <path class="pipe" d="M602 424 L636 424 L636 232 L662 232"/>
              <rect class="body" x="368" y="340" width="12" height="48"/>
              <rect class="body" x="602" y="402" width="12" height="34"/>
              <g class="thin">{sbolts}{dbolts}</g>
            </g>

            <!-- skid -->
            <g class="prt" data-prt="skid">
              <rect class="body" x="70" y="486" width="760" height="14"/>
              <rect class="body" x="70" y="500" width="760" height="12"/>
              <g class="thin">{hatch}</g>
            </g>

            <!-- dimensions -->
            <g class="dim">
              <line x1="70" y1="556" x2="830" y2="556"/>
              <line x1="70" y1="546" x2="70" y2="566"/>
              <line x1="830" y1="546" x2="830" y2="566"/>
              <path d="M78 552 L70 556 L78 560 Z"/>
              <path d="M822 552 L830 556 L822 560 Z"/>
              <rect class="dim-bg" x="404" y="544" width="92" height="24"/>
              <text x="450" y="561" text-anchor="middle">4250 mm</text>

              <line x1="862" y1="162" x2="862" y2="512"/>
              <line x1="852" y1="162" x2="872" y2="162"/>
              <line x1="852" y1="512" x2="872" y2="512"/>
              <path d="M858 170 L862 162 L866 170 Z"/>
              <path d="M858 504 L862 512 L866 504 Z"/>
              <text class="vert" x="862" y="337" text-anchor="middle"
                    transform="rotate(-90 862 337)">2100 mm</text>
            </g>

            <!-- balloons -->
{balloons}

            <!-- title block -->
            <g class="tb">
              <rect x="556" y="588" width="330" height="58"/>
              <line x1="556" y1="616" x2="886" y2="616"/>
              <line x1="762" y1="588" x2="762" y2="646"/>
              <text x="568" y="607">{tb1}</text>
              <text x="568" y="636">{tb2}</text>
              <text class="tb-b" x="774" y="607">LITPROFIT</text>
              <text x="774" y="636">DWG 04 // 06</text>
            </g>
          </svg>

          <ol class="part-list">
{buttons}
          </ol>
        </div>
      </div>
    </section>
""".format(fins=fins, hatch=hatch, sbolts=sbolts, dbolts=dbolts, buttons=buttons,
           ga_e=T("ga_eyebrow"), ga_h=T("ga_h2"), ga_l=T("ga_lead"),
           tb1=i18n.TB[LANG][0].upper(), tb2=i18n.TB[LANG][1].upper(),
           balloons="\n".join([
               balloon(176, 240, "01", "motor", 210, 300),
               balloon(330, 292, "02", "coupling", 344, 332),
               balloon(534, 236, "03", "screw", 512, 280),
               balloon(836, 120, "04", "separator", 790, 176),
               balloon(96, 196, "05", "lines", 110, 250),
           ]))


# ============================================================
# INTERIOR PAGES
# All prose comes from tools/i18n.py; the markup lives here once.
# ============================================================
# ============================================================
# ABOUT — the page below the machine
# It was one prose column: six h2s, a bare <ul> and a paragraph of company
# details, all at the same weight, so nothing in it had a shape. Each block
# below is the shape its own content already has -- a scope of work is a
# numbered register, three ordered steps are a deck you go through one at a
# time, and company details are a title block, which is what a title block is
# for. No new copy except one heading, lifted from the sentence under it.
# ============================================================
def a_scope(items):
    """Scope of work as a numbered register, the way a drawing lists parts."""
    return "\n".join(
        '            <li class="scope-row"><span class="scope-num">%02d</span>'
        '<span class="scope-text">%s</span></li>' % (i + 1, x)
        for i, x in enumerate(items))


def a_titleblock(num):
    """Company details in a title block -- the field on a drawing that carries
    exactly this: who made it, where they are, and their registration."""
    cells = [(T("f_address"), "%s<br>%s<br>%s" % (text(T("addr_street")),
                                                  text(T("addr_city")),
                                                  text(T("addr_country")))),
             (T("company_no"), text(COMPANY_ID)),
             (T("vat"), text(VAT))]
    return """        <div class="tblock reveal">
          <div class="tblock-head">
            <p class="eyebrow"><span class="eyebrow-num">{num}</span><span class="sep">//</span>{legal}</p>
            <h2>{h}</h2>
          </div>
          <div class="tblock-grid">
{cells}
          </div>
        </div>""".format(
        num=num, legal=text(LEGAL), h=text(PT("a_details")),
        cells="\n".join(
            '            <div class="tblock-cell"><p class="tblock-k">%s</p>'
            '<p class="tblock-v">%s</p></div>' % (text(k), v) for k, v in cells))


def about():
    return page_head(PT("about_eyebrow"), PT("about_h1"),
                     PT("about_lead", legal=LEGAL, founded=FOUNDED),
                     [(T("home"), "/"), (PT("about_eyebrow"), None)],
                     path="/about/", wrap="about-hero",
                     aside=text(T("scr_lead"))) + """
    <!-- A photograph of a bench said "we have a workshop". The machine says
         which machine, and it is the one this company is actually known for
         overhauling: SAB 128, SAB 163, Grasso S3-900, CSH8563, OSKA 8591 are
         all twin-screw, and all of them are in the order book. -->
{screw}
    </div>

    <div class="about-body">
{pres}
    <section class="section">
      <div class="container">
        <div class="section-head reveal">
          <p class="eyebrow"><span class="eyebrow-num">01</span><span class="sep">//</span>{cap_e}</p>
          <h2>{h_spec}</h2>
        </div>
        <ol class="scope">
{scope}
        </ol>
      </div>
    </section>

    <section class="section section-alt seam-top">
      <div class="container">
        <div class="section-head reveal">
          <p class="eyebrow"><span class="eyebrow-num">02</span><span class="sep">//</span>{ppl_e}</p>
          <h2>{ppl_h}</h2>
        </div>
        <div class="statement reveal">
          <p class="statement-lead">{people1}</p>
          <p>{people2}</p>
        </div>
      </div>
    </section>

    <section class="section">
      <div class="container">
        <div class="section-head reveal">
          <p class="eyebrow"><span class="eyebrow-num">03</span><span class="sep">//</span>{c_e}</p>
          <h2>{h_cert}</h2>
        </div>
        <div class="asr reveal">
          <div class="asr-item">
            <p class="asr-label">{f_certs}</p>
            <p>{cert1}</p>
            <a class="asr-more" href="{certs}">{c_more}</a>
          </div>
          <div class="asr-item">
            <p class="asr-label">{f_insured}</p>
            <p>{cert2}</p>
          </div>
          <div class="asr-item">
            <p class="asr-label">{rep_e}</p>
            <p>{rep_l}</p>
            <a class="asr-more" href="{partners}">{p_more}</a>
          </div>
        </div>
      </div>
    </section>

    <section class="section section-alt seam-top">
      <div class="container">
{tblock}
      </div>
    </section>
    </div>
{cta}""".format(scope=a_scope(i18n.P[LANG]["a_spec_list"]),
tblock=a_titleblock("04"),
                cap_e=T("cap_eyebrow"), ppl_e=PT("a_people"), ppl_h=PT("a_people_h"),
                c_e=PT("c_eyebrow"), f_certs=T("fact_certs"), f_insured=T("fact_insured"),
                rep_e=T("rep_eyebrow"),
                h_spec=PT("a_spec"),
                people1=PT("a_people_1"), people2=PT("a_people_2"),
                h_how=T("how_h2"), s1=T("step1"), s2=T("step2"), s3=T("step3"),
                how1=T("how1"), how2=T("how2"), how3=T("how3"),
                h_cert=PT("a_cert"), cert1=PT("a_cert_1", legal=LEGAL),
                cert2=PT("a_cert_2"), certs=u("/certificates/"),
                c_more=PT("c_eyebrow").lower(), h_rep=T("rep_eyebrow"),
                rep_l=T("rep_lead"), partners=u("/partners/"),
                p_more=PT("p_eyebrow").lower(),
                screw=recip_3d("screw", hero=True),
                pres=presentation_block(),
                cta=cta(T("cta_h2"), T("cta_p")))


# ============================================================
# VESSEL GENERAL ARRANGEMENT
# A ship in profile, with the four spaces this company works in called out on
# leaders. The site draws a refrigeration circuit and a compressor package and
# never once drew the thing they are fitted to -- which for a ship repair yard
# is the drawing that was missing.
#
# The title block says "typical" and "not to scale" and carries no designer
# credit, deliberately. The compressor drawing signs itself LITPROFIT because
# the PRS certificate approves them to design refrigeration equipment. It does
# not approve them to design vessels, and a signed hull would say it did.
# ============================================================
def vessel_drawing():
    P = []
    add = P.append

    # ---- hull, bow to the right ----
    # Sheer: the deck is lowest amidships and lifts at both ends, which is what
    # stops a profile reading as a barge. The first attempt had a dead flat
    # deck line and a straight wedge for a stem, and looked like one.
    DECK = "M70 146 Q620 174 1150 116"
    add('<path class="vs-hull" d="M70 146 L70 250 Q70 266 108 266 L860 266 '
        'Q1012 266 1074 212 L1150 116 Q620 174 70 146 Z"/>')
    add('<path class="vs-deck" d="%s"/>' % DECK)

    # waterline: dash-dot, the convention for a datum
    add('<line class="vs-wl" x1="24" y1="230" x2="1176" y2="230"/>')
    # right of the forefoot, where the datum line runs clear of the hull.
    # At the left it sat across the transom and the rudder.
    add('<text class="vs-datum vs-datum--end" x="1172" y="222">%s</text>' % text(T("vsl_wl")))

    # ---- rudder and propeller, aft ----
    add('<path class="vs-body" d="M52 236 L52 264 L70 258 L70 240 Z"/>')
    add('<line class="vs-body" x1="70" y1="248" x2="118" y2="248"/>')
    add('<path class="vs-body" d="M84 234 L96 248 L84 262 Z"/>')

    # ---- deck furniture, kept clear of the leader lines ----
    add('<path class="vs-body" d="M250 152 L250 104 L360 104 L360 156"/>')
    add('<path class="vs-body" d="M690 160 L690 120 L724 120 L724 162"/>')
    add('<path class="vs-body" d="M736 162 L736 100 L900 100 L900 158"/>')
    add('<path class="vs-body" d="M792 100 L792 66 L884 66 L884 100"/>')
    for wx in range(756, 881, 26):
        add('<line class="vs-thin" x1="%d" y1="114" x2="%d" y2="132"/>' % (wx, wx))
    # A vertical spar with a centred horizontal yard is a crucifix, whatever
    # it was meant to be. The bare mast with two stays down to the wheelhouse
    # roof reads as rigging: a triangle, and no horizontal at the head at all.
    # A scanner bar was tried there first and put a small cross back on top.
    add('<line class="vs-thin" x1="838" y1="66" x2="838" y2="18"/>')
    add('<line class="vs-thin" x1="838" y1="26" x2="796" y2="66"/>')
    add('<line class="vs-thin" x1="838" y1="26" x2="880" y2="66"/>')

    # ---- the four spaces, dashed like compartment boundaries ----
    def space(x, w, label, h=78):
        # SVG text does not wrap, so a label long enough to need two lines says
        # so with a pipe and gets a tspan rather than running out of its box.
        lines = str(label).split("|")
        spans = "".join('<tspan x="%d" dy="%d">%s</tspan>'
                        % (x + 12, 0 if i == 0 else 15, text(l))
                        for i, l in enumerate(lines))
        return ('<g class="vs-space"><rect x="%d" y="178" width="%d" height="%d"/>'
                '<text x="%d" y="200">%s</text></g>'
                % (x, w, h, x + 12, spans))
    add(space(116, 236, T("vsl_pipe")))     # aft
    add(space(360, 262, T("vsl_er")))       # amidships
    add(space(638, 266, T("vsl_hold")))     # refrigerated hold
    # shorter: the forefoot has begun to rise under it, and a full-height box
    # put its bottom corner outside the hull.
    add(space(918, 104, T("vsl_store"), h=62))

    # ---- balloons: each space leads to the discipline that works in it ----
    # Leader anchors chosen to clear the gantry, funnel and wheelhouse rather
    # than crossing them, the way a leader on a real print is routed.
    def balloon(n, cx, tx, href, label):
        # The visible balloon is r=16 in a 1200-unit viewBox, which on a phone
        # scales to about 9px across. A transparent circle carries the tap
        # target instead. r=44 cleared the 24px WCAG floor and was still only
        # 25px on a 390px screen, well under the 44 this project holds
        # everywhere else -- the viewBox scales the target down with the
        # drawing, so it has to be sized for the narrowest layout, not the
        # widest. r=76 lands at about 43px there. Balloon centres are at least
        # 230 units apart, so two of these still cannot touch.
        # fill:transparent, not fill:none -- none takes no pointer at all.
        return ('<a class="vs-ball" href="%s" aria-label="%s">'
                '<line x1="%d" y1="70" x2="%d" y2="176"/>'
                '<circle class="vs-hit" cx="%d" cy="54" r="76"/>'
                '<circle cx="%d" cy="54" r="16"/>'
                '<text x="%d" y="59">%s</text></a>'
                % (href, attr(label), cx, tx, cx, cx, cx, n))
    add(balloon("03", 150, 200, u("/services/hull-and-piping/"),       T("vsl_pipe")))
    add(balloon("02", 380, 430, u("/services/ship-engine-repair/"),    T("vsl_er")))
    add(balloon("01", 630, 680, u("/services/refrigeration-systems/"), T("vsl_hold")))
    add(balloon("04", 1030, 980, u("/services/spare-parts/"),          T("vsl_store")))

    # ---- title block ----
    add('<g class="vs-tb"><rect x="836" y="292" width="336" height="46"/>'
        '<line x1="836" y1="315" x2="1172" y2="315"/>'
        '<line x1="1046" y1="292" x2="1046" y2="338"/>'
        '<text x="848" y="308">%s</text>'
        '<text x="848" y="331">%s</text>'
        '<text class="vs-tb-b" x="1058" y="308">GA</text>'
        '<text x="1058" y="331">DWG 02</text></g>'
        % (text(T("vsl_tb")), text(T("vsl_tb2"))))

    return """
    <section class="section section-alt vessel-section seam-top">
      <div class="container">
        <div class="section-head reveal">
          <p class="eyebrow"><span class="eyebrow-num">03</span><span class="sep">//</span>{e}</p>
          <h2>{h}</h2>
          <p class="lead">{l}</p>
        </div>
        <div class="vessel bleed reveal">
          <svg class="vs" viewBox="0 0 1200 352" role="img" aria-label="{alt}">{p}</svg>
        </div>
        <!-- On a phone the drawing is 100px tall and the compartment labels are
             hidden, because at that size they collide with their own boxes. That
             left four balloons pointing at four empty rectangles. A legend is
             what a real sheet does when the labels will not fit on the drawing.
             Plain text, not links: the balloons above are already the links, and
             the four service cards two screens up are the same four again. -->
        <ol class="vs-legend reveal">
          <li><span>01</span>{lg1}</li>
          <li><span>02</span>{lg2}</li>
          <li><span>03</span>{lg3}</li>
          <li><span>04</span>{lg4}</li>
        </ol>
      </div>
    </section>""".format(e=T("vsl_eyebrow"), h=T("vsl_h2"), l=T("vsl_lead"),
                         alt=attr(T("vsl_h2")), p="".join(P),
                         lg1=text(T("vsl_hold")), lg2=text(T("vsl_er").replace("|", " ")),
                         lg3=text(T("vsl_pipe")), lg4=text(T("vsl_store")))


# ============================================================
# COMPLETED PROJECTS
# Driven entirely by i18n.PROJECTS. While that list is empty nothing here
# renders, nothing is linked and nothing enters the sitemap -- the site is
# simply as it was. Add a job and it appears in all four places at once.
# ============================================================
def project_url(pr):
    return "/completed-works/%s/" % pr["slug"]


def project_card(pr):
    """A job as a record card: the facts on the left, the scope beneath."""
    # The year is already the record number in the left gutter, where it reads
    # as a date stamp; repeating it in the fact row said 2024 twice on one card.
    facts = []
    for label, val in ((T("prj_vessel"), pr.get("vessel")),
                       (T("prj_owner"), pr.get("owner")),
                       (T("prj_port"), pr.get("port"))):
        if val:
            facts.append('<span><i>%s</i>%s</span>' % (text(label), text(val)))
    days = pr.get("days")
    if days:
        facts.append('<span><i>%s</i>%s&nbsp;%s</span>'
                     % (text(T("prj_days")), days, text(T("prj_days_unit"))))
    # The discipline goes in a column of its own on the right. Left in the fact
    # row it was the fifth item on a line and the card's whole right half was
    # empty; as a column it squares the card up and says at a glance which of
    # the four services the job belongs to.
    svc = i18n.SVC[LANG].get(pr.get("scope"), {})
    return """          <a class="prj-card reveal" href="{href}">
            <span class="prj-num">{n}</span>
            <span class="prj-body">
              <span class="prj-title">{title}</span>
              <span class="prj-lead">{lead}</span>
              <span class="prj-facts">{facts}</span>
            </span>
            <span class="prj-scope">{scope}</span>
          </a>""".format(href=u(project_url(pr)), n=pr.get("year", ""),
                         title=text(pr["title"]), lead=text(pr["lead"]),
                         facts="".join(facts), scope=text(svc.get("title", "")))


def projects_band():
    if not i18n.PROJECTS:
        return ""
    return """
    <section class="section projects-band seam-top">
      <div class="container">
        <div class="section-head reveal">
          <p class="eyebrow"><span class="eyebrow-num">05</span><span class="sep">//</span>{e}</p>
          <h2>{h}</h2>
          <p class="lead">{l}</p>
        </div>
        <div class="prj-grid">
{cards}
        </div>
      </div>
    </section>""".format(e=T("prj_eyebrow"), h=T("prj_h2"), l=T("prj_lead"),
                         cards="\n".join(project_card(p) for p in i18n.PROJECTS))


# ---- where on the ship the job was ----
# The home page carries the full GA with its four balloons linking to the
# services. A job page wants the opposite: the same hull, everything else
# stripped, and one compartment picked out -- so the reader sees where the
# work was before reading a word of what it was.
#
# Every stroke carries pathLength="1", so the draw-on can be written as a
# dasharray of 1 without knowing a single real path length at build time.
# Measuring them would mean either shipping a geometry library or hardcoding
# numbers that go stale the first time the hull is redrawn.
JOB_SPACES = {
    "pipe":  (116, 236, 78, "vsl_pipe"),
    "er":    (360, 262, 78, "vsl_er"),
    "hold":  (638, 266, 78, "vsl_hold"),
    "store": (918, 104, 62, "vsl_store"),
}


def job_profile(pr):
    zones = [z for z in pr.get("zones", []) if z in JOB_SPACES]
    if not zones:
        return ""
    P = []
    add = P.append
    add('<path class="jp-line jp-hull" pathLength="1" d="M70 146 L70 250 Q70 266 108 266 '
        'L860 266 Q1012 266 1074 212 L1150 116 Q620 174 70 146 Z"/>')
    add('<path class="jp-line jp-deck" pathLength="1" d="M70 146 Q620 174 1150 116"/>')
    # not a jp-line: the draw-on works by owning stroke-dasharray, and the
    # datum's whole meaning is its dash-dot. It is wiped in by scaleX instead,
    # which leaves the dash pattern alone.
    add('<line class="jp-wl" x1="24" y1="230" x2="1176" y2="230"/>')
    add('<text class="jp-datum" x="1172" y="222">%s</text>' % text(T("vsl_wl")))
    # rudder and propeller: without them the aft end reads as a cut, not a stern
    add('<path class="jp-line jp-body" pathLength="1" d="M52 236 L52 264 L70 258 L70 240 Z"/>')
    add('<line class="jp-line jp-body" pathLength="1" x1="70" y1="248" x2="118" y2="248"/>')
    add('<path class="jp-line jp-body" pathLength="1" d="M84 234 L96 248 L84 262 Z"/>')

    for key, (x, w, h, label) in JOB_SPACES.items():
        on = key in zones
        lines = str(T(label)).split("|")
        spans = "".join('<tspan x="%d" dy="%d">%s</tspan>'
                        % (x + 12, 0 if i == 0 else 15, text(l))
                        for i, l in enumerate(lines))
        add('<g class="jp-space%s"><rect x="%d" y="178" width="%d" height="%d"/>'
            '<text x="%d" y="200">%s</text></g>'
            % (" is-work" if on else "", x, w, h, x + 12, spans))
        if on:
            # dimension rule under the marked space, the way a print calls out
            # the extent of a job rather than just shading it
            add('<g class="jp-dim"><line x1="%d" y1="286" x2="%d" y2="286"/>'
                '<line x1="%d" y1="280" x2="%d" y2="292"/>'
                '<line x1="%d" y1="280" x2="%d" y2="292"/></g>'
                % (x, x + w, x, x, x + w, x + w))

    return """
      <figure class="jp bleed reveal">
        <svg viewBox="24 96 1152 208" role="img" aria-label="{alt}" focusable="false">
{body}
        </svg>
        <figcaption>{cap}<span class="jp-legend">{legend}</span></figcaption>
      </figure>""".format(
        body="\n".join("          " + x for x in P),
        alt=attr("%s \u2014 %s" % (T("prj_where"), pr.get("vessel", ""))),
        cap=text(T("prj_where")),
        # Below 700px the labels inside the drawing are about four pixels per
        # character -- the home page hides its own there for the same reason.
        # The marked compartments are the whole point of this drawing, so they
        # are repeated here in running type and the CSS swaps which copy shows.
        legend=text(", ".join(str(T(JOB_SPACES[z][3])).replace("|", " ") for z in zones)))


def project_page(pr):
    def row(label, val):
        return ('<div><span>%s</span><b>%s</b></div>' % (text(label), text(val))) if val else ""
    svc = i18n.SVC[LANG].get(pr.get("scope"), {})
    facts = "".join([
        row(T("prj_vessel"), pr.get("vessel")),
        row(T("prj_owner"), pr.get("owner")),
        row(T("prj_year"), pr.get("year")),
        row(T("prj_port"), pr.get("port")),
        row(T("prj_days"), "%s %s" % (pr["days"], T("prj_days_unit")) if pr.get("days") else ""),
        row(T("prj_scope"), svc.get("title", "")),
    ])
    work = "".join("<li>%s</li>" % text(x) for x in pr.get("work", []))
    plant = "".join("<li>%s</li>" % text(x) for x in pr.get("plant", []))
    shots = ""
    for name in pr.get("photos", []):
        rel = "assets/photos/%s.webp" % name
        if not os.path.exists(os.path.join(ROOT, rel)):
            continue
        w, h = img_size(rel)
        shots += ('<figure class="prj-shot"><img src="%s" alt="%s" width="%d" height="%d" '
                  'loading="lazy" decoding="async"></figure>'
                  % (u("/" + rel), attr(pr["title"]), w, h))

    return page_head(T("prj_eyebrow"), pr["title"], pr["lead"],
                     [(T("home"), "/"), (PT("cw_eyebrow"), "/completed-works/"),
                      (pr["title"], None)],
                     path=project_url(pr)) + """
    <section class="container prj-page">
      <div class="prj-record reveal">{facts}</div>
      {profile}
      {work}
      {plant}
      {shots}
      <p class="prj-back"><a href="{all}">{all_label}</a></p>
    </section>
{cta}""".format(
        facts=facts,
        profile=job_profile(pr),
        work=('<h2>%s</h2><ul class="prj-list reveal">%s</ul>' % (text(T("prj_work")), work)) if work else "",
        plant=('<h2>%s</h2><ul class="tags reveal">%s</ul>' % (text(T("prj_plant")), plant)) if plant else "",
        shots=('<div class="prj-shots reveal">%s</div>' % shots) if shots else "",
        all=u("/completed-works/"), all_label=text(T("prj_all")),
        cta=cta(T("cta_h2"), T("cta_p")))


# ============================================================
# SERVICES INDEX + DETAIL
# ============================================================
def services_index():
    return page_head(T("svc_eyebrow"), PT("svc_h1"), PT("svc_page_lead"),
                     [(T("home"), "/"), (T("svc_eyebrow"), None)],
                     path="/services/") + """
    <section class="section" style="padding-top: 0">
      <div class="container">
        <div class="card-grid">
{cards}
        </div>
      </div>
    </section>
{cta}""".format(cards=service_cards("h2"), cta=cta(T("cta_h2"), T("cta_p")))


def service_ld(s):
    """Service, tied to the Organization that provides it.

    `provider` is the same @id the home page's Organization publishes, so the
    four services attach to the company rather than floating as four unrelated
    entities. areaServed is stated because this company's whole claim is that
    it travels -- "wherever the vessel happens to be" -- and a service with no
    area reads as local-only."""
    return ('  <script type="application/ld+json">\n  %s\n  </script>\n'
            % json.dumps({
                "@context": "https://schema.org",
                "@type": "Service",
                "name": strip_tags(s["title"]),
                "description": strip_tags(s["meta"]),
                "serviceType": strip_tags(s["title"]),
                "url": canonical("/services/%s/" % s["slug"]),
                "provider": {"@type": "Organization", "name": LEGAL,
                             "url": canonical("/")},
                "areaServed": {"@type": "Place", "name": "Worldwide"},
            }, ensure_ascii=False))


# Published performance for a six-cylinder semi-hermetic on R404A, at three
# condensing temperatures. Cooling capacity in watts against evaporating
# temperature in degrees C, per EN12900 with 20 C suction gas and no liquid
# subcooling. Figures are the manufacturer's; the chart is ours.
CAP_TO = (-40, -35, -30, -25, -20, -15, -10, -5)
CAP_CURVES = (
    (30, (16741, 22638, 29678, 38014, 47812, 59256, 72553, 87943)),
    (40, (13438, 18595, 24718, 31933, 40375, 50196, 61562, 74665)),
    # the 50 C row has no figure at -5: the machine is outside its envelope there,
    # and a chart that invents a point to close a curve is a chart that lies
    (50, (10395, 14765, 19920, 25960, 32992, 41135, 50514, None)),
)


def capacity_chart():
    L, R, TOP, BOT = 116, 790, 58, 424
    QMAX = 92_000

    def px(to):  return L + (to + 40) / 35 * (R - L)
    def py(q):   return BOT - q / QMAX * (BOT - TOP)

    P = []
    add = P.append

    # frame and grid
    add('<rect class="cc-frame" x="%d" y="%d" width="%d" height="%d"/>'
        % (L, TOP, R - L, BOT - TOP))
    for q in range(0, 100_000, 20_000):
        add('<line class="cc-grid" x1="%d" y1="%.1f" x2="%d" y2="%.1f"/>' % (L, py(q), R, py(q)))
        add('<text class="cc-ax" x="%d" y="%.1f" text-anchor="end">%d</text>'
            % (L - 12, py(q) + 4, q // 1000))
    for to in CAP_TO:
        add('<line class="cc-grid" x1="%.1f" y1="%d" x2="%.1f" y2="%d"/>' % (px(to), TOP, px(to), BOT))
        add('<text class="cc-ax" x="%.1f" y="%d" text-anchor="middle">%d</text>' % (px(to), BOT + 22, to))

    # the three curves
    for tc, row in CAP_CURVES:
        pts = [(px(t), py(q)) for t, q in zip(CAP_TO, row) if q is not None]
        add('<polyline class="cc-line cc-tc%d" points="%s"/>'
            % (tc, " ".join("%.1f,%.1f" % xy for xy in pts)))
        for x, y in pts:
            add('<circle class="cc-dot cc-tc%d" cx="%.1f" cy="%.1f" r="3.4"/>' % (tc, x, y))
        lx, ly = pts[-1]
        add('<text class="cc-lbl cc-tc%d" x="%.1f" y="%.1f">tc %d \u00b0C</text>'
            % (tc, lx + 12, ly + 4, tc))

    add('<text class="cc-ax cc-axis-x" x="%.1f" y="%d" text-anchor="middle">%s \u00b0C</text>'
        % ((L + R) / 2, BOT + 52, text(T("cap_chart_x"))))
    add('<text class="cc-ax" x="%d" y="%d">%s  kW</text>' % (L - 44, TOP - 18, text(T("cap_chart_y"))))

    # Below the axis caption, not across it. At y=454 the block sat exactly
    # where "Evaporating temperature" is centred and the two overprinted.
    # Second time the same fault: 196px of left cell for a 28-character caption
    # at 12px mono. "EN12900 // 20 C suction gas" ran through the divider into
    # DWG 06. Measure the caption, then cut the cell -- not the other way round.
    add('<g class="cc-tb"><rect x="470" y="514" width="378" height="44"/>'
        '<line x1="470" y1="536" x2="848" y2="536"/>'
        '<line x1="740" y1="514" x2="740" y2="558"/>'
        '<text x="482" y="530">%s</text><text x="482" y="552">%s</text>'
        '<text class="cc-tb-b" x="752" y="530">6H-25.2</text>'
        '<text x="752" y="552">DWG 06</text></g>'
        % (text(T("cap_chart_tb")), text(T("cap_chart_tb2"))))

    return """
        <div class="capchart reveal">
          <svg class="cc" viewBox="0 0 900 578" role="img" aria-label="{alt}">{p}</svg>
        </div>""".format(alt=attr(T("cap_chart_h2")), p="".join(P))


def recip_3d(machine="recip", hero=False):
    """The compressor as a live object, above its own elevation.

    Same machine, same numbers: the geometry in js/compressor.js is authored in
    the elevation's units, so the drawing below this is literally this thing
    seen from the side. The callout labels are emitted here rather than in the
    script because the script is not translated and the site is.

    Anchors are model coordinates -- x along the length from the motor end, y
    up from the mounting feet, z across. The renderer projects them every
    frame, so a label follows the casting it points at.
    """
    # Anchors are model coordinates, so they belong to the machine, not to the
    # page. A screw compressor has nothing at 470,110,152 and a reciprocating
    # one has no slide valve.
    if machine == "unit":
        # the same five parts the side elevation on the home page numbers, so
        # the flat drawing and the solid one name things the same way
        # Spread over the height, not lined up along the shaft. Compressor,
        # coupling and motor all sat at y=40 -- true to the machine, useless as
        # a callout: three anchors within a few pixels of each other put three
        # labels in one place and their leaders crossed to get there. Each now
        # points at a different part of its own part.
        tags = [("01", i18n.PARTS_LABEL[LANG]["separator"], "380,110,0"),
                ("02", i18n.PARTS_LABEL[LANG]["screw"],     "990,170,0"),
                ("03", i18n.PARTS_LABEL[LANG]["coupling"],  "1205,40,0"),
                ("04", i18n.PARTS_LABEL[LANG]["motor"],     "1430,-60,0"),
                ("05", T("unit_panel"),                     "290,340,190"),
                # follows the discharge run down from 470 to 300; left where it
                # was, it pointed at empty sky above the skid
                ("06", i18n.PARTS_LABEL[LANG]["lines"],     "840,300,0"),
                ("07", T("unit_frame"),                     "800,-330,0")]
    elif machine == "screw":
        tags = [("01", T("scr_male"),   "380,96,0"),
                ("02", T("scr_female"), "380,-70,0"),
                ("03", T("scr_casing"), "380,250,0"),
                ("04", T("scr_slide"),  "370,-178,0"),
                ("05", T("scr_bearing"), "112,96,0"),
                # the two ends of the same thing, so the colour explains itself
                ("06", T("scr_suction"), "120,170,0"),
                ("07", T("scr_discharge"), "640,170,0")]
    else:
        tags = [("01", T("rec_motor"), "190,252,0"),
                ("02", T("rec_crank"), "470,110,152"),
                ("03", T("rec_head"),  "520,336,0"),
                ("04", T("rec_c2"),    "768,195,0"),
                ("05", T("rec_c1"),    "150,312,0")]
    marks = "".join(
        '<span class="cmp-tag" data-tag data-at="%s"><b>%s</b><span>%s</span></span>'
        % (at, n, text(label)) for n, label, at in tags)

    return """
    <section class="section section-alt cmp-section{hero}">
      <div class="container">
{head}
        <figure class="cmp bleed reveal" data-compressor data-machine="{machine}">
          <div class="cmp-stage">
            <canvas class="cmp-canvas" role="img" aria-label="{alt}"></canvas>
            <span class="cmp-corner cmp-corner--tl"></span>
            <span class="cmp-corner cmp-corner--tr"></span>
            <span class="cmp-corner cmp-corner--bl"></span>
            <span class="cmp-corner cmp-corner--br"></span>
            <p class="cmp-hint">{hint}</p>
          </div>
          <p class="cmp-legend">{marks}</p>
          <figcaption class="cmp-tb"><span>{tb}</span><b>{tb2}</b></figcaption>
        </figure>
      </div>
    </section>
    <script src="{js}" defer></script>""".format(
        machine=machine, hero=(" cmp-section--hero" if hero else " seam-top"),
        # In the About hero the head is gone entirely. A numbered eyebrow and a
        # 58px heading introducing a machine that is right there, already
        # carrying its own title block and seven named callouts, was the page
        # explaining its own illustration.
        head=("" if hero else """        <div class="section-head reveal">
          <p class="eyebrow"><span class="eyebrow-num">%s</span><span class="sep">//</span>%s</p>
          <h2>%s</h2>
          %s
        </div>""" % (
            ("01" if machine in ("screw", "unit") else "05"),
            text(T("unit_eyebrow" if machine == "unit" else
                   ("scr_eyebrow" if machine == "screw" else "cmp_eyebrow"))),
            text(T("unit_h2" if machine == "unit" else
                   ("scr_h2" if machine == "screw" else "cmp_h2"))),
            '<p class="lead">%s</p>' % text(T(
                "unit_lead" if machine == "unit" else
                ("scr_lead" if machine == "screw" else "cmp_lead"))))),
        alt=attr(T("unit_alt" if machine == "unit" else ("scr_alt" if machine == "screw" else "cmp_alt"))),
        hint=text(T("cmp_hint")), marks=marks,
        tb=text(T("unit_tb" if machine == "unit" else ("scr_tb" if machine == "screw" else "cmp_tb"))),
        tb2=text(T("unit_tb2" if machine == "unit" else ("scr_tb2" if machine == "screw" else "cmp_tb2"))),
        js=asset("/js/compressor.js"))


def recip_drawing():
    """Semi-hermetic four-cylinder reciprocating compressor, side elevation.

    Drawn from scratch in this site's own drawing language. The BITZER
    selection sheets for the 4Z-8.2Y were the reference for the FACTS -- the
    673 x 439 x 420 envelope, four cylinders at 55 mm bore and 34 mm stroke,
    28.11 m3/h at 1450 rpm, 140 kg, and the connection schedule a fitter works
    to. Those are measurements, and measurements are not authorship.

    The sheets themselves are BITZER's copyright and are not reproduced here,
    nor traced. Being an authorised service partner is a right to work on the
    machine, not a licence to republish the manufacturer's drawings.
    """
    P = []
    add = P.append

    # ---- feet and mounting line ----
    # The /> was missing here. An unterminated <path> does not error, it eats
    # the tags after it -- which is why the motor housing vanished from the
    # first render while its cooling ribs stayed.
    add('<line class="rc-thin" x1="60" y1="470" x2="880" y2="470"/>')
    for fx in (150, 300, 560, 710):
        add('<path class="rc-body" d="M%d 446 L%d 446 L%d 470 L%d 470 Z"/>'
            % (fx, fx + 54, fx + 62, fx - 8))

    # ---- motor housing, left: a semi-hermetic motor shares the crankcase ----
    add('<path class="rc-body" d="M96 250 Q96 224 128 224 L300 224 L300 446 '
        'L128 446 Q96 446 96 420 Z"/>')
    for cx in range(120, 297, 18):      # cooling ribs
        add('<line class="rc-thin" x1="%d" y1="236" x2="%d" y2="434"/>' % (cx, cx))
    add('<path class="rc-body" d="M172 224 L172 176 L268 176 L268 224"/>')   # terminal box
    add('<line class="rc-thin" x1="188" y1="190" x2="252" y2="190"/>')
    add('<line class="rc-thin" x1="188" y1="204" x2="252" y2="204"/>')

    # ---- crankcase ----
    add('<path class="rc-body" d="M300 268 L640 268 L640 446 L300 446 Z"/>')
    add('<line class="rc-thin" x1="300" y1="392" x2="640" y2="392"/>')        # oil level
    add('<circle class="rc-body" cx="470" cy="356" r="46"/>')                 # crankshaft
    add('<circle class="rc-thin" cx="470" cy="356" r="18"/>')
    add('<line class="rc-cl" x1="420" y1="356" x2="520" y2="356"/>')
    add('<line class="rc-cl" x1="470" y1="306" x2="470" y2="406"/>')

    # ---- two banks of two cylinders, in V ----
    # Rotated about the crankcase top centre, which is where a V actually
    # hinges. The first attempt rotated about the translate origin, so both
    # banks swung away from the block and floated beside it.
    # Each bank hinges on its own INNER base corner and splays outward. Both
    # rotating about one centre point put them through each other in an X.
    for x0, x1, pivot, tilt in ((374, 464, 464, -21), (476, 566, 476, 21)):
        add('<g transform="rotate(%d %d 268)">' % (tilt, pivot)
            + '<path class="rc-body" d="M%d 268 L%d 268 L%d 152 L%d 152 Z"/>' % (x0, x1, x1, x0)
            + '<path class="rc-body" d="M%d 152 L%d 152 L%d 126 L%d 126 Z"/>'
              % (x0 - 10, x1 + 10, x1 + 10, x0 - 10)
            + ''.join('<line class="rc-thin" x1="%d" y1="162" x2="%d" y2="258"/>' % (h, h)
                      for h in (x0 + 22, x0 + 45, x0 + 68))
            + '</g>')

    # ---- suction and discharge, top corners ----
    # Both stubs leave the block itself rather than hanging in space.
    add('<path class="rc-body" d="M640 300 L706 300 L706 250 L760 250"/>')
    add('<path class="rc-thin" d="M694 300 L694 250"/>')
    add('<text class="rc-tag" x="768" y="255">SL</text>')
    # Routed over the motor, not through it: at y=250 it ran straight across the
    # housing and the terminal box, which on a drawing reads as a pipe passing
    # through solid castings.
    add('<path class="rc-body" d="M300 262 L290 262 L290 148 L136 148"/>')
    add('<path class="rc-thin" d="M300 274 L278 274 L278 160 L136 160"/>')
    add('<text class="rc-tag" x="96" y="153">DL</text>')

    # ---- dimensions, off the real envelope ----
    def dim(x1, x2, y, label):
        return ('<g class="rc-dim"><line x1="%d" y1="%d" x2="%d" y2="%d"/>'
                '<line x1="%d" y1="%d" x2="%d" y2="%d"/>'
                '<line x1="%d" y1="%d" x2="%d" y2="%d"/>'
                '<rect class="rc-dim-bg" x="%d" y="%d" width="52" height="16"/>'
                '<text x="%d" y="%d" text-anchor="middle">%s</text></g>'
                % (x1, y - 7, x1, y + 7, x2, y - 7, x2, y + 7, x1, y, x2, y,
                   (x1 + x2) // 2 - 26, y - 8, (x1 + x2) // 2, y + 4, label))
    add(dim(96, 748, 510, "673"))
    add('<g class="rc-dim"><line x1="912" y1="176" x2="912" y2="470"/>'
        '<line x1="905" y1="176" x2="919" y2="176"/>'
        '<line x1="905" y1="470" x2="919" y2="470"/>'
        '<rect class="rc-dim-bg" x="886" y="315" width="52" height="16"/>'
        '<text x="912" y="327" text-anchor="middle">439</text></g>')

    # ---- connection balloons, the schedule a fitter works to ----
    def ball(n, cx, cy, tx, ty):
        return ('<g class="rc-ball"><line x1="%d" y1="%d" x2="%d" y2="%d"/>'
                '<circle cx="%d" cy="%d" r="15"/>'
                '<text x="%d" y="%d">%s</text></g>'
                % (cx, cy, tx, ty, cx, cy, cx, cy + 5, n))
    add(ball("05", 250, 92, 330, 300))     # oil fill plug
    add(ball("06", 350, 92, 402, 438))     # oil drain
    add(ball("08", 452, 92, 520, 288))     # oil return from separator
    add(ball("10", 554, 92, 600, 430))     # oil heater

    # 336 wide could not hold "Semi-hermetic reciprocating" at 12px mono -- the
    # caption ran straight through the divider and into R404A. 412, split 260/152.
    add('<g class="rc-tb"><rect x="520" y="524" width="412" height="46"/>'
        '<line x1="520" y1="547" x2="932" y2="547"/>'
        '<line x1="780" y1="524" x2="780" y2="570"/>'
        '<text x="532" y="540">%s</text><text x="532" y="563">%s</text>'
        '<text class="rc-tb-b" x="792" y="540">R404A</text>'
        '<text x="792" y="563">DWG 05</text></g>'
        % (text(T("rec_tb")), text(T("rec_tb2"))))

    legend = "".join(
        '<li><span>%s</span>%s</li>' % (n, text(T(k)))
        for n, k in (("05", "rec_c5"), ("06", "rec_c6"),
                     ("08", "rec_c7"), ("10", "rec_c8")))

    return """
    <section class="section section-alt recip-section seam-top">
      <div class="container">
        <div class="section-head reveal">
          <p class="eyebrow"><span class="eyebrow-num">02</span><span class="sep">//</span>{e}</p>
          <h2>{h}</h2>
          <p class="lead">{l}</p>
        </div>
        <div class="recip bleed reveal">
          <svg class="rc" viewBox="0 0 980 590" role="img" aria-label="{alt}">{p}</svg>
        </div>
        <ol class="rc-legend reveal">{lg}</ol>
      </div>
    </section>

    <!-- The chart used to sit inside the section above. Two full drawings
         under one heading made that section 241% of a screen, and they are two
         different statements anyway: this is the machine, that is what it
         delivers. One section, one thing. -->
    <section class="section">
      <div class="container">
{chart}
      </div>
    </section>""".format(e=T("rec_eyebrow"), h=T("rec_h2"), l=T("rec_lead"),
                         alt=attr(T("rec_h2")), p="".join(P), lg=legend,
                         chart=capacity_chart())


def service_page(s):
    blocks = []
    for heading, paras in s["blocks"]:
        blocks.append("      <h2>%s</h2>\n%s" % (
            heading, "\n".join("      " + x for x in paras)))
    others = [o for o in services() if o["slug"] != s["slug"]]
    more = "\n".join(card(o, "h3") for o in others)
    f, w, h, alt = s["img"]

    return page_head("%s %s" % (T("svc_eyebrow"), s["num"]), s["title"], s["lead"],
                     [(T("home"), "/"), (T("svc_eyebrow"), "/services/"),
                      (s["title"], None)],
                     path="/services/%s/" % s["slug"]) + service_ld(s) + """
    <div class="container">
      <div class="page-media cornered reveal">
        <img src="{img}" alt="{alt}" width="{w}" height="{h}">
      </div>
    </div>

{recip}
    <section class="container prose">
{blocks}
    </section>

    <section class="section section-alt">
      <div class="container">
        <div class="section-head reveal">
          <p class="eyebrow">{other_e}</p>
          <h2>{other_h}</h2>
        </div>
        <div class="card-grid">
{more}
        </div>
      </div>
    </section>
{cta}""".format(img=u("/assets/photos/" + f), alt=alt, w=w, h=h,
                blocks="\n\n".join(blocks), more=more,
                # The compressor plate belongs to one page: it is that page's
                # machine. Putting a drawing on all four would make it wallpaper.
                recip=(recip_drawing() + recip_3d("unit")) if s["slug"] == "refrigeration-systems" else "",
                other_e=T("svc_eyebrow"), other_h=PT("svc_h1"),
                cta=cta(T("cta_h2"), T("cta_p")))


# ============================================================
# COMPLETED WORKS
# ============================================================
# The workshop photographs. Unlike .page-media, which holds a picture back to
# 72% and desaturates it so text can sit on top, these are shown at full
# strength: they are the evidence, not the texture behind something else.
# Four photographs exist. Two of them carry a service page each -- the valve
# range is what "spare parts" means, and the stripped compressor is what
# "refrigeration systems" means -- so the band keeps the other two rather than
# showing the same picture twice on one visit.
SHOTS = [
    ("workshop-rotors", 1254, 786, "shot_rotors", ""),
    ("workshop-bench",  1320, 968, "shot_bench",  ""),
]


def shots(num="02"):
    figs = []
    for i, (name, w, h, key, mod) in enumerate(SHOTS, 1):
        caption = PT(key)
        figs.append(
            '''          <figure class="shot{mod}">
            <img src="{img}" alt="{alt}" width="{w}" height="{h}" loading="lazy" decoding="async">
            <figcaption><span class="shot-n">{n:02d}</span>{cap}</figcaption>
          </figure>'''.format(
                mod=(" shot--" + mod) if mod else "",
                img=u("/assets/photos/%s.webp" % name),
                alt=attr(caption), w=w, h=h, n=i, cap=text(caption)))
    return """
    <section class="section shots-band seam-top seam-bottom">
      <div class="container">
        <div class="section-head reveal">
          <p class="eyebrow"><span class="eyebrow-num">{num}</span><span class="sep">//</span>{e}</p>
          <h2>{h2}</h2>
          <p class="lead">{lead}</p>
        </div>
        <div class="shots reveal">
{figs}
        </div>
      </div>
    </section>""".format(num=num, e=PT("shots_eyebrow"), h2=PT("shots_h2"),
                         lead=PT("shots_lead"), figs="\n".join(figs))


def completed_works():
    return page_head(PT("cw_eyebrow"), PT("cw_h1"), PT("cw_lead", founded=FOUNDED),
                     [(T("home"), "/"), (PT("cw_eyebrow"), None)],
                     path="/completed-works/") + """
    <section class="container prose">
      <!-- NOTE(LITPROFIT): the old site's version of this page was two headings and
           two stock photographs. To make it genuinely useful we need, per project:
           vessel or plant name, year, port, scope of work, and a photograph. That is
           the single highest-value thing the client can supply. -->
      <h2>{h1}</h2>
      <p>{p1}</p>
      {tags1}

      <h2>{h2}</h2>
      <p>{p2}</p>
      {tags2}

      <h2>{h3}</h2>
      <p>Sealord, Limarko Group, Ocean Whale Company, Baltreids &mdash;
      <a href="{partners}">{p_more}</a>.</p>
    </section>
{gallery}{projects}
{cta}""".format(h1=PT("cw_engines"), p1=PT("cw_engines_p"), tags1=tags(i18n.ENGINES),
                h2=PT("cw_refrig"), p2=PT("cw_refrig_p"), tags2=tags(i18n.SYSTEMS),
                h3=PT("cw_who"), partners=u("/partners/"),
                p_more=PT("p_clients_h2").lower(),
                gallery=shots("03"),
                projects=projects_band(),
                cta=cta(T("cta_h2"), T("cta_p")))


# ============================================================
# PARTNERS
# ============================================================
def partners():
    logos = "\n".join(client_tile(c) for c in CLIENTS)
    return page_head(PT("p_eyebrow"), PT("p_h1"), PT("p_lead"),
                     [(T("home"), "/"), (PT("p_eyebrow"), None)],
                     path="/partners/") + """
    <section class="section partners-band seam-top seam-bottom" style="padding-top: clamp(46px, 5vw, 72px)">
      <div class="container">
        <div class="section-head reveal">
          <p class="eyebrow">{rep_e}</p>
          <h2>{rep_h}</h2>
          <p class="lead">{rep_l}</p>
        </div>
        <div class="partner-grid reveal">
          <div class="partner">
            <p class="partner-role">{tp}</p>
            <h3 class="partner-logo"><img src="{bitzer}" alt="BITZER" width="454" height="159"></h3>
            <p>{rep_b}</p>
          </div>
          <div class="partner">
            <p class="partner-role">{tr}</p>
            <h3 class="partner-logo"><img src="{danfoss}" alt="Danfoss" width="126" height="55"></h3>
            <p>{rep_d}</p>
          </div>
        </div>

        <div class="section-head reveal" style="margin-top: clamp(48px, 6vw, 88px)">
          <p class="eyebrow">{cl_e}</p>
          <h2>{cl_h}</h2>
          <p class="lead">{cl_l}</p>
        </div>
        <div class="client-rail-wrap reveal">
          <ul class="client-rail" id="clientRail">
{logos}
          </ul>
          <button class="rail-btn rail-prev" type="button" aria-label="{rail_prev}"
                  data-rail="-1">&#8592;</button>
          <button class="rail-btn rail-next" type="button" aria-label="{rail_next}"
                  data-rail="1">&#8594;</button>
        </div>
      </div>
    </section>
{cta}""".format(logos=logos, rail_prev=attr(T("rail_prev")),
                rail_next=attr(T("rail_next")), rep_e=T("rep_eyebrow"), rep_h=PT("p_rep_h2"),
                rep_l=PT("p_rep_lead"), tp=T("role_bitzer"), tr=T("role_danfoss"),
                rep_b=T("rep_bitzer"), rep_d=T("rep_danfoss"),
                cl_e=T("clients_eyebrow"), cl_h=PT("p_clients_h2"),
                cl_l=PT("p_clients_lead"),
                bitzer=u("/assets/partners/bitzer.webp"),
                danfoss=u("/assets/partners/danfoss.svg"),
                cta=cta(T("cta_h2"), T("cta_p")))


# ============================================================
# CERTIFICATES
# ============================================================
def certificates():
    notes = {"RINA": PT("c_rina_note"), "PRS": PT("c_prs_note")}
    docs = "\n".join("""        <a class="doc" href="{href}" target="_blank" rel="noopener">
          <span class="doc-shot">
            <img src="{shot}" alt="{alt}" width="{sw}" height="{sh}" loading="lazy" decoding="async">
          </span>
          <span class="doc-body">
            <span class="doc-name">{name}</span>
            <span class="doc-note">{note}</span>
            <span class="doc-facts">
              <span><i>{l_no}</i>{no}</span>
              <span><i>{l_issued}</i>{issued}</span>
              <span><i>{l_valid}</i>{valid}</span>
            </span>
            <span class="doc-get">{open} <span class="doc-size">PDF {size}</span></span>
          </span>
        </a>""".format(href=u("/assets/certs/" + c["file"]),
                       shot=u("/assets/certs/" + c["file"].replace(".pdf", ".webp")),
                       sw=img_size("assets/certs/" + c["file"].replace(".pdf", ".webp"))[0],
                       sh=img_size("assets/certs/" + c["file"].replace(".pdf", ".webp"))[1],
                       alt=attr(PT("c_shot_alt", name=c["name"])),
                       name=c["name"], note=notes[c["name"]], size=c["size"],
                       no=c["no"], issued=c["issued"], valid=c["valid"],
                       l_no=PT("c_no"), l_issued=PT("c_issued"), l_valid=PT("c_valid"),
                       open=PT("c_open")) for c in CERTIFICATES)

    return page_head(PT("c_eyebrow"), PT("c_h1"), PT("c_lead"),
                     [(T("home"), "/"), (PT("c_eyebrow"), None)],
                     path="/certificates/") + """
    <section class="section" style="padding-top: 0">
      <div class="container">
        <div class="docs reveal">
{docs}
        </div>
      </div>
    </section>

    <section class="container prose">
      <h2>{h_scope}</h2>
      <p>{p_scope}</p>
      <ul class="scope-list">
{scope}
      </ul>
      <p>{p_scope_x}</p>

      <h2>{h_what}</h2>
      <p>{p_what}</p>
      <h2>{h_ins}</h2>
      <p>{p_ins}</p>
      <h2>{h_war}</h2>
      <p>{p_war}</p>
    </section>
{cta}""".format(docs=docs, h_what=PT("c_what"), p_what=PT("c_what_p"),
                h_ins=PT("c_ins"), p_ins=PT("a_cert_2"),
                h_war=PT("c_war"), p_war=PT("c_war_p"),
                h_scope=PT("c_scope_h"), p_scope=PT("c_scope_lead"),
                p_scope_x=PT("c_scope_extra"),
                scope="\n".join("        <li>%s</li>" % text(x)
                                 for x in i18n.P[LANG]["c_scope"]),
                cta=cta(T("cta_h2"), T("cta_p")))


# ============================================================
# CONTACTS
# ============================================================
def contacts():
    return page_head(PT("k_eyebrow"), PT("k_h1"), PT("k_lead"),
                     [(T("home"), "/"), (PT("k_eyebrow"), None)],
                     path="/contacts/") + """
    <section class="section" style="padding-top: 0">
      <div class="container contact-grid">
        <div class="reveal">
          <div class="contact-block">
            <h2 class="block-title">{l_addr}</h2>
            <p>{legal}<br>{street}<br>{city}<br>{country}</p>
          </div>
          <div class="contact-block">
            <h2 class="block-title">{l_phone}</h2>
            <p><a href="tel:{phone_href}">{phone}</a></p>
          </div>
          <div class="contact-block">
            <h2 class="block-title">{l_email}</h2>
            <p><a href="mailto:{email}">{email}</a></p>
          </div>
          <div class="contact-block">
            <h2 class="block-title">{l_details}</h2>
            <p>{l_cid}: {cid}<br>{l_vat}: {vat}</p>
          </div>
          <div class="contact-block">
            <h2 class="block-title">{l_service}</h2>
            <p>{p_service}</p>
          </div>
        </div>

        <div class="reveal">
          <h2>{form_h2}</h2>
          <p class="lead" style="margin-bottom: 28px; font-size: var(--text-m)">{form_lead}</p>

          <form class="form" id="enquiryForm" novalidate>
            <div class="field">
              <label for="fName">{f_name}</label>
              <input id="fName" name="name" type="text" required autocomplete="name">
            </div>
            <div class="field">
              <label for="fCompany">{f_company} <span class="opt">{f_opt}</span></label>
              <input id="fCompany" name="company" type="text" autocomplete="organization">
            </div>
            <div class="field">
              <label for="fPhone">{f_phone} <span class="opt">{f_opt}</span></label>
              <input id="fPhone" name="phone" type="tel" autocomplete="tel">
            </div>
            <div class="field">
              <label for="fEmail">{f_email}</label>
              <input id="fEmail" name="email" type="email" required autocomplete="email">
            </div>
            <div class="field">
              <label for="fMsg">{f_msg}</label>
              <textarea id="fMsg" name="message" rows="6" required
                        placeholder="{f_ph}"></textarea>
            </div>
            <div class="field field-check">
              <input id="fConsent" name="consent" type="checkbox" required>
              <label for="fConsent">{consent}</label>
            </div>
            <div class="field">
              <button type="submit" class="btn btn-solid">{f_send}</button>
              <p class="form-note" id="formNote" role="status" aria-live="polite"></p>
            </div>
          </form>
        </div>
      </div>
    </section>
""".format(l_addr=T("f_address"), legal=LEGAL, street=T("addr_street"), city=T("addr_city"),
           country=COUNTRY, l_phone=T("form_phone"), phone=PHONE,
           phone_href=PHONE_HREF, l_email=T("form_email"), email=EMAIL,
           l_details=T("f_details"), l_cid=T("company_no"), cid=COMPANY_ID,
           l_vat=T("vat"), vat=VAT, l_service=PT("k_service"),
           p_service=PT("k_service_p"), form_h2=PT("k_form_h2"),
           form_lead=PT("k_form_lead"), f_name=T("form_name"),
           f_company=T("form_company"), f_opt=T("form_optional"),
           f_phone=T("form_phone"), f_email=T("form_email"),
           f_msg=T("form_message"), f_ph=attr(T("form_placeholder")),
           f_send=T("form_send"),
           consent=T("form_consent", legal=LEGAL,
                     privacy='<a href="%s">%s</a>' % (u("/privacy/"),
                                                      T("form_privacy_link"))))


# ============================================================
# PRIVACY
# ============================================================
def privacy():
    h = i18n.P[LANG]["pr_h"]
    return page_head(PT("pr_eyebrow"), PT("pr_h1"), PT("pr_lead", legal=LEGAL),
                     [(T("home"), "/"), (PT("pr_h1"), None)],
                     path="/privacy/") + """
    <section class="container prose">
      <!-- NOTE(LITPROFIT): this describes what the site technically does today.
           It has NOT been reviewed by a lawyer, and the Lithuanian and Russian are
           translations for convenience. Have all three checked before launch. -->
      <p><strong>{l_upd}:</strong> {today}</p>

      <h2>1. {h0}</h2>
      <p>{who}</p>
      <ul>
        <li>{street}, {city}, {country}</li>
        <li><a href="mailto:{email}">{email}</a></li>
        <li><a href="tel:{phone_href}">{phone}</a></li>
        <li>{l_cid}: {cid}</li>
      </ul>

      <h2>2. {h1}</h2><p>{collect}</p>
      <h2>3. {h2}</h2><p>{third}</p>
      <h2>4. {h3}</h2><p>{basis}</p>
      <h2>5. {h4}</h2><p>{keep}</p>
      <h2>6. {h5}</h2><p>{rights}</p>
      <h2>7. {h6}</h2><p>{changes}</p>
    </section>
""".format(l_upd=PT("pr_updated"), today=datetime.date.today().isoformat(),
           h0=h[0], h1=h[1], h2=h[2], h3=h[3], h4=h[4], h5=h[5], h6=h[6],
           who=PT("pr_who", legal=LEGAL), street=T("addr_street"), city=T("addr_city"),
           country=COUNTRY, email=EMAIL, phone=PHONE, phone_href=PHONE_HREF,
           l_cid=T("company_no"), cid=COMPANY_ID,
           collect=PT("pr_collect"), third=PT("pr_third"), basis=PT("pr_basis"),
           keep=PT("pr_keep"), rights=PT("pr_rights", email=EMAIL),
           changes=PT("pr_changes"))


# ============================================================
# CAREERS
#
# POSITIONS is the only block to edit when a vacancy opens or closes. It is
# EMPTY on purpose: no real vacancies have been supplied, and inventing job
# adverts for a real company would put fictional roles into Google for Jobs
# under their name. With the list empty the page shows the open-application
# route instead, which is true.
#
# To open a role, add a dict with:
#   id, title, count, location, contract, posted (YYYY-MM-DD),
#   valid_through, employment_type, summary, needs (list)
# per language key. Set open=False to retire it without deleting it.
# ============================================================
POSITIONS = [
    dict(
        id="refrigeration-service-engineer",
        open=True,
        # SAMPLE. Set sample=False once this is a real, approved vacancy — that
        # single flag is what lets the JobPosting structured data be emitted and
        # removes the EXAMPLE badge. Until then the role is visible on the page
        # so the layout can be reviewed, but it is NOT published to Google for
        # Jobs: a fictional role indexed under the company's name is the
        # client's problem, not a preview artefact.
        sample=True,
        posted="2026-08-19",
        valid_through="2026-12-31",
        employment_type="FULL_TIME",
        en=dict(title="Refrigeration Service Engineer",
                count="1 position", location="Klaipeda + vessels", contract="Full time",
                summary="Service, fault-finding and overhaul of marine and industrial "
                        "refrigeration plant — compressors, controls and refrigerant "
                        "piping — in the workshop, on board in Klaipeda, and on travel "
                        "jobs where the vessel is.",
                needs=["Experience with screw or reciprocating refrigeration compressors.",
                       "Ability to fault-find on a running plant, not only to replace parts.",
                       "Refrigerant handling certification, or readiness to obtain it.",
                       "Readiness to travel at short notice.",
                       "Working English; Lithuanian or Russian an advantage."]),
        lt=dict(title="Šaldymo įrangos serviso inžinierius",
                count="1 pozicija", location="Klaipėda + laivai", contract="Visa darbo diena",
                summary="Laivų ir pramoninės šaldymo įrangos aptarnavimas, gedimų "
                        "nustatymas ir remontas — kompresoriai, valdymo sistemos ir "
                        "šaltnešio vamzdynai — dirbtuvėse, laivuose Klaipėdoje ir "
                        "komandiruotėse ten, kur yra laivas.",
                needs=["Patirtis su sraigtiniais arba stūmokliniais šaldymo kompresoriais.",
                       "Gebėjimas nustatyti gedimus veikiančioje sistemoje, o ne tik keisti dalis.",
                       "Šaltnešių tvarkymo pažymėjimas arba pasirengimas jį įgyti.",
                       "Pasirengimas vykti į komandiruotes trumpu įspėjimu.",
                       "Anglų kalba; lietuvių ar rusų — privalumas."]),
        ru=dict(title="Инженер по сервису холодильного оборудования",
                count="1 позиция", location="Клайпеда + суда", contract="Полная занятость",
                summary="Обслуживание, поиск неисправностей и ремонт судового и "
                        "промышленного холодильного оборудования — компрессоры, "
                        "автоматика и трубопроводы хладагента — в мастерской, на судах "
                        "в Клайпеде и в командировках там, где находится судно.",
                needs=["Опыт работы с винтовыми или поршневыми холодильными компрессорами.",
                       "Умение находить неисправности на работающей установке, а не только менять детали.",
                       "Сертификат на обращение с хладагентами или готовность его получить.",
                       "Готовность к командировкам в короткие сроки.",
                       "Рабочий английский; литовский или русский — преимущество."]),
    ),
]


def positions_html():
    live = [p for p in POSITIONS if p.get("open")]
    C = i18n.CAR[LANG]
    if not live:
        return """      <div class="notice">
        <p><strong>%s.</strong> %s</p>
      </div>""" % (C["none_h"], C["none_p"])
    out = []
    for p in live:
        d = p[LANG] if LANG in p else p["en"]
        needs = "\n".join("          <li>%s</li>" % n for n in d["needs"])
        badge = ('<span class="position-sample">%s</span>' % i18n.CAR[LANG]["sample"]
                 if p.get("sample") else "")
        out.append("""      <article class="position" id="{pid}">
        <div class="position-head">
          <h3>{title}</h3>
          <p class="position-meta">{badge}<span>{count}</span><span>{location}</span><span>{contract}</span></p>
        </div>
        <p>{summary}</p>
        <ul>
{needs}
        </ul>
      </article>""".format(pid=p["id"], needs=needs, badge=badge,
                              **{k: v for k, v in d.items() if k != "needs"}))
    return "\n".join(out)


def job_postings_ld():
    """Google for Jobs. Emitted only for genuinely open roles — an empty
    POSITIONS list produces no structured data at all, rather than an empty
    shell that would be flagged as invalid."""
    out = []
    for p in POSITIONS:
        if not p.get("open"):
            continue
        # A sample role renders on the page but is never published as structured
        # data. Google for Jobs would otherwise index a vacancy that does not
        # exist, under this company's name.
        if p.get("sample"):
            continue
        d = p.get(LANG, p["en"])
        out.append(jsonld({
            "@context": "https://schema.org",
            "@type": "JobPosting",
            "title": d["title"],
            "description": "<p>%s</p><ul>%s</ul>" % (
                d["summary"], "".join("<li>%s</li>" % n for n in d["needs"])),
            "datePosted": p["posted"],
            "validThrough": p["valid_through"] + "T23:59",
            "employmentType": p["employment_type"],
            "hiringOrganization": {"@type": "Organization", "name": LEGAL,
                                   "sameAs": lang_url("en", "/")},
            "jobLocation": [{"@type": "Place", "address": {
                "@type": "PostalAddress", "streetAddress": STREET,
                "addressLocality": "Klaipeda", "postalCode": "LT-94101",
                "addressCountry": "LT"}}],
            "directApply": True,
        }))
    return "".join(out)


def careers():
    C = i18n.CAR[LANG]
    disc = "\n".join("        <li>%s</li>" % x for x in C["disc"])
    matters = "\n".join("        <li>%s</li>" % x for x in C["matters"])
    return page_head(C["nav"], C["h1"], C["lead"],
                     [(T("home"), "/"), (C["nav"], None)],
                     path="/careers/") + """
    <section class="container prose">
      <h2>{open_h2}</h2>
{positions}

      <h2>{disc_h2}</h2>
      <p>{disc_p}</p>
      <ul>
{disc}
      </ul>

      <h2>{matters_h2}</h2>
      <ul>
{matters}
      </ul>
    </section>

    <section class="section section-alt seam-top" id="apply">
      <div class="container contact-grid">
        <div class="reveal">
          <h2>{apply_h2}</h2>
          <p class="lead" style="font-size: var(--text-m); margin-top: 18px">{apply_p}</p>
        </div>
        <div class="reveal">
          <form class="form" id="applyForm" novalidate>
            <div class="field">
              <label for="aName">{f_name}</label>
              <input id="aName" name="name" type="text" required autocomplete="name">
            </div>
            <div class="field">
              <label for="aEmail">{f_email}</label>
              <input id="aEmail" name="email" type="email" required autocomplete="email">
            </div>
            <div class="field">
              <label for="aPhone">{f_phone} <span class="opt">{f_opt}</span></label>
              <input id="aPhone" name="phone" type="tel" autocomplete="tel">
            </div>
            <div class="field">
              <label for="aRole">{f_role}</label>
              <input id="aRole" name="role" type="text" required placeholder="{f_open}">
            </div>
            <div class="field">
              <label for="aExp">{f_exp}</label>
              <textarea id="aExp" name="message" rows="6" required
                        placeholder="{f_exp_ph}"></textarea>
            </div>
            <div class="field field-check">
              <input id="aConsent" name="consent" type="checkbox" required>
              <label for="aConsent">{consent}</label>
            </div>
            <div class="field">
              <button type="submit" class="btn btn-solid">{f_send}</button>
              <p class="form-note" id="applyNote" role="status" aria-live="polite"></p>
            </div>
          </form>
        </div>
      </div>
    </section>
""".format(positions=positions_html(), disc=disc, matters=matters,
           open_h2=C["open_h2"], disc_h2=C["disc_h2"], disc_p=C["disc_p"],
           matters_h2=C["matters_h2"], apply_h2=C["apply_h2"], apply_p=C["apply_p"],
           f_name=T("form_name"), f_email=T("form_email"), f_phone=T("form_phone"),
           f_opt=T("form_optional"), f_role=C["f_role"], f_open=attr(C["f_open"]),
           f_exp=C["f_exp"], f_exp_ph=attr(C["f_exp_ph"]), f_send=C["f_send"],
           consent=C["consent"] % dict(legal=LEGAL,
               privacy='<a href="%s">%s</a>' % (u("/privacy/"), T("form_privacy_link"))))


# ============================================================
# STRUCTURED DATA
# ============================================================
def org_ld():
    return ('  <script type="application/ld+json">\n  %s\n  </script>\n'
            % json.dumps({
                "@context": "https://schema.org",
                "@type": "Organization",
                "name": LEGAL,
                "alternateName": NAME,
                "url": canonical("/"),
                "logo": ORIGIN + u("/assets/brand/favicon.svg"),
                "foundingDate": FOUNDED,
                "description": TAGLINE,
                "vatID": VAT,
                "taxID": COMPANY_ID,
                "address": {
                    "@type": "PostalAddress",
                    "streetAddress": STREET,
                    "addressLocality": "Klaipeda",
                    "postalCode": "LT-94101",
                    "addressCountry": "LT",
                },
                "contactPoint": {
                    "@type": "ContactPoint",
                    "telephone": "+37067020357",
                    "email": EMAIL,
                    "contactType": "customer service",
                    "availableLanguage": ["en", "lt", "ru"],
                },
            }, indent=2, ensure_ascii=False).replace("\n", "\n  "))


# ============================================================
# BUILD
# ============================================================
def pages():
    """The eight standard pages, in the language being built."""
    return [
        ("/", "%s — %s" % (NAME, T("tagline")), T("hero_lead", legal=LEGAL),
         home, org_ld()),
        ("/about/", PT("about_eyebrow"),
         PT("about_meta", legal=LEGAL, founded=FOUNDED), about, ""),
        ("/services/", T("svc_eyebrow"), PT("svc_meta"), services_index, ""),
        ("/completed-works/", PT("cw_eyebrow"), PT("cw_meta", legal=LEGAL),
         completed_works, ""),
        ("/partners/", PT("p_eyebrow"), PT("p_meta"), partners, ""),
        ("/certificates/", PT("c_eyebrow"), PT("c_meta"), certificates, ""),
        ("/contacts/", PT("k_eyebrow"),
         PT("k_meta", street=T("addr_street"), city=T("addr_city"), country=T("addr_country"),
            phone=PHONE, email=EMAIL), contacts, ""),
        ("/careers/", i18n.CAR[LANG]["nav"],
         i18n.CAR[LANG]["meta"] % dict(legal=LEGAL), careers, job_postings_ld()),
        ("/privacy/", PT("pr_h1"), PT("pr_lead", legal=LEGAL), privacy, ""),
    ]


def notfound_body():
    return """
    <section class="container notfound">
      <div>
        <p class="code">404</p>
        <h1>{h1}</h1>
        <p class="lead" style="margin: 20px auto 0">{lead}</p>
        <div class="btn-row" style="justify-content: center">
          <a class="btn btn-solid" href="{home}">{b1}</a>
          <a class="btn btn-outline" href="{contacts}">{b2}</a>
        </div>
      </div>
    </section>
""".format(h1=PT("nf_h1"), lead=PT("nf_lead"), home=u("/"),
           contacts=u("/contacts/"), b1=PT("nf_home"), b2=PT("nf_contact"))


# ---------------- write every language ----------------
SITEMAP_ROWS = []

for _lang in i18n.LANGS:
    LANG = _lang
    for path, title, desc, fn, extra in pages():
        write(outfile(path), page(path, title, desc, fn(), head_extra=extra))
        SITEMAP_ROWS.append((_lang, path))
    for _s in services():
        _p = "/services/%s/" % _s["slug"]
        write(outfile(_p), page(_p, _s["title"], _s["meta"], service_page(_s)))
        SITEMAP_ROWS.append((_lang, _p))
    # One page per completed job. The list is empty, so this loop does nothing
    # and no /completed-works/<slug>/ exists -- add a job and the page, the
    # card and the sitemap line all appear together.
    for _pr in i18n.PROJECTS:
        _p = project_url(_pr)
        write(outfile(_p), page(_p, _pr["title"], _pr["lead"], project_page(_pr)))
        SITEMAP_ROWS.append((_lang, _p))

# 404 is served by GitHub Pages for any unmatched path anywhere on the host, so
# there is one, in English, at the root.
LANG = "en"
write("404.html", page("/404.html", PT("nf_h1"), PT("nf_lead"), notfound_body(),
                       noindex=True, active=""))


# ---------------- sitemap ----------------
# Built from the same list that wrote the HTML, so a renamed page cannot leave a
# dead URL behind, and every language is listed with its alternates.
FREQ = {"/": ("monthly", "1.0"), "/services/": ("monthly", "0.9"),
        "/about/": ("monthly", "0.8"), "/completed-works/": ("monthly", "0.7"),
        "/partners/": ("monthly", "0.7"), "/certificates/": ("yearly", "0.6"),
        "/contacts/": ("yearly", "0.7"), "/careers/": ("monthly", "0.6"),
        "/privacy/": ("yearly", "0.2")}


def sitemap_xml():
    rows = []
    for lang, path in SITEMAP_ROWS:
        freq, pri = FREQ.get(path, ("monthly", "0.8"))
        alts = "\n".join(
            '    <xhtml:link rel="alternate" hreflang="%s" href="%s"/>'
            % (i18n.LOCALE[lg][0], lang_url(lg, path)) for lg in i18n.LANGS)
        rows.append(
            "  <url>\n"
            "    <loc>%s</loc>\n%s\n"
            "    <lastmod>%s</lastmod>\n"
            "    <changefreq>%s</changefreq>\n"
            "    <priority>%s</priority>\n"
            "  </url>" % (lang_url(lang, path), alts, LASTMOD, freq, pri))
    return ('<?xml version="1.0" encoding="UTF-8"?>\n'
            '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9"\n'
            '        xmlns:xhtml="http://www.w3.org/1999/xhtml">\n'
            + "\n".join(rows) + "\n</urlset>\n")


write("sitemap.xml", sitemap_xml())
# The calculator is private and encrypted; it is in no sitemap and no menu,
# and crawlers are asked to leave it alone. Its contents are unreadable
# without the passphrase either way — this just keeps it out of results.
write("robots.txt",
      "User-agent: *\nAllow: /\nDisallow: %s/calculator/\n\nSitemap: %s\n"
      % (BASE, ORIGIN + BASE + "/sitemap.xml"))

print("\nBASE=%r ORIGIN=%r  languages=%s" % (BASE, ORIGIN, ",".join(i18n.LANGS)))
print("Set BASE='' and ORIGIN to the live domain, add CNAME, and rebuild to migrate.")
