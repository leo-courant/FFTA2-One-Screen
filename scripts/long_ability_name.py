#!/usr/bin/env python3
"""Ticket 22: put one ability name from the game's table into the ability list and save
the gameplay screen (original 4:3 picture), to measure how wide the game draws it.
usage: long_ability_name.py INDEX OUT.png     (index into the name table; 247 = "Thunder
Flare Tome", the widest found, 87 px).  The name replaces Potion and Phoenix Down in Luso's
Items list in states/s_battle2.dst; neighbouring names in memory are overwritten, which only
matters for this test picture."""
import os, sys
sys.path.insert(0, "scripts")
from emu import boot, rom_blob, view_settings
from desmume.controls import Keys, keymask
idx = int(sys.argv[1]); out = sys.argv[2]
d = open('rom/ffta2.nds','rb').read()
names = d[0x2a978ac:0x2a995cd].split(b'\0')
name = names[idx]
emu = boot("states/s_battle2.dst", rom="build/ffta2-1screen.nds", frames=1)
blob = open(os.environ["BLOB"], "rb").read() if os.environ.get("BLOB") else rom_blob("build/ffta2-1screen.nds")
at, _ = view_settings(blob)      # widescreen off: screen_w, screen_h, wide_x, wide_y, nudge_x, nudge_y
for i, v in enumerate((256, 192, 4096, 4096, 0, 0)): emu.memory.write_long(0x02143E20 + at + 4 * i, v)
m = emu.memory.unsigned
for base in (0x231a072, 0x231a099):      # Potion (left column), Phoenix Down (right column)
    for i, b in enumerate(name + b'\0'): m[base + i] = b
KEYS = {k: getattr(Keys, "KEY_" + k) for k in "A B X Y UP DOWN".split()}
def cyc(n):
    for _ in range(n): emu.cycle(False)
for step in "w10,B,w40,B,w40,B,w40,UP,w15,Y,w90,DOWN,w15,A,w120,DOWN,w40,A,w120".split(","):
    if step[0] == "w": cyc(int(step[1:]))
    else:
        emu.input.keypad_add_key(keymask(KEYS[step])); cyc(4); emu.input.keypad_rm_key(keymask(KEYS[step])); cyc(4)
emu.screenshot().crop((0,192,256,384)).save(out)
