# LITPROFIT — website

Static site (HTML/CSS/JS, no build step to serve), rebuilding **litprofit.com**
for UAB "Litprofit". Same architecture as the ALPROJECTS Group site.
Made by ALDY.

**Preview:** https://aldy-lab.github.io/litprofit/

Status: **Trilingual — English, Lithuanian and Russian — built and audited.**
37 pages, all passing the device audit.

## Build

```
python3 tools/build.py     # regenerates every page, sitemap.xml, robots.txt
python3 tools/audit.py     # device audit — must pass before committing
python3 tools/make-og.py   # re-renders the share cards (only after a design change)
```

Share cards are screenshotted from a real page in a real browser using the
site's own stylesheet and self-hosted Montserrat, so a card cannot drift away
from the site's typography. **Anything interpolated into an HTML attribute
must go through `attr()`** — `LEGAL` is `UAB "Litprofit"`, whose raw double
quotes silently terminate a `content="..."` attribute. Unescaped, the
homepage shipped a meta description four characters long.

The output is committed, so nothing runs to serve the site. Everything is
generated, including `index.html`, which is what makes the base-path switch
below possible.

## Structure

```
tools/build.py       page shells and markup — the only file to edit for layout
tools/i18n.py        every user-facing string in all three languages
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
| Lockup | `assets/brand/logo-lockup.svg` | monogram + wordmark, what the site renders |
| Wordmark | `assets/brand/logo-wordmark.svg` | supplied, outlined paths |
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
**FONTS** — page 14's section title, exactly as page 21's is `GRAPHIC`. It was
briefly shipped as the logo before a screenshot caught it. The real wordmark
was supplied separately and is now in `logo-wordmark.svg`; anything extracted
from a guideline page SVG should be rendered and read before it is trusted.

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

## The general arrangement drawing

Homepage section `04 // General arrangement`, anchored at `#drawing`. A side
elevation of a skid-mounted marine screw compressor package — the machine this
company overhauls more than any other — drawn to workshop conventions: hairline
geometry, a dash-dot shaft centre line, ticked dimension lines whose labels
interrupt the line rather than sit on it, a hatched skid, numbered balloons on
leaders, and a title block.

Take a part and the rest of the package fades back while that assembly lights
up in brand navy with its balloon.

**A 3D model was considered and rejected.** It needs a WebGL library vendored
into a site whose premise is no dependencies and no third-party requests, plus
a licensed compressor model nobody has. Hand-drawn SVG is lighter, exact, and
recolours with the palette for free.

**An earlier version was a four-box refrigeration-cycle flowchart.** It was
accurate but read as a teaching aid rather than as design, so it was replaced
rather than tuned.

Two implementation points:

- **The SVG is `aria-hidden` and the five buttons carry the content.** A screen
  reader gets an ordered description of the package instead of unlabelled
  shapes, and the section is fully operable from the keyboard. Hover and focus
  light the same part; `aria-expanded` reports state.
- **The `0fr` → `1fr` accordion needs an inner element with `min-height: 0`**,
  or the grid row keeps its min-content height and nothing collapses.

The dimension figures (4250 mm, 2100 mm) are plausible for a package of this
type but are **illustrative, not a real machine's**. Swap them for a genuine
unit's if the drawing is ever used as anything but decoration.

## The hero drawing

A **marine provision refrigeration P&ID**, full-bleed behind the hero and drawn
the way a chief engineer would expect to read one:

- two compressor sets, each with accumulator, oil separator, sight glass and
  suction/discharge gauges (`P1`–`P4`);
- two seawater-cooled condensers with their tube bundles;
- three refrigerated spaces at their working temperatures — chiller `+2 °C`,
  freezer `-20 °C`, pre-storage `+17 °C` — each with a finned evaporator coil
  and fan;
- discharge, liquid and suction lines in three colours, carrying gate valves,
  check valves, solenoids, filter driers, sight glasses and thermostatic
  expansion valves;
- a legend and a title block.

Room names are translated; the tag letters are not, because `P1` and `TXV` are
the same on any drawing in any yard.

**Repetition is generated, not typed.** Two identical compressor sets, two
condensers and three room coils come from one function each, so the drawing
stays editable rather than being six hundred lines of hand-placed geometry.

