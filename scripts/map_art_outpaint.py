"""usage: map_art_outpaint.py MODEL.pt MAP_FULL.png MAP_TEX.png OUTDIR [UP] [FADE_RIGHT]

Step 2 of the map of Ivalice's extended edges (ticket 36, ADR 0018): extend the
picture with LaMa (big-lama, TorchScript, CPU).  MAP_FULL is the game's own
picture (408x300, map_art_dump.py); the faded band at its left and right edges
is repainted too, and a margin all round is added.  The result is brought back
to the texture's 16 colours: OUTDIR/map_ext.png (and map_ext_rgb.png).  The
released art was made with UP=2 (1 gives blotchy parchment, 4 a flat sea).
FADE_RIGHT (default 8) is how much of the picture's right end is repainted:
its fade starts about 13 texels from the end (16 used, ticket 36).

Needs numpy, torch and pillow, which the mod's .venv does not have: use a
separate virtualenv, and keep the model and the output in work/.
Next: map_art_pack.py.
"""
import sys
import numpy as np
import torch
from PIL import Image

PX, PY, FADE = 64, 32, 8
UP = int(sys.argv[5]) if len(sys.argv) > 5 else 1   # run LaMa on the picture enlarged UP times
FADE_R = int(sys.argv[6]) if len(sys.argv) > 6 else FADE
MODEL, FULL, TEX, OUT = sys.argv[1:5]
src = Image.open(FULL).convert("RGB")
W, H = src.size
cw, ch = W + 2 * PX, H + 2 * PY
ch8 = (ch + 7) // 8 * 8
img = Image.new("RGB", (cw, ch8))
img.paste(src, (PX, PY))
mask = np.ones((ch8, cw), np.float32)
mask[PY:PY + H, PX + FADE:PX + W - FADE_R] = 0      # keep the picture, not its faded sides
big = img.resize((cw * UP, ch8 * UP), Image.NEAREST)
bmask = np.kron(mask, np.ones((UP, UP), np.float32))
x = torch.from_numpy(np.asarray(big, np.float32) / 255).permute(2, 0, 1)[None]
mk = torch.from_numpy(bmask)[None, None]
model = torch.jit.load(MODEL, map_location="cpu").eval()
with torch.no_grad():
    out = model(x * (1 - mk), mk)[0].permute(1, 2, 0).clamp(0, 1).numpy()
out = Image.fromarray((out * 255).astype(np.uint8)).resize((cw, ch8), Image.BOX)
res = np.asarray(out)[:ch]
keep = np.asarray(img)[:ch]
res = np.where(mask[:ch, :, None] > 0, res, keep)
pal = Image.open(TEX).getpalette()[:48]
pimg = Image.new("P", (1, 1))
pimg.putpalette(pal + [0] * (768 - 48))
q = Image.fromarray(res).quantize(palette=pimg, dither=Image.Dither.NONE)
q.save(OUT + "/map_ext.png")
Image.fromarray(res).save(OUT + "/map_ext_rgb.png")
print("extended", q.size)
