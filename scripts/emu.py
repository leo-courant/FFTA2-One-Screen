"""Shared helper: open ROM + state quietly."""
import os, sys
os.environ.setdefault("SDL_VIDEODRIVER", "dummy"); os.environ.setdefault("SDL_AUDIODRIVER", "dummy")
from desmume.emulator import DeSmuME
BLOB_ADDR = 0x02143E20


def rom_blob(rom):
    """The mod's code blob as patched into ROM (the third ARM9 autoload section),
    or None for an unmodified ROM."""
    d = open(rom, "rb").read()
    u32 = lambda o: int.from_bytes(d[o:o + 4], "little")
    lst = 0x4000 + u32(0x4000 + 0xBA0) - 0x02000000
    if u32(0x4000 + 0xBA4) - u32(0x4000 + 0xBA0) < 36 or u32(lst + 24) != BLOB_ADDR:
        return None
    n = u32(lst + 28)
    return d[lst - n:lst]


def rom_bss(rom):
    """Where the mod's variables are (ADR 0017): (address, size) of the zeroed area the
    blob's autoload entry declares after it, or (address, 0) for older builds."""
    d = open(rom, "rb").read(0x4000 + 0x130000)
    u32 = lambda o: int.from_bytes(d[o:o + 4], "little")
    lst = 0x4000 + u32(0x4000 + 0xBA0) - 0x02000000
    n = u32(lst + 28) if u32(lst + 24) == BLOB_ADDR else 0
    return BLOB_ADDR + n, u32(lst + 32) if n else 0


def view_settings(blob):
    """Where the display settings sit in the blob (view_cfg in src/hook.c, after its
    "VIEW" marker) and their values: screen_w, screen_h, wide_x, wide_y, nudge_x, nudge_y."""
    at = blob.index(b"VIEW") + 4
    v = [int.from_bytes(blob[at + 4 * i:at + 4 * i + 4], "little", signed=True) for i in range(6)]
    return at, dict(zip(("screen_w", "screen_h", "wide_x", "wide_y", "nudge_x", "nudge_y"), v))
def boot(state=None, rom="rom/ffta2.nds", frames=3):
    emu = DeSmuME(); emu.open(rom); emu.volume_set(0)
    if state:
        emu.savestate.load_file(state)
        # re-inject the hook code: BLOB if given, else the blob inside the ROM
        b = open(os.environ["BLOB"], "rb").read() if os.environ.get("BLOB") else rom_blob(rom)
        if b:
            b += bytes(-len(b) % 4)
            for i in range(0, len(b), 4):
                emu.memory.write_long(0x02143E20 + i, int.from_bytes(b[i:i+4], "little"))
            # the mod's variables start at zero, as they did when they sat in the blob
            at, n = rom_bss(rom)
            for i in range(0, n, 4):
                emu.memory.write_long(at + i, 0)
            # and re-apply the code patches (hooks) the state's RAM predates, or undo the
            # ones it carries that this ROM lacks (patch.py --no-hooks, ticket 02)
            new = open(rom, "rb").read()[0x4000:0x4000 + 0x121660]
            old = open("rom/ffta2.nds", "rb").read()[0x4000:0x4000 + 0x121660]
            mod = open(os.environ.get("STATE_ROM", "build/ffta2-1screen.nds"), "rb").read()[0x4000:0x4000 + 0x121660]
            for i in range(0, len(new), 4):
                if (new[i:i+4] != old[i:i+4] or mod[i:i+4] != old[i:i+4]) and i != 0x7F44:   # keep the state's heap start
                    emu.memory.write_long(0x02000000 + i, int.from_bytes(new[i:i+4], "little"))
    for _ in range(frames): emu.cycle(False)
    return emu


def save_clean(emu, path, tries=240):
    """Save a state at a frame where the CPU is not inside the mod's code (program counter
    and live stack), so the state also runs on later builds, whose code has moved.
    Returns how many frames were waited, or None if every frame was inside (saved anyway)."""
    m, r = emu.memory.unsigned, emu.memory.register_arm9
    inside = lambda v: BLOB_ADDR <= v < BLOB_ADDR + 0x8000
    for n in range(tries):
        sp = r.sp & 0xFFFFFFFC
        stack = [m.read_long(a) for a in range(sp, min(sp + 0x400, 0x027E3F80), 4)] if 0x027E0000 <= sp < 0x027E4000 else []
        if not inside(r.pc & 0xFFFFFFFF) and not inside(r.lr & 0xFFFFFFFF) and not any(inside(v) for v in stack):
            emu.savestate.save_file(path)
            return n
        emu.cycle(False)
    emu.savestate.save_file(path)
    return None
