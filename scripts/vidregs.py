#!/usr/bin/env python3
"""Dump the video setup of a savestate: vidregs.py STATE...  (one emulator per process)"""
import os, subprocess, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
if len(sys.argv) > 2:
    for s in sys.argv[1:]:
        subprocess.run([sys.executable, __file__, s], stderr=subprocess.DEVNULL)
    sys.exit(0)
from emu import boot
emu = boot(sys.argv[1], rom="build/ffta2-1screen.nds", frames=4)
sys.stdout.flush()
m = emu.memory.unsigned
r8 = lambda a: m[a]; r16 = m.read_short; r32 = m.read_long
print("==", sys.argv[1])
print(" VRAMCNT A-G: " + " ".join("%s=%02x" % (c, r8(0x04000240 + i)) for i, c in zip((0, 1, 2, 3, 4, 5, 6), "ABCDEFG")),
      "H=%02x I=%02x" % (r8(0x04000248), r8(0x04000249)), "POWCNT1=%04x" % r16(0x04000304))
for name, base in (("main", 0x04000000), ("sub ", 0x04001000)):
    d = r32(base)
    print(" %s DISPCNT=%08x mode=%d bg0_3d=%d layers(bg0-3,obj)=%s win=%d%d%d extpal(bg,obj)=%d%d objmap=%s charbase=%d screenbase=%d" % (
        name, d, d & 7, (d >> 3) & 1, format((d >> 8) & 31, "05b")[::-1], (d >> 13) & 1, (d >> 14) & 1, (d >> 15) & 1,
        (d >> 30) & 1, (d >> 31) & 1, "1D" if d & 0x10 else "2D", (d >> 24) & 7, (d >> 27) & 7))
    for i in range(4):
        c = r16(base + 8 + 2 * i)
        print("   BG%d CNT=%04x prio=%d char=%d %s screen=%d size=%d  scroll=%d,%d" % (
            i, c, c & 3, (c >> 2) & 15, "8bpp" if c & 0x80 else "4bpp", (c >> 8) & 31, c >> 14,
            r16(base + 0x10 + 4 * i) & 511, r16(base + 0x12 + 4 * i) & 511))
    print("   BLDCNT=%04x BLDALPHA=%04x BLDY=%04x WININ=%04x WINOUT=%04x" % tuple(r16(base + o) for o in (0x50, 0x52, 0x54, 0x48, 0x4A)))
