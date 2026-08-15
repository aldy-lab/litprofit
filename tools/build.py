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
import io
import json
import os
import re

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
STREET = "Svajones str. 30"
CITY = "LT-94101 Klaipeda"
COUNTRY = "Lithuania"
COMPANY_ID = "302568798"
VAT = "LT100005766815"
FOUNDED = "2010"

# The logo lockup is the supplied monogram plus the name set in the site
# typeface. The guidelines' own heavy wordmark has not been supplied as
# vector artwork — the only outlined lettering in the page SVG is the section
# title "FONTS" and the light page furniture, neither of which is the
# wordmark. Set LOGO_LOCKUP to a real lockup SVG when one arrives and it
# replaces mark + text everywhere.
LOGO_MARK = "/assets/brand/logo-mark-white.svg"
LOGO_LOCKUP = ""

# Header call-to-action. Set this to the company's Calendly link and the
# button points at it; while it is empty the button falls back to the
# contacts page, so nothing dead ever ships.
BOOKING_URL = ""      # e.g. "https://calendly.com/litprofit/30min"
BOOKING_LABEL = "Book a call"

LASTMOD = datetime.date.today().isoformat()


def u(path):
    """Site-absolute URL for a path, honouring BASE."""
    if path == "/":
        return BASE + "/" if BASE else "/"
    return BASE + path


def canonical(path):
    return ORIGIN + u(path)




def lockup():
    """The brand lockup: monogram + name."""
    if LOGO_LOCKUP:
        return '<img class="brand-lockup" src="%s" alt="%s" width="467" height="100">' % (
            u(LOGO_LOCKUP), NAME)
    # alt="" on the mark: the adjacent text already names the company, and a
    # second "LITPROFIT" would be read out twice by a screen reader.
    return ('<img class="brand-mark" src="%s" alt="" width="272" height="200">'
            '<span class="brand-word">%s</span>' % (u(LOGO_MARK), NAME))


# ============================================================
# NAVIGATION
# ============================================================
NAV = [
    ("About", "/about/"),
    ("Services", "/services/"),
    ("Completed works", "/completed-works/"),
    ("Partners", "/partners/"),
    ("Certificates", "/certificates/"),
    ("Contacts", "/contacts/"),
]


def header(active):
    items = "\n".join(
        '        <a href="%s"%s>%s</a>' % (
            u(href), ' aria-current="page"' if href == active else "", label)
        for label, href in NAV)
    return """  <a class="skip-link" href="#main">Skip to content</a>

  <header class="site-header">
    <nav class="nav" aria-label="Main">
      <a class="brand" href="{home}" aria-label="{name} — home">{logo}</a>

      <div class="nav-links" id="navLinks">
{items}
        <a class="nav-cta-mobile" href="{book}"{book_attrs}>{book_label}</a>
      </div>

      <div class="nav-actions">
        <a class="btn btn-book" href="{book}"{book_attrs}>{book_label}</a>
        <button class="burger" type="button" aria-label="Menu"
                aria-expanded="false" aria-controls="navLinks">
          <span></span><span></span><span></span>
        </button>
      </div>
    </nav>
  </header>""".format(home=u("/"), logo=lockup(),
                      name=NAME, items=items,
                      book=BOOKING_URL or u("/contacts/"),
                      book_attrs=' target="_blank" rel="noopener"' if BOOKING_URL else "",
                      book_label=BOOKING_LABEL)


FOOTER = """  <footer class="site-footer">
    <div class="container">
      <div class="footer-top">
        <div class="footer-col footer-brand">
          <div class="brand">{logo}</div>
          <p>{tagline}</p>
        </div>

        <div class="footer-col">
          <h2 class="col-title">Address</h2>
          <p>{street}<br>{city}<br>{country}</p>
        </div>

        <div class="footer-col">
          <h2 class="col-title">Contacts</h2>
          <ul>
            <li><a href="tel:{phone_href}">{phone}</a></li>
            <li><a href="mailto:{email}">{email}</a></li>
          </ul>
        </div>

        <div class="footer-col">
          <h2 class="col-title">Company details</h2>
          <p>{legal}<br>ID: {cid}<br>VAT: {vat}</p>
        </div>

        <div class="footer-col">
          <h2 class="col-title">Site</h2>
          <ul>
{navlinks}
          </ul>
        </div>
      </div>

      <div class="footer-bottom">
        <span>&copy; {founded}&ndash;<span data-year>2026</span> {legal}</span>
        <span class="spacer"><a href="{privacy}">Privacy policy</a></span>
      </div>
    </div>
  </footer>""".format(
    logo=lockup(), name=NAME, tagline=TAGLINE,
    street=STREET, city=CITY, country=COUNTRY, phone=PHONE, phone_href=PHONE_HREF,
    email=EMAIL, legal=LEGAL, cid=COMPANY_ID, vat=VAT, founded=FOUNDED,
    privacy=u("/privacy/"),
    navlinks="\n".join('            <li><a href="%s">%s</a></li>' % (u(h), l)
                       for l, h in NAV))


# ============================================================
# PAGE SHELL
# ============================================================
def page(path, title, description, body, head_extra="", noindex=False, active=None):
    full_title = title if title.startswith(NAME) else "%s — %s" % (title, NAME)
    robots = "noindex, follow" if noindex else "index, follow"
    return """<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>{full_title}</title>
  <meta name="description" content="{description}">
  <link rel="canonical" href="{canon}">
  <meta name="robots" content="{robots}">
  <meta name="theme-color" content="#070824">
  <meta property="og:site_name" content="{name}">
  <meta property="og:title" content="{full_title}">
  <meta property="og:description" content="{description}">
  <meta property="og:type" content="website">
  <meta property="og:url" content="{canon}">
  <meta property="og:locale" content="en">
  <meta name="twitter:card" content="summary_large_image">
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
  </main>

{footer}

  <script src="{js}"></script>
</body>
</html>
""".format(full_title=full_title, description=description, canon=canonical(path),
           robots=robots, name=NAME, icon=u("/assets/brand/favicon.svg"),
           font=u("/assets/fonts/montserrat-latin.woff2"),
           fonts_css=u("/css/fonts.css"), style_css=u("/css/style.css"),
           js=u("/js/main.js"), head_extra=head_extra,
           header=header(active if active is not None else path), body=body,
           footer=FOOTER)


