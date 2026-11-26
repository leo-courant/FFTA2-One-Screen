#!/usr/bin/env python3
"""Play any story event (scene) from a DeSmuME state, and catch full-screen sprite pictures
(ticket 29).

usage: [SCRIPT=k] play_event.py STATE EVENT OUTDIR [PRESSES] [WAIT]
The game starts a scene with FUN_02093964(event, battle script). The next time it does
(from STATE: a state shortly before a scene change, e.g. states/t_intro40.dst, whose next
scene is the library, event 103, about 117 presses on), EVENT is put in its place, so the
game loads and plays that event's scripts instead. Then A is pressed PRESSES times
(default 400), WAIT frames apart (default 22). SCRIPT=k: the first script the game starts
in that event (FUN_020991D4) is replaced by script k, for scripts that normally run only
later (after a battle, say).
Every frame the sprite queue is checked, just before it is drawn, for quads exactly as
wide as the 4:3 picture and centred (what queue_widen in src/hook.c widens). The first
frame with one is saved as OUTDIR/ev<EVENT>_full.dst (EVENT -1: no swap, the story's own
order, to watch a scene where it really comes), a screenshot of both screens every
8 presses goes to OUTDIR/ev<EVENT>_pNNN.png, and a summary to stdout: the presses at which
full-width quads were seen and their texture parameters, and the effects loaded
(kind, number: kind 1 = effect/event/eNNN.efx). Env ROM as for emu.py."""
import os, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from emu import boot, rom_blob, view_settings
from desmume.controls import Keys, keymask

state, event, out = sys.argv[1], int(sys.argv[2]), sys.argv[3]
presses = int(sys.argv[4]) if len(sys.argv) > 4 else 400
wait = int(sys.argv[5]) if len(sys.argv) > 5 else 22
os.makedirs(out, exist_ok=True)
rom = os.environ.get("ROM", "build/ffta2-1screen.nds")
emu = boot(state, rom=rom, frames=0)
mem = emu.memory
m = mem.unsigned
_, view = view_settings(rom_blob(rom))
wx, nx = view["wide_x"], view["nudge_x"]
st = {"press": 0, "swapped": None, "saved": False, "seen": {}, "fx": [], "script": None}
want_script = int(os.environ["SCRIPT"]) if os.environ.get("SCRIPT") else None


def on_load(addr, size):
    r = mem.register_arm9
    if st["swapped"] is None:
        st["swapped"] = r.r0
        if event >= 0:
            r.r0 = event
    print("scene load: event %d (asked %d), battle script %d, at press %d" % (r.r0, st["swapped"], r.r1, st["press"]), file=sys.stderr)
    return True


def s32(v):
    return v - (1 << 32) if v & 0x80000000 else v


def on_draw(addr, size):
    q = m.read_long(m.read_long(0x01FFCF3C))
    a, end = m.read_long(q), m.read_long(q + 8)
    while a < end:
        if m.read_long(a) == 0x002B2A29 and m.read_long(a + 16) == 0x00401811:
            m0, m1, m4, m12 = (s32(m.read_long(a + 20 + 4 * k)) for k in (0, 1, 4, 12))
            if not m1 and not m4 and abs(m0 - 2 * wx) <= 4 and abs(m12 - nx) <= 8:
                tex = m.read_long(a + 8)
                st["seen"].setdefault(tex, []).append(st["press"])
                if not st["saved"]:
                    st["saved"] = True
                    st["pending_save"] = True
        a += 0xA0
    return True


def on_script(addr, size):
    r = mem.register_arm9
    if st["swapped"] is not None and st["script"] is None and want_script is not None:
        st["script"] = r.r0
        r.r0 = want_script
        print("script start: %d in place of %d at press %d" % (want_script, st["script"], st["press"]), file=sys.stderr)
    return True


def on_fx(addr, size):
    r = mem.register_arm9
    st["fx"].append((r.r0, r.r1, st["press"]))
    return True


mem.register_exec(0x02093964, on_load)
mem.register_exec(0x020991D4, on_script)
mem.register_exec(0x02049DAC, on_fx)
mem.register_exec(0x0208F97C, on_draw)


def cyc(n):
    for _ in range(n):
        emu.cycle(False)
        if st.pop("pending_save", False):
            emu.savestate.save_file(os.path.join(out, "ev%d_full.dst" % event))
            emu.screenshot().save(os.path.join(out, "ev%d_full.png" % event))


for i in range(1, presses + 1):
    st["press"] = i
    emu.input.keypad_add_key(keymask(Keys.KEY_A)); cyc(4)
    emu.input.keypad_rm_key(keymask(Keys.KEY_A)); cyc(wait)
    if i % 8 == 0:
        emu.screenshot().save(os.path.join(out, "ev%d_p%03d.png" % (event, i)))
print("event %d%s: effects loaded: %s" % (event, " script %d" % want_script if want_script is not None else "",
      " ".join("%d/%d@%d" % f for f in st["fx"])))
print("event %d: full-width quads:" % event)
for tex, ps in st["seen"].items():
    fmt = (tex >> 26) & 7
    print("  tex %08x %dx%d fmt %d wrap %d%d flip %d%d: presses %d..%d (%d frames)" % (
        tex, 8 << ((tex >> 20) & 7), 8 << ((tex >> 23) & 7), fmt, (tex >> 16) & 1, (tex >> 17) & 1,
        (tex >> 18) & 1, (tex >> 19) & 1, min(ps), max(ps), len(ps)))
