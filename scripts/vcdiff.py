#!/usr/bin/env python3
"""Apply an xdelta3 / VCDIFF patch (RFC 3284) without the xdelta tool: used to put other
mods on a test ROM (ticket 27).  Handles the default code table and xdelta3's Adler-32
window checksum; refuses secondary compression and custom code tables.

usage: vcdiff.py SOURCE PATCH OUT
"""
import sys
import zlib


def _table():
    """The default instruction code table (RFC 3284, section 5.6): (type1, size1, mode1,
    type2, size2, mode2) per opcode; types 0 NOOP, 1 ADD, 2 RUN, 3 COPY."""
    t = [(2, 0, 0, 0, 0, 0)]
    t += [(1, s, 0, 0, 0, 0) for s in range(18)]
    for m in range(9):
        t += [(3, 0, m, 0, 0, 0)] + [(3, s, m, 0, 0, 0) for s in range(4, 19)]
    for m in range(6):
        t += [(1, a, 0, 3, c, m) for a in range(1, 5) for c in range(4, 7)]
    for m in range(6, 9):
        t += [(1, a, 0, 3, 4, m) for a in range(1, 5)]
    t += [(3, 4, m, 1, 1, 0) for m in range(9)]
    assert len(t) == 256
    return t


TABLE = _table()


class Reader:
    def __init__(self, data, pos=0):
        self.d, self.p = data, pos

    def byte(self):
        b = self.d[self.p]
        self.p += 1
        return b

    def int(self):
        v = 0
        while True:
            b = self.byte()
            v = (v << 7) | (b & 0x7F)
            if not b & 0x80:
                return v

    def take(self, n):
        s = self.d[self.p:self.p + n]
        self.p += n
        return s


def apply(source, patch):
    r = Reader(patch)
    if r.take(3) != b"\xd6\xc3\xc4" or r.byte() != 0:
        raise ValueError("not a VCDIFF patch")
    hdr = r.byte()
    if hdr & 1:
        raise ValueError("secondary compression is not supported")
    if hdr & 2:
        raise ValueError("custom code tables are not supported")
    if hdr & 4:
        r.take(r.int())                     # application header (xdelta3 puts file names there)
    out = bytearray()
    while r.p < len(patch):
        win = r.byte()
        if win & 3 == 3:
            raise ValueError("bad window indicator")
        seg = b""
        if win & 3:
            size, pos = r.int(), r.int()
            seg = source[pos:pos + size] if win & 1 else bytes(out[pos:pos + size])
        r.int()                             # length of the delta encoding
        target_len = r.int()
        if r.byte():
            raise ValueError("compressed sections are not supported")
        data_len, inst_len, addr_len = r.int(), r.int(), r.int()
        cksum = None
        if win & 4:                         # xdelta3: Adler-32 of the target window
            cksum = int.from_bytes(r.take(4), "big")
        data, inst, addrs = Reader(r.take(data_len)), Reader(r.take(inst_len)), Reader(r.take(addr_len))
        near, same = [0] * 4, [0] * (3 * 256)
        nxt = 0
        t = bytearray()

        def copy_addr(mode, here):
            nonlocal nxt
            if mode == 0:
                a = addrs.int()
            elif mode == 1:
                a = here - addrs.int()
            elif mode < 6:
                a = near[mode - 2] + addrs.int()
            else:
                a = same[(mode - 6) * 256 + addrs.byte()]
            near[nxt] = a
            nxt = (nxt + 1) % 4
            same[a % (3 * 256)] = a
            return a

        while inst.p < len(inst.d):
            code = TABLE[inst.byte()]
            for typ, size, mode in (code[0:3], code[3:6]):
                if typ == 0:
                    continue
                if size == 0:
                    size = inst.int()
                if typ == 1:
                    t += data.take(size)
                elif typ == 2:
                    t += bytes([data.byte()]) * size
                else:
                    a = copy_addr(mode, len(seg) + len(t))
                    if a + size <= len(seg):
                        t += seg[a:a + size]
                    elif a >= len(seg) and a - len(seg) + size <= len(t):
                        t += t[a - len(seg):a - len(seg) + size]
                    else:
                        for i in range(size):       # overlaps the target being built
                            k = a + i
                            t.append(seg[k] if k < len(seg) else t[k - len(seg)])
        if len(t) != target_len:
            raise ValueError("window decoded to %d bytes, expected %d" % (len(t), target_len))
        if cksum is not None and zlib.adler32(bytes(t)) != cksum:
            raise ValueError("window checksum mismatch: wrong source file?")
        out += t
    return bytes(out)


if __name__ == "__main__":
    if len(sys.argv) != 4:
        sys.exit(__doc__)
    src, pat, dst = sys.argv[1:]
    open(dst, "wb").write(apply(open(src, "rb").read(), open(pat, "rb").read()))
    print("wrote", dst)
