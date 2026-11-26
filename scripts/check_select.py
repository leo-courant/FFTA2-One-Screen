#!/usr/bin/env python3
"""Check the SELECT controls (ticket 19, ADR 0006) on the current build.

usage: check_select.py STATE CASE [SHOTDIR]     (one DeSmuME per process: run once per case)
  CASE basic  taps and holds of SELECT, incl. a 25-frame hold that must count as a tap
       peek   overlay opened by a tap stays through D-pad presses, B and A close it
       combo  L/R/A/DOWN held with SELECT: neither the tap nor the hold may fire
       reset  L+R+START+SELECT for 1 s: the game must reset (SHOTDIR gets before/afterNs.png)
Writes banner / overlay / screen-swap after each step to stderr (DeSmuME eats stdout); variables are found with nm build/hook.elf, so ROM (env, default build/ffta2-1screen.nds) must be the last build.
"""
import sys, os, subprocess
sys.path.insert(0, "scripts")
from emu import boot, rom_blob
from desmume.controls import Keys, keymask
st, case = sys.argv[1:3]; shots = sys.argv[3] if len(sys.argv) > 3 else None
sym = {l.split()[2]: int(l.split()[0], 16) for l in subprocess.run(["nm", "build/hook.elf"], capture_output=True, text=True).stdout.splitlines() if len(l.split()) == 3}
rom = os.environ.get("ROM", "build/ffta2-1screen.nds")
# the symbols are those of the last build: refuse a ROM built from different code or settings
if rom_blob(rom).rstrip(b"\0") != open("build/hook.bin", "rb").read().rstrip(b"\0"):
    sys.exit("build/hook.elf is not the code inside %s: rebuild that ROM last" % rom)
emu = boot(st, rom=rom, frames=10)
r8 = lambda n: emu.memory.unsigned.read_byte(sym[n])
K = {k: keymask(getattr(Keys, "KEY_" + k)) for k in "A B X Y L R START SELECT UP DOWN LEFT RIGHT".split()}
log = []
def state(tag):
    log.append(f"{tag:24s} banner={r8('banner_enabled')} overlay={r8('ov_manual')} swap={emu.memory.unsigned.read_short(0x04000304) >> 15}")
def run(n):
    for _ in range(n): emu.cycle(False)
def hold(keys, n, tag=None, mid=None):
    for k in keys: emu.input.keypad_add_key(K[k])
    if mid: run(mid); state(tag + " (held %d)" % mid); run(n - mid)
    else: run(n)
    for k in keys: emu.input.keypad_rm_key(K[k])
    run(6)
    if tag: state(tag)
state("start")
if case == "basic":
    hold(["SELECT"], 6, "tap", mid=3)
    hold(["SELECT"], 6, "tap again")
    hold(["SELECT"], 40, "hold 40", mid=29)
    state("after hold (29 + 11)")
    hold(["SELECT"], 40, "hold 40 again")
    hold(["SELECT"], 25, "hold 25 (a tap)")
    hold(["SELECT"], 25, "hold 25 again")
elif case == "peek":
    hold(["SELECT"], 6, "tap")
    hold(["DOWN"], 6, "DOWN")
    hold(["RIGHT"], 6, "RIGHT")
    hold(["B"], 6, "B")
    hold(["SELECT"], 6, "tap")
    hold(["A"], 6, "A")
elif case == "combo":
    # each other key held with SELECT: neither tap nor hold
    for k in ["L", "R", "A", "DOWN"]:
        hold([k, "SELECT"], 6, k + "+SELECT tap")
        hold([k, "SELECT"], 40, k + "+SELECT hold")
elif case == "reset":
    if shots: emu.screenshot().save(f"{shots}/before.png")
    for k in ["L", "R", "START"]: emu.input.keypad_add_key(K[k])
    run(2); emu.input.keypad_add_key(K["SELECT"]); run(60); state("L+R+START+SELECT held 60")
    for k in K: emu.input.keypad_rm_key(K[k])
    run(6); state("released")
    for i in range(1, 7):
        run(60)
        if shots: emu.screenshot().save(f"{shots}/after{i}s.png")
    state("6 s later")
sys.stderr.write(f"== {st} {case}\n" + "\n".join(log) + "\n")   # DeSmuME swallows stdout
