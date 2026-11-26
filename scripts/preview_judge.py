#!/usr/bin/env python3
"""The law announcement's judge over one whole loop (ticket 35): preview/judge.html.

usage: preview_judge.py
Needs shots/t35 (one loop = 31 frames):
  cyc/c0..c30.png  scripts/solo.py LAW_STATE "w4,sc0,w1,sc1,w1,..." (Deck preset, 1280x800)
  ref/f0..f30.png  the same moment in a --no-hooks build: play.py captures, both screens
where LAW_STATE is made from s_worldmap.dst by the lawintro steps of scripts/solo_menus.sh."""
import os, time
import numpy as np
from PIL import Image

OUT = "preview/t35"
N = 31
os.makedirs(OUT, exist_ok=True)
mod = [Image.open("shots/t35/cyc/c%d.png" % i).convert("RGB") for i in range(N)]
ref = [Image.open("shots/t35/ref/f%d.png" % i).convert("RGB").crop((0, 192, 256, 384)) for i in range(N)]


def solidity(im, box):          # how strongly the judge shows: spread of colours in the circle
    return np.array(im.crop(box)).astype(int).std()


# start both loops on the same moment: the frame where the judge is faintest
m0 = min(range(N), key=lambda i: solidity(mod[i], (205, 305, 310, 425)))
r0 = min(range(N), key=lambda i: solidity(ref[i], (4, 66, 34, 100)))
mod = mod[m0:] + mod[:m0]
ref = ref[r0:] + ref[:r0]
full = dict(save_all=True, duration=33, loop=0, lossless=True)   # half speed, to be able to follow it
mod[0].save(OUT + "/mod.webp", append_images=mod[1:], **full)
mc = [m.crop((160, 220, 520, 480)) for m in mod]
rc = [r.crop((0, 48, 103, 122)).resize((361, 259), Image.NEAREST) for r in ref]
mc[0].save(OUT + "/mod_circle.webp", append_images=mc[1:], **full)
rc[0].save(OUT + "/ref_circle.webp", append_images=rc[1:], **full)
t = int(time.time())
open("preview/judge.html", "w").write("""<!doctype html><meta charset=utf-8>
<meta name=viewport content="width=device-width,initial-scale=1"><title>Law announcement judge</title>
<style>body{background:#16161a;color:#ddd;font:15px/1.5 system-ui;margin:0;padding:24px}
h1{font-size:22px;margin:0 0 6px}p{color:#aaa;max-width:85ch}.frame{overflow-x:auto}
img{image-rendering:pixelated;display:block;outline:1px solid #444;max-width:none}
.two{display:flex;gap:24px;flex-wrap:wrap}figcaption{color:#cde;margin-top:4px}figure{margin:0}</style>
<h1>Law announcement judge (ticket 35)</h1>
<p>The mod's screen on the Deck preset, half speed. The judge grows, fades out and starts over, about twice a second
at full speed. The review capture with the empty circle was taken at the end of a fade.</p>
<div class=frame><img src="t35/mod.webp?t=%d" style="width:1280px"></div>
<p>Close-up of the same loop. The unmodified game does exactly this, so nothing was changed.</p>
<div class=two><figure><img src="t35/mod_circle.webp?t=%d"><figcaption>Mod (Deck)</figcaption></figure>
<figure><img src="t35/ref_circle.webp?t=%d"><figcaption>Unmodified game</figcaption></figure></div>
<p><b>What else to look at:</b> the panel's right end stops short of the screen edge. In the unmodified game it runs
off the edge of the 4:3 picture.</p>
""" % (t, t, t))
print("preview/judge.html written", m0, r0)
