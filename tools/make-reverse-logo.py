#!/usr/bin/env python3
"""Generate a reverse (white-on-transparent) version of a client logo.

Most of the client logos are ink on a transparent canvas, so the CSS knockout
(`brightness(0) invert(1)`) reverses them correctly: every opaque pixel goes
white, the transparent gaps stay gaps, and any detail knocked out of the mark
survives because it was never painted in the first place.

Ocean Whale Company is the exception. Its artwork has a solid white disc baked
in as a background plate -- 60% of its opaque pixels are near-white -- so the
whale is drawn ON white rather than knocked out of it. A CSS filter cannot tell
plate from ink: it pushes both to white and the mark collapses into a
featureless disc. The plate has to be removed in the pixels instead.

So: drop near-white to transparent, take everything darker as ink and paint it
flat white, and ramp across the boundary so the antialiased edges stay smooth.

    python3 tools/make-reverse-logo.py assets/clients/ocean-whale-company.png
"""
import sys, os
from PIL import Image

# Luminance window over which a pixel fades from ink to plate. Everything below
# INK is solid ink; everything above PLATE is background to be dropped.
INK, PLATE = 0.75, 0.95


def reverse(src, dst):
    im = Image.open(src).convert("RGBA")
    out = Image.new("RGBA", im.size)
    px, ox = im.load(), out.load()
    for y in range(im.size[1]):
        for x in range(im.size[0]):
            r, g, b, a = px[x, y]
            if not a:
                continue
            lum = (0.2126 * r + 0.7152 * g + 0.0722 * b) / 255
            ink = (PLATE - lum) / (PLATE - INK)
            ink = 0.0 if ink < 0 else (1.0 if ink > 1 else ink)
            ox[x, y] = (255, 255, 255, int(round(a * ink)))
    out = out.crop(out.getbbox() or (0, 0) + im.size)
    out.save(dst)
    return out.size


if __name__ == "__main__":
    if len(sys.argv) != 2:
        sys.exit(__doc__)
    src = sys.argv[1]
    stem, ext = os.path.splitext(src)
    dst = stem + "-rev" + ext
    w, h = reverse(src, dst)
    print("%s  ->  %s  %dx%d" % (src, dst, w, h))
