# Brand guidelines — working notes

Source: LITPROFIT Brand Guidelines, 36 pages, "MADE BY ALDY". Supplied as
per-page PDF exports.

**Received so far: pages 33, 34, 35, 36** — the application mockups (pencils,
presentation box, truck curtain, shipping containers, illuminated sign) and the
closing slide.

**Still needed** — these are the pages that actually set the CSS tokens:

- the colour palette page, with hex/Pantone/CMYK values;
- the typography page, naming the wordmark face and the text face, with the
  weights and the type scale;
- the logo construction page — clear space, minimum size, the safe area;
- the logo misuse page, so the site does not commit one;
- any page covering iconography, photography treatment or the grid.

## What pages 33–36 establish

**The identity is new.** The mark on these pages is a geometric monogram — an
interlocking L and P with a hard diagonal cut — and it is not the logo the live
litprofit.com serves. The wordmark is set in a heavy geometric sans, wide and
tightly spaced.

**There is no red.** The current site's logo SVG contains `#ed1c25`, and nothing
in these four pages uses it. The palette here is deep indigo navy, white, a mid
warm grey, and black. Treat the sampled `#273e94` / `#ed1c25` / `#79aee2` in the
README as superseded, pending the palette page.

**Navy is the dominant colour** and carries the identity — full-bleed
backgrounds, container sides, the sign face. White is the mark's reversed form.
Grey appears as a material (packaging, pencils) rather than as an interface
colour. Black is used as a separate ground, not as a shade of the navy.

Estimated from the mockup renders: navy is around `#1B1B63`, a deep indigo
noticeably darker and more violet than the old `#273e94`. **This is an estimate
off JPEG-compressed artwork — do not commit it as a token.** The palette page
governs.

**`//` is a brand device.** The guideline page furniture numbers pages as
`33 // 36`. It is a cheap, distinctive detail to carry into the site as a
separator — in eyebrows, breadcrumbs and the footer.

**Supporting type is caps with wide letterspacing**, in a light weight, at small
sizes — `LITPROFIT`, `BRAND GUIDELINES`. That maps directly onto the site's
eyebrow and label styles.

**Photography is dark and industrial** — low-key lighting, night yards, wet
concrete, workers in silhouette. That is a strong steer for the site's hero
treatment, and it suggests a dark site rather than the light one the current
litprofit.com uses.

## Consequences for the build

The typeface is the open question. Montserrat is already vendored in
`assets/fonts/` as a stand-in, and it is not what the wordmark is set in. If the
brand face is a licensed commercial font, using it as a webfont needs a separate
web licence — worth resolving early, because it changes the whole page.

If Russian is added later, the chosen face needs a Cyrillic subset. The
Montserrat files vendored now cover latin and latin-ext only, so Lithuanian
diacritics are fine but Cyrillic is not.
