# LITPROFIT — website

Static site (HTML/CSS/JS, no build step to serve), rebuilding **litprofit.com**
for UAB "Litprofit". Same architecture as the ALPROJECTS Group site.
Made by ALDY.

**Preview:** https://aldy-lab.github.io/litprofit/

Status: **English site built and audited.** The visual layer is provisional —
it is driven entirely by CSS tokens, pending the brand guidelines' colour and
typography pages. Lithuanian and Russian are to follow.

## Build

```
python3 tools/build.py     # regenerates every page, sitemap.xml, robots.txt
python3 tools/audit.py     # device audit — must pass before committing
```

The output is committed, so nothing runs to serve the site. Everything is
generated, including `index.html`, which is what makes the base-path switch
below possible.

## Structure

```
tools/build.py       every page's content and the page shell — the only file
                     to edit for copy changes
tools/audit.py       Playwright audit: structure, links, mobile
css/style.css        design tokens + all styles
css/fonts.css        self-hosted Montserrat @font-face
js/main.js           config block, header, menu, reveals, enquiry form
assets/brand/        logo
assets/clients/      ten client logos
assets/certs/        RINA and PRS certificates (PDF)
docs/                harvested source content, brand notes
```

Pages: home, about, services (+ four service pages), completed works, partners,
certificates, contacts, privacy, 404.

## Going live on the real domain

The site currently serves from a GitHub *project* URL, so every absolute path
carries a `/litprofit` prefix. To move to the real domain:

1. in `tools/build.py`, set `BASE = ""` and `ORIGIN = "https://litprofit.com"`;
2. add a `CNAME` file containing the domain;
3. `python3 tools/build.py` and commit.

No `CNAME` is committed yet on purpose — adding one before the DNS exists takes
the github.io preview down too, leaving nothing to look at.

## Three switches at the top of `tools/build.py`

| Constant | Effect while empty | Set it to |
|---|---|---|
| `LOGO_FILE` | header and footer render a plain `LITPROFIT` wordmark | the new logo SVG |
| `BOOKING_URL` | the "Book a call" button falls back to `/contacts/` | the Calendly link |
| `BASE` / `ORIGIN` | site serves from the `/litprofit/` project path | `""` + the real domain |

Nothing dead ever ships: each one degrades to something that works.

## What is provisional

- **The palette.** `--navy-*` in `css/style.css` is estimated from the brand
  guidelines' mockup pages, which are compressed artwork. The colour page has
  not arrived. Replacing that one block recolours the whole site; nothing
  outside it names a colour.
- **The typeface.** Montserrat is a stand-in. The wordmark in the guidelines is
  a heavier geometric sans. If the brand face is licensed, using it as a webfont
  needs a separate **web** licence.
- **The logo.** `assets/brand/` holds the logo from the *old* site. It contains
  red, which appears nowhere in the new identity, so it is **not used** — the
  header and footer render a wordmark instead. Shipping no mark beats shipping
  the wrong one. Set `LOGO_FILE` when the new monogram is exported.
- **Photography.** `assets/photos/` is re-encoded from the old site, which caps
  at **800px wide** — fine for cards, soft for a full-bleed hero, which is why
  the hero image is held back to 30% opacity and reads as texture. Real
  photography of the company's own work would be the single biggest visual
  upgrade available.
- **Completed works.** The old site's version was two headings and two stock
  photos. The page is written from what the rest of the site establishes, but to
  be genuinely useful it needs, per project: vessel or plant name, year, port,
  scope, and a photograph.

### One image was dropped on purpose

The old site's `engine-repair.jpg` carries a **visible stock watermark** —
diagonal lines and a circular agency mark, clear once the contrast is lifted.
litprofit.com is serving an unlicensed comp image today. It is excluded from
this build; the engine-repair card uses the ship's-engine-room photograph
instead, which is more authentic anyway. Worth checking what licence the
remaining stock images were bought under.

See [`docs/brand-notes.md`](docs/brand-notes.md) for what the guidelines
establish so far and what is still outstanding.

