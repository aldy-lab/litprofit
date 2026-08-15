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
| `LOGO_LOCKUP` | header/footer render the monogram + the name in Montserrat | a real lockup SVG |
| `BOOKING_URL` | the "Book a call" button falls back to `/contacts/` | the Calendly link |
| `BASE` / `ORIGIN` | site serves from the `/litprofit/` project path | `""` + the real domain |

Nothing dead ever ships: each one degrades to something that works.

## Brand

| Asset | File | Notes |
|---|---|---|
| Monogram | `assets/brand/logo-mark.svg` | supplied artwork, `currentColor` for inline use |
| Monogram, white | `assets/brand/logo-mark-white.svg` | for `<img>` on the navy ground |
| Favicon | `assets/brand/favicon.svg` | white mark on a `#15196D` tile |

**Navy is `#15196D`** — taken from the guideline page artwork itself (the
full-bleed background rect of the supplied SVG), not sampled off a compressed
render. The rest of `--navy-*` is that hue carried down to usable grounds.

**The pattern, as rivets.** The guidelines call for "small squares arranged in
a strict grid". Drawn as a flat all-over field, that reads as a blueprint grid
— which is the ALPROJECTS motif, and this is a different company. So the square
and its strict spacing are kept, but built as a **rivet**: a bright square face
with a dark square dropped a fraction down-right, so it sits proud of the
surface like a fastener on steel plate.

That also decides placement. Rivets run along seams and plate edges, not across
open faces, so the main use is `.seam-top` / `.seam-bottom` — a single row at a
section boundary, reading as a plate joint. The pattern page's corner squares
become four corner rivets on image panels (`.cornered`), as though the panel
were bolted down.

Both come from one `--rivet` data URI, drawn at full strength with each use
dialling it down through its own `opacity`.

Two things to know if you edit this: `.seam-top` and `.seam-bottom` occupy
`::before` and `::after`, which is why the partnership band's glow is a
background *layer* rather than a pseudo-element. And a seam on both sides of one
boundary stacks two rivet rows at double opacity — the hero deliberately has no
bottom seam because the band below it already carries a top one.

### Two traps in the supplied artwork

**`currentColor` does not work through `<img>`.** An SVG referenced with `<img>`
loads as an independent document with no CSS inheritance, so `currentColor`
resolves to its initial value — black — and a white-on-navy mark vanishes.
Hence the separate `logo-mark-white.svg`.

**The big outlined word in the page SVG is not the wordmark.** It reads
**FONTS** — it is page 14's section title, exactly as page 21's is `GRAPHIC`.
It was briefly shipped as the logo before a screenshot caught it. The only
`LITPROFIT` lettering in that file is the light 40%-opacity page furniture,
which is not the wordmark weight either. **The heavy wordmark as vector is
still needed.**

## Design notes

- **The services grid is not four equal boxes.** Refrigeration is the company's
  original discipline and its deepest bench, so it takes a feature card with
  three compact cards beside it. Equal weighting would have said something
  untrue about the business. Driven by `FEATURE_SLUG` in `tools/build.py`; the
  grid only rearranges when a card is marked as the feature, so it degrades to
  a plain responsive grid otherwise (`:has(.card--feature)`).
- **Sections are numbered `01 // Services`**, after the guidelines' own page
  numbering (`21 // 36`). Only the homepage is numbered — it is the one page
  that reads as a sequence.
- **The promise is three numbered steps**, not a run-on line with arrows. It is
  a sequence, and numbering says so without the arrows.
- **Figures use `tabular-nums`** so the four stats sit on a common rhythm
  instead of each setting its own width.
- **Measure is constrained per element, not per container.** Capping
  `.section-head` itself squeezed 62px headings into four-line wraps *and*
  narrowed the lead inside it — the heading and the lead now get their own
  `max-width`, with `text-wrap: balance` evening out the last line.

## The refrigeration cycle

The homepage carries an interactive schematic of a vapour-compression loop —
compressor, condenser, expansion valve, evaporator — because refrigeration is
what the company actually sells and nothing on the old site showed it.

A 3D model was the alternative and was rejected: it needs a WebGL library
vendored into a site whose whole premise is no dependencies and no third-party
requests, plus a licensed compressor model nobody has. A drawing is lighter,
exact, and can say things a render cannot.

The copy names what fails at each station — scaled condenser tubes showing up
as rising head pressure, superheat set at the expansion valve exposing a plant
that was never properly commissioned. That is the register a chief engineer
reads in, and it is the company's own field.

Two implementation points:

- **The SVG is `aria-hidden` and the four buttons carry the content.** A screen
  reader gets an ordered, readable description of the cycle rather than a soup
  of unlabelled shapes, and the section is fully operable from the keyboard.
  Hover and focus light the same station; `aria-expanded` reports state.
- **The `0fr` → `1fr` accordion needs an inner element with `min-height: 0`.**
  Without it the grid row keeps its min-content height and nothing collapses —
  which is what happened on the first build, leaving every stage full-size.

Temperature coding — warm on the high-pressure leg, cool on the low — is the
one place a colour outside the brand palette earns its keep. It is what makes
a schematic legible at a glance.

## Hidden features

Nothing here is announced or required, and none of it changes what the page
says.

- **A console signature.** Open devtools and the `//` device is drawn in ASCII,
  raked at the monogram's angle, with the company line and who built it.
- **The work light.** Double-click the hero. The photograph sits at 30% under a
  heavy gradient; a second copy at full strength is revealed inside a soft
  circle that follows the cursor, with a warm rim so it reads as a lamp rather
  than a hole cut in the artwork. It is the gesture of walking into a dark
  engine room with a torch, which is the job. Moving the pointer off the hero
  puts it away.

Implementation notes: the pointer position is written to a CSS custom property
once per animation frame, because `pointermove` fires far faster than the
screen repaints and every write invalidates style. The whole thing is behind a
`CSS.supports("mask-image", …)` check, and a double-click landing on a link or
button is ignored so it cannot swallow a real click.

### What was here before

A "shop drawing" mode that turned the page into a blueprint. It was cut: it
looked cluttered, and it retreads the blueprint motif already used on the
ALPROJECTS site, which is the opposite of making this one feel like its own
company.

## The brand angle

The monogram is built on one diagonal. Measured off the supplied artwork, its
long slash runs **24.41°** from vertical and its short slash **25.03°** — they
agree, so it is a real constant of the mark rather than a guess. `--slant` is
that value, and it drives the eyebrow tick, the slice cut off each card index
badge, and the light sweep that crosses a card on hover. Using the mark's own
geometry is what makes the styling read as LITPROFIT's rather than as generic
diagonal decoration.

## Partner logos

`assets/partners/` holds BITZER's and Danfoss's own marks, taken from their
official sites and shown on white plates because both are full-colour brand
assets — recolouring another company's trademark is not ours to do.

Using them to state a factual partnership is ordinary nominative use, and the
partnership is real. **Both companies publish partner logo kits and usage
rules, though**, so it is worth having whoever manages each relationship
confirm these are the approved marks in the approved treatment before launch.

## What is provisional

- **The typeface.** Montserrat is a stand-in, including for the name beside the
  monogram. The guidelines' wordmark is a heavier geometric sans and has not
  been supplied as vector artwork. If the brand face is licensed, using it as a
  webfont needs a separate **web** licence.
- **The wordmark.** Only the monogram was supplied as vector. The lockup is
  therefore monogram + `LITPROFIT` set in the site face. See the note below.
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
