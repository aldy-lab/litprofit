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
    return ('<div class="langs" role="group" aria-label="%s">%s</div>'
            % (attr(T("lang_label")), "".join(out)))


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
          </ul>
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
           fonts_css=u("/css/fonts.css"), style_css=u("/css/style.css"),
           js=u("/js/main.js"), head_extra=head_extra,
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


def page_head(eyebrow, h1, lead, trail=None, path=None):
    return """
    <section class="container page-head">
      {crumb}
      <p class="eyebrow">{sheet}{eyebrow}</p>
      <h1>{h1}</h1>
      <p class="lead">{lead}</p>
    </section>
""".format(crumb=crumb(trail) if trail else "", eyebrow=eyebrow, h1=h1, lead=lead,
           sheet=sheet_tag(path) if path else "")


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
    dict(name="RINA", file="rina-certificate-2025.pdf", size="329 KB", thumb_h=1165,
         no="REC037725XF", issued="2025-05-08", valid="2028-05-12",
         note="Italian classification society"),
    dict(name="PRS", file="prs-certificate.pdf", size="961 KB", thumb_h=1273,
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
    return """          <a class="{cls}" href="{href}">
            <span class="card-media">
              <span class="card-num">{num}</span>
              <img src="{img}" alt="{alt}" width="{w}" height="{h}" loading="lazy">
            </span>
            <span class="card-body">
              <{lv}>{title}</{lv}>
              <p>{short}</p>
              <span class="card-more">{more}</span>
            </span>
          </a>""".format(cls=cls, href=u("/services/%s/" % s["slug"]),
                         img=u("/assets/photos/" + f),
                         alt=alt, w=w, h=h, lv=level, num=s["num"],
                         title=s["title"], short=s["short"], more=T("read_more"))


# Refrigeration leads: it is the company's original discipline and the one it
# has the deepest bench in, so it gets the feature card rather than being one
# of four equal boxes — and, being first, it is 01.
FEATURE_SLUG = "refrigeration-systems"




def service_cards(level="h3"):
    sv = services()
    out = [card(sv[0], level, "feature")]
    out += [card(x, level, "compact") for x in sv[1:]]
    return "\n".join(out)


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

    # discharge: compressors -> condensers (high pressure)
    add('<path class="rp-pipe rp-hp" d="M348 138 L420 138 L420 300 L248 300 L248 320"/>')
    add('<path class="rp-pipe rp-hp" d="M348 512 L420 512 L420 674 L248 674 L248 694"/>')
    # liquid line: condensers -> receiver header -> rooms
    add('<path class="rp-pipe rp-lq" d="M426 358 L640 358 L640 620 L700 620"/>')
    add('<path class="rp-pipe rp-lq" d="M426 732 L640 732"/>')
    add('<path class="rp-pipe rp-lq" d="M700 620 L700 170 L790 170"/>')
    add('<path class="rp-pipe rp-lq" d="M700 200 L1190 200"/>')
    add('<path class="rp-pipe rp-lq" d="M700 574 L1190 574"/>')
    # suction: rooms -> accumulators (low pressure)
    add('<path class="rp-pipe rp-lp" d="M930 396 L930 440 L560 440 L560 200 L96 200"/>')
    add('<path class="rp-pipe rp-lp" d="M1340 396 L1340 452 L590 452 L590 574"/>')
    add('<path class="rp-pipe rp-lp" d="M1340 770 L1340 812 L560 812 L560 574 L96 574"/>')

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
      <div class="container hero-inner">
        <p class="eyebrow eyebrow-plain">{he} <span class="sep">//</span> {hs} {founded}</p>
        <h1>{h1}</h1>
        <p class="lead">{hlead}</p>
        <ul class="promise">
          <li><a href="#consult"><span class="step-num">01</span><span class="step-label">{s1}</span></a></li>
          <li><a href="#organise"><span class="step-num">02</span><span class="step-label">{s2}</span></a></li>
          <li><a href="#ensure"><span class="step-num">03</span><span class="step-label">{s3}</span></a></li>
        </ul>
        <div class="btn-row">
          <a class="btn btn-solid" href="{book}"{book_attrs}>{book_label}</a>
          <a class="btn btn-outline" href="{services}">{hsvc}</a>
        </div>
        <p class="hero-trust">
          <span>{tp} <b>BITZER</b></span>
          <span>{tr} <b>DANFOSS</b></span>
          <span>{tc} <b>RINA</b> <span class="sep">//</span> <b>PRS</b></span>
          <!-- Rides at the end of the trust rule rather than floating over the
               hero's bottom edge: absolutely positioned, it collided with this
               strip the moment the hero was tightened to fit a laptop. In the
               flow it costs no height at all and cannot collide with anything. -->
          <button type="button" class="frost-note" id="frostToggle"
                  aria-pressed="false" data-on="{fha}" data-off="{fho}" title="{fha}">
            <span class="frost-lead" aria-hidden="true"></span>
            <svg class="frost-flake" viewBox="0 0 16 16" aria-hidden="true">
              <g stroke="currentColor" stroke-width="1.1" stroke-linecap="round">
                <path d="M8 1.6v12.8M2.5 4.8l11 6.4M2.5 11.2l11-6.4"/>
                <path d="M5.9 3.1 8 4.5l2.1-1.4M5.9 12.9 8 11.5l2.1 1.4"/>
              </g>
            </svg>
            <span>{fh}</span>
            <span class="visually-hidden">{fha}</span>
          </button>
        </p>
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

    <section class="section">
      <div class="container">
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

    <section class="section">
      <div class="container split">
        <div class="reveal">
          <p class="eyebrow"><span class="eyebrow-num">03</span><span class="sep">//</span>{how_e}</p>
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

{cycle}
    <section class="section section-alt">
      <div class="container">
        <div class="split" style="align-items: center">
          <div class="reveal">
            <p class="eyebrow"><span class="eyebrow-num">05</span><span class="sep">//</span>{cap_e}</p>
            <h2 class="lightwords">{cap_h}</h2>
            <p class="lead">{cap_l}</p>
            <div class="btn-row">
              <a class="btn btn-outline" href="{refrig}">{refrig_label}</a>
            </div>
          </div>
          <div class="media-panel cornered reveal">
            <img src="{plant_img}" alt="Industrial refrigeration compressor plant"
                 width="800" height="555" loading="lazy">
          </div>
        </div>

        <div class="section-head reveal" style="margin-top: clamp(56px, 7vw, 104px)">
          <p class="eyebrow"><span class="eyebrow-num">06</span><span class="sep">//</span>{cl_e}</p>
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
                hero_drawing=hero_drawing(),
                rail_prev=attr(T("rail_prev")), rail_next=attr(T("rail_next")),
                hero_drawing_lit=hero_drawing(lit=True),
                he=T("hero_eyebrow"), hs=T("hero_since"), h1=T("hero_h1"),
                hlead=T("hero_lead", legal=LEGAL), s1=T("step1"), s2=T("step2"),
                s3=T("step3"), hsvc=T("hero_services"), tp=T("role_bitzer"),
                tr=T("role_danfoss"), tc=T("trust_cert"),
                fh=text(T("frost_hint")), fha=attr(T("frost_hint_a11y")),
                fho=attr(T("frost_hint_off")),
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
          <p class="eyebrow"><span class="eyebrow-num">04</span><span class="sep">//</span>{ga_e}</p>
          <h2>{ga_h}</h2>
          <p class="lead">{ga_l}</p>
        </div>

        <div class="drawing reveal" id="drawing">
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
def about():
    spec = "\n".join("        <li>%s</li>" % x for x in i18n.P[LANG]["a_spec_list"])
    return page_head(PT("about_eyebrow"), PT("about_h1"),
                     PT("about_lead", legal=LEGAL, founded=FOUNDED),
                     [(T("home"), "/"), (PT("about_eyebrow"), None)],
                     path="/about/") + """
    <div class="container">
      <div class="page-media page-media--low cornered reveal">
        <img src="{shot}" alt="{shot_alt}" width="1320" height="968">
      </div>
    </div>

    <section class="container prose">
      <h2>{h_spec}</h2>
      <ul>
{spec}
      </ul>

      <h2>{h_people}</h2>
      <p>{people1}</p>
      <p>{people2}</p>

      <h2>{h_how}</h2>
      <h3>{s1}</h3><p>{how1}</p>
      <h3>{s2}</h3><p>{how2}</p>
      <h3>{s3}</h3><p>{how3}</p>

      <h2>{h_cert}</h2>
      <p>{cert1} <a href="{certs}">{c_more}</a></p>
      <p>{cert2}</p>

      <h2>{h_rep}</h2>
      <p>{rep_l} <a href="{partners}">{p_more}</a></p>

      <h2>{h_details}</h2>
      <p>{legal}<br>{street}<br>{city}<br>{country}<br>
      {l_cid}: {cid}<br>{l_vat}: {vat}</p>
    </section>
{cta}""".format(spec=spec, h_spec=PT("a_spec"), h_people=PT("a_people"),
                shot=u("/assets/photos/workshop-bench.webp"),
                shot_alt=attr(PT("shot_bench")),
                people1=PT("a_people_1"), people2=PT("a_people_2"),
                h_how=T("how_h2"), s1=T("step1"), s2=T("step2"), s3=T("step3"),
                how1=T("how1"), how2=T("how2"), how3=T("how3"),
                h_cert=PT("a_cert"), cert1=PT("a_cert_1", legal=LEGAL),
                cert2=PT("a_cert_2"), certs=u("/certificates/"),
                c_more=PT("c_eyebrow").lower(), h_rep=T("rep_eyebrow"),
                rep_l=T("rep_lead"), partners=u("/partners/"),
                p_more=PT("p_eyebrow").lower(), h_details=PT("a_details"),
                legal=LEGAL, street=T("addr_street"), city=T("addr_city"), country=T("addr_country"),
                l_cid=T("company_no"), cid=COMPANY_ID, l_vat=T("vat"), vat=VAT,
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
                      (s["title"], None)]) + """
    <div class="container">
      <div class="page-media cornered reveal">
        <img src="{img}" alt="{alt}" width="{w}" height="{h}">
      </div>
    </div>

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
{gallery}
{cta}""".format(h1=PT("cw_engines"), p1=PT("cw_engines_p"), tags1=tags(i18n.ENGINES),
                h2=PT("cw_refrig"), p2=PT("cw_refrig_p"), tags2=tags(i18n.SYSTEMS),
                h3=PT("cw_who"), partners=u("/partners/"),
                p_more=PT("p_clients_h2").lower(),
                gallery=shots("03"),
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
            <img src="{shot}" alt="{alt}" width="900" height="{sh}" loading="lazy" decoding="async">
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
                       sh=c.get("thumb_h", 1200),
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
