#!/usr/bin/env python3
"""Render page one of each certificate as a WebP thumbnail.

    python3 tools/make-cert-thumbs.py

A certificates page that lists accreditations and shows none of them is a page
of claims. The thumbnail lets a reader see the document -- the society's mark,
the company name, the certificate number -- before deciding whether to open the
PDF, which is what makes the claim checkable rather than merely stated.

Quick Look rather than sips: sips rasterises a PDF at 72dpi, which is 612px
across and visibly soft the moment it is shown at any size. qlmanage renders at
whatever height it is asked for.
"""
import os
import subprocess
import sys
from PIL import Image

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CERTS = os.path.join(ROOT, "assets", "certs")
# The thumbnail is displayed at a maximum of 186px (clamp(150px, 15vw, 186px))
# and is never used anywhere else, so 900 was 5x what the densest screen can
# show. 380 covers 186 at 2x with a little room, and takes ~85 KB off the
# certificates page.
WIDTH = 380
QUALITY = 84


def main():
    pdfs = [f for f in sorted(os.listdir(CERTS)) if f.lower().endswith(".pdf")]
    if not pdfs:
        sys.exit("No PDFs in %s" % CERTS)
    tmp = os.path.join("/tmp", "litprofit-certthumbs")
    subprocess.run(["rm", "-rf", tmp], check=False)
    os.makedirs(tmp, exist_ok=True)

    for pdf in pdfs:
        src = os.path.join(CERTS, pdf)
        subprocess.run(["qlmanage", "-t", "-s", "1600", "-o", tmp, src],
                       capture_output=True)
        rendered = os.path.join(tmp, pdf + ".png")
        if not os.path.exists(rendered):
            print("%-34s could not be rendered" % pdf)
            continue
        im = Image.open(rendered).convert("RGB")
        h = round(im.size[1] * WIDTH / im.size[0])
        im = im.resize((WIDTH, h), Image.LANCZOS)
        dest = os.path.join(CERTS, os.path.splitext(pdf)[0] + ".webp")
        im.save(dest, "WEBP", quality=QUALITY, method=6)
        print("%-34s -> %-34s %4dx%-4d %5dKB" % (
            pdf, os.path.basename(dest), im.size[0], im.size[1],
            os.path.getsize(dest) // 1024))


if __name__ == "__main__":
    main()
