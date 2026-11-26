"""usage: map_reach.py STATE [KEYS] [--wait=N] [--every=N] [--shots=DIR]

How far beyond its picture the map of Ivalice is seen (ticket 36).  From a
state on the map, presses each key of KEYS in turn (default: a walk over every
area: ">" is the R button, "<" the L button, which cycle the areas there;
L, R, U, D are the D-pad), waits N frames (default
45) for the pan to settle, traces one frame and finds the map's main piece
(texture coordinates 0,0 .. 408,256).  The screen's corners are mapped back
into the picture's texels: the texels the view reaches left of 0, right of
408, above 0 and below 300 (the picture is 408x300) are printed per stop, then
the largest of each over the walk.  Run it with ROM set to each preset's
build: the view's width is the preset's.  With --every=N, frames during the
pans are traced too (every N frames), and --shots=DIR saves a picture at each
new worst.  Mid-pan readings are not to be trusted on their own: gxtrace's
matrix model now and then misreads the map's transform for a frame, sometimes
with an absurd view size (skipped and counted) and sometimes only shifted
(ticket 36: readings of 41 below and 195 above, pictures showing the map at
rest).  Pans move between resting positions, so the resting stops are the
figures to use; check any larger reading against its picture.
"""
import os
import sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from emu import boot
from desmume.controls import Keys, keymask
import gxtrace

args = [a for a in sys.argv[1:] if not a.startswith("--")]
wait, every = 45, 0
for a in sys.argv[1:]:
    if a.startswith("--wait="):
        wait = int(a[7:])
    if a.startswith("--every="):       # also trace every N frames while the map pans
        every = int(a[8:])
shots = next((a[8:] for a in sys.argv[1:] if a.startswith("--shots=")), None)   # a picture at each new worst
state = args[0]
keys = args[1] if len(args) > 1 else ">" * 24
K = {"L": Keys.KEY_LEFT, "R": Keys.KEY_RIGHT, "U": Keys.KEY_UP, "D": Keys.KEY_DOWN, "<": Keys.KEY_L, ">": Keys.KEY_R}
emu = boot(state, rom=os.environ.get("ROM", "build/ffta2-1screen.nds"), frames=3)


def cyc(n):
    for _ in range(n):
        emu.cycle(False)


def main_piece():
    gx, _ = gxtrace.trace_frame(emu)
    for p in gx.polys:
        tc = p.get("tc", [])
        if len(p["v"]) == 4 and len(tc) == 4 and (p["tex"] & 0xFFFF) == 0 \
                and min(t[0] for t in tc) == 0 and max(t[0] for t in tc) == 408 \
                and min(t[1] for t in tc) == 0 and max(t[1] for t in tc) == 256:
            return p
    return None


def reach(p):
    """texels beyond the picture at the view's edges: left, right, top, bottom"""
    v, tc = p["v"], p["tc"]
    # affine map screen -> texel from three corners
    (x0, y0), (x1, y1), (x2, y2) = v[0], v[1], v[2]
    (s0, t0), (s1, t1), (s2, t2) = tc[0], tc[1], tc[2]
    det = (x1 - x0) * (y2 - y0) - (x2 - x0) * (y1 - y0)
    if abs(det) < 1e-6:
        return (1e9,) * 4                   # degenerate (a misread): fails plausible()
    def tex(x, y):
        a = ((x - x0) * (y2 - y0) - (x2 - x0) * (y - y0)) / det
        b = ((x1 - x0) * (y - y0) - (x - x0) * (y1 - y0)) / det
        return s0 + a * (s1 - s0) + b * (s2 - s0), t0 + a * (t1 - t0) + b * (t2 - t0)
    cs = [tex(x, y) for x in (0, 256) for y in (0, 192)]
    ss, ts = [c[0] for c in cs], [c[1] for c in cs]
    return -min(ss), max(ss) - 408, -min(ts), max(ts) - 300


worst = [-1e9] * 4
seen = set()
size, skipped = None, 0


def plausible(r):
    """the map does not zoom: the view always spans the same number of texels"""
    global size, skipped
    w, h = r[0] + r[1] + 408, r[2] + r[3] + 300
    if size is None:
        size = (w, h)
    if abs(w - size[0]) > 0.02 * size[0] or abs(h - size[1]) > 0.02 * size[1]:
        skipped += 1
        return False
    return True
for i, k in enumerate(" " + keys):
    if k != " ":
        emu.input.keypad_add_key(keymask(K[k])); cyc(10)
        emu.input.keypad_rm_key(keymask(K[k]))
    if every:
        for f in range(0, wait, every):
            cyc(every)
            p = main_piece()
            if p and plausible(reach(p)):
                r = reach(p)
                if any(a > b + 0.05 for a, b in zip(r, worst)):
                    if shots:
                        os.makedirs(shots, exist_ok=True)
                        emu.screenshot().save("%s/%02d_%02d.png" % (shots, i, f + every))
                    print("%3d %s  frame %2d  left %6.1f  right %6.1f  top %6.1f  bottom %6.1f (panning)" % ((i, k, f + every) + r), flush=True)
                worst = [max(a, b) for a, b in zip(worst, r)]
    else:
        cyc(wait)
    p = main_piece()
    if not p:
        print("%3d %s  no map piece" % (i, k))
        continue
    r = reach(p)
    if not plausible(r):
        continue
    key = tuple(round(x) for x in r)
    if key not in seen:
        seen.add(key)
        print("%3d %s  left %6.1f  right %6.1f  top %6.1f  bottom %6.1f" % ((i, k) + r), flush=True)
    worst = [max(a, b) for a, b in zip(worst, r)]
print("stops %d  worst: left %.1f  right %.1f  top %.1f  bottom %.1f  (%d misread frames skipped)" % ((len(seen),) + tuple(worst) + (skipped,)))
