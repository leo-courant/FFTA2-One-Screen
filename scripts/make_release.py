#!/usr/bin/env python3
"""Build the files a release ships (ticket 21) and refuse the release if any of them holds
bytes of the game.

usage: .venv/bin/python scripts/make_release.py [OUTDIR]      (default dist/release; ~2 min)

Needs the clean ROM at rom/ffta2.nds and the map art at work/map_art/map_art.lz
(ADR 0018).  Writes to OUTDIR:
  ffta2-1screen-<preset>.bps      one BPS patch per display preset, for the clean USA ROM
                                  (Flips, Rom Patcher JS, ...); made by scripts/bps.py
  ffta2-1screen-patcher.py        the Python patcher with every preset, for ROMs other mods
                                  have changed (scripts/make_patcher.py, ADR 0011)
  SHA256SUMS, ROM.txt             checksums of the files, and of the ROM the patches expect

Every patch is applied back to the clean ROM and must give exactly what scripts/patch.py
builds.  Then scripts/check_no_game_bytes.py runs on every file (and on what the patcher
carries encoded).  As a guard on the check itself, a naive patch that stores every changed
byte must be caught; if it isn't, the check is broken and the release fails too.  A failed
release leaves no files in OUTDIR.
"""
import hashlib
import json
import os
import shutil
import struct
import subprocess
import sys
import tempfile
import zlib

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
sys.path.insert(0, HERE)
import bps                                          # noqa: E402
import check_no_game_bytes as check                 # noqa: E402
import make_patcher                                 # noqa: E402

ROM = os.path.join(ROOT, "rom", "ffta2.nds")
NAME = "ffta2-1screen"


def naive_bps(src, tgt):
    """A BPS that stores every changed 4 KB block as new data: what a careless tool makes."""
    out = bytearray(b"BPS1" + bps._num(len(src)) + bps._num(len(tgt)) + bps._num(0))
    t = 0
    for s, e in bps._changed(src, tgt):
        if t < s:
            out += bps._num(((s - t - 1) << 2) | bps.SOURCE_READ)
        out += bps._num(((e - s - 1) << 2) | bps.TARGET_READ) + tgt[s:e]
        t = e
    if t < len(tgt):
        out += bps._num(((len(tgt) - t - 1) << 2) | bps.SOURCE_READ)
    out += struct.pack("<II", zlib.crc32(src), zlib.crc32(tgt))
    return bytes(out + struct.pack("<I", zlib.crc32(out)))


def main():
    """Each run works in a folder of its own under build/ (removed afterwards), and patch.py
    compiles there too (FFTA2_BUILD_DIR), so releases or builds running at the same time in
    other sessions can't delete or overwrite each other's files."""
    os.makedirs(os.path.join(ROOT, "build"), exist_ok=True)
    work = tempfile.mkdtemp(prefix="release-", dir=os.path.join(ROOT, "build"))
    os.environ["FFTA2_BUILD_DIR"] = work            # inherited by the patch.py runs
    try:
        release(work)
    finally:
        shutil.rmtree(work, ignore_errors=True)


def release(work):
    out = os.path.abspath(sys.argv[1] if len(sys.argv) > 1 else os.path.join(ROOT, "dist", "release"))
    src = open(ROM, "rb").read()
    files, mods, failed = [], {}, []
    art = os.path.join(ROOT, "work", "map_art", "map_art.lz")
    if not os.path.exists(art):                 # ticket 36, ADR 0018: released builds have it
        sys.exit("RELEASE REFUSED:\n  no %s (the map of Ivalice's edges): make it with "
                 "scripts/map_art_pack.py" % os.path.relpath(art, ROOT))

    for preset in make_patcher.PRESETS:
        rom_out, js = os.path.join(work, preset + ".nds"), os.path.join(work, preset + ".json")
        subprocess.check_call([sys.executable, os.path.join(HERE, "patch.py"), ROM, rom_out,
                               "--display", preset, "--json", js])
        tgt = open(rom_out, "rb").read()
        if b"GUARD BUILD" in tgt:                # patch.py --guard (ticket 25) is for testing only
            failed.append("the %s build is a guard test build" % preset)
        mods[preset] = json.load(open(js))
        patch = bps.make(src, tgt)
        if bps.apply(src, patch) != tgt:
            failed.append("%s.bps does not rebuild the %s ROM" % (NAME, preset))
        st = bps.stats(patch)
        print("%s.bps: %d bytes; new bytes %d, moved from the ROM %d, runs %d"
              % (preset, len(patch), st["TargetRead"][1], st["SourceCopy"][1], st["TargetCopy"][1]))
        path = os.path.join(work, "%s-%s.bps" % (NAME, preset))
        open(path, "wb").write(patch)
        files.append(path)
        if preset == "deck":
            control = os.path.join(work, "naive-control.bps")
            open(control, "wb").write(naive_bps(src, tgt))
        os.remove(rom_out)

    patcher = os.path.join(work, NAME + "-patcher.py")
    make_patcher.write(mods, patcher)
    files.append(patcher)

    # --- the check: no stretch of the game's bytes in anything that ships --------
    for path in files:
        for label, data in check.payloads(path):
            hits = check.shared_stretches(src, data)
            print("check %s: %s" % (os.path.relpath(label, ROOT),
                  "%d stretch(es) of game bytes, longest %d" % (len(hits), max(n for _, n, _ in hits))
                  if hits else "no game bytes"))
            if hits:
                failed.append("%s holds game bytes" % os.path.relpath(label, ROOT))
    hits = check.shared_stretches(src, open(control, "rb").read())
    print("check on a naive patch (must be caught): %d stretch(es)" % len(hits))
    if not hits:
        failed.append("the check missed the game bytes in a naive patch: the check is broken")
    os.remove(control)

    if failed:
        sys.exit("RELEASE REFUSED:\n  " + "\n  ".join(failed))

    # written to a folder of this run's, then swapped in whole: OUTDIR never mixes two runs' files
    stage = os.path.join(work, "out")
    os.makedirs(stage)
    sums = []
    for path in files:
        dest = os.path.join(stage, os.path.basename(path))
        shutil.copyfile(path, dest)
        sums.append("%s  %s" % (hashlib.sha256(open(dest, "rb").read()).hexdigest(), os.path.basename(dest)))
    open(os.path.join(stage, "SHA256SUMS"), "w").write("\n".join(sums) + "\n")
    open(os.path.join(stage, "ROM.txt"), "w").write(
        "The .bps patches apply to this ROM only (Final Fantasy Tactics A2: Grimoire of the Rift, USA):\n"
        "  size   %d bytes\n  CRC32  %08X\n  SHA-1  %s\n"
        "For a ROM that other mods have changed, use %s-patcher.py instead.\n"
        % (len(src), zlib.crc32(src), hashlib.sha1(src).hexdigest(), NAME))
    os.makedirs(os.path.dirname(out), exist_ok=True)
    old = out + ".old-%d" % os.getpid()
    if os.path.isdir(out):
        os.rename(out, old)
    shutil.move(stage, out)
    shutil.rmtree(old, ignore_errors=True)
    print("release files in %s:" % os.path.relpath(out, ROOT))
    for name in sorted(os.listdir(out)):
        print("  %-30s %7d bytes" % (name, os.path.getsize(os.path.join(out, name))))


if __name__ == "__main__":
    main()
