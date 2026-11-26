#!/usr/bin/env python3
"""Turn a downloaded DS save into the raw 64 KB save the game wants (ticket 24).

    python3 -I scripts/import_save.py DOWNLOAD OUT.sav

DOWNLOAD may be a raw save, an Action Replay .duc (500-byte header), a DeSmuME
.dsv (footer starting "|<--Snip"), or a .zip holding one of those. Only the save
bytes are kept; nothing in the download is run. Stdlib only.
"""
import sys
import zipfile

SIZE = 0x10000
DUC_HEADER = 500
DSV_MARK = b"|<--Snip above here to create a raw sav by excluding this DeSmuME savedata footer:"


def from_zip(path):
    with zipfile.ZipFile(path) as z:
        names = [n for n in z.namelist() if not n.endswith("/")]
        saves = [n for n in names if n.lower().rsplit(".", 1)[-1] in ("sav", "duc", "dsv", "bin")]
        if len(saves) != 1:
            sys.exit(f"zip holds {names}; expected exactly one save")
        print(f"zip member: {saves[0]}", file=sys.stderr)
        return saves[0].lower(), z.read(saves[0])


def raw_save(name, data):
    if DSV_MARK in data:
        data = data[: data.index(DSV_MARK)]
        kind = "DeSmuME .dsv"
    elif name.endswith(".duc") or len(data) == SIZE + DUC_HEADER:
        data = data[DUC_HEADER:]
        kind = "Action Replay .duc"
    else:
        kind = "raw"
    if len(data) < SIZE:
        sys.exit(f"{kind}: {len(data)} save bytes, expected {SIZE}")
    if len(data) > SIZE and any(data[SIZE:]) and set(data[SIZE:]) != {0xFF}:
        sys.exit(f"{kind}: {len(data)} bytes and the tail past 64 KB is not padding")
    print(f"{kind}: kept {SIZE} bytes", file=sys.stderr)
    return data[:SIZE]


def main():
    if len(sys.argv) != 3:
        sys.exit(__doc__)
    src, out = sys.argv[1], sys.argv[2]
    if zipfile.is_zipfile(src):
        name, data = from_zip(src)
    else:
        name, data = src.lower(), open(src, "rb").read()
    with open(out, "wb") as f:
        f.write(raw_save(name, data))


if __name__ == "__main__":
    main()
