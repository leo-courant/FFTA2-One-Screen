#!/usr/bin/env python3
"""Ticket 23: a battle-2 savestate whose info screen shows the longest objective, law and
privilege the game has, each drawn by the game itself, so the banner can be checked with them.

usage: longest_texts.py OUT_STATE [OBJ LAW PRIV]
  (from the repo root; ~30 s; needs states/s_worldmap.dst and states/s_battle2.dst)
Texts default to the longest of each kind measured in ticket 07
(work/text-widths.tsv: game text, so kept out of git).
Then e.g.: scripts/solo.py OUT_STATE w10,slong OUTDIR

How: battle 2's objective is drawn onto the info screen (text layer BG1, rows 0-1) on the
9th press of the scene after travelling there; its string sits at 0x021CF1D8 until then.
For each text, the route is replayed with that string swapped (as ticket 07 measured
widths), and the drawn cells are read back.  Then, in s_battle2, the three are written
into the objective, law and privilege rows, in fresh tiles, each recoloured to the colour
group the row already uses (law red, privilege teal)."""
import os, subprocess, sys, tempfile
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)

OBJ_STR = 0x021CF1D8
ROUTE_TO_SCENE = ("DOWN12,w60,DOWN12,w60,LEFT12,w60,LEFT12,w60,UP12,w60,RIGHT12,w60,A12,w150"
                  + ",A,w70,A,w90" * 14)          # scripts/to_saves.sh, battle 2, first segment
ROWS = {"obj": 0, "law": 3, "priv": 6}           # the info screen's text rows (two rows each)
FREE_TILE = 0x280                                # BG1 tiles from here on are unused in battle


def enc(text):
    """the game's 1-byte text encoding; {xx} inserts a raw byte"""
    out, i = bytearray(), 0
    while i < len(text):
        ch = text[i]
        if ch == "{":
            out.append(int(text[i + 1:i + 3], 16)); i += 4; continue
        if ch == " ": out.append(1)
        elif "A" <= ch <= "Z": out.append(2 + ord(ch) - 65)
        elif "a" <= ch <= "z": out.append(0x1C + ord(ch) - 97)
        elif "0" <= ch <= "9": out.append(0x67 + ord(ch) - 48)
        elif ch == "!": out.append(0x73)
        elif ch == "-": out.append(0x8D)
        else: raise ValueError(ch)
        i += 1
    return bytes(out) + b"\xc2\x00\xc1"


def boot_quiet(state):
    import contextlib, io
    with contextlib.redirect_stdout(io.StringIO()):
        from emu import boot
        return boot(state, rom=os.environ.get("ROM", "build/ffta2-1screen.nds"), frames=1)


def bg1(m):
    cnt = m.read_short(0x0400100A)
    return 0x06200000 + ((cnt >> 2) & 15) * 0x4000, 0x06200000 + ((cnt >> 8) & 31) * 0x800


def draw_one(scene_state, text, out):
    """child process: let the game draw `text` as the objective; write its cells to `out`"""
    from desmume.controls import Keys, keymask
    emu = boot_quiet(scene_state)
    m = emu.memory.unsigned
    def press():
        emu.input.keypad_add_key(keymask(Keys.KEY_A))
        for _ in range(4): emu.cycle(False)
        emu.input.keypad_rm_key(keymask(Keys.KEY_A))
        for _ in range(4): emu.cycle(False)
    for i in range(9):                  # drawn on the 9th press; swapped from the 5th on to be safe
        if i >= 4:
            for j, b in enumerate(enc(text)):
                emu.memory.write_byte(OBJ_STR + j, b)
        press()
        for _ in range(70 if i % 2 == 0 else 90): emu.cycle(False)
    char, smap = bg1(m)
    cells = []
    for c in range(32):
        e = [m.read_short(smap + (r * 32 + c) * 2) for r in (0, 1)]
        if any(x & 0x3FF for x in e):
            cells.append((c, [bytes(m[char + (x & 0x3FF) * 32:char + (x & 0x3FF) * 32 + 32]) for x in e]))
    with open(out, "wb") as f:
        import pickle; pickle.dump(cells, f)


def main():
    out_state = sys.argv[1]
    import csv
    rows = list(csv.reader(open(os.path.join(HERE, "..", "work", "text-widths.tsv")), delimiter="\t"))
    longest = {}
    for kind, w, t in rows:
        if int(w) > longest.get(kind, (0, ""))[0]:
            longest[kind] = (int(w), t)
    texts = sys.argv[2:5] if len(sys.argv) >= 5 else [longest[k][1] for k in ("obj", "law", "priv")]
    tmp = tempfile.mkdtemp()
    scene = os.path.join(tmp, "scene.dst")
    subprocess.check_call([sys.executable, os.path.join(HERE, "play.py"), "states/s_worldmap.dst", scene, ROUTE_TO_SCENE, tmp],
                          stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    procs = [subprocess.Popen([sys.executable, __file__, "--draw", scene, t, os.path.join(tmp, "%d.pkl" % i)],
                              stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL) for i, t in enumerate(texts)]
    if any(p.wait() for p in procs):
        sys.exit("a drawing run failed")
    import pickle
    drawn = [pickle.load(open(os.path.join(tmp, "%d.pkl" % i), "rb")) for i in range(3)]

    emu = boot_quiet("states/s_battle2.dst")
    m = emu.memory.unsigned
    char, smap = bg1(m)
    def w16(a, v): emu.memory.write_short(a, v)
    tile = FREE_TILE
    for kind, cells in zip(("obj", "law", "priv"), drawn):
        r0 = ROWS[kind]
        old = [(c, m.read_short(smap + (r0 * 32 + c) * 2)) for c in range(32)]
        used = [(c, e) for c, e in old if e & 0x3FF]
        start, pal = used[0][0], used[0][1] & 0xF000
        # the row's colour group: high two bits of its first inked pixel
        grp = None
        for c, e in used:
            for byte in m[char + (e & 0x3FF) * 32:char + (e & 0x3FF) * 32 + 32]:
                for v in (byte & 15, byte >> 4):
                    if v and grp is None: grp = v >> 2
        src_start = cells[0][0]
        for r in (0, 1):
            for c in range(start, 32):
                w16(smap + ((r0 + r) * 32 + c) * 2, 0)
        for c, pair in cells:
            col = start + c - src_start
            if col >= 32:
                print("warning: %s cut at the info screen's edge" % kind); break
            for r, data in enumerate(pair):
                if not any(data):
                    continue
                buf = bytearray(data)
                for i, byte in enumerate(buf):
                    lo, hi = byte & 15, byte >> 4
                    lo = (lo & 3) | (grp << 2) if lo else 0
                    hi = (hi & 3) | (grp << 2) if hi else 0
                    buf[i] = lo | (hi << 4)
                for i in range(0, 32, 2):
                    w16(char + tile * 32 + i, buf[i] | (buf[i + 1] << 8))
                w16(smap + ((r0 + r) * 32 + col) * 2, pal | tile)
                tile += 1
    for _ in range(10):                  # a few frames on, as play.py's states are saved (a state saved
        emu.cycle(False)                 # right after loading would not run under another preset's build)
    emu.savestate.save_file(out_state)
    print("wrote", out_state, "with:", " | ".join(texts))


if __name__ == "__main__":
    if sys.argv[1] == "--draw":
        draw_one(*sys.argv[2:5])
    else:
        main()