def write(path, html):
    full = os.path.join(ROOT, path)
    d = os.path.dirname(full)
    if d:
        os.makedirs(d, exist_ok=True)
    io.open(full, "w", encoding="utf-8").write(html)
    print("wrote %-44s %6d bytes" % (path, len(html)))


def outfile(url_path):
    """/services/ -> services/index.html, so URLs stay clean."""
    if url_path == "/":
        return "index.html"
    return url_path.strip("/") + "/index.html"


# ============================================================
# SHARED FRAGMENTS
# ============================================================
def cta(heading, text, primary=("Send an enquiry", "/contacts/"),
        secondary=("Call " + PHONE, "tel:" + PHONE_HREF)):
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


def page_head(eyebrow, h1, lead, trail=None):
    return """
    <section class="container page-head">
      {crumb}
      <p class="eyebrow">{eyebrow}</p>
      <h1>{h1}</h1>
      <p class="lead">{lead}</p>
    </section>
""".format(crumb=crumb(trail) if trail else "", eyebrow=eyebrow, h1=h1, lead=lead)


def tags(items):
    return '<ul class="tags">\n%s\n      </ul>' % "\n".join(
        "        <li>%s</li>" % i for i in items)


# ============================================================
# SERVICES — the content model
# Every equipment name, manufacturer and standard here is carried over
# from litprofit.com verbatim. The prose around them is rewritten; the
# lists are not, because they are the part a customer checks.
# ============================================================
SERVICES = [
    dict(
        slug="ship-engine-repair",
        img=("svc-engine-repair.webp", 600, 410, "Marine diesel engine in a ship's engine room"),
        num="01",
        title="Ship equipment and engine repair",
        short="Maintenance and overhaul of 4-stroke and 2-stroke diesel engines, "
              "engine room machinery and deck equipment.",
        meta="Overhaul and repair of 4-stroke and 2-stroke marine diesel engines, "
             "engine room machinery and deck equipment. MAN, Wartsila, Yanmar, "
             "Hyundai Himsen, MAK, Caterpillar, Deutz, Daihatsu.",
        lead="Keeping a vessel's machinery inside its operating envelope — main "
             "engines, auxiliaries, and the deck equipment the crew depends on.",
        blocks=[
            ("Diesel engine overhaul",
             ["<p>We overhaul and repair <strong>4-stroke and 2-stroke diesel "
              "engines</strong> of most types and models. Work runs from diagnostics "
              "through to the upgrades that restore efficiency and extend service "
              "life, on main and auxiliary engines alike.</p>",
              "<p>Engines we work on regularly:</p>",
              tags(["MAN", "Wartsila", "Yanmar", "Hyundai Himsen", "MAK",
                    "Caterpillar", "Deutz", "Daihatsu"])]),
            ("Engine room machinery",
             ["<p>Beyond the engines themselves, we maintain and repair the rest of "
              "the machinery space — reduction gears, shafting and the auxiliary "
              "equipment that surrounds the main plant.</p>"]),
            ("Deck equipment",
             ["<p>Deck equipment is maintained on a regular cycle so that it works "
              "when it is needed: deck systems, ladders and steps, life-saving "
              "appliances and associated gear. Where equipment has been damaged, we "
              "repair it back to full working condition.</p>"]),
            ("How we work",
             ["<p>We use quality tooling and vetted sources of spare parts, and every "
              "repair is carried out to meet the applicable safety standards. All "
              "work and equipment carries our warranty.</p>"]),
        ],
    ),
    dict(
        slug="refrigeration-systems",
        img=("svc-refrigeration.webp", 800, 609, "Industrial refrigeration compressor plant"),
        num="02",
        title="Refrigeration systems and equipment",
        short="Design, modernisation, compressor overhaul, installation and "
              "commissioning of marine and industrial refrigeration.",
        meta="Marine and industrial refrigeration: compressor overhaul, system "
             "modernisation, class-approved design documentation, installation and "
             "commissioning. SABROE, BITZER, HOWDEN, KUHLAUTOMAT, STAL, GRASSO, MYCOM.",
        lead="The company's original discipline, and still the deepest — more than "
             "a decade of refrigeration work on fishing vessels and shore plant.",
        blocks=[
            ("What we carry out",
             ["<ul>"
              "<li>Diagnostics and repair of refrigeration compressors, at all levels "
              "of complexity.</li>"
              "<li>Diagnostics and repair of commercial and marine refrigeration "
              "equipment.</li>"
              "<li>Consultancy on selecting, installing and maintaining refrigeration "
              "equipment.</li>"
              "<li>Development of automatic control systems for compressors and "
              "refrigeration plant.</li>"
              "<li>Design documents and working drawings for ship refrigeration "
              "equipment, prepared to classification society requirements — including "
              "getting them approved.</li>"
              "<li>Installation of refrigeration equipment and refrigerant piping.</li>"
              "<li>Start-up, adjustment and handover to the client.</li>"
              "</ul>",
              "<p>We take both one-off jobs and regular contracted service work. All "
              "equipment and spare parts we manufacture and supply comply with quality "
              "and international standards.</p>"]),
            ("Compressors we service",
             [tags(["SABROE — Denmark", "BITZER — Germany", "HOWDEN — Scotland",
                    "KUHLAUTOMAT — Germany", "STAL — Sweden", "HALLSCREW — England",
                    "GRASSO — Netherlands", "MYCOM — Japan"])]),
            ("Systems we modernise",
             ["<p>Modernisation and repair of refrigeration systems for fishing "
              "vessels and shore installations:</p>",
              tags(["GRASSO / KUHLAUTOMAT", "HOWDEN", "MYCOM", "SABROE", "STAL",
                    "AERZEN", "YORK DYKIN", "HITACHI"])]),
        ],
    ),
    dict(
        slug="hull-and-piping",
        img=("svc-hull-piping.webp", 800, 533, "Welder joining a steel pipe bend"),
        num="03",
        title="Hull and piping works",
        short="Steel and stainless steel pipe systems for shipbuilding, ship repair "
              "and industry, including surface coating.",
        meta="Manufacture of steel and stainless steel pipe systems for shipbuilding, "
             "ship repair and industry. Hull and steel structure repair, galvanising "
             "and paint work, delivered worldwide.",
        lead="Pipe systems and steel structures, from the drawing through to a "
             "coated, finished product delivered wherever it is needed.",
        blocks=[
            ("Pipe systems",
             ["<p>We manufacture <strong>all types of steel and stainless steel pipe "
              "systems</strong> used in shipbuilding, ship repair and other "
              "industries, and we carry out major repairs to hulls and other steel "
              "structures.</p>",
              "<p>Surface coating is done in house — galvanising and paint work — so "
              "the product leaves finished rather than needing another supplier.</p>"]),
            ("The full scope",
             ["<p>Our team of qualified specialists can take a project end to end: "
              "the design work, ordering and delivering the materials, and carrying "
              "out the work itself to schedule and to standard.</p>",
              "<p>At the customer's request, finished products are shipped to any "
              "country in the world.</p>"]),
        ],
    ),
    dict(
        slug="spare-parts",
        img=("svc-spare-parts.webp", 450, 300, "Spare parts warehouse shelving"),
        num="04",
        title="Supply of spare parts",
        short="Sourcing and delivery of spare parts and consumables for marine "
              "engines and refrigeration compressors.",
        meta="Supply of spare parts for marine engines and refrigeration compressors "
             "— MAN, Wartsila, Caterpillar, SULZER, Sabroe, Bitzer, Howden, Mycom, "
             "Danfoss valves. Warehouse in Klaipeda.",
        lead="Selecting, ordering and delivering the parts a repair needs — with "
             "stock held in Klaipeda so the common ones do not wait on a supplier.",
        blocks=[
            ("What we source",
             ["<p>On request we will select, order and deliver spare parts and special "
              "equipment.</p>",
              "<h3>Compressors and their parts</h3>",
              tags(["STALL", "Sabroe", "Bitzer", "Howden", "Mycom", "J&amp;E Hall"]),
              "<h3>2-stroke and 4-stroke engine parts</h3>",
              tags(["MAN", "VOLVO PENTA", "Wartsila", "STX", "Yanmar", "MTU",
                    "Hyundai Himsen", "CUMMINS", "MAK", "SULZER", "Caterpillar",
                    "DETROIT DIESEL", "Deutz", "ROLLS ROYCE", "Daihatsu", "SCANIA",
                    "WICHMANN", "GUASCOR"]),
              "<h3>Refrigerant pumps and their parts</h3>",
              tags(["HERMETIC", "WITT"]),
              "<h3>Turbogenerator parts</h3>",
              tags(["ABB", "KBB", "MET", "NAPIER", "MAN"]),
              "<h3>Also supplied</h3>",
              "<ul>"
              "<li>Parts for heat exchangers.</li>"
              "<li>Valves and their parts — Danfoss, AWP and others.</li>"
              "<li>Assembly and supply of complete refrigeration units.</li>"
              "</ul>"]),
            ("Delivery time",
             ["<p>We work to keep delivery times short, and we hold a "
              "<strong>warehouse in Klaipeda</strong> for that reason — it is what "
              "lets us offer a better combination of price and delivery date than "
              "sourcing every part from scratch.</p>"]),
        ],
    ),
]

