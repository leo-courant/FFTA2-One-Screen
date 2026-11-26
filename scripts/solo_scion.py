#!/usr/bin/env python3
"""A Scion's animation exactly as the mod shows it (ticket 26), from the fast test emulator.

usage: solo_scion.py K OUTDIR FRAMES        FRAMES: comma list of frames into the animation, or A-B/STEP
(frames from about 200 on: the lead-in before them uses the normal view, see solo.py)
Like solo.py: the animation is played once per piece of the tall view (read from ROM's
"TALL" settings), each run drawing one unsqueezed 256x192 piece, and the pieces are stitched
and enlarged to FIT=WxH (default 1280x800). The trails the game makes by blending each frame
into the last are there too, since every piece goes through the same capture."""
import os, subprocess, sys, tempfile
from PIL import Image
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
from emu import rom_blob
k, out, frames = sys.argv[1:4]
if "-" in frames:       # A-B/STEP
    ab, _, step = frames.partition("/")
    a, _, e = ab.partition("-")
    frames = ",".join(str(v) for v in range(int(a), int(e), int(step or 1)))
os.makedirs(out, exist_ok=True)
b = rom_blob(os.environ.get("ROM", "build/ffta2-1screen.nds"))
at = b.index(b"TALL") + 4
W, H = (int.from_bytes(b[at + 4 * i:at + 4 * i + 4], "little") for i in (0, 1))
EX, EY = (W - 256) // 2, (H - 192) // 2


def spots(edge, size, piece, unit):
    first = edge - unit * -(-edge // unit)
    last = edge + unit * -(-(size - piece - edge) // unit)
    res = [first]
    while res[-1] < last:
        res.append(min(last, res[-1] + (piece // unit) * unit))
    return res


PIECES = [(px, py, (EX - px) * 32, (py - EY) * 128 // 3)
          for py in spots(EY, H, 192, 3) for px in spots(EX, W, 256, 1)]
fit = tuple(int(v) for v in os.environ.get("FIT", "1280x800").split("x"))
with tempfile.TemporaryDirectory() as tmp:
    procs = [subprocess.Popen([sys.executable, os.path.join(HERE, "play_scion.py"), k, os.path.join(tmp, str(i)), frames if "," in frames else frames + ",-1"],
                              env=dict(os.environ, TILE="%d,%d" % (ox, oy)), stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
             for i, (px, py, ox, oy) in enumerate(PIECES)]
    if any(p.wait() for p in procs):
        sys.exit("a piece failed to run")
    for f in frames.split(","):
        full = Image.new("RGB", (W, H))
        for i, (px, py, ox, oy) in enumerate(PIECES):
            full.paste(Image.open(os.path.join(tmp, str(i), "%s_%04d.png" % (k, int(f)))).convert("RGB").crop((0, 192, 256, 384)), (px, py))
        full.resize(fit, Image.NEAREST).save(os.path.join(out, "%s_%04d.png" % (k, int(f))))
