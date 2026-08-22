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

### A duplicate key was hiding a column heading

`set` declared `note` twice — once as the "Unit / Note" column heading and
again as the footer sentence. JavaScript keeps the last one silently, so the
Settings table printed a whole paragraph where a two-word heading belonged. The
heading is `unit` now.

A duplicate key in an object literal throws nothing and lints as valid, so it
is worth re-running the scan after editing `T`:

```
python3 - <<'X'
import io, re
s = io.open("tools/calc/app.html", encoding="utf-8").read()
blk = s[s.index("const T = {"):s.index("/* ================= seeded rows")]
for m in re.finditer(r"(\w+):\{([^{}]*)\}", blk):
    keys = re.findall(r"(?:^|,)\s*(\w+)\s*:", m.group(2))
    dup = {k for k in keys if keys.count(k) > 1}
    if dup: print("DUPLICATE", m.group(1), sorted(dup))
X
```

### Portfolio, and closing a project

**Portfolio** is the first tab: every project side by side with revenue, cost,
profit, margin and a target chip. Clicking a row opens it. Sort by any column.

- **The company total uses a revenue-weighted margin**, not an average of the
  project margins — a €2k job at 90% must not drag the company figure around.
- **Filter by client** (which also matches vessel and project ID) **and by
  period.** The period filter is an **overlap** test, not "started within":
  asking what ran during February returns the job that began in January and
  finished in March, which is the question anyone is actually asking.
- **Export portfolio** writes one row per project plus the company line, so the
  whole book goes to an accountant as one file. Both exports carry a UTF-8 BOM
  and CRLF endings so Excel opens them correctly — verified at byte level.

**Closing a project** makes it read-only, so a finished job cannot be edited by
accident. That is enforced in the markup — the inputs are genuinely `disabled`,
not merely greyed — so they cannot be typed into, pasted into or reached by the
keyboard navigation, and the add/duplicate/delete controls are gone. A banner
says so and offers Reopen. Closed projects still export, print and total
normally; they are frozen, not archived.

### Made for data entry

It is a sheet people fill in for an hour, so it behaves like one:

- **Keyboard down a column.** `Enter` moves to the next row in the same column,
  `Shift+Enter` back up, `↑`/`↓` likewise on number cells, `Esc` leaves the
  field. Tab already crossed a row; nothing moved *down* one, which is how these
  are actually filled in.
- **Undo on delete.** A deleted row goes to a toast with **Undo** for nine
  seconds and comes back with its figures. There is no server-side history to
  fall back on, so a mis-click had been final.
- **Duplicate a row**, keeping the label it was showing — a copy of "Freight"
  reads "Freight" and stops following the language, because it is now the
  user's row.
- **Headings and totals stay put.** The grid scrolls inside its own box with the
  column names pinned to the top and the totals to the bottom. Sticky resolves
  inside that box, not the page: an `overflow-x` container is a scroll container
  on *both* axes, so page-relative sticky would never have worked.
- **Autosave.** Typing schedules a write 700 ms after the last keystroke, so a
  row of figures becomes one write rather than thirty. Anything structural —
  new project, delete, close, language, theme — writes immediately, because
  those are not things to leave sitting in a timer.

  Every path writes the **whole** state object, which is what makes the
  debounce safe: a structural save also carries whatever keystroke is still
  pending.

  The toolbar reports it and nothing else does: a pulsing dot on `Saving`, then
  `Saved 14:32`, green for 1.4 s and grey after. Amber only if a write actually
  failed. `Cmd/Ctrl+S` writes now — muscle memory in something that looks like
  a spreadsheet, and it stops the browser offering to save the page to disk.
  `Cmd/Ctrl+Shift+S` still writes the backup file, a different intention.

  **The ways out are covered**, since nothing should depend on the debounce
  finishing: `beforeunload`, `pagehide` (iOS does not fire `beforeunload`
  reliably) and `visibilitychange` all flush first. `localStorage` is
  synchronous, so this is a real write, not a request for one — which is why
  there is no longer a "you have unsaved changes" dialog. There is nothing to
  lose, and that dialog was never something the user could act on.

  Verified: a keystroke inside the debounce window survives a `pagehide`, and
  survives a reload with the Save button gone from the DOM.
- **The data sheets get a wider column than the reading views.** `main` was
  capped at 1400px for everything. Labor is 1514px of columns, so it was
  clipped by 194px at *every* screen size — Plan Total, Actual Total and
  Difference, the three numbers the sheet exists to produce, were unreachable
  on a 1920px monitor, and macOS overlay scrollbars meant nothing on screen
  said so. Sheets go to 1760px (`main[data-view="sheet"]`); dashboard, project
  card and settings stay at 1400px, where a measure that wide is already
  generous. Where it still cannot fit — Labor below about 1600px — the table
  keeps a permanently visible thin scrollbar rather than a silent clip.