# (display name, file, intrinsic width, intrinsic height) — the real pixel
# dimensions, so the browser reserves the right box and the row does not
# reflow as the logos load.
CLIENTS = [
    ("Norebo", "logo-norebo.png", 400, 69),
    ("Sealord", "logo-sealord-paua.png", 140, 60),
    ("Limarko Group", "limarko-group.png", 400, 120),
    ("Ocean Whale Company", "ocean-whale-company.png", 400, 135),
    ("Baltreids", "logo-baltreids.png", 66, 82),
    ("Alliance Marine", "logo-alliance-marine.png", 248, 155),
    ("Seafish Trade", "logo-seafish-trade.png", 282, 179),
    ("Santavilte", "santavilte.png", 400, 89),
    ("LZK", "logo-lzk.png", 208, 208),
    ("OWH", "logo-owh.png", 246, 161),
]

CERTIFICATES = [
    dict(name="RINA", file="rina-certificate-2025.pdf", size="329 KB", date="2025-10-21",
         note="Italian classification society"),
    dict(name="PRS", file="prs-certificate.pdf", size="961 KB", date="2025-10-21",
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
              <span class="card-more">Read more</span>
            </span>
          </a>""".format(cls=cls, href=u("/services/%s/" % s["slug"]),
                         img=u("/assets/photos/" + f),
                         alt=alt, w=w, h=h, lv=level, num=s["num"],
                         title=s["title"], short=s["short"])


# Refrigeration leads: it is the company's original discipline and the one it
# has the deepest bench in, so it gets the feature card rather than being one
# of four equal boxes.
FEATURE_SLUG = "refrigeration-systems"


def service_cards(level="h3"):
    feature = [x for x in SERVICES if x["slug"] == FEATURE_SLUG]
    rest = [x for x in SERVICES if x["slug"] != FEATURE_SLUG]
    out = [card(x, level, "feature") for x in feature]
    out += [card(x, level, "compact") for x in rest]
    return "\n".join(out)


# ============================================================
# HOME
# ============================================================
def home():
    cards = service_cards("h3")

    logos = "\n".join(
        '          <li><img src="%s" alt="%s" width="%d" height="%d" loading="lazy"></li>'
        % (u("/assets/clients/" + f), n, w, h) for n, f, w, h in CLIENTS)

    return """
    <section class="hero">
      <div class="hero-media">
        <img src="{hero_img}" alt="" width="800" height="533" fetchpriority="high">
      </div>
      <div class="container hero-inner">
        <p class="eyebrow eyebrow-plain">Klaipeda, Lithuania <span class="sep">//</span> since {founded}</p>
        <h1>Ship repair and maintenance all over the world</h1>
        <p class="lead">{legal} overhauls marine engines, refrigeration plant and
        piping systems for fishing fleets, shipowners and shore installations —
        wherever the vessel happens to be.</p>
        <ul class="promise">
          <li><span class="step-num">01</span><span class="step-label">We consult</span></li>
          <li><span class="step-num">02</span><span class="step-label">We organise</span></li>
          <li><span class="step-num">03</span><span class="step-label">We ensure</span></li>
        </ul>
        <div class="btn-row">
          <a class="btn btn-solid" href="{book}"{book_attrs}>{book_label}</a>
          <a class="btn btn-outline" href="{services}">Our services</a>
        </div>
        <p class="hero-trust">
          <span>Authorised partner <b>BITZER</b></span>
          <span>Marine line representative <b>DANFOSS</b></span>
          <span>Certified <b>RINA</b> <span class="sep">//</span> <b>PRS</b></span>
        </p>
        <span class="scroll-cue" aria-hidden="true"></span>
      </div>
    </section>

    <section class="section section-tight partners-band seam-top seam-bottom">
      <div class="container">
        <div class="section-head reveal">
          <p class="eyebrow"><span class="eyebrow-num">01</span><span class="sep">//</span>Representation</p>
          <h2>We represent BITZER and DANFOSS</h2>
          <p class="lead">Two of the biggest names in refrigeration and marine
          controls appoint us directly. That is not a reseller arrangement — it is
          factory backing on the parts, the pricing and the warranty.</p>
        </div>
        <div class="partner-grid reveal">
          <div class="partner">
            <p class="partner-role">Authorised partner</p>
            <p class="partner-name">BITZER</p>
            <p>One of the largest independent manufacturers of refrigeration
            compressors in the world. As an authorised partner we supply and service
            BITZER equipment directly, rather than through an intermediary — which
            shortens both the parts chain and the warranty conversation.</p>
          </div>
          <div class="partner">
            <p class="partner-role">Marine line representative</p>
            <p class="partner-name">DANFOSS</p>
            <p>We represent the Danfoss marine line: controls, valves and components
            for refrigeration and engine room systems, specified and supplied for
            vessels rather than adapted from shore equipment.</p>
          </div>
        </div>
      </div>
    </section>

    <section class="section">
      <div class="container">
        <ul class="facts reveal">
          <li class="fact">
            <p class="fact-value">{years}+</p>
            <p class="fact-label">Years in refrigeration</p>
          </li>
          <li class="fact">
            <p class="fact-value">24/7</p>
            <p class="fact-label">Service response</p>
          </li>
          <li class="fact">
            <p class="fact-value">2</p>
            <p class="fact-label">Class certificates</p>
          </li>
          <li class="fact">
            <p class="fact-value">&euro;250k</p>
            <p class="fact-label">Liability insured</p>
          </li>
        </ul>
      </div>
    </section>

    <section class="section section-alt" id="services">
      <div class="container">
        <div class="section-head reveal">
          <p class="eyebrow"><span class="eyebrow-num">02</span><span class="sep">//</span>Services</p>
          <h2>Four disciplines, one contractor</h2>
          <p class="lead">Most jobs need more than one of these at once. Handling them
          under a single contract is what removes the coordination problem from the
          shipowner's desk.</p>
        </div>
        <div class="card-grid">
{cards}
        </div>
      </div>
    </section>

    <section class="section">
      <div class="container split">
        <div class="reveal">
          <p class="eyebrow"><span class="eyebrow-num">03</span><span class="sep">//</span>How we work</p>
          <h2>Consult, organise, ensure</h2>
          <p class="lead">Three steps, in that order — it is how the company has
          described itself for years, and it holds up.</p>
        </div>
        <div class="pillars reveal">
          <div class="pillar">
            <h3>We consult</h3>
            <p>Advice shaped by experience, where the technology is going, and what
            you actually need and can spend. Every customer gets proper time.</p>
          </div>
          <div class="pillar">
            <h3>We organise</h3>
            <p>We arrange and carry out every stage of the repair and service work,
            because your time is worth more than the coordination.</p>
          </div>
          <div class="pillar">
            <h3>We ensure</h3>
            <p>We control the work as it runs and keep your representatives informed
            of progress — no surprises at handover.</p>
          </div>
        </div>
      </div>
    </section>

    <section class="section section-alt">
      <div class="container">
        <div class="split" style="align-items: center">
          <div class="reveal">
            <p class="eyebrow"><span class="eyebrow-num">04</span><span class="sep">//</span>Capability</p>
            <h2>A decade of refrigeration, on ships and ashore</h2>
            <p class="lead">Compressor overhauls, class-approved design
            documentation, plant installation and commissioning — on fishing vessels
            and shore installations alike.</p>
            <div class="btn-row">
              <a class="btn btn-outline" href="{refrig}">Refrigeration systems</a>
            </div>
          </div>
          <div class="media-panel cornered reveal">
            <img src="{plant_img}" alt="Industrial refrigeration compressor plant"
                 width="800" height="555" loading="lazy">
          </div>
        </div>

        <div class="section-head reveal" style="margin-top: clamp(56px, 7vw, 104px)">
          <p class="eyebrow"><span class="eyebrow-num">05</span><span class="sep">//</span>Clients</p>
          <h2>Who we work with</h2>
        </div>
        <ul class="logo-wall reveal">
{logos}
        </ul>
      </div>
    </section>
{cta}""".format(founded=FOUNDED, legal=LEGAL, services=u("/services/"),
                cards=cards, logos=logos,
                hero_img=u("/assets/photos/hero-welding.webp"),
                plant_img=u("/assets/photos/plant-room.webp"),
                refrig=u("/services/refrigeration-systems/"),
                book=BOOKING_URL or u("/contacts/"),
                book_attrs=' target="_blank" rel="noopener"' if BOOKING_URL else "",
                book_label=BOOKING_LABEL,
                years=datetime.date.today().year - int(FOUNDED),
                cta=cta("24/7 service",
                        "We are ready to provide prompt and competent assistance — "
                        "tell us the vessel, the equipment and the port, and we will "
                        "come back with a plan."))


# ============================================================
# ABOUT
# ============================================================
def about():
    return page_head(
        "About us", "A Klaipeda ship repair company, working worldwide",
        "%s was established in %s. More than a decade in the refrigeration equipment "
        "market, a long list of completed projects, and business partners who have "
        "stayed." % (LEGAL, FOUNDED),
        [("Home", "/"), ("About", None)]) + """
    <section class="container prose">
      <h2>What we specialise in</h2>
      <ul>
        <li>Design and selection of industrial refrigeration equipment.</li>
        <li>Modernisation and repair of refrigeration systems for fishing boats and
        shore installations.</li>
        <li>Installation and supply of refrigeration equipment.</li>
        <li>Overhaul of main and auxiliary engines.</li>
        <li>Positioning of ships in the port of Klaipeda, Lithuania, for repair works.</li>
      </ul>

      <h2>The people</h2>
      <p>We have a team of reliable, qualified and time-tested professionals, and we
      provide a <strong>warranty on all works and equipment</strong>. The company is
      guided by what customers need now rather than what it was set up to do in
      {founded} — our specialists are there to advise as much as to execute.</p>
      <p>We are committed to continuous improvement and pay close attention to
      developments in the market. We take each customer's wishes and suggestions into
      account, and aim to offer the solution that is most sensible on cost, on time,
      and on the equipment supplied.</p>

      <h2>How we work</h2>
      <h3>We consult</h3>
      <p>Our consultations are guided by our experience, by where the technology is
      heading, and by your own requirements and budget. We give each customer
      exceptional attention and time.</p>
      <h3>We organise</h3>
      <p>Because we respect your time, we organise and carry out all the necessary
      stages of the repair and service work ourselves.</p>
      <h3>We ensure</h3>
      <p>We control the work process and keep the customer's representatives informed
      about progress as it happens.</p>

      <h2>Certification and cover</h2>
      <p>{legal} holds the <strong>RINA</strong> certificate, and is certified by the
      <strong>Polish Register of Shipping (PRS)</strong>. Both are published in full on
      the <a href="{certs}">certificates page</a>.</p>
      <p>The company's civil liability is insured with <strong>Compensa Vienna
      Insurance Group, ADB</strong> for <strong>EUR 250,000</strong>, under insurance
      policy no. 230 0008143 / 2020.</p>

      <h2>Representation</h2>
      <p>We represent two well-known manufacturers on the global market:
      <strong>BITZER</strong>, for whom we are an authorised partner, and
      <strong>DANFOSS</strong>, for whom we are a marine line representative. More on
      the <a href="{partners}">partners page</a>.</p>

      <h2>Company details</h2>
      <p>{legal}<br>{street}<br>{city}<br>{country}<br>
      Company ID: {cid}<br>VAT code: {vat}</p>
    </section>
{cta}""".format(founded=FOUNDED, legal=LEGAL, certs=u("/certificates/"),
                partners=u("/partners/"), street=STREET, city=CITY, country=COUNTRY,
                cid=COMPANY_ID, vat=VAT,
                cta=cta("Talk to us about your vessel",
                        "Tell us the equipment and the port. We will tell you what it "
                        "takes to put it right."))


# ============================================================
# SERVICES INDEX + DETAIL
# ============================================================
def services_index():
    # h2, not h3: this page has no section heading above the cards, so h3 here
    # would jump the outline straight from h1.
    cards = service_cards("h2")

    return page_head(
        "Services", "What we repair, supply and install",
        "Marine engines, refrigeration plant, pipe systems and the spare parts that "
        "keep all three running.",
        [("Home", "/"), ("Services", None)]) + """
    <section class="section" style="padding-top: 0">
      <div class="container">
        <div class="card-grid">
{cards}
        </div>
      </div>
    </section>
{cta}""".format(cards=cards,
                cta=cta("Not sure which one you need?",
                        "Most jobs cross more than one of these. Describe the problem "
                        "and we will scope it."))


def service_page(s):
    blocks = []
    for heading, paras in s["blocks"]:
        blocks.append("      <h2>%s</h2>\n%s" % (
            heading, "\n".join("      " + p for p in paras)))

    others = [o for o in SERVICES if o["slug"] != s["slug"]]
    more = "\n".join(card(o, "h3") for o in others)

    f, w, h, alt = s["img"]
    return page_head(
        "Service " + s["num"], s["title"], s["lead"],
        [("Home", "/"), ("Services", "/services/"), (s["title"], None)]) + """
    <div class="container">
      <div class="page-media cornered reveal">
        <img src="{img}" alt="{alt}" width="{w}" height="{h}">
      </div>
    </div>

    <section class="container prose">""".format(
        img=u("/assets/photos/" + f), alt=alt, w=w, h=h) + """
{blocks}
    </section>

    <section class="section section-alt">
      <div class="container">
        <div class="section-head reveal">
          <p class="eyebrow">Other services</p>
          <h2>What else we do</h2>
        </div>
        <div class="card-grid">
{more}
        </div>
      </div>
    </section>
{cta}""".format(blocks="\n\n".join(blocks), more=more,
                cta=cta("Ask about " + s["title"].lower(),
                        "Send us the equipment details and the port, and we will come "
                        "back with a scope and a price."))


# ============================================================
# COMPLETED WORKS
# ============================================================
def completed_works():
    return page_head(
        "Completed works", "Where the work has been done",
        "Two strands run through everything the company has delivered since %s: "
        "engines, and refrigeration." % FOUNDED,
        [("Home", "/"), ("Completed works", None)]) + """
    <section class="container prose">
      <!-- NOTE(LITPROFIT): the old site's "Completed works" page was two headings
           and two stock photographs — no project detail at all. This page is written
           from what the rest of the site establishes. To make it genuinely useful we
           need, per project: vessel or plant name, year, port, scope of work, and a
           photograph. That is the single highest-value thing the client can supply. -->

      <h2>Ship equipment and engine repair</h2>
      <p>Overhauls of main and auxiliary engines carried out on fishing vessels and
      commercial ships, covering both 4-stroke and 2-stroke plant from
      <strong>MAN, Wartsila, Yanmar, Hyundai Himsen, MAK, Caterpillar, Deutz</strong>
      and <strong>Daihatsu</strong>, alongside the engine room and deck equipment that
      surrounds them.</p>
      <p>Where a vessel needs to come alongside for the work, we arrange its
      positioning in the port of Klaipeda.</p>

      <h2>Refrigeration equipment</h2>
      <p>The company's longest-running line of work: modernisation and repair of
      refrigeration systems on fishing boats and shore installations, compressor
      overhauls, class-approved design documentation, installation of plant and
      refrigerant piping, and commissioning through to handover.</p>
      <p>Systems worked on include <strong>GRASSO / KUHLAUTOMAT, HOWDEN, MYCOM,
      SABROE, STAL, AERZEN, YORK DYKIN</strong> and <strong>HITACHI</strong>.</p>

      <h2>Who the work was for</h2>
      <p>Clients include <strong>Norebo</strong>, <strong>Sealord</strong>,
      <strong>Limarko Group</strong>, <strong>Ocean Whale Company</strong> and
      <strong>Baltreids</strong> — the full list is on the
      <a href="{partners}">partners page</a>.</p>
    </section>
{cta}""".format(partners=u("/partners/"),
                cta=cta("Have a similar job?",
                        "Tell us the vessel, the equipment and the port, and we will "
                        "come back with a scope and a price."))


# ============================================================
# PARTNERS
# ============================================================
def partners():
    logos = "\n".join(
        '          <li><img src="%s" alt="%s" width="%d" height="%d" loading="lazy"></li>'
        % (u("/assets/clients/" + f), n, w, h) for n, f, w, h in CLIENTS)

    return page_head(
        "Partners", "Manufacturers we represent, clients we work for",
        "Two authorised representations, and a client list built up over more than a "
        "decade.",
        [("Home", "/"), ("Partners", None)]) + """
    <section class="section partners-band seam-top seam-bottom" style="padding-top: clamp(46px, 5vw, 72px)">
      <div class="container">
        <div class="section-head reveal">
          <p class="eyebrow">Representation</p>
          <h2>Manufacturers we represent</h2>
          <p class="lead">Two direct appointments — factory backing on parts, pricing
          and warranty.</p>
        </div>
        <div class="partner-grid reveal">
          <div class="partner">
            <p class="partner-role">Authorised partner</p>
            <h3 class="partner-name">BITZER</h3>
            <p>BITZER is one of the largest independent manufacturers of refrigeration
            compressors in the world. Being an authorised partner means we supply and
            service the equipment directly rather than through an intermediary, which
            shortens both the parts chain and the warranty conversation.</p>
          </div>
          <div class="partner">
            <p class="partner-role">Marine line representative</p>
            <h3 class="partner-name">DANFOSS</h3>
            <p>We represent the Danfoss marine line: controls, valves and components
            for refrigeration and engine room systems, specified and supplied for
            vessels rather than adapted from shore equipment.</p>
          </div>
        </div>

        <div class="section-head reveal" style="margin-top: clamp(48px, 6vw, 88px)">
          <p class="eyebrow">Clients</p>
          <h2>Companies we have worked for</h2>
          <p class="lead">Fishing groups, shipowners and shipyards across the Baltic
          and beyond.</p>
        </div>
        <ul class="logo-wall reveal">
{logos}
        </ul>
      </div>
    </section>
{cta}""".format(logos=logos,
                cta=cta("Work with us",
                        "We take one-off jobs and regular contracted service work "
                        "alike."))


# ============================================================
# CERTIFICATES
# ============================================================
def certificates():
    docs = "\n".join("""        <a class="doc" href="{href}" target="_blank" rel="noopener">
          <span class="doc-name">{name}</span>
          <span class="doc-meta">{note} <span class="sep">//</span> PDF {size} <span class="sep">//</span> {date}</span>
          <span class="doc-get">Open</span>
        </a>""".format(href=u("/assets/certs/" + c["file"]), **c) for c in CERTIFICATES)

    return page_head(
        "Certificates", "Certification and cover",
        "Class approvals, and the liability insurance behind the work.",
        [("Home", "/"), ("Certificates", None)]) + """
    <section class="section" style="padding-top: 0">
      <div class="container">
        <div class="docs reveal">
{docs}
        </div>
      </div>
    </section>

    <section class="container prose">
      <h2>What these cover</h2>
      <p><strong>RINA</strong> is an Italian classification society; <strong>PRS</strong>
      is the Polish Register of Shipping. Certification by a class society is what lets
      a shipowner accept our work and documentation without commissioning a separate
      inspection to verify it.</p>

      <h2>Insurance</h2>
      <p>The civil liability of {legal} is insured with <strong>Compensa Vienna
      Insurance Group, ADB</strong> for the amount of <strong>EUR 250,000</strong>,
      under insurance policy no. 230 0008143 / 2020.</p>

      <h2>Warranty</h2>
      <p>We provide a warranty on all works and equipment. All equipment and spare
      parts manufactured and supplied by the company comply with quality and
      international standards.</p>
    </section>
{cta}""".format(docs=docs, legal=LEGAL,
                cta=cta("Need our documents for a tender?",
                        "We can supply certification and insurance paperwork on "
                        "request."))


# ============================================================
# CONTACTS
# ============================================================
def contacts():
    return page_head(
        "Contacts", "Talk to us",
        "Enquiries reach people who can answer technical questions, not a call centre.",
        [("Home", "/"), ("Contacts", None)]) + """
    <section class="section" style="padding-top: 0">
      <div class="container contact-grid">
        <div class="reveal">
          <div class="contact-block">
            <h2 class="col-title">Address</h2>
            <p>{legal}<br>{street}<br>{city}<br>{country}</p>
          </div>
          <div class="contact-block">
            <h2 class="block-title">Phone</h2>
            <p><a href="tel:{phone_href}">{phone}</a></p>
          </div>
          <div class="contact-block">
            <h2 class="block-title">Email</h2>
            <p><a href="mailto:{email}">{email}</a></p>
          </div>
          <div class="contact-block">
            <h2 class="col-title">Company details</h2>
            <p>Company No.: {cid}<br>VAT code: {vat}</p>
          </div>
          <div class="contact-block">
            <h2 class="block-title">Service</h2>
            <p>24/7 &mdash; we are ready to always provide prompt and competent
            assistance.</p>
          </div>
        </div>

        <div class="reveal">
          <h2>Send an enquiry</h2>
          <p class="lead" style="margin-bottom: 28px; font-size: var(--text-m)">
          The fastest route to a useful answer is the vessel or plant, the equipment,
          the port and your timescale.</p>

          <form class="form" id="enquiryForm" novalidate>
            <div class="field">
              <label for="fName">Name</label>
              <input id="fName" name="name" type="text" required autocomplete="name">
            </div>
            <div class="field">
              <label for="fCompany">Company <span class="opt">(optional)</span></label>
              <input id="fCompany" name="company" type="text" autocomplete="organization">
            </div>
            <div class="field">
              <label for="fPhone">Phone <span class="opt">(optional)</span></label>
              <input id="fPhone" name="phone" type="tel" autocomplete="tel">
            </div>
            <div class="field">
              <label for="fEmail">Email</label>
              <input id="fEmail" name="email" type="email" required autocomplete="email">
            </div>
            <div class="field">
              <label for="fMsg">Message</label>
              <textarea id="fMsg" name="message" rows="6" required
                        placeholder="Vessel or plant, the equipment, the port, and when you need it done."></textarea>
            </div>
            <div class="field field-check">
              <input id="fConsent" name="consent" type="checkbox" required>
              <label for="fConsent">I agree that {legal} may use these details to
              respond to my enquiry, as described in the
              <a href="{privacy}">privacy policy</a>.</label>
            </div>
            <div class="field">
              <button type="submit" class="btn btn-solid">Send enquiry</button>
              <p class="form-note" id="formNote" role="status" aria-live="polite"></p>
            </div>
          </form>
        </div>
      </div>
    </section>
""".format(legal=LEGAL, street=STREET, city=CITY, country=COUNTRY, phone=PHONE,
           phone_href=PHONE_HREF, email=EMAIL, cid=COMPANY_ID, vat=VAT,
           privacy=u("/privacy/"))


# ============================================================
# PRIVACY
# ============================================================
def privacy():
    return page_head(
        "Legal", "Privacy policy",
        "How %s handles personal data collected through this website." % LEGAL,
        [("Home", "/"), ("Privacy", None)]) + """
    <section class="container prose">
      <!-- NOTE(LITPROFIT): this describes what the site technically does today.
           It has NOT been reviewed by a lawyer. Have it checked against your actual
           internal processes before relying on it. -->
      <p><strong>Last updated:</strong> {today}</p>

      <h2>1. Who we are</h2>
      <p>{legal} is the controller of personal data collected through this website.</p>
      <ul>
        <li>{street}, {city}, {country}</li>
        <li>Email: <a href="mailto:{email}">{email}</a></li>
        <li>Phone: <a href="tel:{phone_href}">{phone}</a></li>
        <li>Company ID: {cid}</li>
      </ul>

      <h2>2. What we collect</h2>
      <p>This website has no user accounts, no analytics and sets no cookies of its
      own. Data reaches us in three ways:</p>
      <ul>
        <li><strong>The enquiry form.</strong> The name, company, phone, email and
        message you enter, in order to answer your enquiry.</li>
        <li><strong>Direct contact.</strong> If you email or call us, we receive
        whatever you choose to send.</li>
        <li><strong>Server logs.</strong> The site is hosted on GitHub Pages, which
        records technical request data including IP address and browser user-agent for
        security and reliability.</li>
      </ul>

      <h2>3. Third parties that receive data</h2>
      <ul>
        <li><strong>GitHub, Inc.</strong> &mdash; website hosting and request logs.</li>
      </ul>
      <p>This site loads no third-party scripts, fonts, analytics or embeds. The
      typeface is served from our own domain, so browsing this site does not disclose
      your IP address to any advertising or analytics company.</p>

      <h2>4. Legal basis</h2>
      <ul>
        <li><strong>Consent</strong> (GDPR Art. 6(1)(a)) &mdash; submitting the enquiry
        form. You may withdraw it at any time.</li>
        <li><strong>Legitimate interest</strong> (Art. 6(1)(f)) &mdash; responding to
        enquiries, and keeping the site secure and available.</li>
      </ul>

      <h2>5. How long we keep it</h2>
      <p>Enquiries are kept as long as needed for the enquiry or the resulting project,
      and for any statutory retention period that applies to it. Hosting logs are
      retained according to GitHub's own schedule.</p>

      <h2>6. Your rights</h2>
      <p>Under the GDPR you may request access to your data, correction, erasure,
      restriction of processing, portability, and you may object to processing based on
      legitimate interest. Write to <a href="mailto:{email}">{email}</a> and we will
      respond within one month.</p>
      <p>If you believe we have handled your data improperly, you may lodge a complaint
      with the Lithuanian State Data Protection Inspectorate (Valstybine duomenu
      apsaugos inspekcija), L. Sapiegos g. 17, Vilnius.</p>

      <h2>7. Changes</h2>
      <p>If this policy changes, the revised version will be published on this page
      with a new date at the top.</p>
    </section>
""".format(today=datetime.date.today().strftime("%d %B %Y"), legal=LEGAL,
           street=STREET, city=CITY, country=COUNTRY, email=EMAIL, phone=PHONE,
           phone_href=PHONE_HREF, cid=COMPANY_ID)


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
PAGES = [
    ("/", "%s — %s" % (NAME, TAGLINE),
     "%s — ship repair and maintenance all over the world. Marine engine overhaul, "
     "refrigeration systems, hull and piping works, and spare parts supply from "
     "Klaipeda, Lithuania." % LEGAL, home, org_ld()),

    ("/about/", "About us",
     "%s was established in %s in Klaipeda, Lithuania. Marine refrigeration and engine "
     "repair specialists, RINA and PRS certified." % (LEGAL, FOUNDED), about, ""),

    ("/services/", "Services",
     "Marine engine repair, refrigeration systems, hull and piping works and spare "
     "parts supply — from a single contractor in Klaipeda, Lithuania.",
     services_index, ""),

    ("/completed-works/", "Completed works",
     "Engine overhauls and refrigeration projects delivered by %s for fishing fleets, "
     "shipowners and shore installations." % LEGAL, completed_works, ""),

    ("/partners/", "Partners",
     "Authorised BITZER partner and DANFOSS marine line representative. Clients "
     "include Norebo, Sealord, Limarko Group, Ocean Whale Company and Baltreids.",
     partners, ""),

    ("/certificates/", "Certificates",
     "RINA and PRS certification, and EUR 250,000 civil liability insurance with "
     "Compensa Vienna Insurance Group.", certificates, ""),

    ("/contacts/", "Contacts",
     "%s, %s, %s. Phone %s, email %s. 24/7 service."
     % (STREET, CITY, COUNTRY, PHONE, EMAIL), contacts, ""),

    ("/privacy/", "Privacy policy",
     "How %s handles personal data collected through this website." % LEGAL,
     privacy, ""),
]

for path, title, desc, fn, extra in PAGES:
    write(outfile(path), page(path, title, desc, fn(), head_extra=extra))

for s in SERVICES:
    p = "/services/%s/" % s["slug"]
    write(outfile(p), page(p, s["title"], s["meta"], service_page(s)))


# ---------------- 404 ----------------
# GitHub Pages serves /404.html for any unmatched path.
NOTFOUND = """
    <section class="container notfound">
      <div>
        <p class="code">404</p>
        <h1>Page not found</h1>
        <p class="lead" style="margin: 20px auto 0">The page you asked for is not
        here. It may have moved when the site was rebuilt.</p>
        <div class="btn-row" style="justify-content: center">
          <a class="btn btn-solid" href="%s">Go to the homepage</a>
          <a class="btn btn-outline" href="%s">Contact us</a>
        </div>
      </div>
    </section>
""" % (u("/"), u("/contacts/"))
write("404.html", page("/404.html", "Page not found",
                       "The page you asked for is not here.", NOTFOUND,
                       noindex=True, active=""))


# ---------------- sitemap ----------------
# Generated from the same list that writes the HTML, so a renamed page can
# never leave a dead URL behind in the sitemap.
SITEMAP = [("/", "monthly", "1.0"),
           ("/services/", "monthly", "0.9")] + \
          [("/services/%s/" % s["slug"], "monthly", "0.8") for s in SERVICES] + \
          [("/about/", "monthly", "0.8"),
           ("/completed-works/", "monthly", "0.7"),
           ("/partners/", "monthly", "0.7"),
           ("/certificates/", "yearly", "0.6"),
           ("/contacts/", "yearly", "0.7"),
           ("/privacy/", "yearly", "0.2")]

urls = "\n".join(
    "  <url>\n"
    "    <loc>%s</loc>\n"
    "    <lastmod>%s</lastmod>\n"
    "    <changefreq>%s</changefreq>\n"
    "    <priority>%s</priority>\n"
    "  </url>" % (canonical(loc), LASTMOD, freq, pri)
    for loc, freq, pri in SITEMAP)
write("sitemap.xml",
      '<?xml version="1.0" encoding="UTF-8"?>\n'
      '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\n'
      + urls + "\n</urlset>\n")

write("robots.txt",
      "User-agent: *\nAllow: /\n\nSitemap: %s\n" % (ORIGIN + u("/sitemap.xml")))

print("\nBASE=%r ORIGIN=%r" % (BASE, ORIGIN))
print("Set BASE='' and ORIGIN to the live domain, add CNAME, and rebuild to migrate.")
