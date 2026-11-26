#!/usr/bin/env python3
"""Build the patcher players run (ticket 27): scripts/modpatch.py with the mod description
of every display preset built in, as one Python file that needs nothing but Python 3.

usage: make_patcher.py [OUT.py]        (default dist/ffta2-1screen-patcher.py; about 30 s)

It compiles each preset with scripts/patch.py (which needs the clean ROM at rom/ffta2.nds
to check the result applies), then checks the patcher for bytes of the game with
scripts/check_no_game_bytes.py.  The file holds the mod's code and hashes only.
"""
import json
import os
import re
import subprocess
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
PRESETS = ["deck", "16x9", "4x3"]
MARK = re.compile(r"^MODS = \{\}.*$", re.M)   # the whole line, comment included


def write(mods, out):
    """Write the patcher: scripts/modpatch.py with `mods` ({preset: description}) built in."""
    src = open(os.path.join(HERE, "modpatch.py")).read()
    assert len(MARK.findall(src)) == 1
    line = "MODS = json.loads(%r)" % json.dumps(mods, separators=(",", ":"))
    src = MARK.sub(lambda m: line, src)
    open(out, "w").write(src)
    print("wrote %s (%d KB)" % (out, os.path.getsize(out) // 1024))


def main():
    out = sys.argv[1] if len(sys.argv) > 1 else os.path.join(ROOT, "dist", "ffta2-1screen-patcher.py")
    tmp = os.path.join(ROOT, "build", "patcher")
    os.makedirs(tmp, exist_ok=True)
    os.makedirs(os.path.dirname(os.path.abspath(out)), exist_ok=True)
    mods = {}
    for p in PRESETS:
        js, rom = os.path.join(tmp, p + ".json"), os.path.join(tmp, p + ".nds")
        subprocess.check_call([sys.executable, os.path.join(HERE, "patch.py"), os.path.join(ROOT, "rom", "ffta2.nds"),
                               rom, "--display", p, "--json", js])
        os.remove(rom)
        mods[p] = json.load(open(js))
    write(mods, out)
    subprocess.check_call([sys.executable, os.path.join(HERE, "check_no_game_bytes.py"),
                           os.path.join(ROOT, "rom", "ffta2.nds"), out])


if __name__ == "__main__":
    main()
