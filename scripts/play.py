#!/usr/bin/env python3
"""Step-wise play on the current build, chaining savestates.

usage: play.py IN_STATE OUT_STATE SCRIPT [SHOTDIR]
  IN_STATE "-" boots the ROM cold. OUT_STATE "-" saves nothing.
Env: ROM (default build/ffta2-1screen.nds), BLOB (hook code re-injected after loading
so old states run the current mod code; default: the blob inside ROM), PLAIN=1 (widescreen off), TILE=ox,oy (one piece of the wide view; used by solo.py), DUMP=dir (main RAM
saved as dir/<name>.bin at every screenshot step), QUEST=N[:S] (the next quest battle is
quest N's, see below).
SCRIPT steps (comma separated), as run.py plus:
  w<N>  wait            <KEY><N>  hold key N frames (default 4), release, wait 4
  s<name>  screenshot of both screens to SHOTDIR/<name>.png
  p<addr>=<val>  write a 16-bit value (hex) to memory
  e<file>  export the cartridge save (raw .sav, usable in melonDS) to <file>
  i<file>  import a raw .sav as the cartridge save and reset (use first, on a cold boot)
  <step>*<N>  repeat a step N times, e.g. A4*20 (each followed by w20)
"""
import os, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from emu import boot, rom_blob, view_settings, save_clean
from desmume.controls import Keys, keymask
inp, outp, script = sys.argv[1:4]
shots = sys.argv[4] if len(sys.argv) > 4 else "shots/t03"
os.makedirs(shots, exist_ok=True)
rom = os.environ.get("ROM", "build/ffta2-1screen.nds")
emu = boot(None if inp == "-" else inp, rom=rom, frames=1)
blob = open(os.environ["BLOB"], "rb").read() if os.environ.get("BLOB") else rom_blob(rom)
if os.environ.get("PLAIN"):
    # PLAIN=1: widescreen off for this run (the original 4:3 picture, which is what a
    # DS-resolution screenshot can show cleanly).
    at, _ = view_settings(blob)
    for i, v in enumerate((256, 192, 4096, 4096, 0, 0)):
        emu.memory.write_long(0x02143E20 + at + 4 * i, v)
KEYS = {k: getattr(Keys, "KEY_" + k) for k in "A B X Y L R START SELECT UP DOWN LEFT RIGHT".split()}
def cyc(n):
    for _ in range(n): emu.cycle(False)
def do(step):
    if step[0] == "w" and step[1:].isdigit(): cyc(int(step[1:]))
    elif step[0] == "s":
        emu.screenshot().save(os.path.join(shots, step[1:] + ".png"))
        if os.environ.get("DUMP"):   # DUMP=dir: main RAM at each screenshot, for memory diffs
            open(os.path.join(os.environ["DUMP"], step[1:] + ".bin"), "wb").write(bytes(emu.memory.unsigned[0x02000000:0x02400000]))
    elif step[0] == "e": print("export", step[1:], emu.backup.export_file(step[1:]))
    elif step[0] == "i": print("import", step[1:], emu.backup.import_file(step[1:], 0x10000)); emu.reset()
    elif step[0] == "p":
        a, v = step[1:].split("="); emu.memory.write_short(int(a, 16), int(v, 16))
    else:
        name = step.rstrip("0123456789"); n = int(step[len(name):] or 4)
        emu.input.keypad_add_key(keymask(KEYS[name])); cyc(n)
        emu.input.keypad_rm_key(keymask(KEYS[name])); cyc(4)
if os.environ.get("TILE"):
    # TILE=ox,oy: draw one unsqueezed piece of the widescreen view (see tile_cfg in
    # src/hook.c and scripts/solo.py, which runs the four pieces and stitches them)
    at = blob.index(b"TILE")
    ox, oy = (int(v) for v in os.environ["TILE"].split(","))
    for i, v in enumerate((1, ox & 0xFFFFFFFF, oy & 0xFFFFFFFF)):
        emu.memory.write_long(0x02143E20 + at + 4 + 4 * i, v)
if os.environ.get("SCENE") is not None:
    # SCENE=EVENT[:SCRIPT][@N] (ticket 24): the Nth scene load from here (event_load
    # 0x02093964, default the first) gets this event and battle script instead (empty or -1
    # keeps the game's). Every scene load is logged to stderr (SCENE= alone only logs).
    spec, _, nth = os.environ["SCENE"].partition("@")
    want = [int(v) if v not in ("", "-1") else None for v in (spec + ":").split(":")[:2]]
    nth = int(nth or 1)
    loads = []
    def on_load(addr, size):
        r = emu.memory.register_arm9
        asked = (r.r0, r.r1)
        if len(loads) == nth - 1:
            if want[0] is not None: r.r0 = want[0]
            if want[1] is not None: r.r1 = want[1]
        loads.append(asked)
        print("scene load: event %d script %d (asked %d %d)" % (r.r0, r.r1, *asked), file=sys.stderr)
        return True
    emu.memory.register_exec(0x02093964, on_load)
if os.environ.get("QUEST"):
    # QUEST=N (ticket 38): the quest battle set up next is quest N's. 0x02093A8C(quest, scene
    # row, record) starts every quest battle (files 10 and 11 of sysdata: FUN_020CB248 and
    # quest_record), so all three arguments are replaced and the battlefield, scene, battle
    # script and unit set all become quest N's.
    # QUEST=N:S: and the first scene script queued (evcmd 0x22, FUN_020D3A80) is S; a chained
    # quest's dispatcher queues its after-battle talk, not the battle (18: QUEST=18:0).
    qn, _, first = os.environ["QUEST"].partition(":")
    qn, done, queued = int(qn), [], []
    def on_queue(addr, size):
        r = emu.memory.register_arm9
        if done and first and not queued:
            queued.append(r.r0)
            r.r0 = int(first)
        return True
    if first: emu.memory.register_exec(0x020D3A80, on_queue)
    def on_quest(addr, size):
        r = emu.memory.register_arm9
        if not done and r.r0 not in (0, 0xFFFFFFFF, qn):
            done.append(r.r0)
            tab = emu.memory.unsigned.read_long
            base = lambda n: tab(tab(0x020CAEF8) + n * 8)
            print("battle quest: %d instead of %d" % (qn, r.r0), file=sys.stderr)
            r.r0, r.r1, r.r2 = qn, base(10) + 8 * qn, base(11) + 100 * qn
        return True
    emu.memory.register_exec(0x02093A8C, on_quest)
for step in script.split(","):
    step = step.strip()
    if not step: continue
    if "*" in step:
        s, n = step.split("*")
        for _ in range(int(n)): do(s); cyc(20)
    else: do(step)
if outp != "-":
    if save_clean(emu, outp) is None: print("note: %s was saved inside the mod's code; it may not run on later builds" % outp, file=sys.stderr)
