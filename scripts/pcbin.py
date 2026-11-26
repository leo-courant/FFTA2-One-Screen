#!/usr/bin/env python3
"""Read files from the game's archive (master/pc.bin) by path, through its hash index
(master/pc.idx), the way the game does (FUN_0201FA3C, ticket 29).

usage: pcbin.py PATH...            prints offset, size and unpacked size of each path
       pcbin.py --dump PATH OUT    writes the file's bytes (as stored) to OUT
As a module: lookup(path) -> (offset, size, unpacked size) or None; read(path) -> bytes.
Index: u32 at +0 = slot count (a power of two); slot = hash(path) & (count-1), 9-byte
records from +8. hash: h = first char, then h = h*37 + c. A record with bit 0 clear is
the file; with bit 0 set it points to a list of colliding paths, each told apart by
(char, position) pairs. Unpacked size 0 = stored as is."""
import os, struct, sys
ROOT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "unpacked", "files", "master")
_idx = _bin = None


def _load():
    global _idx, _bin
    if _idx is None:
        _idx = open(os.path.join(ROOT, "pc.idx"), "rb").read()
        _bin = open(os.path.join(ROOT, "pc.bin"), "rb")


def h37(path):
    b = path.encode()
    h = b[0]
    for c in b[1:]:
        h = (h * 37 + (c if c < 128 else c - 256)) & 0xFFFFFFFF
    return h


def lookup(path):
    _load()
    n = struct.unpack_from("<I", _idx, 0)[0]
    w0, w1 = struct.unpack_from("<II", _idx, 8 + (h37(path) & (n - 1)) * 9)
    b8 = _idx[8 + (h37(path) & (n - 1)) * 9 + 8]
    size = ((w1 & 0x1FFFF) * 0x40 + (w0 >> 26)) * 4
    if not w0 & 1:
        return ((w0 & 0x3FFFFFF) >> 1) * 4, size, b8 * 4
    # collision list
    usize = b8
    base = (w0 & 0x3FFFFFF) >> 1
    count = _idx[base]
    p = base
    pb = path.encode()
    for i in range(count):
        q = p + (5 if i == 0 else 0xD)
        ok = True
        while _idx[q]:
            ch, pos = _idx[q], _idx[q + 1]
            if pos >= len(pb) or pb[pos] != ch:
                ok = False
            q += 2
        if ok:
            off = struct.unpack_from("<I", _idx, p + 1)[0] * 4
            if i:
                size = struct.unpack_from("<I", _idx, p + 5)[0] * 4
                usize = struct.unpack_from("<I", _idx, p + 9)[0]
            return off, size, (usize & 0x7FFFFF) * 4
        p = q
    return None


def read(path):
    r = lookup(path)
    if not r:
        return None
    _bin.seek(r[0])
    return _bin.read(r[1])


if __name__ == "__main__":
    if sys.argv[1] == "--dump":
        open(sys.argv[3], "wb").write(read(sys.argv[2]))
    else:
        for p in sys.argv[1:]:
            print(p, lookup(p))
