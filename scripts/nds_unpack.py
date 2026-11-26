#!/usr/bin/env python3
"""Unpack a Nintendo DS ROM: header, ARM9/ARM7 (ARM9 BLZ-decompressed),
overlays (decompressed), and the NitroFS file tree.

usage: nds_unpack.py ROM OUTDIR
"""
import json
import os
import struct
import sys


def u32(b, o):
    return struct.unpack_from("<I", b, o)[0]


def u16(b, o):
    return struct.unpack_from("<H", b, o)[0]


def blz_decompress(data):
    """Bottom-LZ (backwards LZSS) used for ARM9 and overlays."""
    end = len(data)
    inc_len = u32(data, end - 4)
    if inc_len == 0:
        return bytes(data)
    hdr = u32(data, end - 8)
    header_len = hdr >> 24
    enc_len = hdr & 0xFFFFFF
    keep = end - enc_len
    out = bytearray(data) + bytes(inc_len)
    src = end - header_len
    dst = end + inc_len
    while src > keep:
        src -= 1
        flags = data[src]
        for _ in range(8):
            if src <= keep:
                break
            if flags & 0x80:
                src -= 1
                b1 = data[src]
                src -= 1
                b2 = data[src]
                info = (b1 << 8) | b2
                length = (info >> 12) + 3
                disp = (info & 0xFFF) + 3
                for _ in range(length):
                    dst -= 1
                    out[dst] = out[dst + disp]
            else:
                src -= 1
                dst -= 1
                out[dst] = data[src]
            flags = (flags << 1) & 0xFF
    return bytes(out)


def main():
    rom_path, out = sys.argv[1], sys.argv[2]
    rom = open(rom_path, "rb").read()
    os.makedirs(out, exist_ok=True)

    h = {
        "title": rom[0:12].rstrip(b"\0").decode("ascii", "replace"),
        "gamecode": rom[12:16].decode("ascii", "replace"),
        "arm9_off": u32(rom, 0x20), "arm9_entry": u32(rom, 0x24),
        "arm9_ram": u32(rom, 0x28), "arm9_size": u32(rom, 0x2C),
        "arm7_off": u32(rom, 0x30), "arm7_entry": u32(rom, 0x34),
        "arm7_ram": u32(rom, 0x38), "arm7_size": u32(rom, 0x3C),
        "fnt_off": u32(rom, 0x40), "fnt_size": u32(rom, 0x44),
        "fat_off": u32(rom, 0x48), "fat_size": u32(rom, 0x4C),
        "ovt9_off": u32(rom, 0x50), "ovt9_size": u32(rom, 0x54),
        "ovt7_off": u32(rom, 0x58), "ovt7_size": u32(rom, 0x5C),
        "rom_used": u32(rom, 0x80),
    }

    # ---- ARM9 ----
    arm9 = bytearray(rom[h["arm9_off"]:h["arm9_off"] + h["arm9_size"]])
    magic = bytes.fromhex("dec00621") [::-1] + bytes.fromhex("2106c0de")[::-1]
    # module params end with nitrocode 0x2106C0DE, 0xDEC00621 (LE words)
    pos = arm9.find(struct.pack("<II", 0x2106C0DE, 0xDEC00621))
    h["arm9_module_params_off"] = pos - 28 if pos >= 0 else None
    h["arm9_compressed"] = False
    if pos >= 0:
        cse_field = pos - 8
        cse = u32(arm9, cse_field)
        if cse:
            h["arm9_compressed"] = True
            h["arm9_compressed_static_end"] = cse
            cut = cse - h["arm9_ram"]
            dec = bytearray(blz_decompress(bytes(arm9[:cut])))
            dec[cse_field:cse_field + 4] = b"\0\0\0\0"
            arm9 = dec + arm9[cut:]
        mp = pos - 28
        h["autoload_list_start"] = u32(arm9, mp)
        h["autoload_list_end"] = u32(arm9, mp + 4)
        h["autoload_start"] = u32(arm9, mp + 8)
        h["bss_start"] = u32(arm9, mp + 12)
        h["bss_end"] = u32(arm9, mp + 16)
    h["arm9_decompressed_size"] = len(arm9)
    open(os.path.join(out, "arm9.bin"), "wb").write(arm9)
    open(os.path.join(out, "arm7.bin"), "wb").write(
        rom[h["arm7_off"]:h["arm7_off"] + h["arm7_size"]])
    open(os.path.join(out, "header.bin"), "wb").write(rom[:0x4000])

    # ---- FAT ----
    nfiles = h["fat_size"] // 8
    fat = [(u32(rom, h["fat_off"] + 8 * i), u32(rom, h["fat_off"] + 8 * i + 4))
           for i in range(nfiles)]

    # ---- overlays ----
    ovdir = os.path.join(out, "overlays")
    os.makedirs(ovdir, exist_ok=True)
    overlays = []
    for i in range(h["ovt9_size"] // 32):
        e = h["ovt9_off"] + 32 * i
        oid, ram, size, bss, si_s, si_e, fid, flags = struct.unpack_from("<8I", rom, e)
        s, t = fat[fid]
        raw = rom[s:t]
        compressed = bool((flags >> 24) & 1)
        data = blz_decompress(raw) if compressed else raw
        name = "ov_%03d.bin" % oid
        open(os.path.join(ovdir, name), "wb").write(data)
        overlays.append({
            "id": oid, "ram": ram, "ram_size": size, "bss_size": bss,
            "static_init_start": si_s, "static_init_end": si_e,
            "file_id": fid, "compressed": compressed,
            "rom_size": len(raw), "size": len(data), "file": name,
        })
    h["overlays"] = overlays

    # ---- NitroFS ----
    fnt = h["fnt_off"]
    files = []

    def walk(dir_id, path):
        e = fnt + 8 * (dir_id & 0xFFF)
        sub = fnt + u32(rom, e)
        fid = u16(rom, e + 4)
        while True:
            t = rom[sub]
            sub += 1
            if t == 0:
                break
            n = t & 0x7F
            name = rom[sub:sub + n].decode("shift_jis", "replace")
            sub += n
            if t & 0x80:
                did = u16(rom, sub)
                sub += 2
                walk(did, path + [name])
            else:
                files.append((fid, "/".join(path + [name])))
                fid += 1

    if h["fnt_size"]:
        walk(0xF000, [])
    froot = os.path.join(out, "files")
    listing = []
    for fid, p in files:
        s, t = fat[fid]
        dest = os.path.join(froot, p)
        os.makedirs(os.path.dirname(dest), exist_ok=True)
        open(dest, "wb").write(rom[s:t])
        listing.append({"id": fid, "path": p, "size": t - s, "rom_off": s})
    h["file_count"] = len(listing)
    json.dump(h, open(os.path.join(out, "rom.json"), "w"), indent=1)
    json.dump(listing, open(os.path.join(out, "files.json"), "w"), indent=1)

    for k, v in h.items():
        if k == "overlays":
            continue
        print(k, hex(v) if isinstance(v, int) and not isinstance(v, bool) else v)
    print("overlays:", len(overlays))
    for o in overlays:
        print("  ov%03d ram=%08x size=%06x bss=%05x comp=%d" % (
            o["id"], o["ram"], o["size"], o["bss_size"], o["compressed"]))


if __name__ == "__main__":
    main()
