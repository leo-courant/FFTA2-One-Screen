#!/usr/bin/env python3
"""Build the patched FFTA2 (USA) ROM.

usage: patch.py IN.nds OUT.nds [--display deck|16x9|4x3 | --size WxH] [--view WxH] [--nudge X,Y]
                [--json MOD.json]

IN may already carry other mods (ticket 27): only the places this mod changes are
checked.  The applying is done by scripts/modpatch.py (standard library only), the same
code players run from the release; --json also writes the mod description it applies.

Display presets (ADR 0007) pick the view, the number of game pixels shown, for the
display the emulator fills:
  deck  Steam Deck 1280x800 -> 366x228 view, 3.5 screen px per game px (default; ADR 0009;
        the even 4x of ADR 0004 is --view 320x200)
  16x9  16:9 monitor 1920x1080 -> 384x216 view, 5 screen px per game px
        (wants melonDS's internal resolution at 9x)
  4x3   plain 4:3 -> 256x192, the game's own view
--size WxH picks the view for any display by the same rule (view_for); --view sets
the view directly.  --nudge sets the sub-pixel nudge in projection units; the presets'
are measured, a custom size starts at 0,0 (docs/test-saves.md, "Display presets").

What it does:
  * compiles src/hook.c into a blob linked at BLOB_ADDR
  * assembles the changes to the game code (each with a hash of the bytes it replaces)
  * modpatch.apply: grows the ARM9 binary (the blob is appended as a third startup
    "autoload" section, which the game's own boot code copies to BLOB_ADDR), moves
    whatever lies after the ARM9 binary to the end of the ROM to make room, moves the
    main heap start up by BLOB_RESERVE, and hooks the tail of the per-frame key update
"""
import argparse
import base64
import hashlib
import json
import os
import struct
import subprocess
import sys
import zlib
import keystone
from modpatch import apply, Refusal, FORMAT

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
EXPECT_SHA1 = "7ec7646c527be6af87e3c7ab0ed454f952842001"     # the clean USA dump
ARM9_SHA1 = "5c3408b37808cdf6590a5dcf466fa4c4a6fc7bce"       # its ARM9 binary (0x121678 bytes at 0x4000)
BLOB_ADDR = 0x02143E20      # original main heap start
BLOB_RESERVE = 0x8000
BSS_ROOM = 0x8000           # the mod's variables, right after the reserve, zeroed at boot (ADR 0017)
HUD_TEX_SIZE = 0x2000       # top of texture bank B the banner and turn order share with the game (ADR 0008)
ARENA_LO_LITERAL = 0x02007F44
HOOK = 0x0201EA60
MAP_ART = os.path.join(ROOT, "work", "map_art", "map_art.lz")   # map_art_pack.py (ticket 36, ADR 0018)

ks = keystone.Ks(keystone.KS_ARCH_ARM, keystone.KS_MODE_ARM)


def asm(src, addr):
    enc, _ = ks.asm(src, addr)
    return bytes(enc)


# display presets: display size in screen pixels (None: the plain game), sub-pixel nudge,
# and the view when it is not the one view_for picks
PRESETS = {
    "deck": ((1280, 800), (3, -3), (366, 228)),  # 3.5x, chosen by the user over the even 4x (ADR 0009)
    "16x9": ((1920, 1080), (3, -3), None),  # measured in melonDS 1.1, OpenGL 9x (8x cannot be even)
    "4x3": (None, (0, 0), None),
}
MAX_W, MAX_H = 768, 384     # the menus' floor is repeated one old screen to either side