- **Autocomplete from your own history.** Every text column marked `ac` in
  `sheetConfigs`, plus client / vessel / PM on the project card, is fed back as
  a `datalist` built from what has already been typed **across all projects** —
  that is the point, since the value of the list is that it remembers the last
  job. Same crew, same three subcontractors, same yard, job after job, and all
  of it was being retyped in full.

  Opt-in per column deliberately: invoice numbers are unique by definition and
  free-text notes are not worth suggesting, so neither carries the flag.
  Most-used first, then alphabetical, capped at 40, so the common answer is the
  first one offered. Measured at 1.9 ms to build across 40 projects.
- **Undo across every edit, not just row deletion.** `Ctrl/Cmd+Z`, with
  `Ctrl/Cmd+Shift+Z` and `Ctrl/Cmd+Y` for redo. Before this, undo covered
  exactly one action — deleting a row, for nine seconds. Typing over a good
  figure destroyed it with no history and no server copy to fall back on.

  **Whole-state snapshots, not inverse operations.** Every view already renders
  from `state`, so restoring is an assignment plus a `render()`; there is no
  second code path that can drift out of step with the first.

  Three things make it behave the way people expect:
  - **One field is one step.** `pushUndo(group)` coalesces a run of edits to the
    same field and `focusout` ends the run, so `Ctrl+Z` takes back the number
    that was typed, not one keystroke of it. The snapshot is taken on the first
    keystroke only, which is also why typing stays at 1.4 ms.
  - **Language and theme are preferences, not work.** They are carried across a
    restore, so undoing a figure cannot also throw back a theme somebody
    switched in between.
  - **Nothing that changes nothing takes a step.** Export and backup never
    snapshot; a confirm that gets declined pops the one it took. Importing a
    backup *does* snapshot, so replacing everything is reversible.

  ⚠️ **Depth is capped by bytes as well as count** — `UNDO_MAX` 80 steps,
  `UNDO_BYTES` 8 MB, size wins. A snapshot is the whole state and 40 projects
  measured 654 KB, so a plain 80-step cap would have parked **52 MB** of
  history in memory. Verified: a small portfolio keeps all 80 steps, a 661 KB
  one keeps 12 and stays under 8 MB. The stack is memory-only and a reload
  clears it.
- **The margin never leaves the screen.** A strip under the tabs, inside
  `.chrome` so it travels with the header, showing plan and actual margin,
  target, plan and actual profit, and the same verdict chip the portfolio uses.
  It repaints on every keystroke, so the number moves as the job is built
  instead of only when someone opens the dashboard.

  **It shows plan *and* actual, and that is not cosmetic.** Actual alone meant a
  job being planned — where every actual column is empty by definition — read
  `0 %` and `BELOW TARGET` in red for the whole of the phase where the strip is
  most useful. Where nothing has been entered it prints an em dash rather than
  a zero, and with nothing entered at all there is no verdict chip: an
  untouched project should look untouched, not catastrophic. The chip follows
  whichever figure is real and is labelled `PLAN` or `ACTUAL` so it can never
  be read as the other.

  Labels join with `·` rather than a space — `PLAN · MARGIN` reads as two tags
  in Lithuanian and Russian, where a two-noun phrase would not agree. Hidden on
  the portfolio (every project at once) and the dashboard (which says all of
  this in full), and on a phone all but the two margins stand down. Repainting
  toggles `hidden`, so it calls `measureChrome()` — `--chrome-h` is what keeps
  the sticky table header sitting directly beneath the chrome.
- **A failed write says so** instead of silently losing the entry.
- **One menu instead of nine buttons.** The toolbar carried Save, New,
  Duplicate, Close, Delete, Export CSV, Backup JSON, Import, Print, language
  and theme — twelve controls that wrapped onto two rows at 1440px and gave
  `Delete` exactly the same weight as `Duplicate`.

  It is five now: the project picker, the save status, **Print report**, a `⋯`
  menu and the two icon toggles. Print stays outside because it is what the
  tool is *for*; everything else is an occasional command and should take a
  deliberate step to reach. Inside, the items are grouped **Project** / **Data**
  with `Delete` alone below a rule, in red.

  Click-away and `Escape` both close it, `Escape` returns focus to the button,
  and `↑`/`↓` walk the items — the headings and rules are not stops. Measured:
  one row at every width from 700px to 1440px, and the panel stays on screen
  down to 390px, where it is right-anchored to a button that sits mid-screen
  and used to hang 50px off the left edge.

  ⚠️ **`header.app` must not have a `backdrop-filter`.** It had
  `blur(12px)` behind `--surface-1`, which is `#ffffff` and `#0c0e30` — both
  fully opaque, so the blur could never be seen. It was not free: it made the
  header a *backdrop root*, and the rivet seam and the page behind it were
  composited back over the part of the open menu that overflows the header.
  Measured `#bdbcc4` seam dots inside the menu with it, flat `#ffffff` without.
  Same family as the `filter` on `<body>` that broke `position: fixed` on the
  site. The header carries `position: relative; z-index: 2` instead.
