#!/usr/bin/env python3
"""Fail if a file meant for publishing holds a stretch of the original game's bytes
(publishing rules; tickets 21 and 27).

usage: check_no_game_bytes.py ROM FILE...        (exit 1 if any stretch is found; ~20 s)

Each FILE is checked as it is, and so is what it carries encoded: the mod's code and
new bytes inside a mod description (.json) or a patcher with built-in descriptions
(base64 and hex there would hide game bytes from a plain search).  A stretch counts when
it is at least MIN bytes long and not mostly one byte value: runs of 00, FF or spaces are
everywhere (indentation in a text file matches padding in the ROM), so a stretch with
fewer than 4 different byte values, or one value filling 3/4 of it, is not counted.
"""
import ast
import base64
import json
import re
import sys

import numpy as np

MIN = 16


def payloads(path):
    """(label, bytes) for the file and everything it carries encoded."""
    raw = open(path, "rb").read()
    out = [(path, raw)]
    text = raw.decode("utf-8", "replace")
    mods = []
    try:
        mods = [json.loads(text)]
    except ValueError:
        m = re.search(r"^MODS = json\.loads\((.*)\)\s*$", text, re.M)
        if m:
            mods = list(json.loads(ast.literal_eval(m.group(1))).values())
    for mod in mods:
        if isinstance(mod, dict) and "blob" in mod:
            tag = "%s [%s]" % (path, mod.get("preset", "?"))
            out.append((tag + " code", base64.b64decode(mod["blob"])))
            out.append((tag + " edits", b"".join(bytes.fromhex(e["data"]) for e in mod.get("edits", []))))
    return out


def trivial(piece):
    counts = sorted((piece.count(bytes([b])) for b in set(piece)), reverse=True)
    return len(counts) < 4 or counts[0] * 4 >= len(piece) * 3


def shared_stretches(rom, data, min_len=MIN):
    """Stretches of `data` (offset, length, rom offset) of min_len+ bytes also found in `rom`."""
    keys = {}
    for i in range(len(data) - 7):
        w = data[i:i + 8]
        if w.count(w[:1]) != 8:
            keys.setdefault(int.from_bytes(w, "little"), []).append(i)
    if not keys:
        return []
    karr = np.array(sorted(keys), dtype="<u8")
    found = {}
    grown = {}                                     # rom - data offset -> stretches already grown
    for a in range(8):
        arr = np.frombuffer(rom, dtype="<u8", offset=a, count=(len(rom) - a) // 8)
        for j in np.nonzero(np.isin(arr, karr))[0]:
            r = a + 8 * int(j)
            for i in keys[int(arr[j])]:
                if any(s <= i < e for s, e in grown.get(r - i, ())):
                    continue                       # inside a match already grown: same stretch
                s, rs = i, r                       # grow the match both ways
                while s > 0 and rs > 0 and data[s - 1] == rom[rs - 1]:
                    s, rs = s - 1, rs - 1
                n = 0
                while s + n < len(data) and rs + n < len(rom) and data[s + n] == rom[rs + n]:
                    n += 1
                if n > 8:
                    grown.setdefault(rs - s, []).append((s, s + n))
                if n >= min_len and not trivial(data[s:s + n]) and found.get(s, (0,))[0] < n:
                    found[s] = (n, rs)
    return sorted((s, n, rs) for s, (n, rs) in found.items())


def main():
    if len(sys.argv) < 3:
        sys.exit(__doc__)
    rom = open(sys.argv[1], "rb").read()
    bad = 0
    for path in sys.argv[2:]:
        for label, data in payloads(path):
            hits = shared_stretches(rom, data)
            longest = max((n for _, n, _ in hits), default=0)
            print("%s: %d bytes, %s" % (label, len(data),
                  "no game bytes (no shared stretch of %d+ bytes)" % MIN if not hits else
                  "%d stretch(es) of game bytes, longest %d" % (len(hits), longest)))
            for s, n, rs in hits[:10]:
                print("    at %#x, %d bytes = ROM %#x" % (s, n, rs))
            bad += len(hits)
    sys.exit(1 if bad else 0)


if __name__ == "__main__":
    main()
