# LITPROFIT — website

Static site (HTML/CSS/JS, no build step), rebuilding **litprofit.com** for
UAB "Litprofit". Same architecture as the ALPROJECTS Group site. Made by ALDY.

Status: **foundation** — repo scaffolded, existing site content and assets
harvested. The visual design is pending the Figma corporate style export.

## The company

UAB "Litprofit" — ship repair and maintenance, worldwide. Founded 2010,
based in Klaipeda, Lithuania. Positioning line: *We consult → We organise →
We ensure*.

| | |
|---|---|
| Address | Svajones str. 30, LT-94101 Klaipeda, Lithuania |
| Phone | +370 670 20 357 |
| Email | info@litprofit.com |
| Company ID | 302568798 |
| VAT | LT100005766815 |
| Insurance | Compensa Vienna Insurance Group ADB, EUR 250,000 (policy 230 0008143 / 2020) |

Authorised partner of **BITZER**; marine line representative for **DANFOSS**.
Certified by **RINA** and **PRS** (PDFs in `assets/certs/`).

## Brand colours

Sampled from the company logo — the starting palette until the Figma export
lands:

| Token | Value | Where it comes from |
|---|---|---|
| deep blue | `#273e94` | logo wordmark, dominant |
| red | `#ed1c25` | logo accent |
| light blue | `#79aee2` | logo secondary |

## Structure of the old site

Eleven pages, trilingual (EN at root, `/lt`, `/ru`), on Lithuanian slugs:

```
/                                              home
/about-us                                      about
/paslaugos                                     services index
/paslaugos/laivu-irangos-ir-varikliu-remontas  ship equipment and engine repair
/paslaugos/saldymo-sistemos-ir-iranga          refrigeration systems and equipment
/paslaugos/laivu-korpusu-ir-vamzdynu-darbai    hull and piping works
/paslaugos/atsarginiu-daliu-tiekimas           supply of spare parts
/projektai                                     completed works
/clients                                       partners
/sertifikatai                                  certificates
/contacts                                      contacts
```

Full text of every English page is preserved in
[`docs/source-site-EN.txt`](docs/source-site-EN.txt) so nothing is lost in the
rebuild.

Known weaknesses in the old site, to fix in this one:

- "Skaityti toliau" (Lithuanian for *read more*) is left untranslated on the
  English pages, including the homepage;
- the contact form labels are Lithuanian on the English page
  (Vardas / Telefonas / El. paštas / Žinutė);
- only the homepage has a `<meta name="description">`, and it is in Lithuanian
  on the English page;
- "Completed works" and "Partners" are effectively empty — a heading and some
  logos, no project copy;
- the English slugs are Lithuanian, which costs relevance on English queries.

## What is here now

```
assets/brand/     logo.svg, logo-inverted.svg (from the live site)
assets/clients/   ten client/partner logos, 400x400 PNG
assets/certs/     RINA and PRS certificates, PDF
docs/             harvested source content
```

## Hosting

GitHub Pages off `main`. Until a domain is pointed at it, the site serves from
the project URL — no `CNAME` file is committed yet, because adding one before
DNS exists takes the default URL down too.