`preserveAspectRatio="meet"` — `slice` was tried first and cropped the freezer
and pre-storage rooms straight off the canvas. A radial mask suppresses the
drawing only where the headline actually sits, rather than down the whole left
side, which is where the compressor sets live.

### The work light — double-click the hero

The plant is held back so the headline keeps its contrast; the lamp reveals a
circle of it at full strength under the cursor, the way a hand lamp works over
a print on a bench. Moving the pointer off the hero puts it away.

**It reveals a second, brighter copy of the drawing.** `backdrop-filter:
brightness()` was tried first and is wrong on a dark ground — it amplifies the
navy into a bright blue disc instead of picking out the linework, because there
is almost no luminance in the lines to amplify. Caught on a screenshot.

A double-click is also a word-select gesture, so the handler calls
`preventDefault()` and clears the selection; without it the lamp left a
highlighted word behind every time.

## The project calculator (private)

`/calculator/` — the project profitability workbook as a web app, restyled onto
the site's own tokens. Nine sheets, every formula unchanged: labour with
employer burden and daily allowance, subcontractors, travel, materials,
logistics, a KPI dashboard against a target margin, CSV export, JSON
backup/restore, and a print report. Trilingual, and all data stays in the
browser's `localStorage` — nothing is transmitted anywhere.

### Everything translates, including the categories

The seeded rows used to be copied into the project **as text** when it was
created, so a project started in English stayed English for ever — the tab read
`KELIONĖS` above rows still saying "Flights".

Rows now carry a **language-independent key** (`flights`, `freight`, `spares`)
and the label is resolved at render time from the current language. Anything
typed into a cell is stored on the row and wins from then on, so a real entry
like "Klaipeda → Vigo" is never overwritten by a language switch. Rows added
with **+ Add row** have no key, so they show exactly what was typed.

This runs through the table, the CSV export and the print report alike —
verified in all three languages, and confirmed that no English default survives
in a Lithuanian or Russian export.

**Existing projects are migrated automatically**, once, on load — and imported
backups too, since a backup can predate the change. Each seeded row is matched
against the defaults of *every* language; an exact hit means the text was a
default rather than something a person typed, so the row gets its key back and
the matching fields are cleared so they resolve. A field the user actually
changed does not match, so it is left alone.

That was needed because a project started while the interface was Russian kept
Russian rows under English headers for ever. Verified against a project built to
match exactly that: the labels follow the interface again, a hand-written note
in a description survives untouched, and every figure is unchanged.

### Light and dark

Dark by default, matching the site; light exists because this is a spreadsheet
people stare at for an hour and print from, and the site's reading conditions
are not those. The toggle sits in the header and follows the operating system
until someone chooses for themselves, after which the choice is pinned. The
white lockup is inverted on the light ground and the seam rivets flip dark.

### Where the data lives

**In the browser, in `localStorage`, under the key `litprofit_v1`.** Nothing is
transmitted anywhere — there is no database and no server. Consequences worth
knowing before anyone relies on it:

- **Per browser, per device, per profile.** Two people do not see each other's
  projects, and the same person sees different data on laptop and phone.
- **Clearing site data deletes everything.** So does "clear cookies and site
  data", some privacy extensions, and macOS Safari's 7-day eviction for sites
  the user has not visited.
- **Private/incognito windows lose it on close.**
- **Roughly 5 MB.** Hundreds of projects, not thousands.

**Backup JSON is the only backup that exists.** It should be part of the
routine, not an afterthought — and Import restores it on any device, which is
also how you move a project between people.

If shared, multi-user data is ever needed, that is a real backend (Supabase,
Firebase, a small Postgres) and a different piece of work. It cannot be
retrofitted onto a static page.

### It is encrypted, not hidden

GitHub Pages has no server, so a JavaScript gate that compares a password and
reveals a hidden `<div>` is theatre — View Source walks straight past it. The
published page contains **only ciphertext**:

**The login is real, not a string comparison.** A username checked in
JavaScript adds nothing — it is one more line to walk past. Both fields feed
the key derivation, so a wrong username fails exactly as a wrong password does.
Verified: right-user/wrong-password, wrong-user/right-password and a mismatched
pair from two valid accounts are all rejected.