- **The storage notice** states plainly that this is browser-only and that
  Backup JSON is the only backup, dismissible once read.

**On a phone** every one of the ten tabs is free of horizontal page overflow at
360/390/430 — verified. The row's own name stays pinned while the columns scroll
sideways, fields are 16px so iOS does not zoom on focus, and the toolbar scrolls
away while the tabs stay pinned. Two things that took finding: the lockup's
strapline is 257px of non-wrapping caps and alone pushed a 390px page to 436px;
and `display: contents` is what frees the tabs to stick, since a sticky child
only sticks within its parent's box and the wrapper's box ends with the header.

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

### Light by default

**Light is the default, dark is opt-in and remembered.** The site is dark
because it is a marketing page read for a minute; this is a spreadsheet stared
at for an hour and printed from, and those are not the same reading conditions.

The sign-in screen is light too. It was the brand navy, but a dark gate handing
over to a light app flashes on unlock, and the tool should feel like one piece.
The white lockup is inverted on both, and the seam rivets flip dark.

Nothing follows the operating system any more — a fixed default is easier to
support than one that depends on a setting nobody remembers changing. Verified
that a fresh install comes up light even under a dark OS.

Installs still holding the old `auto` value are migrated to light, since `auto`
meant "never chose". **An explicit `dark` is a decision and survives** — checked
both ways, along with dark persisting across a reload.

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

## The client rail

The clients section is a row of cards that scrolls sideways: logo knocked out
to white, company name, and a sector line. Arrows on pointer devices, swipe on
touch, and the arrows **disable at each end** rather than sitting there doing
nothing.

### Why the logos are white and not full colour

They went through three states, and the reasoning matters if anyone is tempted
to change it back.

Greyscaled and dimmed was wrong: it threw away real artwork. Sampling the files
settles that — Santavilte is `#0090f0` and `#f00000`, Seafish Trade purple and
orange, Sealord navy, Limarko an orange flag.

Full colour on a **white plate** showed the artwork honestly, but put nine
bright rectangles across a dark page.

Full colour with **no plate** is what the design asked for and it does not
work, because these are print logos drawn for white paper. Measured against the
card ground, five of the nine fall below 2:1 — LZK `1.0`, limarko `1.2`,
seafish `1.3`, alliance-marine `1.4`, sealord `1.7` — with baltreids `2.4` and
OWH `2.1` weak, and only ocean-whale `3.7` and santavilte `4.6` passing. Most
of the wall would simply be invisible.

So: **knocked out to white**, which is the usual convention for a client wall
on a dark ground and treats every mark identically rather than recolouring
some and not others.

The cost of a knockout is any mark carrying detail *inside* it. `brightness(0)
invert(1)` pushes shape and detail to white together. Seven of the nine survive
because their detail is transparent gaps that were never painted — OWH's globe
lines, LZK's anchor, Seafish's sphere all come through.

⚠️ **Two logos need better files from the client.**

- **Ocean Whale Company** ships with a solid white disc baked in behind the
  whale, so a CSS filter cannot tell plate from ink and the mark flattens into
  a blank circle. `tools/make-reverse-logo.py` strips the plate in the pixels
  and writes `ocean-whale-company-rev.png`, which is what the build uses. That
  is a repair, not a substitute for a real reverse logo — ask for one.
- **Baltreids** is only `66x82` in the source. At the 76px display height it is
  fine on a 1x screen and mushy on a retina one; the wordmark under the mark is
  not legible. No filter fixes resolution. **Ask for a file at 300px or wider.**
  Do not crop the wordmark off to hide it — that is altering their trademark.

It replaced a five-column grid, which had hard-coded five because ten logos
divide evenly by five. Removing one client left a ragged half-empty row — the
exact failure a fixed grid invites. A rail does not care how many there are.

