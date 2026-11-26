#!/usr/bin/env python3
"""List the big pictures of a Scion's animation (ticket 26): every sprite-queue quad, in game
pixels of the tall picture (0,0 = its middle, the 4:3 picture is -128..128 x -192..192), that
reaches both old side edges, or one of them, grouped by texture.
usage: scion_quads.py K [FRAMES]"""
import os, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from play_scion import start, DUAL, NAMES, log
k = int(sys.argv[1]); frames = int(sys.argv[2]) if len(sys.argv) > 2 else 1300
emu = start(k); m = emu.memory.unsigned
import collections
s32 = lambda v: v - (1 << 32) if v >> 31 else v
s16 = lambda v: (v & 0xffff) - 0x10000 if v & 0x8000 else v & 0xffff
groups = collections.OrderedDict(); st = {"n": None, "max": 0}


def draw(a, size):
    if st["n"] is None or not m.read_long(DUAL + 4): return True
    q = m.read_long(m.read_long(0x01FFCF3C)); p, end = m.read_long(q), m.read_long(q + 8)
    st["max"] = max(st["max"], (end - p) // 0xA0)
    W, H = 640, 400
    while p < end:
        e = [m.read_long(p + 4 * i) for i in range(40)]; p += 0xA0
        if e[0] != 0x002B2A29: continue
        M = [s32(v) / 4096 for v in e[5:21]]
        pts = []
        for i in (25, 29, 32, 36):
            x, y = s16(e[i]) / 4096, s16(e[i] >> 16) / 4096
            z = s16(e[i + 1]) / 4096
            cx, cy = x * M[0] + y * M[4] + z * M[8] + M[12], x * M[1] + y * M[5] + z * M[9] + M[13]
            w = x * M[3] + y * M[7] + z * M[11] + M[15] or 1
            pts.append((cx / w * W / 2, cy / w * H / 2))
        xs, ys = [p_[0] for p_ in pts], [p_[1] for p_ in pts]
        if max(ys) < -192 or min(ys) > 192: continue
        l, r = min(xs), max(xs)
        kind = "both" if l <= -120 and r >= 120 else "left" if l <= -120 < r else "right" if r >= 120 > l else None
        if not kind: continue
        t = e[2]; rot = abs(M[1]) + abs(M[4]) > .01 or len({round(x) for x in xs}) > 2
        uv = [(s16(e[i]) / 16, s16(e[i] >> 16) / 16) for i in (24, 27, 31, 34)]
        fmt = (t >> 26) & 7
        key = (kind, "%dx%d" % (8 << ((t >> 20) & 7), 8 << ((t >> 23) & 7)) if fmt else "-", "fmt%d" % fmt, "tex%05x" % ((t & 0xffff) * 8), "wrap%d%d" % ((t >> 16) & 1, (t >> 17) & 1), "flip%d%d" % ((t >> 18) & 1, (t >> 19) & 1), "rot" if rot else "axis")
        g = groups.setdefault(key, [st["n"], st["n"], 0, 1e9, -1e9, 1e9, -1e9, 99, -1, None, set()])
        g[1] = st["n"]; g[2] += 1; g[3] = min(g[3], l); g[4] = max(g[4], r); g[5] = min(g[5], min(ys)); g[6] = max(g[6], max(ys))
        al = (e[1] >> 16) & 31; g[7] = min(g[7], al); g[8] = max(g[8], al); g[9] = uv; g[10].add((e[1]>>4)&3)
    return True


emu.memory.register_exec(0x0208F97C, draw)
for f in range(frames):
    emu.cycle(False)
    o = m.read_long(DUAL + 0x18)
    if o and st["n"] is None: st["n"] = 0
    if st["n"] is not None:
        st["n"] += 1
        if not o and st["n"] > 200: break
print("%s: up to %d quads a frame" % (NAMES[k], st["max"]), file=sys.stderr)
for key, g in groups.items():
    print("Q %s frames %d..%d n=%d  x %.0f..%.0f y %.0f..%.0f alpha %d..%d mode %s uv %s" % (" ".join(key), *g[:9], g[10], g[9]), file=sys.stderr)