| | |
|---|---|
| content key | 32 random bytes; the app is encrypted under it once |
| per account | PBKDF2-HMAC-SHA256(username + NUL + password), 310,000 iterations, own 16-byte salt, wrapping the content key with AES-256-GCM |
| payload | AES-256-GCM under the content key |
| integrity | GCM's auth tag — wrong credentials fail rather than yielding garbage |

Wrapping one content key per account means **revoking someone is a rebuild
without their entry**, and changing one password does not re-encrypt the app or
disturb anyone else.

**Usernames are not stored.** Only the wrapped keys ship; the browser tries each
in turn. The file does not disclose who has access. Verified: neither username
nor password appears anywhere in the output.

Verified on the built file: zero occurrences of `computeDash`, `targetMargin`,
`LS_KEY` or any UI string. The encryption runs in a headless browser through
WebCrypto rather than in Python, so it is literally the same implementation
that decrypts it and the two cannot drift.

### Rebuilding it

```
CALC_USERS='[["alice","secret"],["bob","other"]]' python3 tools/build-calc.py
```

**Credentials are never stored in this repository.** They come from the
environment, because this repo is public and committed passwords would protect
nothing.

⚠️ **`tools/calc/app.html` is gitignored.** `tools/` is served by GitHub Pages
— `tools/build.py` returns 200 — and the repo is public, so committing the
plaintext app would publish exactly what the ciphertext protects. **Keep a
backup of that file:** without it the calculator can be decrypted in a browser
but not rebuilt or edited.

If the calculator's *source* also needs to be confidential, the repository
itself has to be private. Encryption of the published page cannot fix a public
repo.

## Careers

`/careers/` in all three languages, in the nav and the pager.

`POSITIONS` in `build.py` holds one **sample** role — Refrigeration Service
Engineer, in all three languages — so the layout can be reviewed.

**It carries `sample=True`, and that one flag does two things:** it shows an
`EXAMPLE` badge on the card, and it withholds the `JobPosting` structured data.
Without the second part, a role that does not exist would be indexed by Google
for Jobs under this company's name — a preview convenience turning into the
client's problem. Verified: the careers page emits zero `JobPosting` blocks in
all three languages.

To publish a real vacancy: set `sample=False` (or drop the key) and check
`posted` / `valid_through` are current — stale posts get demoted. To close one,
set `open=False` rather than deleting it.

The application form shares one handler with the enquiry form — a second copy
of that logic would be a second place to fix it.

## Languages

English at the root, Lithuanian under `/lt/`, Russian under `/ru/` — 12 pages
each, plus one shared 404.

- **All strings live in `tools/i18n.py`.** The markup stays in `build.py`, so a
  layout change is made once rather than three times. A missing key raises at
  build time instead of silently shipping English into a Lithuanian page.
- **The Lithuanian and Russian are the company's own wording** wherever their
  old site had an equivalent — the equipment vocabulary, the service names and
  the *Konsultuojame / Organizuojame / Užtikriname* triad are theirs.
- **`u()` decides asset vs page.** Assets are shared between languages, pages
  are not; deciding that in one function is what kept the language switch from
  touching every template.
- **hreflang on every page**, with `x-default` on English, and the sitemap
  carries `xhtml:link` alternates. Without them the three versions of a page
  compete with each other in search instead of being understood as
  translations.
- **The switcher goes to the same page in the other language**, not to its
  homepage — dumping a reader back at the top is the usual way these get it
  wrong. Verified: EN service page → LT stays on that service page.
- **Cyrillic is a separate font subset** under `unicode-range`, so English and
  Lithuanian pages never download it.
- The 404 exists once, at the root. GitHub Pages serves it for any unmatched
  path on the host, so `lang_url()` collapses `/404.html` to `/` — otherwise
  the switcher pointed at `/lt/404.html`, which does not exist.

⚠️ **The privacy policy is a legal text.** The Lithuanian and Russian are
translations for convenience; have all three reviewed before launch.

⚠️ **The address is inconsistent on the client's own site** and needs
confirming — see below.

