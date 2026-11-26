#!/usr/bin/env python3
"""Contact sheet of gameplay screens only, in rows: sheet2.py OUT.png PERROW IMG..."""
import sys
from PIL import Image, ImageDraw
out, per, paths = sys.argv[1], int(sys.argv[2]), sys.argv[3:]
ims = [Image.open(p).convert("RGB").crop((0, 192, 256, 384)) for p in paths]
rows = (len(ims) + per - 1) // per
sheet = Image.new("RGB", (260 * per, 206 * rows), "magenta")
d = ImageDraw.Draw(sheet)
for i, (im, p) in enumerate(zip(ims, paths)):
    x, y = (i % per) * 260, (i // per) * 206
    sheet.paste(im, (x, y + 12)); d.text((x + 2, y), p.rsplit("/", 1)[-1][:-4], fill="white")
sheet.save(out)
