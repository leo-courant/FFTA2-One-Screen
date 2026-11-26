#!/usr/bin/env python3
"""Apply the FFTA2 single-screen mod to a Final Fantasy Tactics A2 (USA) ROM, clean or
already changed by another mod (ticket 27).  Python 3 standard library only: no compiler.

usage: python3 <this file> IN.nds OUT.nds [--display deck|16x9|4x3]
       python3 scripts/modpatch.py IN.nds OUT.nds --mod MOD.json      (in the repo)

Other mods go on first, this one last.  Only the places this mod changes are checked:
each must still hold the game's original bytes, compared by hash.  When one doesn't,
nothing is written and every clash is listed with its game address and our name for it.
The file holds the mod's own code and hashes only, never bytes of the game.

How a mod description looks (patch.py builds it; the release embeds one per display preset):
  blob, blob_addr   the mod's code, loaded by the game's boot code as a third ARM9
                    "autoload" section appended after the ARM9 binary
  edits             [{addr, data, len, sha1, name, hook}]: new bytes at an ARM9 RAM
                    address, and the SHA-1 of the original bytes they replace
  To make room after the ARM9 binary, whatever lies there (the overlay table, overlays,
  other files) is moved to free space at the end of the ROM, wherever the ROM's own
  header and file table say it is.
"""
import base64
import hashlib
import json
import struct
import sys

FORMAT = 1
GAME_CODE = b"A6FE"                 # Final Fantasy Tactics A2 (USA)
ARM9_RAM = 0x02000000
MODULE_PARAMS = 0xBA0               # in the ARM9 binary: autoload list, bss, compression, magic
NITRO_MAGIC = 0xDEC00621
ALIGN = 0x200

MODS = {}                           # filled in by the release (scripts/make_patcher.py)


class Refusal(Exception):
    """The ROM can't take the mod; the message says why.  Nothing has been written."""


def crc16(data):
    crc = 0xFFFF
    for b in data:
        crc ^= b
        for _ in range(8):
            crc = (crc >> 1) ^ 0xA001 if crc & 1 else crc >> 1
    return crc


def _regions(rom, u32):
    """Every stretch of the ROM the header or the file table points at:
    (start, end, kind, where its offsets are written)."""
    out = []
    for name, off_at, size_at in (("ARM7 binary", 0x30, 0x3C), ("file name table", 0x40, 0x44),
                                  ("file table", 0x48, 0x4C), ("ARM9 overlay table", 0x50, 0x54),
                                  ("ARM7 overlay table", 0x58, 0x5C)):
        s, n = u32(off_at), u32(size_at)
        if n:
            out.append((s, s + n, name, ("header", off_at)))
    b = u32(0x68)
    if b:
        ver = struct.unpack_from("<H", rom, b)[0] if b + 2 <= len(rom) else 0
        size = {1: 0x840, 2: 0x940, 3: 0xA40, 0x103: 0x23C0}.get(ver, 0x840)
        out.append((b, b + size, "banner", ("banner", 0x68)))
    fat, nfat = u32(0x48), u32(0x4C) // 8
    for i in range(nfat):
        s, e = u32(fat + 8 * i), u32(fat + 8 * i + 4)
        if e > s:
            out.append((s, e, "file %d" % i, ("fat", fat + 8 * i)))
    return sorted(out)