## Navigation and page furniture

The site reads as a set of sheets, after the drawing's own title block
(`DWG 04 // 06`). Every main page carries its sheet number in the eyebrow and
ends with a **previous / next pager** — a page that dead-ends at the footer
gives the reader nowhere to go, which is a navigation failure rather than a
styling one. `SHEETS` in `tools/build.py` is the single ordered list driving
both.

## Client logos

Linked where the company's own site could be **verified** — each candidate
domain was fetched and its page title matched against the company name. Four
of ten are confirmed: Norebo, Sealord, Seafish Trade, Santavilte. The other six
render as plain tiles, because a logo linked to the wrong company is worse than
a logo that does not link at all. Add a URL to `CLIENTS` and the tile becomes a
link automatically.

## The ALDY credit

Footer, bottom right: the ALDY mark plus "Made by ALDY". `ALDY_URL` at the top
of `tools/build.py` is empty, so it renders as text and mark with no dead link
— set it to the studio URL and it becomes one.

## Scroll behaviour

- **Progress**: a hairline on the header's own bottom edge, so it reads as part
  of the rule already there rather than a bar bolted on top.
- **Parallax**: the hero photograph drifts at 0.16 of the scroll rate, and only
  while the hero is still on screen.
- **Stagger**: grid children arrive in sequence, 70ms apart.

All three are skipped entirely under `prefers-reduced-motion` — not shortened,
skipped, since a parallax that still moves is the thing that setting is about.
Verified by running the page in a reduced-motion context and confirming the
transform is never written.

## Hidden features

Nothing here is announced or required, and none of it changes what the page
says.

- **A console signature.** Open devtools and the `//` device is drawn in ASCII,
  raked at the monogram's angle, with the company line and who built it.
- **Frost.** Type `FROST`. The page goes on cold test: a banner strikes across
  the top reading `Cold test // RSW circuit // Setpoint -25 C // Recording`,
  registration marks land in the corners, the glass frosts over, ice grains
  drift down, and a probe reads out `RSW TANK // PROBE`,
  falling from deck temperature to the &minus;25&nbsp;&deg;C an RSW tank or
  blast freezer actually runs at — blinking `Cooling` on the way down, then
  settling to `Holding`. It thaws by itself after **11 seconds**, or type
  `FROST` again to stop it early; an easter egg you cannot get out of is a bug.

  The fern is a real dendrite — a stem with recursively smaller branches at a
  fixed 58&deg;, which is roughly how ice grows on glass. It was generated
  once by a script (340 segments) and baked in as path data, so nothing
  computes it at runtime, and one crystal is mirrored into all four corners.
  It draws itself on by retreating a single long dash along the path, so the
  branches appear trunk-first in the order the generator produced them.

  Under `prefers-reduced-motion` the ice still appears — that is the point of
  the egg — but nothing draws, drifts or blinks its way in.

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

- **The typeface.** Montserrat is a stand-in for body and headings. It is no
  longer used for the logo — the wordmark is supplied artwork now, so no web
  font licence question touches the brand mark itself.
- **Photography.** `assets/photos/` is re-encoded from the old site, which caps
  at **800px wide** — fine for cards, soft for a full-bleed hero, which is why
  the hero image is held back to 30% opacity and reads as texture. Real
  photography of the company's own work would be the single biggest visual
  upgrade available.
- **Completed works.** The old site's version was two headings and two stock
  photos. The page is written from what the rest of the site establishes, but to
  be genuinely useful it needs, per project: vessel or plant name, year, port,
  scope, and a photograph.

### The address does not agree with itself

Their existing site gives three different addresses:

| Source | Address |
|---|---|
| English pages | Svajones str. **30** |
| Lithuanian footer | Svajonės g. **3** |
| Lithuanian contacts page | **Naujoji Uosto g. 3** |
| Russian pages | ул. Svajones **3** |

This site currently publishes the English one, `Svajones str. 30`, because
changing it on a guess would be worse than keeping it. Two of the three
languages say number 3, and the Lithuanian contacts page — the page most likely
to have been updated on a move — gives a different street entirely. **Ask the
client which is current before launch.** It is one constant in `build.py`.

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