**BITZER and DANFOSS stay in their own section above.** They are manufacturers
we represent, not customers; merging them into the client list would misstate
both relationships.

Their roles are the client's own official wording, given 2026-08-22, and live
in `i18n.py` as `role_bitzer` (*Authorised marine service partner*) and
`role_danfoss` (*Marine refrigeration partner*). The keys were `trust_partner`
and `trust_rep`; they were renamed because each now belongs to one named
partner rather than being a generic label somebody might reuse. Each string is
rendered **twice** — the hero trust line and the partner card — on the
homepage and on `/partners`, in all three languages. Change it in one place.

⚠️ These are claims about a manufacturer relationship, in six places per
language. If either agreement is ever reworded, this is the string to bring
back into line.

**The partner cards share a row grid.** The official roles are long enough to
wrap onto two lines in Lithuanian and Russian, and in Lithuanian only *one* of
the two wraps — which left the boxes uneven and, worse, the logos beneath them
out of step by the height of a line. `.partner-grid` declares
`grid-template-rows: auto auto 1fr` and each `.partner` is `grid-row: span 3`
with `grid-template-rows: subgrid`, so role, logo and body text each start on a
line both cards share. The label box still hugs its own text — that part is
meant to differ. Reserving two lines everywhere would have bought the same
alignment with dead space at full width.

Behind `@supports not (grid-template-rows: subgrid)` the cards fall back to the
flex column they were before: unaligned, never broken. Measured at 1440, 1100
and 900px in all three languages: logo tops and body-text tops both spread 0px.

⚠️ **Six of the nine sector lines are blank on purpose.** Only Sealord, Seafish
Trade and Santavilte say what they do on their own sites. A descriptive line
under someone else's logo is a claim about their business, so the rest stay
empty until the client confirms them. Fill in the last field of `CLIENTS` in
`build.py` and add the key to `SECTORS` in `i18n.py`.

## The calculator database

Until now the figures lived in one browser's `localStorage` and nowhere else:
another device, another browser, or clearing site data and they were gone.
They can live in Postgres instead, shared by the whole team.

**It is optional and it is off by default.** With `CALC_SUPABASE_URL` unset,
every line of the cloud code is inert and the calculator behaves exactly as it
always has. Same rule as the booking link: an unset value removes the feature
rather than shipping a broken one.

### Setting it up

1. **Create a Supabase project** in the **EU (Frankfurt)** region. Keeping the
   data in the EU is what keeps the GDPR story a short one.
2. **Run `db/schema.sql`** in the SQL editor. It is idempotent — safe to run
   again after an edit.
3. ⚠️ **Turn public sign-ups OFF.** *Authentication → Sign In / Providers →
   Email → disable "Allow new users to sign up".* This matters more than
   anything else on the list: every signed-in user can read and write every
   project, so leaving sign-ups open would let anyone who finds the page create
   an account and read the company's margins. Add people by hand under
   *Authentication → Users*.
4. **Copy the Project URL and the publishable key** from *Project Settings →
   API Keys*. The URL is `https://<project-ref>.supabase.co`, where the ref is
   the string in the dashboard address.

   Take the **publishable** key (`sb_publishable_…`). Never a secret key —
   `sb_secret_…` or the legacy `service_role` JWT — because those bypass row
   level security entirely. The build refuses both if one is pasted by mistake.

   The older `anon` JWT still works and Supabase deprecates it at the end of
   2026, so use the publishable key on anything set up now.
5. **Build and publish:**

   ```sh
   CALC_SUPABASE_URL="https://xxxx.supabase.co" \
   CALC_SUPABASE_KEY="sb_publishable_..." \
       python3 tools/build-calc.py
   ```

   `CALC_SUPABASE_ANON_KEY` is still read as a fallback, because that is what
   the key was called when this was written.

**The publishable key is meant to be public.** It names the project; it grants
nothing. Row level security decides who reads what, and a request carrying only
this key reads nothing at all — verified: anonymous is blocked on all four of
read projects, read history, read profiles, and insert.

### One login, not two

The passphrase gate exists because a static host has no server to check a
password against, so the page was encrypted instead. A database changes that:
Supabase Auth is a real login, checked somewhere the visitor does not control,
and it brings per-person accounts, password reset, and removing one person
without re-encrypting for everybody.

Keeping both would mean typing two passwords to reach one tool, and the weaker
would set the pace. So **when the database is configured, `build-calc.py`
ships the page as plain HTML** and the gate moves to the login form. It stays
`noindex, nofollow` and unlinked, but hiding it was never what protected it —
the figures are not in the file at all now.

### Two people, one job

