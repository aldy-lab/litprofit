#!/usr/bin/env python3
"""Turn the client's workshop photographs into site assets.

    python3 tools/make-photos.py ~/Downloads/litprofit-photos

Two things it does that matter:

TRIMS THE BARS. Some of these are video frames, letterboxed with a flat dark
grey rather than true black -- photo4 carried 25 rows of it above the picture
and 186 below. A naive "crop the black" test misses that, and the bars then
survive into the page as a stripe nobody can explain.

RE-ENCODES TO WEBP. The site is otherwise WebP throughout, self-hosted, and
makes no third-party request; a stray JPEG would be both heavier and out of
step with everything around it.
"""
import os
import sys
from PIL import Image

# name, source file, and how the picture is used -- the crop follows the use,
# because a banner and a card want different parts of the same photograph.
PLAN = [
    ("workshop-valves",   "photo1 copy.jpeg", None),
    ("workshop-overhaul", "photo2 copy.jpeg", None),
    ("workshop-bench",    "photo3 copy.jpeg", None),
    ("workshop-rotors",   "photo4 copy.jpeg", None),
]
OUT = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
                   "assets", "photos")
QUALITY = 82
BAR = 40          # a row this flat and this dark is packaging, not picture


def content_box(im):
    """The picture inside whatever was padded around it."""
    g = im.convert("L")
    w, h = g.size
    px = g.load()
    step_x = max(1, w // 160)
    step_y = max(1, h // 160)
    rows = [sum(px[x, y] for x in range(0, w, step_x)) / len(range(0, w, step_x))
            for y in range(h)]
    cols = [sum(px[x, y] for y in range(0, h, step_y)) / len(range(0, h, step_y))
            for x in range(w)]
    top = next((y for y, v in enumerate(rows) if v > BAR), 0)
    bot = next((y for y in range(h - 1, -1, -1) if rows[y] > BAR), h - 1)
    left = next((x for x, v in enumerate(cols) if v > BAR), 0)
    right = next((x for x in range(w - 1, -1, -1) if cols[x] > BAR), w - 1)
    return left, top, right + 1, bot + 1


def main():
    src = os.path.expanduser(sys.argv[1] if len(sys.argv) > 1
                             else "~/Downloads/litprofit-photos")
    os.makedirs(OUT, exist_ok=True)
    print("%-20s %-13s %-13s %8s  %s" % ("name", "source", "after crop", "webp", "trimmed"))
    for name, filename, _ in PLAN:
        path = os.path.join(src, filename)
        if not os.path.exists(path):
            print("%-20s MISSING %s" % (name, path))
            continue
        im = Image.open(path).convert("RGB")
        before = im.size
        box = content_box(im)
        im = im.crop(box)
        dest = os.path.join(OUT, name + ".webp")
        im.save(dest, "WEBP", quality=QUALITY, method=6)
        trimmed = (before[0] - im.size[0], before[1] - im.size[1])
        print("%-20s %5dx%-7d %5dx%-7d %6dKB  %dpx wide, %dpx tall" % (
            name, before[0], before[1], im.size[0], im.size[1],
            os.path.getsize(dest) // 1024, trimmed[0], trimmed[1]))


if __name__ == "__main__":
    main()
