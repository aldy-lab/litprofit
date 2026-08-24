#!/usr/bin/env python3
"""Card-sized copies of the service photographs.

The same file serves two very different slots: a full-width banner on the
service page (about 1325px) and a thumbnail in the compact card on the home
page (148px). One file cannot suit both -- the card was being handed 1313px of
valve photograph to draw 148px of it, which is roughly forty times the pixels
it can show.

These are the small end of a srcset. The originals stay exactly as they are and
remain what the banner loads.
"""
import os
from PIL import Image

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SRC = os.path.join(ROOT, "assets", "photos")
WIDTH = 320          # 148px CSS at 2x, with a little room
QUALITY = 82

# every photograph that appears in a compact card
NAMES = ["workshop-valves", "svc-hull-piping", "svc-engine-repair", "workshop-overhaul"]

def main():
    saved = 0
    for name in NAMES:
        src = os.path.join(SRC, name + ".webp")
        if not os.path.exists(src):
            print("  missing, skipped: %s" % name); continue
        im = Image.open(src)
        if im.width <= WIDTH:
            print("  %-24s already %dpx" % (name, im.width)); continue
        h = round(im.height * WIDTH / im.width)
        out = os.path.join(SRC, "%s-card.webp" % name)
        im.resize((WIDTH, h), Image.LANCZOS).save(out, "WEBP", quality=QUALITY, method=6)
        was, now = os.path.getsize(src), os.path.getsize(out)
        saved += was - now
        print("  %-24s %4dpx %5.0fKB  ->  %3dx%-3d %4.0fKB"
              % (name, im.width, was/1024, WIDTH, h, now/1024))
    print("\n  a card now costs %.0f KB less than the banner it used to load" % (saved/1024))

if __name__ == "__main__":
    main()
