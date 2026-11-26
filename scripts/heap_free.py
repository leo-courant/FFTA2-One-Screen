"""usage: heap_free.py [--rom ROM] [--frames N] STATE...

How much of the game's main RAM heaps is free (ticket 36: may the mod's code
reserve grow, which moves the main heap start up and shrinks the heap?).

The game makes NNS "expanded heaps" (head signature EXPH) in the arena whose
start the mod moves (arena_lo_literal).  For each state this finds every
expanded heap head in main RAM, walks its free list (blocks signed "FR") and
prints the heap's range, total free bytes and largest free block.  With
--frames N it plays N frames and reports the lowest free total seen.
"""
import argparse
import os
import sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from emu import boot

ap = argparse.ArgumentParser()
ap.add_argument("states", nargs="+")
ap.add_argument("--rom", default="build/ffta2-1screen.nds")
ap.add_argument("--frames", type=int, default=0)
ap.add_argument("--every", type=int, default=10)
ap.add_argument("--cold", type=int, default=0, metavar="N", help="STATE is ignored: boot the ROM cold and play N frames first")
args = ap.parse_args()

LO, HI = 0x02000000, 0x023E0000
SIG = 0x45585048            # "EXPH"


def heaps(emu):
    ram = b"".join(bytes(emu.memory.unsigned[a:a + 0x40000]) for a in range(LO, HI, 0x40000))
    u32 = lambda a: int.from_bytes(ram[a - LO:a - LO + 4], "little")
    out = []
    i = ram.find(b"HPXE")
    while i >= 0:
        if i % 4 == 0:
            h = LO + i
            start, end = u32(h + 0x18), u32(h + 0x1C)
            if LO <= start < end <= HI:
                out.append(h)
        i = ram.find(b"HPXE", i + 1)
    return out


def walk(emu, h):
    m = emu.memory.unsigned
    start, end = m.read_long(h + 0x18), m.read_long(h + 0x1C)
    free, big, n = 0, 0, 0
    b = m.read_long(h + 0x24)           # free list head
    while b and n < 10000:
        if not LO <= b < HI - 16 or m.read_short(b) != 0x4652:   # "FR" (reading outside RAM crashes py-desmume)
            return start, end, None, None
        size = m.read_long(b + 4)
        free += size
        big = max(big, size)
        b = m.read_long(b + 12)         # next
        n += 1
    return start, end, free, big


for st in args.states:
    emu = boot(None if args.cold else st, args.rom, frames=args.cold or 3)
    hs = heaps(emu)
    low = {}
    for f in range(0, args.frames + 1, args.every):
        if f:
            for _ in range(args.every):
                emu.cycle(False)
            hs = heaps(emu)
        for h in hs:
            s, e, free, big = walk(emu, h)
            if free is None:
                continue
            k = (s, e)
            if k not in low or free < low[k][0]:
                low[k] = (free, big, f)
    for (s, e), (free, big, f) in sorted(low.items()):
        print("%-28s heap %08X-%08X (%7d B)  free %7d B  largest %7d B  (frame %d)"
              % (os.path.basename(st), s, e, e - s, free, big, f))
