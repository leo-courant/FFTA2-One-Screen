#!/usr/bin/env python3
"""The mod's single screen, exactly as widescreen shows it, from the fast test emulator.

usage: solo.py IN_STATE SCRIPT OUTDIR [OUT_STATE]
SCRIPT is a play.py script; every s<name> step becomes OUTDIR/<name>.png: the view (read
from ROM; 366x228 for the Deck preset) enlarged to FIT=WxH with nearest-neighbour, as an
emulator does (env, default 1280x800, the Deck), or SCALE times when SCALE is set (SCALE=5
for the 16:9 preset's 1920x1080).

The test emulator renders at DS resolution, where the squeezed widescreen picture
loses one column in six.  So the same script is run four times from the same state,
each run drawing one unsqueezed 256x192 piece of the view (TILE in play.py),
and the pieces are stitched and enlarged.  The runs are deterministic, so the
pieces agree where they overlap; a warning is printed if they do not.
The result matches melonDS at Deck resolution apart from colour rounding and animation
phase.  Limits: only what the gameplay screen draws in 3D (all battle and menu screens
seen so far); 2D layers and the SELECT screen swap come out repeated.  Polygons cut by
a piece's edge are textured with slightly different rounding, so pieces can differ by
a texel on noisy textures; that is not a fault."""
import os, subprocess, sys, tempfile
from PIL import Image, ImageChops
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
from emu import rom_blob, view_settings
state, script, out = sys.argv[1:4]
out_state = sys.argv[4] if len(sys.argv) > 4 else "-"
os.makedirs(out, exist_ok=True)
blob = open(os.environ["BLOB"], "rb").read() if os.environ.get("BLOB") else \
    rom_blob(os.environ.get("ROM", "build/ffta2-1screen.nds"))
cfg = view_settings(blob)[1]
W, H = cfg["screen_w"], cfg["screen_h"]
SCALE = int(os.environ.get("SCALE", 0))    # 0: FIT (default the Deck's 1280x800)
EX, EY = (W - 256) // 2, (H - 192) // 2


def spots(edge, size, piece, unit):
    """Piece positions along one axis, from the view's first pixel to its last, each a
    whole number of `unit` pixels from the unshifted piece (at `edge`): shifts must be
    whole projection units or the pieces round differently.  Across, 1 px is 32 units;
    down, 3 px are 128."""
    first = edge - unit * -(-edge // unit)                      # at or before 0
    last = edge + unit * -(-(size - piece - edge) // unit)      # at or after size - piece
    out = [first]
    while out[-1] < last:
        out.append(min(last, out[-1] + (piece // unit) * unit))
    return out


PIECES = [(px, py, (EX - px) * 32, (py - EY) * 128 // 3)
          for py in spots(EY, H, 192, 3) for px in spots(EX, W, 256, 1)]
with tempfile.TemporaryDirectory() as tmp:
    procs = []
    for i, (px, py, ox, oy) in enumerate(PIECES):
        env = dict(os.environ, TILE="%d,%d" % (ox, oy))
        env.pop("PLAIN", None)
        procs.append(subprocess.Popen(
            [sys.executable, os.path.join(HERE, "play.py"), state, out_state if i == 0 else "-", script, os.path.join(tmp, str(i))],
            env=env, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL))
    if any(p.wait() for p in procs):
        sys.exit("a piece failed to run")
    for name in sorted(os.listdir(os.path.join(tmp, "0"))):
        full = Image.new("RGB", (W, H))
        pieces = [Image.open(os.path.join(tmp, str(i), name)).convert("RGB").crop((0, 192, 256, 384)) for i in range(len(PIECES))]
        for piece, (px, py, ox, oy) in zip(pieces, PIECES):
            full.paste(piece, (px, py))
        # each piece should agree with the finished picture wherever it overlaps it
        differ = 0
        for piece, (px, py, ox, oy) in zip(pieces, PIECES):
            d = ImageChops.difference(full.crop((px, py, px + 256, py + 192)), piece).convert("L")
            differ += sum(d.histogram()[1:])
        size = (W * SCALE, H * SCALE) if SCALE else tuple(int(v) for v in os.environ.get("FIT", "1280x800").split("x"))
        full.resize(size, Image.NEAREST).save(os.path.join(out, name))
        print(name, "" if differ < 80000 else "note: pieces disagree in %d overlapping pixels: a 2D layer or the screen swap, which this method cannot show" % differ)