def apply(rom, mod, hooks=True, say=print):
    """Return the patched ROM as bytes, or raise Refusal.  `rom` is not changed."""
    if mod.get("format") != FORMAT:
        raise Refusal("this mod description is format %r; the patcher reads format %d" % (mod.get("format"), FORMAT))
    rom = bytearray(rom)
    u32 = lambda o: struct.unpack_from("<I", rom, o)[0]
    p32 = lambda o, v: struct.pack_into("<I", rom, o, v)
    if len(rom) < 0x8000 or bytes(rom[0xC:0x10]) != GAME_CODE:
        raise Refusal("not Final Fantasy Tactics A2 (USA): the game code is %r, expected %r"
                      % (bytes(rom[0xC:0x10]).decode("latin-1"), GAME_CODE.decode()))
    if hashlib.sha1(rom).hexdigest() == mod["rom_sha1"]:
        say("clean FFTA2 (USA) ROM")
    else:
        say("not the clean FFTA2 (USA) dump (another mod, or a different dump): "
            "checking only the places this mod changes")

    # --- the ARM9 binary: where it is and how it is built -------------------------
    arm9_off, arm9_ram, arm9_size = u32(0x20), u32(0x28), u32(0x2C)
    if arm9_ram != ARM9_RAM:
        raise Refusal("the ARM9 binary loads at 0x%08x, not 0x%08x" % (arm9_ram, ARM9_RAM))
    mp = arm9_off + MODULE_PARAMS
    list_s, list_e = u32(mp), u32(mp + 4)
    if u32(mp + 0x1C) != NITRO_MAGIC:
        raise Refusal("the ARM9 binary's parameter block is not where the game has it (0x%x): "
                      "another mod has rebuilt or moved the game code" % (ARM9_RAM + MODULE_PARAMS))
    if u32(mp + 0x14):
        raise Refusal("the ARM9 binary is compressed (a ROM tool repacked it): "
                      "decompress it with that tool, then apply this mod")
    at = arm9_off + list_s - ARM9_RAM               # the autoload list: the blob goes here
    if list_e - list_s == 36 and u32(at + 24) == mod["blob_addr"]:
        raise Refusal("this ROM already has the single-screen mod: start again from the ROM without it")
    footer = bytes(rom[arm9_off + arm9_size:arm9_off + arm9_size + 12])
    if list_e - list_s != 24 or list_e - ARM9_RAM != arm9_size or footer[:4] != struct.pack("<I", NITRO_MAGIC):
        raise Refusal("the end of the ARM9 binary is not laid out as in the game (size 0x%x): another mod "
                      "has added code there; the two mods can't be combined this way" % arm9_size)
    old_list = bytes(rom[at:at + 24])

    # --- every place the mod changes must still hold the game's bytes -------------
    clashes = []
    for e in mod["edits"]:
        off = arm9_off + e["addr"] - ARM9_RAM
        if hashlib.sha1(rom[off:off + e["len"]]).hexdigest() != e["sha1"]:
            clashes.append("  0x%08x  %-22s  holds %s, not the game's original %d bytes"
                           % (e["addr"], e["name"] or "?", bytes(rom[off:off + e["len"]]).hex(), e["len"]))
    if clashes:
        raise Refusal("another mod has changed %d place(s) this mod needs; nothing was written:\n%s\n"
                      "Those places are listed in docs/symbols.tsv of the mod's repository."
                      % (len(clashes), "\n".join(clashes)))
    if hashlib.sha1(rom[arm9_off:arm9_off + arm9_size]).hexdigest() != mod["arm9_sha1"]:
        say("note: the game code (ARM9) differs from the clean game elsewhere; this mod's places are "
            "untouched, but if the other mod changes code this mod relies on, it may misbehave in play")

    # --- make room after the ARM9 binary ----------------------------------------
    blob = base64.b64decode(mod["blob"])
    new_list = old_list + struct.pack("<III", mod["blob_addr"], len(blob), mod.get("bss", 0))   # bss: the game's startup zeroes it
    tail = blob + new_list
    need = at + len(tail) + 12
    regions = _regions(rom, u32)
    end = max([u32(0x80)] + [e for _, e, _, _ in regions])
    end = (end + ALIGN - 1) & ~(ALIGN - 1)
    for s, e, name, (kind, where) in regions:
        if s >= need or e <= at:
            continue
        if s < at:
            raise Refusal("the %s overlaps the end of the ARM9 binary (0x%x..0x%x)" % (name, s, e))
        n = e - s
        dest = bytes(rom[end:end + n])
        if end + n > len(rom):
            raise Refusal("no free space left at the end of the ROM for the %s (0x%x bytes)" % (name, n))
        if dest.count(dest[:1]) != n or dest[:1] not in (b"\xff", b"\x00"):
            raise Refusal("the space after the ROM's last file (0x%x) is not empty: another mod may "
                          "keep data there" % end)
        rom[end:end + n] = rom[s:e]
        rom[s:e] = b"\xff" * n
        if kind == "fat":
            p32(where, end)
            p32(where + 4, end + n)
        else:
            p32(where, end)
        end = (end + n + ALIGN - 1) & ~(ALIGN - 1)
    p32(0x80, end)

    # --- append the blob as a third autoload section ------------------------------
    rom[at:at + len(tail)] = tail
    rom[at + len(tail):at + len(tail) + 12] = footer
    p32(mp, list_s + len(blob))
    p32(mp + 4, list_s + len(blob) + len(new_list))
    p32(0x2C, list_s + len(tail) - ARM9_RAM)

    # --- the changes in the game code ----------------------------------------
    for e in mod["edits"]:
        if hooks or not e["hook"]:
            off = arm9_off + e["addr"] - ARM9_RAM
            rom[off:off + e["len"]] = bytes.fromhex(e["data"])
    struct.pack_into("<H", rom, 0x15E, crc16(rom[:0x15E]))
    return bytes(rom)


def main(argv):
    import argparse
    ap = argparse.ArgumentParser(description="Apply the FFTA2 single-screen mod to an FFTA2 (USA) ROM.")
    ap.add_argument("src", help="the ROM: your own dump, with other mods already applied if you use any")
    ap.add_argument("dst", help="where to write the modded ROM")
    if MODS:
        ap.add_argument("--display", choices=sorted(MODS), default="deck" if "deck" in MODS else sorted(MODS)[0],
                        help="display preset: deck (Steam Deck 1280x800), 16x9 (1920x1080 monitor), 4x3 (plain)")
    ap.add_argument("--mod", help="a mod description (.json) instead of a built-in preset")
    args = ap.parse_args(argv)
    if args.mod:
        mod = json.load(open(args.mod))
    elif MODS:
        mod = MODS[args.display]
    else:
        sys.exit("no mod description: pass --mod FILE.json (scripts/patch.py --json writes one)")
    if args.src == args.dst:
        sys.exit("write to a new file, not over the ROM you read from")
    try:
        out = apply(open(args.src, "rb").read(), mod)
    except Refusal as r:
        sys.exit("not applied: %s" % r)
    open(args.dst, "wb").write(out)
    print("wrote %s (%s preset)" % (args.dst, mod.get("preset", "?")))


if __name__ == "__main__":
    main(sys.argv[1:])