def view_for(w, h):
    """The view for a display of w x h screen pixels: the largest whole number of
    screen pixels per game pixel that still shows at least the game's 192 rows, so
    every game pixel is the same size.  Where that would zoom out by more than
    12.5% (216 rows), the view keeps 192 rows and pixels are uneven instead."""
    k = max(1, h // 192)
    vh = h / k
    if vh > 216:
        k = h / 192
    even = lambda v: max(2, 2 * round(v / 2))
    return even(w / k), even(h / k)


def tall_for(display):
    """The view for a Scion's animation (ticket 26): the two screens as one 256x384
    picture, at the largest even scale (in half steps) that fits the display's height."""
    if not display:
        return 512, 384         # a 4:3 display of any size
    w, h = display
    k = max(1, int(2 * h / 384) / 2)
    even = lambda v: 2 * round(v / 2)
    return even(w / k), even(h / k)


def margins(vw, vh):
    """Extra pixels kept beyond the old 256x192 view (map cells, backdrop bands,
    layout pieces): a little more than the view's own side area, rounded so the
    patched instructions can hold them; none for the plain game."""
    ex, ey = (vw - 256) // 2, (vh - 192) // 2
    side = 0 if ex <= 0 else -(-ex // 16) * 16 + 32
    vert = 0 if ey <= 0 else -(-ey // 4) * 4 + 4
    return side, vert


def build_dir():
    """Where the compile happens: build/, or FFTA2_BUILD_DIR (make_release.py gives each run its
    own, so builds running at the same time don't overwrite each other's hook.elf or art)."""
    return os.path.abspath(os.environ.get("FFTA2_BUILD_DIR") or os.path.join(ROOT, "build"))


def build_blob(defines):
    out = build_dir()
    os.makedirs(out, exist_ok=True)
    zig = [sys.executable, "-m", "ziglang"]
    elf, binf = os.path.join(out, "hook.elf"), os.path.join(out, "hook.bin")
    ld = os.path.join(out, "link.ld")          # src/link.ld with the variables' address filled in
    open(ld, "w").write(open(os.path.join(ROOT, "src", "link.ld")).read().replace(
        ". = BSS_ADDR;", ". = 0x%X;" % (BLOB_ADDR + BLOB_RESERVE)))
    subprocess.check_call(cwd=out, args=zig + [   # cwd: map_art.c .incbin's map_art.lz from it
        "cc", "-target", "arm-freestanding-eabi", "-mcpu=arm946e_s", "-marm",
        "-Os", "-g", "-ffreestanding", "-nostdlib", "-fno-pic", "-fno-builtin",
        "-Wall", "-Wl,-T," + ld] +
        ["-D%s=%d" % kv for kv in defines.items()] + [
        os.path.join(ROOT, "src", "hook.c"), "-o", elf])
    subprocess.check_call(zig + ["objcopy", "-O", "binary", elf, binf])
    blob = open(binf, "rb").read()
    used = len(blob)
    assert used <= BLOB_RESERVE, "blob too big (%d bytes; --reserve)" % used
    sym = {l.split()[2]: int(l.split()[0], 16) for l in subprocess.run(
        ["nm", elf], capture_output=True, text=True, check=True).stdout.splitlines() if len(l.split()) == 3}
    bss = sym["bss_end"] - sym["bss_start"]
    assert sym["bss_start"] == BLOB_ADDR + BLOB_RESERVE and bss <= BSS_ROOM, "variables too big (%d bytes; BSS_ROOM)" % bss
    # always the same size: what the mod moves inside the ROM then stays put between builds,
    # and test savestates (which remember where the game's files are) keep working
    blob += b"\0" * (BLOB_RESERVE - used)
    return blob, used, bss


def parse_size(text):
    w, _, h = text.lower().partition("x")
    return int(w), int(h)


def main():
    global BLOB_RESERVE
    ap = argparse.ArgumentParser(description="Build the patched FFTA2 (USA) ROM.")
    ap.add_argument("src")
    ap.add_argument("dst")
    ap.add_argument("--display", choices=sorted(PRESETS), default="deck")
    ap.add_argument("--size", type=parse_size, help="display WxH in screen pixels, instead of a preset")
    ap.add_argument("--view", type=parse_size, help="view WxH in game pixels, instead of the preset's")
    ap.add_argument("--tall", type=parse_size, help="view WxH in game pixels during a Scion's animation "
                    "(256x384 or more), instead of the one picked for the display")
    ap.add_argument("--nudge", type=lambda t: tuple(int(v) for v in t.split(",")),
                    help="sub-pixel nudge X,Y in projection units")
    ap.add_argument("--no-hooks", action="store_true",
                    help="same ROM layout and code blob but no hooks: the unmodified game in a ROM "
                         "the test savestates load in (reference pictures, ticket 02)")
    ap.add_argument("--json", metavar="MOD.json", help="also write the mod description that is applied")
    ap.add_argument("--guard", action="store_true",
                    help="test build for playing (ticket 25): a red dot top left when the game "
                         "clashes with the mod's video memory; never for publishing")
    ap.add_argument("--define", action="append", default=[], metavar="NAME=N",
                    help="extra compile-time setting for src/hook.c (testing looks, e.g. TURN_STYLE=2)")
    ap.add_argument("--no-map-art", action="store_true",
                    help="leave out the map of Ivalice's extended edges even when %s is there" % os.path.relpath(MAP_ART, ROOT))
    ap.add_argument("--map-art", metavar="FILE.lz", default=MAP_ART,
                    help="the map art to build in (default %s; trying other art)" % os.path.relpath(MAP_ART, ROOT))
    ap.add_argument("--reserve", type=lambda t: int(t, 0), metavar="BYTES",
                    help="memory set aside for the code blob (default 0x%X); another value moves the game's "
                         "heap, so savestates made with the default no longer load" % BLOB_RESERVE)
    args = ap.parse_args()
    if args.reserve:
        BLOB_RESERVE = args.reserve
    display, nudge, preset_view = PRESETS[args.display]
    if args.size:
        display, nudge, preset_view = args.size, (0, 0), None
    vw, vh = args.view or preset_view or (view_for(*display) if display else (256, 192))
    if args.nudge:
        nudge = args.nudge
    if not (256 <= vw <= MAX_W and 192 <= vh <= MAX_H) or vw % 2 or vh % 2:
        sys.exit("view %dx%d not supported: needs even sizes from 256x192 to %dx%d" % (vw, vh, MAX_W, MAX_H))
    side, vert = margins(vw, vh)
    tw, th = args.tall or tall_for(display)
    # the map of Ivalice's extended edges: derived from the game's picture, so not in the
    # repository; built in when map_art_pack.py has made it, and only where the view is wide
    art = (side or vert) and not args.no_map_art and os.path.exists(args.map_art)
    if art:
        data = open(args.map_art, "rb").read()
        os.makedirs(build_dir(), exist_ok=True)
        open(os.path.join(build_dir(), "map_art.lz"), "wb").write(data)
        # zig caches the compile, and the .incbin'd art is not part of its key: the art's
        # checksum goes into the command line, so other art is always compiled in
        art = zlib.crc32(data) & 0x7FFFFFFF | 1
    elif (side or vert) and not args.no_map_art:
        print("note: no %s, so the map of Ivalice keeps the game's sea at its edges "
              "(scripts/map_art_dump.py, map_art_outpaint.py, map_art_pack.py make it)" % os.path.relpath(MAP_ART, ROOT))
    blob, used, bss = build_blob({"VIEW_W": vw, "VIEW_H": vh, "NUDGE_X": nudge[0], "NUDGE_Y": nudge[1],
                       "SIDE_MARGIN": side, "V_MARGIN": vert, "HUD_TEX_SIZE": HUD_TEX_SIZE,
                       "TALL_W": tw, "TALL_H": th,
                       **({"GUARD": 1} if args.guard else {}), **({"MAP_ART": art} if art else {}),
                       **{k: int(v, 0) for k, v in (d.split("=") for d in args.define)}})
    names = symbol_names()
    edits = []

    def put(addr, data, expect):
        assert len(data) == len(expect)
        edits.append({"addr": addr, "data": data.hex(), "len": len(expect),
                      "sha1": hashlib.sha1(expect).hexdigest(), "name": names.get(addr, ""),
                      "hook": addr != ARENA_LO_LITERAL})

    # --- hint labels without their second copy (ticket 34, widescreen only) ---
    if side or vert:
        for a in (0x0204CF84, 0x0204D19C):
            put(a, asm("bl 0x%x" % (BLOB_ADDR + 84), a), asm("cmp r0, #1", 0))
    # --- heap starts after the blob and its variables ----------------------
    put(ARENA_LO_LITERAL, struct.pack("<I", BLOB_ADDR + BLOB_RESERVE + BSS_ROOM),
        struct.pack("<I", BLOB_ADDR))
    # --- per-frame hook: tail of key update (FUN_0201e8a8) ---------------
    put(HOOK, asm("b 0x%x" % BLOB_ADDR, HOOK), struct.pack("<I", 0xE1C010B8))

    # --- widescreen: hook G3_OrthoW after the matrix is built --------------
    put(0x02005270, asm("bl 0x%x" % (BLOB_ADDR + 4), 0x02005270), struct.pack("<I", 0xE59D0064))

    # --- side areas: backdrop bands and map cells beyond the old 256px view --
    put(0x020D5368, asm("mov r7, #%d" % (256 + 2 * side), 0), asm("mov r7, #0x100", 0))
    put(0x020D5364, asm("mov r0, #%d" % (192 + 2 * vert), 0), asm("mov r0, #0xc0", 0))   # and taller
    # (and while the camera is zoomed out, in a Scion's lead-in, where the sizes are 20.12)
    put(0x020D5A8C, struct.pack("<I", (256 + 2 * side + 1) << 12), struct.pack("<I", 0x101000))
    put(0x020D5430, asm("mov r0, #0x%x" % (-(-(192 + 2 * vert + 1) // 4) * 4 << 12 if vert else 0xc1000), 0), asm("mov r0, #0xc1000", 0))
    put(0x020D54AC, asm("bl 0x%x" % (BLOB_ADDR + 8), 0x020D54AC), asm("bl 0x0208FAC0", 0x020D54AC))
    put(0x0208B0BC, asm("b 0x%x" % (BLOB_ADDR + 12), 0x0208B0BC), asm("push {r3, lr}", 0))

    # --- game panels slide to the screen edges ----------------------------
    put(0x020B2E98, asm("bl 0x%x" % (BLOB_ADDR + 16), 0x020B2E98), asm("str r3, [r1, #0x30]", 0))
    put(0x020B095C, asm("bl 0x%x" % (BLOB_ADDR + 20), 0x020B095C), asm("ldrsh r2, [r6, #0xc]", 0))
    put(0x02053338, asm("bl 0x%x" % (BLOB_ADDR + 24), 0x02053338), asm("bl 0x020525E8", 0x02053338))
    put(0x02053320, asm("bl 0x%x" % (BLOB_ADDR + 32), 0x02053320), asm("bl 0x0204F944", 0x02053320))
    put(0x0205332C, asm("bl 0x%x" % (BLOB_ADDR + 36), 0x0205332C), asm("bl 0x0204FFFC", 0x0205332C))
    put(0x0204B514, asm("bl 0x%x" % (BLOB_ADDR + 28), 0x0204B514), asm("ldrsh r2, [r11, #0xa]", 0))
    # a sprite sitting on a moved corner ornament follows it (after its draw entry is queued)
    put(0x02034C5C, asm("bl 0x%x" % (BLOB_ADDR + 44), 0x02034C5C), asm("ldr r0, [sp, #0x28]", 0))

    # menus: the patterned floor repeats into the side areas
    put(0x020D60C0, asm("bl 0x%x" % (BLOB_ADDR + 48), 0x020D60C0), asm("bl 0x020D4BE0", 0x020D60C0))
    # a map with clip areas (the mist maps of quests 18, 23, 24): the layer's parts are culled
    # against the old screen, which throws the repeats away (ticket 30; the third corner is
    # always index 2, so its x and y are read straight from the stack to make room for the sub)
    if side or vert:
        put(0x020D50E4, asm("add r0, r0, #%d" % (256 + side), 0), asm("add r0, r0, #0x100", 0))
        put(0x020D50FC, asm("add r0, r0, #%d" % (192 + vert), 0), asm("add r0, r0, #0xc0", 0))
        for at, corner, cam, margin, idx in ((0x020D5114, 0x38, 0x32, side, "r2, [r0, r1]"), (0x020D5128, 0x40, 0x30, vert, "r1, [r0, r1]")):
            reg = idx[:2]
            put(at, b"".join(asm(i, 0) for i in ("ldrsh %s, [sp, #0x%x]" % (reg, corner), "ldrsh r0, [sp, #0x%x]" % cam, "sub r0, r0, #%d" % margin)),
                b"".join(asm(i, 0) for i in ("add r0, sp, #0x%x" % (corner - 4), "ldrsh %s" % idx, "ldrsh r0, [sp, #0x%x]" % cam)))

    # a full-screen map picture (clan parchment) carries its edge on into the side areas
    put(0x0208CE08, asm("bl 0x%x" % (BLOB_ADDR + 52), 0x0208CE08), asm("mov r1, #1", 0))

    # the ability list of View Abilities is made more compact: its grid widget is narrowed
    put(0x020B34C0, asm("bl 0x%x" % (BLOB_ADDR + 56), 0x020B34C0), asm("bl 0x020B3208", 0x020B34C0))

    # a full-screen still picture (the title) is mirrored into the side areas (ticket 12)
    put(0x020B0B4C, asm("bl 0x%x" % (BLOB_ADDR + 60), 0x020B0B4C), asm("str r1, [ip, #4]", 0))

    # a story scene's full-screen sprite picture reaches the real edges (ticket 29)
    put(0x0208F97C, asm("bl 0x%x" % (BLOB_ADDR + 64), 0x0208F97C), asm("bl 0x01FFB390", 0x0208F97C))

    # mist is cut around the windows where the mod puts them (ticket 30)
    put(0x02031EE0, asm("bl 0x%x" % (BLOB_ADDR + 88), 0x02031EE0), asm("bl 0x020573B0", 0x02031EE0))

    # the cover drawn over the whole picture (white at the end of the last story battle, black,
    # dimmed): 256x192 at 0,0.  Its first colour stores are redundant (a loop fills all four
    # right after), which leaves room to store its new corner (ticket 30)
    if side or vert:
        minus = lambda n: asm("mvn lr, #%d" % (n - 1) if n else "mov lr, #0", 0)
        put(0x020881B0, minus(side) + asm("strh lr, [sp]", 0), asm("strh r4, [sp, #0x1a]", 0) + asm("ldrh lr, [sp, #0x1a]", 0))
        put(0x020881C0, asm("mov r3, #0x%x" % ((256 + 2 * side) << 12), 0) + asm("mov r2, #0x%x" % ((192 + 2 * vert) << 12), 0) +
            minus(vert) + asm("strh lr, [sp, #2]", 0),
            asm("mov r3, #0x100000", 0) + asm("mov r2, #0xc0000", 0) + asm("strh lr, [sp, #0x18]", 0) + asm("strh lr, [sp, #0x16]", 0))

    # Scion animations: both screens drawn as one tall picture (ticket 26)
    put(0x0201D6F8, asm("bl 0x%x" % (BLOB_ADDR + 68), 0x0201D6F8), asm("bl 0x020F94F8", 0x0201D6F8))
    put(0x020E847C, asm("bl 0x%x" % (BLOB_ADDR + 72), 0x020E847C), asm("bl 0x02083834", 0x020E847C))
    put(0x020E7FD8, asm("bl 0x%x" % (BLOB_ADDR + 80), 0x020E7FD8), asm("str r1, [r2]", 0))
    put(0x020E81FC, asm("bl 0x%x" % (BLOB_ADDR + 76), 0x020E81FC), asm("bl 0x02004B68", 0x020E81FC))

    # the layout renderer skips pieces outside 0..256 x 0..192; allow the margins
    put(0x020B145C, asm("cmp r0, #%d" % (256 + side), 0), asm("cmp r0, #0x100", 0))
    put(0x020B146C, asm("cmn r0, #%d" % side if side else "cmp r0, #0", 0), asm("cmp r0, #0", 0))
    put(0x020B1460, asm("cmplt r2, #%d" % (192 + 2 * vert), 0), asm("cmplt r2, #0xc0", 0))
    put(0x020B1474, asm("cmngt r0, #%d" % (2 * vert) if vert else "cmpgt r0, #0", 0), asm("cmpgt r0, #0", 0))

    # --- 3D banner: draw just before the game swaps buffers ----------------
    put(0x0201E274, asm("bl 0x%x" % (BLOB_ADDR + 40), 0x0201E274), asm("bl 0x01FFB51C", 0x0201E274))

    mod = {"format": FORMAT, "preset": args.display if not (args.size or args.view or args.nudge or args.define or args.guard or args.no_map_art or args.map_art != MAP_ART) else "custom",
           "view": [vw, vh], "nudge": list(nudge), "rom_sha1": EXPECT_SHA1, "arm9_sha1": ARM9_SHA1,
           "blob_addr": BLOB_ADDR, "blob": base64.b64encode(blob).decode(), "bss": BSS_ROOM, "edits": edits}
    if args.json:
        json.dump(mod, open(args.json, "w"), indent=1)
    try:
        out = apply(open(args.src, "rb").read(), mod, hooks=not args.no_hooks)
    except Refusal as r:
        sys.exit("not applied: %s" % r)
    open(args.dst, "wb").write(out)
    print("wrote %s (view %dx%d, nudge %d,%d; blob %d of %d bytes used, variables %d of %d%s)"
          % (args.dst, vw, vh, nudge[0], nudge[1], used, BLOB_RESERVE, bss, BSS_ROOM, "; map art" if art else ""))


def symbol_names():
    """Our name for each address, from docs/symbols.tsv (for clash messages)."""
    names = {}
    for line in open(os.path.join(ROOT, "docs", "symbols.tsv")):
        f = line.rstrip("\n").split("\t")
        if len(f) >= 3 and f[0].startswith("0x"):
            names[int(f[0], 16)] = f[2]
    return names


if __name__ == "__main__":
    main()
