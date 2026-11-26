#!/usr/bin/env python3
"""Ticket 07: play.py steps that stretch the second battle's text runs on the info
screen (objective, law, privilege) to given widths, by repeating each run's own
rendered cells, so the banner can be checked with the longest texts in the game.

usage: banner_stretch.py OBJ LAW PRIV OUT.steps     (cells of text; 0 = leave as is)
Then: scripts/solo.py states/s_battle2.dst "$(cat OUT.steps),w10,sNAME" OUTDIR

The longest texts in the game's tables (master/pc.bin, ~5 px per character):
  objective  48 characters   about 28 cells
  law        27 characters   about 18 cells
  privilege  19 characters   about 13 cells
so 28 18 13 is the worst case.  Words come out cut where the repeat stops; that is
the test, not the banner."""
import contextlib, io, os, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
with contextlib.redirect_stdout(io.StringIO()):
    from emu import boot
    emu = boot("states/s_battle2.dst", rom=os.environ.get("ROM", "build/ffta2-1screen.nds"), frames=1)
m = emu.memory.unsigned
r16 = lambda a: m[a] | (m[a + 1] << 8)
base = 0x06200000 + ((r16(0x0400100A) >> 8) & 31) * 0x800      # info screen BG1 map
steps = []
# (row, first text column, last text column) of each run in s_battle2
for (row, start, end), n in zip(((0, 4, 13), (3, 5, 8), (6, 5, 11)), map(int, sys.argv[1:4])):
    src = [(r16(base + 2 * (row * 32 + c)), r16(base + 2 * ((row + 1) * 32 + c))) for c in range(start, end + 1)]
    for i in range(min(n, 32 - start)):
        top, bottom = src[i % len(src)]
        steps += ["p%x=%x" % (base + 2 * (row * 32 + start + i), top),
                  "p%x=%x" % (base + 2 * ((row + 1) * 32 + start + i), bottom)]
open(sys.argv[4], "w").write(",".join(steps))
