#!/usr/bin/env python3
"""Which texture memory does one frame of a savestate actually reference?
tex_usage.py STATE  -> merged byte ranges (hex), from the polygon trace."""
import sys
sys.path.insert(0, 'scripts')
from emu import boot
import gxtrace
emu = boot(sys.argv[1], rom='build/ffta2-1screen.nds', frames=3)
gx, unk = gxtrace.trace_frame(emu)
BPP = {1: 8, 2: 2, 3: 4, 4: 8, 5: 2, 6: 8, 7: 16}
r = []
for p in gx.polys:
    t = p['tex']; f = (t >> 26) & 7
    if not f or not p['v']: continue
    w, h = 8 << ((t >> 20) & 7), 8 << ((t >> 23) & 7)
    a = (t & 0xFFFF) * 8
    r.append((a, a + w * h * BPP[f] // 8, f, w, h))
r = sorted(set(r))
sys.stderr.write("USE %s\n" % sys.argv[1])
for a, b, f, w, h in r:
    sys.stderr.write("USE   %05x-%05x fmt%d %dx%d\n" % (a, b, f, w, h))