Everybody can edit everything, so two people can open the same project. Each
save states the revision it read; the update matches on that revision and bumps
it. **A stale save matches no row**, so instead of quietly overwriting a
colleague the app stops and asks: *load their version* or *keep mine and
overwrite theirs*. It never picks for you — whichever way it goes, somebody's
figures are discarded.

Who holds the row is read back **from the server** at that moment. The local
copy's `updated_by` is usually the person reading the message — their own last
save — so trusting it named the wrong colleague in the one message where that
matters most.

### A closed project is closed in the database, not just on screen

Closing a job disabled the inputs in the browser and stopped there. A `PATCH`
straight at the REST endpoint rewrote it anyway — verified before the fix by
renaming a closed project to `HACKED` through the API. For a tool whose point
is that a finished job cannot be changed by accident, the rule has to live
where the data does, so `guard_locked_project` refuses it.

Reopening is still allowed — that is the way back in. The guard only refuses a
write that leaves the project closed, and it reads `new.data` rather than
`new.locked`, because the column is filled in by `sync_project_columns` and
`BEFORE` triggers fire in name order: `projects_guard` runs first, while
`new.locked` still holds the old value.

### Undo, refresh, and sessions that end

Three things were local-only and had to learn about the server:

- **Undo did not reach it.** The figure came back on screen while the database
  kept the newer one, and the snapshot carried an **old `rev`** — so the next
  ordinary save collided with the user's own undo and blamed a colleague for
  it. `cloudReconcile()` now runs after undo and redo: it re-reads the server's
  revisions, re-creates a project that undo brought back, removes one that undo
  took away, and rewrites the rest. `rev` belongs to the row, never to the
  undo stack.
- **Nothing ever re-read the server**, so a shared tool showed each person a
  private snapshot from whenever they opened the tab. It pulls when the tab
  comes back to the front, and on demand from **Refresh from server** in the
  menu — never while edits are in flight, which would throw away what is being
  typed. Verified: a half-typed field survives a refresh.
- **An expired session went quiet.** It showed `Not saved to server` and let
  someone keep typing into a tab that could no longer write anything. It now
  returns to the sign-in screen and says why.

  ⚠️ And **signing back in used to discard the queued work** — the pull replaced
  `state.projects` wholesale and took it with it. Anything queued goes up
  *before* the pull now, through the normal revision check, so a genuine clash
  still surfaces as a conflict rather than being resolved behind anyone's back.
  Verified: text typed after the session died survives re-authentication and
  reaches the database.

### What is kept where

| | |
|---|---|
| Projects, figures, history | Postgres — the record |
| Language, theme, open tab, filters | `localStorage` — per person, per browser |

`localStorage` still holds a copy of the projects. That is what makes a reload
instant and what keeps the figures readable if the network drops. The server is
the record; the browser copy is a convenience.

Every revision is kept, trimmed to the last 50 per project, with who changed it
and when. The app is granted `SELECT` on that table and nothing else, so the
audit trail is append-only from the outside.

### Cost, honestly

Build and test on the **Free** plan: 500 MB, and £0. Two things make it wrong
for the live tool — it **pauses after a week of inactivity**, and it has **no
automatic backups**. Move to **Pro (~$25/month)** at handover, which removes
both. It is a plan change, not a migration: same code, same database.

⚠️ **Storage.** 40 projects measured 654 KB, and history multiplies that. 500 MB
is a long way off at this scale, but it is not unlimited — worth a look once
there are hundreds of jobs.

## Booking (Calendly)

`BOOKING_URL` in `build.py` points at the company's Calendly. Every **Book a
call** — header, mobile menu, hero — uses it.

**The widget is fetched on the click, never on page load.** The button is a
plain link that works with JavaScript off; clicking it upgrades to Calendly's
own popup, loading `widget.js` and `widget.css` at that moment. If the fetch
fails or a blocker eats it, the original link is followed instead, so the
button is never a dead end.

That ordering is the whole point. Embedding the widget normally would send
every visitor's IP to Calendly whether or not they ever book, and this site
otherwise makes **no third-party request at all**. Verified: browsing the
homepage, contacts and both translations produces zero off-site requests; the
first Calendly request appears only after the click.

**The privacy policy was updated in all three languages** to name Calendly LLC
and state exactly this — that nothing reaches them until you open the booking
window, and that once you do they receive your IP and what you enter. Leaving
the old "loads no third-party scripts" wording in place would have made the
policy untrue.

There is still **no cookie banner on this site**, because it sets no cookies
and calls nobody until asked. Calendly shows its own consent notice inside its
popup — that one is theirs, and only appears for people who open it.

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
