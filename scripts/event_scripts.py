#!/usr/bin/env python3
"""Walk the game's event scripts (story scenes) and list commands, ticket 29.

usage: event_scripts.py [--op HEX] [--stats]
  --op 38   every "play effect" command: scene block, script, kind, effect number, last byte
The scripts live in ev_all.pak (folder event/rom), one block per event number, indexed by
ev_all_rom.idx in the same folder (u32 count, then 6-byte records: offset/4 in bits 3..26, packing in
bits 0..2; a block runs to the next record's offset). The game loads event N with
FUN_02093964 (N, battle script) and starts script k of it with FUN_020991D4. A block is: four u32 offsets
(the last one, h3, points to its script table), a table at +h3 of u32 offsets (relative
to the table) to each script, the scripts back to back. A script is a list of commands:
u16 opcode, then a fixed length per opcode from the game's table at 0x0211A33C
({length, handler} pairs, 185 opcodes; interpreter FUN_0209C888). Scene blocks are
told apart by the index; the script table runs until the lowest offset.

usage as a module: events() -> {event: (start, end)} in pack(); scripts(d, s, e); walk(...)."""
import os, struct, sys
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
ROOT = os.path.join(HERE, "..")
import pcbin
EVENTS = "event/rom/"     # the folder; file names are joined on so no full game path is quoted


def op_lengths():
    b = open(os.path.join(ROOT, "work", "arm9_0x02000800.bin"), "rb").read()
    return [struct.unpack_from("<I", b, 0x0211A33C + 8 * i - 0x02000800)[0] for i in range(185)]


def pack():
    return pcbin.read(EVENTS + "ev_all.pak")


def events():
    """{event number: (start, end)} of each non-empty block in pack()"""
    d = pcbin.read(EVENTS + "ev_all_rom.idx")
    n = (len(d) - 4) // 6
    offs = [((int.from_bytes(d[4 + 6 * i:10 + 6 * i], "little") & 0x7FFFFFF) >> 3) * 4 for i in range(n)]
    end = len(pack())
    out = {}
    for i, o in enumerate(offs):
        nxt = next((x for x in offs[i + 1:] if x > o), end)
        if o < end and nxt > o and (i + 1 == n or offs[i + 1] != o):
            out[i] = (o, nxt)
    return out


def scripts(d, s, e):
    if e - s < 16:
        return []
    h3 = struct.unpack_from("<I", d, s + 12)[0]
    if not 16 <= h3 < e - s:
        return []
    t = s + h3
    offs = []
    lo = None
    k = 0
    while lo is None or k * 4 < lo:
        o = struct.unpack_from("<I", d, t + 4 * k)[0]
        if not (0 < o < e - t):
            break
        offs.append(o)
        lo = o if lo is None else min(lo, o)
        k += 1
    starts = sorted(set(offs))
    ends = {a: b for a, b in zip(starts, starts[1:] + [e - t])}
    return [(t + o, t + ends[o]) for o in offs]


def walk(d, a, b, L):
    p = a
    while p + 2 <= b:
        op = d[p] | d[p + 1] << 8
        if op >= len(L):
            yield p, None, d[p:p + 2]
            return
        yield p, op, d[p:p + L[op]]
        p += L[op]


if __name__ == "__main__":
    L = op_lengths()
    d = pack()
    want = int(sys.argv[sys.argv.index("--op") + 1], 16) if "--op" in sys.argv else None
    bad = total = nscr = 0
    ev = events()
    for si, (s, e) in sorted(ev.items()):
        for ci, (a, b) in enumerate(scripts(d, s, e)):
            nscr += 1
            for p, op, raw in walk(d, a, b, L):
                total += 1
                if op is None:
                    bad += 1
                elif op == want:
                    print("event %d\tscript %d\t@%06x\t%s" % (si, ci, p, raw.hex(" ")))
    if "--stats" in sys.argv:
        print("events %d scripts %d commands %d bad stops %d" % (len(ev), nscr, total, bad), file=sys.stderr)
