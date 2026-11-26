#!/usr/bin/env python3
"""A melonDS capture of a known moment, on any build: load a melonDS savestate, press keys, capture.

usage: melon_state.py STATE.ml1 OUT.png [step ...]      (from the VS Code flatpak; ~20 s)
Env: ROM (default build/ffta2-1screen.nds), SIZE (display, default 1280x800),
     SAVE=path.ml1 (also save a new state after the steps: the way to make a state
     further on), STATE_ROM (the build the state was made on, as for emu.py; only
     matters when hooks were removed since), FPS=60 (run melonDS at that speed for
     this capture instead of the test config's 240; needed whenever SELECT is pressed:
     at 4x speed the rig's key press lasts about 30 game frames, the tap/hold limit),
     SCION=K (ticket 26: from states/m_battle2.ml1, the Cure spell's ability record
     becomes Scion K's, as in scripts/play_scion.py).
     POKE=addr=val[,...] (16-bit values in hex written into main RAM before the state runs,
     as p steps in play.py; 0212D7F6=810 wins the battle at its next check, ticket 40).
Steps: see scripts/melon_state_run.sh (x:1.5 = press A, wait 1.5 s; s:name = extra capture).

A melonDS savestate holds main RAM, and with it the mod's code of the build that
made it.  As emu.py does for DeSmuME states, the state is first brought up to the
build in ROM: the mod's blob is written at BLOB_ADDR and every ARM9 word the build
patches is re-applied.  States therefore stay usable across builds; they must be
remade when BLOB_RESERVE changes (the heap moves), like the DeSmuME ones.
Base states live in states/m_*.ml1 (docs/test-saves.md).  Uses the shared melonDS
rig: refuses to run while any melonDS runs."""
import os, shlex, shutil, struct, subprocess, sys, time
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
from emu import BLOB_ADDR, rom_blob, rom_bss

ARM9_SIZE = 0x121660        # the static ARM9 binary, 0x02000000.. (as in emu.py)
HEAP_LITERAL = 0x7F44       # keep the state's heap start


def inject(state, rom, state_rom):
    d = bytearray(open(state, "rb").read())
    if d[:4] != b"MELN" or d[0x10:0x14] != b"NDSG":
        sys.exit("%s: not a melonDS savestate of the expected layout" % state)
    ram = 0x24                                  # NDSG section data + 4: main RAM, 0x02000000..
    blob = rom_blob(rom)
    if blob is None:
        sys.exit("%s has no mod blob" % rom)
    at = ram + BLOB_ADDR - 0x02000000
    d[at:at + len(blob)] = blob
    b_at, b_n = rom_bss(rom)                    # and its variables start at zero (ADR 0017)
    d[ram + b_at - 0x02000000:ram + b_at - 0x02000000 + b_n] = bytes(b_n)
    new = open(rom, "rb").read()[0x4000:0x4000 + ARM9_SIZE]
    old = open(os.path.join(HERE, "..", "rom", "ffta2.nds"), "rb").read()[0x4000:0x4000 + ARM9_SIZE]
    mod = open(state_rom, "rb").read()[0x4000:0x4000 + ARM9_SIZE]
    for i in range(0, ARM9_SIZE, 4):
        if (new[i:i + 4] != old[i:i + 4] or mod[i:i + 4] != old[i:i + 4]) and i != HEAP_LITERAL:
            d[ram + i:ram + i + 4] = new[i:i + 4]
    for poke in filter(None, os.environ.get("POKE", "").split(",")):
        a, v = poke.split("=")
        struct.pack_into("<H", d, ram + int(a, 16) - 0x02000000, int(v, 16))
    if os.environ.get("SCION"):
        # ability records: sysdata file 5, 0x18 bytes each; 0x37 = Cure, 0x289.. = the Scions
        table = struct.unpack_from("<I", d, ram + 0x00131458 + 8 * 5)[0] - 0x02000000
        src = ram + table + (0x289 + int(os.environ["SCION"])) * 0x18
        dst = ram + table + 0x37 * 0x18
        d[dst:dst + 0x18] = d[src:src + 0x18]
    return d


def main():
    if len(sys.argv) < 3:
        sys.exit(__doc__)
    state, out, steps = sys.argv[1], os.path.abspath(sys.argv[2]), sys.argv[3:]
    if os.environ.get("SAVE") and "save" not in steps:
        steps.append("save")
    root = os.path.abspath(os.path.join(HERE, ".."))
    rom = os.path.abspath(os.environ.get("ROM", os.path.join(root, "build/ffta2-1screen.nds")))
    state_rom = os.environ.get("STATE_ROM", os.path.join(root, "build/ffta2-1screen.nds"))
    w, h = os.environ.get("SIZE", "1280x800").split("x")
    host = lambda cmd: subprocess.run(["flatpak-spawn", "--host", "sh", "-c", cmd], cwd=os.path.expanduser("~"),
                                      capture_output=True, text=True)
    if host("pgrep -x melonDS").stdout.strip():
        sys.exit("melonDS is already running (another rig?); not starting a second one")
    base = os.path.join(root, "build", "mstate")
    for ext in (".nds", ".ml1", ".ml2", ".sav"):
        if os.path.exists(base + ext):
            os.remove(base + ext)
    os.link(rom, base + ".nds")
    open(base + ".ml1", "wb").write(inject(state, rom, state_rom))
    os.makedirs(os.path.dirname(out), exist_ok=True)
    if os.path.exists(out):
        os.remove(out)
    waits = sum(float(s.split(":")[-1]) if ":" in s and not s.startswith("s:") else 1 for s in steps)
    run = " ".join(shlex.quote(a) for a in [os.path.join(HERE, "melon_state_run.sh"), base + ".nds", out] + steps)
    t = time.time()
    fps = os.environ.get("FPS")
    # FPS: melonDS reads its speed from its real config on this PC; set it for this
    # run and put the previous line back afterwards (as melon_battle2.sh does)
    pre = post = ""
    if fps:
        float(fps)
        conf = "~/.var/app/net.kuribo64.melonDS/config/melonDS/melonDS.toml"
        pre = "C=%s; O=$(grep '^TargetFPS = ' $C); sed -i 's/^TargetFPS = .*/TargetFPS = %s/' $C; " % (conf, fps)
        post = "; sed -i \"s/^TargetFPS = .*/$O/\" $C"
    host("cd ~; %stimeout %d gamescope --backend headless -W %s -H %s -w %s -h %s -f -- %s >/dev/null 2>&1; "
         "pkill -x gamescope; pkill -KILL -x melonDS%s" % (pre, 60 + 2 * waits, w, h, w, h, run, post))
    if os.environ.get("SAVE"):
        if not os.path.exists(base + ".ml2"):
            sys.exit("no state was saved")
        shutil.copy(base + ".ml2", os.environ["SAVE"])
        print("saved", os.environ["SAVE"])
    for ext in (".ml1", ".ml2", ".sav", ".nds"):
        if os.path.exists(base + ext):
            os.remove(base + ext)
    if not os.path.exists(out):
        sys.exit("no capture (see %s.log)" % out[:-4])
    print("%s (%.0f s)" % (out, time.time() - t))


main()
