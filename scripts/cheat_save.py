#!/usr/bin/env python3
"""Make a late-game save by applying Action Replay data codes to a state (ticket 24).

    .venv/bin/python scripts/cheat_save.py IN_STATE OUT_STATE [CHEATS]

Reads the libretro cheat file for the USA game (work/cheats/ffta2-usa.cht, from
github.com/libretro/libretro-database, cht/Nintendo - Nintendo DS/; not in git), runs the
named cheats once on IN_STATE's memory, plays a few frames and saves OUT_STATE. CHEATS is a
comma list of cheat numbers (default DEFAULT below). Only codes that write the game's
save data (0x0212B000-0x0212E400) are allowed: cheats that patch game code are refused,
so the save holds nothing the unmodified game could not reach by playing.

The interpreter covers the Action Replay DS codes those cheats use: 0/1/2 (32/16/8-bit
write), 9 and 5 (conditions on KEYINPUT, taken as true: the cheat runs once on purpose),
C (loop), D0-D2 (ends), D3 (offset), D4 (add to data), D5 (data), D6-D8 (write data at
offset, step offset), DC (add to offset). Env: ROM, BLOB as in play.py; POKE="ADDR=VAL,..."
(hex, byte writes into the same save data); FLAGS="0x4c,0x51-0x64,..." (event flags to set,
bit numbers from 0x0212D734, the game's flag field; default DEFAULT_FLAGS, FLAGS=- for none).

Event flags found for ticket 24 (by logging the game's flag test 0x0208A674 while a screen
opens, scratch tool; see the ticket):
  0x4C           shop menu gets Bazaar and Sell Loot
  0x51-0x64      the 20 areas drawn on the world map
  0x2E0-0x4DF    one per mission; setting them fills Notices but empties the Quest Roster
  0x4E0-0x569    world map places
Don't set 0x58E-0x593 (they change when a mission is accepted): with them set, loading the
save restarts the game's opening.
"""
import os, re, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from emu import boot

CHT = "work/cheats/ffta2-usa.cht"
# gil, CP, rumors, laws, jobs unlocked, all tasks completed, all areas controlled,
# privileges, all items, all loot, jobs mastered, max level, all skills learnt,
# clan skills, auction awards / records
# Cheat 6 ("All Tasks Have Been Completed") is left out: with every quest marked done the pub
# has nothing to offer. Cheat 7 marks them all unfinished instead.
DEFAULT = "1,2,3,4,5,7,8,17,24,25,47,50,56,32,222,225"
DEFAULT_FLAGS = "0x4c,0x51-0x64,0x4e0-0x569"
# Story progress (u16 at 0x0212D714, read by 0x020D3A5C): 90 on the first world map; a quest is
# offered when progress >= its storyRequirement (quest record +4, check 0x020F3124). Story quests
# need 20..1290, side quests up to 1240, clan trials 160..530. 1240 offers nearly everything
# without the final story steps.
DEFAULT_PROGRESS = 1240
FLAG_BASE = 0x0212D734
DATA_LO, DATA_HI = 0x0212B000, 0x0212E400


def load(path):
    t = open(path).read()
    d = dict(re.findall(r'^(\w+) = "(.*)"$', t, re.M))
    return {int(k[5:-5]): (d[k], d.get(k[:-5] + "_code", "")) for k in d if k.endswith("_desc")}


class AR:
    def __init__(self, emu):
        self.emu, self.writes = emu, 0

    def put(self, addr, val, size):
        if not DATA_LO <= addr < DATA_HI:
            raise SystemExit(f"write to {addr:08X} is outside the save data: refused")
        m = self.emu.memory
        {4: m.write_long, 2: m.write_short, 1: m.write_byte}[size](addr, val)
        self.writes += 1

    def run(self, code):
        w = [int(x, 16) for x in code.split("+") if x]
        lines = [(w[i], w[i + 1]) for i in range(0, len(w), 2)]
        off = data = 0
        i, loop = 0, None
        while i < len(lines):
            a, v = lines[i]; t = a >> 28
            if t == 0: self.put((a & 0x0FFFFFFF) + off, v, 4)
            elif t == 1: self.put((a & 0x0FFFFFFF) + off, v & 0xFFFF, 2)
            elif t == 2: self.put((a & 0x0FFFFFFF) + off, v & 0xFF, 1)
            elif t in (5, 9):
                if (a & 0x0FFFFFFF) != 0x04000130:
                    raise SystemExit(f"condition on {a:08X}: not a key check, refused")
            elif t == 0xC: loop = (i, v)
            elif a >> 24 == 0xD0: pass
            elif a >> 24 in (0xD1, 0xD2):
                if loop and loop[1] > 0:
                    loop = (loop[0], loop[1] - 1); i = loop[0]
                elif a >> 24 == 0xD2: off = data = 0; loop = None
                else: loop = None
            elif a >> 24 == 0xD3: off = v
            elif a >> 24 == 0xD4: data = (data + v) & 0xFFFFFFFF
            elif a >> 24 == 0xD5: data = v
            elif a >> 24 == 0xD6: self.put(v + off, data, 4); off += 4
            elif a >> 24 == 0xD7: self.put(v + off, data & 0xFFFF, 2); off += 2
            elif a >> 24 == 0xD8: self.put(v + off, data & 0xFF, 1); off += 1
            elif a >> 24 == 0xDC: off += v
            else: raise SystemExit(f"code type {a:08X} not supported")
            i += 1


def main():
    if len(sys.argv) < 3:
        sys.exit(__doc__)
    inp, outp = sys.argv[1:3]
    pick = sys.argv[3] if len(sys.argv) > 3 else DEFAULT
    cheats = load(CHT)
    emu = boot(inp, rom=os.environ.get("ROM", "build/ffta2-1screen.nds"), frames=1)
    ar = AR(emu)
    for n in (int(x) for x in pick.split(",")):
        name, code = cheats[n]
        before = ar.writes
        ar.run(code)
        print(f"{n:3} {name}: {ar.writes - before} writes", file=sys.stderr)
    flags = os.environ.get("FLAGS", DEFAULT_FLAGS)
    for r in filter(None, flags.split(",") if flags != "-" else []):
        lo, hi = (int(x, 16) for x in (r.split("-") + [r])[:2])
        for bit in range(lo, hi + 1):
            a = FLAG_BASE + (bit >> 3)
            ar.put(a, emu.memory.unsigned[a] | 1 << (bit & 7), 1)
        print(f"flags {lo:#x}-{hi:#x}", file=sys.stderr)
    prog = int(os.environ.get("PROGRESS", DEFAULT_PROGRESS))
    ar.put(0x0212D714, prog, 2)
    print(f"story progress {prog}", file=sys.stderr)
    # Auction month: event variable 0xC3 (0x0212D8F7), set by the story event that
    # introduces auctions; each new day, 0x020CAC64 opens the auction houses while the
    # month (day of year at save base + 0x40, 20-day months) equals it.  The save is on
    # the 1st of Silversun (month 8), so a day's travel opens them.  AUCTION=0 for none.
    month = int(os.environ.get("AUCTION", 8))
    ar.put(0x0212D8F7, month, 1)
    print(f"auction month {month}", file=sys.stderr)
    for p in filter(None, os.environ.get("POKE", "").split(",")):
        a, v = (int(x, 16) for x in p.split("="))
        ar.put(a, v, 1)
        print(f"poke {a:08X}={v:02X}", file=sys.stderr)
    for _ in range(10): emu.cycle(False)
    emu.savestate.save_file(outp)


if __name__ == "__main__":
    main()
