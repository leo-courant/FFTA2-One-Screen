#!/usr/bin/env python3
"""Contact sheet: sheet.py OUT.png IMG..."""
import sys
from PIL import Image, ImageDraw
out, paths = sys.argv[1], sys.argv[2:]
ims = [Image.open(p).convert("RGB") for p in paths]
w, h = ims[0].size
sheet = Image.new("RGB", ((w + 6) * len(ims), h + 14), "magenta")
d = ImageDraw.Draw(sheet)
for i, (im, p) in enumerate(zip(ims, paths)):
    sheet.paste(im, (i * (w + 6), 14))
    d.text((i * (w + 6) + 2, 1), p.rsplit("/", 1)[-1], fill="white")
sheet.save(out)
