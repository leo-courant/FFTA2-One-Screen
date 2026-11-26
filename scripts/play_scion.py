#!/usr/bin/env python3
"""Play any of the 13 Scion animations in battle from a DeSmuME state (ticket 26).

usage: play_scion.py K OUTDIR [EVERY [FRAMES]]
K: 0..12 = Belias, Mateus, Shemhazai, Hashmal, Famfrit, Adrammelech, Cuchulainn, Zalera,
Chaos, Zeromus, Exodus, Ultima, Zodiark (effect ids 0x152 + K, abilities 0x289 + K).
From states/s_battle2.dst (the white mage's command menu) Cure is cast on the caster, and
every ability record the game looks up from the confirmation on is the Scion's instead
(FUN_020cb14c): the damage and the targets are Cure's, the animation is the Scion's own.
Saves both screens to OUTDIR/<K>_<frame>.png every EVERY frames (default 30), counted from
the first frame of the two-screen mode (dual3d_state +0x18; EVERY may also be a list, 200,260), and prints when the mode and
its capture start and stop. SAVE=N:FILE saves a state N frames into the mode.
Env ROM, STATE as usual (ROM=build/ffta2-ref.nds shows the unmodified picture)."""
import os, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from emu import boot, rom_blob, BLOB_ADDR
from desmume.controls import Keys, keymask
NAMES = "belias mateus shemhazai hashmal famfrit adrammelech cuchulainn zalera chaos zeromus exodus ultima zodiark".split()
CAST = [(Keys.KEY_DOWN, 10), (Keys.KEY_A, 30), (Keys.KEY_DOWN, 10), (Keys.KEY_A, 30),
        (Keys.KEY_A, 30), (Keys.KEY_A, 40), (Keys.KEY_A, 90), (Keys.KEY_A, 0)]


def log(*a):
    print(*a, file=sys.stderr, flush=True)


def start(k, state=None, rom=None):
    """Boot and cast; returns the emulator a few frames after the confirmation."""
    emu = boot(state or os.environ.get("STATE", "states/s_battle2.dst"),
               rom=rom or os.environ.get("ROM", "build/ffta2-1screen.nds"), frames=1)
    if os.environ.get("TILE"):      # one unsqueezed piece of the view (solo_scion.py), as in play.py
        at = rom_blob(rom or os.environ.get("ROM", "build/ffta2-1screen.nds")).index(b"TILE")
        for i, v in enumerate([1] + [int(v) & 0xFFFFFFFF for v in os.environ["TILE"].split(",")]):
            emu.memory.write_long(BLOB_ADDR + at + 4 + 4 * i, v)
    armed = []

    def on_ability(addr, size):
        if armed:
            emu.memory.register_arm9.r0 = 0x289 + k
        return True
    emu.memory.register_exec(0x020CB14C, on_ability)
    for i, (key, wait) in enumerate(CAST):
        if i == len(CAST) - 1:
            armed.append(1)
        emu.input.keypad_add_key(keymask(key))
        for _ in range(4): emu.cycle(False)
        emu.input.keypad_rm_key(keymask(key))
        for _ in range(4 + wait): emu.cycle(False)
    return emu


DUAL = 0x02131BB8
if __name__ == "__main__":
    k, out = int(sys.argv[1]), sys.argv[2]
    every = sys.argv[3] if len(sys.argv) > 3 else "30"
    wanted = (lambda n: n in {int(v) for v in every.split(",")}) if "," in every else (lambda n: n % int(every) == 0)
    frames = int(sys.argv[4]) if len(sys.argv) > 4 else 2400
    os.makedirs(out, exist_ok=True)
    emu = start(k)
    m = emu.memory.unsigned
    save = os.environ.get("SAVE", "").split(":")
    n, on, cap, variants = None, 0, 0, set()
    for f in range(frames):
        emu.cycle(False)
        o, c = m.read_long(DUAL + 0x18), m.read_long(DUAL + 4)
        if o and n is None:
            n = 0
        if o != on: log("%s: frame %s (cast +%d): mode %d" % (NAMES[k], n, f, o)); on = o
        if c != cap: log("%s: frame %s: capture %d" % (NAMES[k], n, c)); cap = c
        if o and m.read_long(DUAL + 0x10): variants.add(m.read_long(DUAL + 0x10))
        if n is not None:
            if wanted(n): emu.screenshot().save(os.path.join(out, "%d_%04d.png" % (k, n)))
            if save[0] and n == int(save[0]): emu.savestate.save_file(save[1])
            n += 1
            if not o and n > 120:
                for _ in range(60): emu.cycle(False)
                emu.screenshot().save(os.path.join(out, "%d_after.png" % k))
                break
    log("%s: OBJ priority variants seen: %s" % (NAMES[k], sorted(variants)))