## The company

UAB "Litprofit" — ship repair and maintenance, worldwide. Founded 2010, based in
Klaipeda, Lithuania. Positioning: *We consult → We organise → We ensure*.

| | |
|---|---|
| Address | Svajones str. 30, LT-94101 Klaipeda, Lithuania |
| Phone | +370 670 20 357 |
| Email | info@litprofit.com |
| Company ID | 302568798 |
| VAT | LT100005766815 |
| Insurance | Compensa Vienna Insurance Group ADB, EUR 250,000 (policy 230 0008143 / 2020) |

Authorised partner of **BITZER**; marine line representative for **DANFOSS**.
Certified by **RINA** and **PRS**.

## What changed from the old site

The old site's full English text is preserved in
[`docs/source-site-EN.txt`](docs/source-site-EN.txt). Every equipment list,
manufacturer name, certificate and number carries over exactly; the prose around
them is rewritten. Fixed in the process:

- **English URLs.** The old English pages sat on Lithuanian slugs
  (`/paslaugos/saldymo-sistemos-ir-iranga`), which costs relevance on English
  queries. Now `/services/refrigeration-systems/`.
- **Untranslated Lithuanian.** "Skaityti toliau" appeared as the read-more link
  on every English page, and the contact form's labels were Lithuanian
  (Vardas / Telefonas / El. paštas / Žinutė).
- **Meta descriptions.** Only the homepage had one, and it was in Lithuanian.
  Every page now has its own, plus canonical, Open Graph and
  `Organization` structured data.
- **The two thin pages.** "Completed works" and "Partners" were headings with
  almost nothing under them.

## Mobile and accessibility

`tools/audit.py` drives a real device context — DPR 3, touch — at 360, 375, 390,
412 and 430px, because Chrome's headless window clamps around 500px and these
widths cannot be tested by resizing.

It checks, on all 13 pages: one `<h1>`, no heading-level jumps, no image without
`alt`, no link without an accessible name, no duplicate `id`s, no JS errors,
every internal link resolving to a file that exists, no horizontal overflow, no
tap target under 24px (WCAG 2.2), and no text field under 16px — below that, iOS
Safari zooms the page on focus. It also drives the menu: open, close,
`aria-expanded`, and the body scroll lock and its restore.

The first run reported 393 problems. What it caught:

- inline and footer links 16–19px tall, under the 24px minimum. `padding-block`
  on an *inline* element grows the hit area without pushing lines apart, so this
  costs nothing visually;
- the consent checkbox at 20×20;
- heading-level jumps from `h1` straight to `h3` where a page had no `h2` of its
  own — the footer and contact-block headings are levelled to `h2`, and the
  services index cards to `h2`. The CSS targets those by **class**, not by tag,
  so a level can change without breaking the styling.

### Two bugs the audit could not have caught

Both were found by looking at screenshots:

- **`.reveal` hid the whole site.** Scroll-reveal started at `opacity: 0`, so
  every section below the hero rendered blank until JavaScript ran — and stayed
  blank if it never did. The rules are now scoped to `.js`, set by an inline
  script in `<head>` before the stylesheet paints. A stylesheet should not hide
  content by default.
- **The client logos were destroyed by a filter.** Knocking them out to white
  with `brightness(0) invert(1)` flattens every opaque pixel to white, so any
  mark with knockout detail — Ocean Whale, LZK, OWH — collapsed into a
  featureless white disc. They now sit on white tiles, unaltered. They are other
  companies' trademarks; recolouring them is not ours to do.

## No horizontal scrolling — how it is enforced

`overflow-x` lives on `<html>`, not `<body>`: setting it on body makes body a
scroll container, which changes how `position: sticky` resolves. That is the
safety net, not the fix. The actual guarantee is `min-width: 0` on grid and flex
children (they default to `min-width: auto` and refuse to shrink below their
content), `overflow-wrap: break-word` on body, and no `100vw` anywhere — it
includes the scrollbar and overflows by its width.
