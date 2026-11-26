"""usage: map_art_tear.py LEFT_EXT.png RIGHT_EXT.png OUT.png [--tear=X] [--seed=N]

Step 2b of the map of Ivalice's extended edges (ticket 36, ADR 0018): put
together the extended picture from two outpaint runs, the left side (picture
x < 204) from LEFT_EXT and the right side from RIGHT_EXT (both map_ext.png from
map_art_outpaint.py, 16 colours, the picture at 64, 32).  With --tear=X the
right side is torn like the left one: the parchment stops along a ragged edge
around picture x = X and flat sea (colour 1, the left side's sea) lies beyond.
The edge wanders a few texels row by row (smooth noise) and frays into loose
specks, as LaMa's left side does.
"""
import random
import sys
from PIL import Image

PX, PY, W, H = 64, 32, 408, 300
SEA = 1

args = [a for a in sys.argv[1:] if not a.startswith("--")]
opt = dict(a[2:].split("=", 1) for a in sys.argv[1:] if a.startswith("--"))
left, right = Image.open(args[0]), Image.open(args[1])
assert left.mode == right.mode == "P" and left.size == right.size
out = left.copy()
lp, rp, op = left.load(), right.load(), out.load()
w, h = out.size
for y in range(h):
    for x in range(PX + 204, w):
        op[x, y] = rp[x, y]

if "tear" in opt:
    rnd = random.Random(int(opt.get("seed", 36)))
    tear = PX + int(opt["tear"])

    def smooth(n, step, amp):
        """value noise: a random value every `step` rows, eased in between"""
        keys = [rnd.uniform(-amp, amp) for _ in range(n // step + 2)]
        vals = []
        for y in range(n):
            k, f = divmod(y, step)
            f /= step
            f = f * f * (3 - 2 * f)
            vals.append(keys[k] * (1 - f) + keys[k + 1] * f)
        return vals

    big, mid, small = smooth(h, 30, 6), smooth(h, 7, 3.5), smooth(h, 2, 1.5)
    for y in range(h):
        edge = tear + big[y] + mid[y] + small[y]
        for x in range(PX + 204, w):
            d = x - edge
            # beyond the edge: sea, with a few loose specks of parchment near it;
            # just inside it: a few holes of sea, so the edge frays
            if d > 0 and not (d < 6 and rnd.random() < 0.3 * (6 - d) / 6):
                op[x, y] = SEA
            elif -4 < d <= 0 and rnd.random() < 0.25 * (4 + d) / 4:
                op[x, y] = SEA
out.save(args[2])
print("wrote", args[2])
