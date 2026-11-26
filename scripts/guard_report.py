#!/usr/bin/env python3
"""Read the guard's record (patch.py --guard, ticket 25) out of a savestate.

usage: guard_report.py STATE [SCRIPT]
  STATE  a melonDS savestate (.ml1 .. .ml8: read directly) or a DeSmuME one (.dst: played
         on ROM, env, default build/ffta2-guard.nds, with play.py steps SCRIPT, default w1)
Prints "no clash recorded" or the hits: how many, which kinds, first and last frame.
The record is guard_info in src/hook.c, after a "GURD" marker in main RAM."""
import contextlib, io, os, struct, sys
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
from emu import BLOB_ADDR

KINDS = {1: "the game wrote into the overlay texture",
         2: "the game wrote into the parked copy of bank A",
         4: "a main BG layer showed the parked copy"}


def ram_of(state, script):
    if state.endswith(".dst"):
        os.environ.setdefault("SDL_VIDEODRIVER", "dummy")
        from emu import boot
        from desmume.controls import Keys, keymask
        with contextlib.redirect_stdout(io.StringIO()):
            emu = boot(state, rom=os.environ.get("ROM", "build/ffta2-guard.nds"), frames=1)
        keys = {k: keymask(getattr(Keys, "KEY_" + k)) for k in "A B X Y L R START SELECT UP DOWN LEFT RIGHT".split()}
        for step in script.split(","):
            n = step.rstrip("0123456789")
            k = int(step[len(n):] or 4)
            if n == "w":
                for _ in range(k): emu.cycle(False)
            elif n in keys:
                emu.input.keypad_add_key(keys[n])
                for _ in range(k): emu.cycle(False)
                emu.input.keypad_rm_key(keys[n])
                for _ in range(4): emu.cycle(False)
        return bytes(emu.memory.unsigned[BLOB_ADDR:BLOB_ADDR + 0x10000])
    d = open(state, "rb").read()
    if d[:4] != b"MELN":
        sys.exit("%s: not a melonDS or DeSmuME savestate" % state)
    at = 0x24 + BLOB_ADDR - 0x02000000
    return d[at:at + 0x10000]


def main():
    if len(sys.argv) < 2:
        sys.exit(__doc__)
    ram = ram_of(sys.argv[1], sys.argv[2] if len(sys.argv) > 2 else "w1")
    # the marker's value also sits in the code as a constant: take the copy followed by
    # a plausible record (hits > 0, kinds 1..7, first frame <= last frame)
    rec = None
    for i in range(0, len(ram) - 20, 4):     # code and variables (ADR 0017)
        if ram[i:i + 4] == b"GURD":
            h, k, f, l = struct.unpack_from("<4I", ram, i + 4)
            if h and 1 <= k <= 7 and f <= l:
                rec = i
    if rec is None:
        print("no clash recorded", file=sys.stderr)
        return
    i = rec
    hits, kinds, first, last = struct.unpack_from("<4I", ram, i + 4)
    print("%d clash checks failed, frames %d..%d:" % (hits, first, last), file=sys.stderr)
    for bit, text in KINDS.items():
        if kinds & bit:
            print("  - " + text, file=sys.stderr)


if __name__ == "__main__":
    main()
