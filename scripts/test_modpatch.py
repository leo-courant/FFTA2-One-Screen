#!/usr/bin/env python3
"""Tests for applying the mod to ROMs other than the clean dump (ticket 27).

usage: python3 scripts/test_modpatch.py [OTHER_MOD.xdelta ...]      (plain python3: the
       patcher must need nothing but the standard library; about 1 min)

Needs rom/ffta2.nds (the clean dump) and dist/ffta2-1screen-patcher.py (make_patcher.py).
Every ROM the patcher accepts is written to build/t27/ok_<case>.nds for a boot test
(scripts/boot_check.sh); refused cases must leave no output file.
"""
import hashlib
import os
import struct
import subprocess
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
OUT = os.path.join(ROOT, "build", "t27")
PATCHER = os.path.join(ROOT, "dist", "ffta2-1screen-patcher.py")
sys.path.insert(0, HERE)
import vcdiff                                   # noqa: E402

clean = open(os.path.join(ROOT, "rom", "ffta2.nds"), "rb").read()
u32 = lambda r, o: struct.unpack_from("<I", r, o)[0]
failed = []


def run_patcher(name, rom, display="deck"):
    """Run the release patcher as a player would; return (exit code, output text, out path)."""
    src, dst = os.path.join(OUT, "in_%s.nds" % name), os.path.join(OUT, "ok_%s.nds" % name)
    open(src, "wb").write(rom)
    if os.path.exists(dst):
        os.remove(dst)
    p = subprocess.run([sys.executable, "-I", PATCHER, src, dst, "--display", display],
                       capture_output=True, text=True)
    os.remove(src)
    return p.returncode, (p.stdout + p.stderr).strip(), dst


def expect(name, rom, ok, *say, display="deck"):
    code, text, dst = run_patcher(name, rom, display)
    good = (code == 0) == ok and os.path.exists(dst) == ok and all(s in text for s in say)
    print("%s %-14s %s\n%s" % ("PASS" if good else "FAIL", name, "applied" if code == 0 else "refused",
                               "\n".join("      " + l[:160] for l in text.splitlines()[-12:])))
    if not good:
        failed.append(name)
    return dst


def move(rom, start, end, to):
    """Move a stretch to `to` (as a ROM tool laying files out differently would)."""
    rom[to:to + end - start] = rom[start:end]
    rom[start:end] = b"\xff" * (end - start)


def main():
    os.makedirs(OUT, exist_ok=True)
    # 1. the clean dump: every preset gives the same ROM as the build script
    for d in ("deck", "16x9", "4x3"):
        dst = expect("clean_" + d, clean, True, "clean FFTA2", display=d)
        ref = os.path.join(ROOT, "build", "ffta2-1screen.nds")
        if d == "deck" and os.path.exists(dst) and os.path.exists(ref):
            same = open(dst, "rb").read() == open(ref, "rb").read()
            print("%s clean_deck is the same ROM as build/ffta2-1screen.nds (patch.py)" % ("PASS" if same else "FAIL"))
            if not same:
                failed.append("clean_deck_same")
        if d != "deck" and os.path.exists(dst):
            os.remove(dst)                      # keep one clean build for the boot test
    # 2. a ROM that is not FFTA2 USA
    bad = bytearray(clean); bad[0xC:0x10] = b"A6FP"
    expect("other_game", bytes(bad), False, "not Final Fantasy Tactics A2 (USA)")
    # 3. another mod changed two places this mod needs: refused, both named
    clash = bytearray(clean)
    for a in (0x0201EA60, 0x020B145C):
        clash[a - 0x02000000 + 0x4000] ^= 0xFF
    expect("clash", bytes(clash), False, "hook_entry", "layout_clip_checks", "2 place(s)")
    # 4. a data-only change elsewhere in ARM9: applies, with a note
    data = bytearray(clean); data[0x4000 + 0x110000] ^= 0x01
    expect("arm9_data", bytes(data), True, "not the clean", "differs from the clean game")
    # 5. the mod applied twice
    once = open(os.path.join(OUT, "ok_clean_deck.nds"), "rb").read()
    expect("twice", once, False, "already has the single-screen mod")
    # 6. laid out by another tool: the overlay table moved to the end of the ROM
    lay = bytearray(clean)
    used = (u32(lay, 0x80) + 0x1FF) & ~0x1FF
    s, n = u32(lay, 0x50), u32(lay, 0x54)
    move(lay, s, s + n, used)
    struct.pack_into("<I", lay, 0x50, used)
    struct.pack_into("<I", lay, 0x80, used + n)
    expect("ovt_moved", bytes(lay), True)
    # 7. ... and the ARM7 binary right after the ARM9 binary (the overlay table and the
    #    files that were there moved to the end)
    lay = bytearray(clean)
    end = (u32(lay, 0x80) + 0x1FF) & ~0x1FF
    arm9_end = (0x4000 + u32(lay, 0x2C) + 12 + 0x1FF) & ~0x1FF
    a7, a7n = u32(lay, 0x30), u32(lay, 0x3C)
    fat = u32(lay, 0x48)
    for i in range(u32(lay, 0x4C) // 8):     # every file in the ARM7 binary's new place
        fs, fe = u32(lay, fat + 8 * i), u32(lay, fat + 8 * i + 4)
        if fs >= arm9_end + a7n or fe <= fs:
            continue
        move(lay, fs, fe, end)
        struct.pack_into("<II", lay, fat + 8 * i, end, end + fe - fs)
        end = (end + fe - fs + 0x1FF) & ~0x1FF
    s, n = u32(lay, 0x50), u32(lay, 0x54)
    move(lay, s, s + n, end)
    struct.pack_into("<I", lay, 0x50, end)
    end = (end + n + 0x1FF) & ~0x1FF
    tmp = bytes(lay[a7:a7 + a7n])
    lay[a7:a7 + a7n] = b"\xff" * a7n
    lay[arm9_end:arm9_end + a7n] = tmp
    struct.pack_into("<I", lay, 0x30, arm9_end)
    struct.pack_into("<I", lay, 0x80, end)
    struct.pack_into("<H", lay, 0x15E, __import__("modpatch").crc16(lay[:0x15E]))
    expect("arm7_after", bytes(lay), True)
    # 8. something kept in the free space after the last file
    junk = bytearray(clean)
    at = (u32(junk, 0x80) + 0x1FF) & ~0x1FF
    junk[at + 0x10:at + 0x20] = b"another mod data"
    expect("free_used", bytes(junk), False, "is not empty")
    # 9. a compressed ARM9 binary
    comp = bytearray(clean); struct.pack_into("<I", comp, 0x4000 + 0xBA0 + 0x14, 0x02100000)
    expect("compressed", bytes(comp), False, "compressed")
    # 10. real mods for FFTA2 USA, given as xdelta patches of the clean dump
    for path in sys.argv[1:]:
        name = os.path.basename(path).split(".")[0][:14]
        modded = vcdiff.apply(clean, open(path, "rb").read())
        expect(name, modded, True, "not the clean")
    print("\n%d failed: %s" % (len(failed), " ".join(failed)) if failed else "\nall passed")
    sys.exit(1 if failed else 0)


if __name__ == "__main__":
    main()
