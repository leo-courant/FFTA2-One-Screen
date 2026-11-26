#!/usr/bin/env python3
"""Headless DeSmuME driver.

usage: run.py ROM OUTDIR SCRIPT [--load STATE] [--save STATE]

SCRIPT is a comma list of steps:
  w<N>        wait N frames
  <key><N>    hold key for N frames (default 4) then release and wait 4;
              keys: A B X Y L R START SELECT UP DOWN LEFT RIGHT
  t<x>:<y>    tap touch screen at x,y for 4 frames
  s<name>     screenshot to OUTDIR/<name>.png
"""
import os
import sys
from desmume.emulator import DeSmuME
from desmume.controls import Keys, keymask

args = sys.argv[1:]
load = save = None
if "--load" in args:
    i = args.index("--load"); load = args[i + 1]; del args[i:i + 2]
if "--save" in args:
    i = args.index("--save"); save = args[i + 1]; del args[i:i + 2]
rom, out, script = args[0], args[1], args[2]
os.makedirs(out, exist_ok=True)

emu = DeSmuME()
emu.open(rom)
emu.volume_set(0)
if load:
    emu.savestate.load_file(load)
    # A savestate restores RAM, including the original code; re-apply any
    # ARM9 differences between this ROM and the unmodified reference ROM.
    ref = os.environ.get("REF_ROM")
    if ref and os.path.realpath(ref) != os.path.realpath(rom):
        a = open(rom, "rb").read()[0x4000:0x4000 + 0x121678]
        b = open(ref, "rb").read()[0x4000:0x4000 + 0x121678]
        n = 0
        for i in range(len(a)):
            if a[i] != b[i]:
                emu.memory.unsigned[0x02000000 + i] = a[i]
                n += 1
        print("re-applied", n, "patched bytes")

KEYS = {k: getattr(Keys, "KEY_" + k) for k in
        "A B X Y L R START SELECT UP DOWN LEFT RIGHT".split()}
frame = 0


def cycle(n=1):
    global frame
    for _ in range(n):
        emu.cycle(False)
        frame += 1


for step in script.split(","):
    step = step.strip()
    if not step:
        continue
    if step[0] == "w" and step[1:].isdigit():
        cycle(int(step[1:]))
    elif step[0] == "s":
        emu.screenshot().save(os.path.join(out, step[1:] + ".png"))
    elif step[0] == "t" and ":" in step:
        x, y = step[1:].split(":")
        emu.input.touch_set_pos(int(x), int(y))
        cycle(4)
        emu.input.touch_release()
        cycle(4)
    else:
        name = step.rstrip("0123456789")
        n = int(step[len(name):] or 4)
        emu.input.keypad_add_key(keymask(KEYS[name]))
        cycle(n)
        emu.input.keypad_rm_key(keymask(KEYS[name]))
        cycle(4)
if save:
    emu.savestate.save_file(save)
print("frames", frame, "POWCNT1=%04x" % emu.memory.unsigned.read_short(0x04000304))
