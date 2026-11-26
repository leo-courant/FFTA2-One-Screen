#!/usr/bin/env python3
"""Half-size contact sheet of both screens: thumbs.py OUT.png PERROW IMG..."""
import sys
from PIL import Image, ImageDraw
out, per, paths = sys.argv[1], int(sys.argv[2]), sys.argv[3:]
ims = [Image.open(p).convert("RGB").resize((192, 288)) for p in paths]
sheet = Image.new("RGB", (196 * per, 302 * ((len(ims) + per - 1) // per)), "magenta")
d = ImageDraw.Draw(sheet)
for i, (im, p) in enumerate(zip(ims, paths)):
    x, y = (i % per) * 196, (i // per) * 302
    sheet.paste(im, (x, y + 12)); d.text((x + 2, y), p.rsplit("/", 1)[-1][:-4], fill="white")
sheet.save(out)
