#!/usr/bin/env python3
"""BPS patches (ticket 21): make one that holds no bytes of the source file, and apply one.

usage: bps.py make SOURCE TARGET OUT.bps
       bps.py apply SOURCE PATCH.bps OUT

BPS (byuu's format, read by Flips, Rom Patcher JS, beat and others) rebuilds the target
from four actions: SourceRead (the source's byte at the same place), TargetRead (new bytes
stored in the patch), SourceCopy (bytes from anywhere in the source) and TargetCopy (bytes
already written, which also makes runs).  The mod moves part of the game to the end of
the ROM (ADR 0001, 0011), so a patch that stored every changed byte would carry game data.
`make` stores as new bytes only what the source does not have: moved stretches become
SourceCopy, runs of one value become TargetCopy.  Standard library only.
"""
import struct
import sys
import zlib

SOURCE_READ, TARGET_READ, SOURCE_COPY, TARGET_COPY = range(4)
WINDOW = 32          # source stretches are indexed every WINDOW bytes, by their next WINDOW bytes
MARGIN = 1 << 20     # how far around the changed parts the source is searched for moved bytes
MIN_RUN = 8          # a run of one byte value at least this long becomes a TargetCopy


def _num(n):
    out = bytearray()
    while True:
        x = n & 0x7F
        n >>= 7
        if n == 0:
            out.append(0x80 | x)
            return bytes(out)
        out.append(x)
        n -= 1


def _signed(n):
    return _num((abs(n) << 1) | (n < 0))


def _changed(src, tgt):
    """(start, end) stretches of the target that differ from the source at the same place."""
    out, step = [], 1 << 12
    n, i = len(tgt), 0
    while i < n:
        if tgt[i:i + step] == src[i:i + step]:
            i += step
            continue
        j = min(i + step, n)
        if not out or out[-1][1] < i:
            out.append([i, j])
        else:
            out[-1][1] = j
        i = j
    return out


def make(src, tgt):
    """BPS patch turning `src` into `tgt`; stores as new bytes only what `src` lacks."""
    src, tgt = bytes(src), bytes(tgt)
    spans = _changed(src, tgt)
    index = {}                                  # WINDOW bytes of the source -> where they start
    for s, e in spans:
        lo, hi = max(0, s - MARGIN), min(len(src), e + MARGIN)
        for p in range(lo - lo % WINDOW, hi - WINDOW + 1, WINDOW):
            w = src[p:p + WINDOW]
            if w.count(w[:1]) != WINDOW:        # runs are handled as runs, not looked up
                index.setdefault(w, p)

    out = bytearray(b"BPS1" + _num(len(src)) + _num(len(tgt)) + _num(0))
    state = {"src_rel": 0, "tgt_rel": 0}
    lit = bytearray()

    def flush():
        if lit:
            out.extend(_num(((len(lit) - 1) << 2) | TARGET_READ) + lit)
            lit.clear()

    def source_read(n):
        flush()
        out.extend(_num(((n - 1) << 2) | SOURCE_READ))

    def source_copy(at, n):
        flush()
        out.extend(_num(((n - 1) << 2) | SOURCE_COPY) + _signed(at - state["src_rel"]))
        state["src_rel"] = at + n

    def target_copy(at, n):
        flush()
        out.extend(_num(((n - 1) << 2) | TARGET_COPY) + _signed(at - state["tgt_rel"]))
        state["tgt_rel"] = at + n

    def same_len(a, ai, b, bi, limit):
        """how many bytes a[ai:] and b[bi:] share, up to limit (compared in blocks)."""
        n, blk = 0, 4096
        while n < limit:
            k = min(blk, limit - n)
            if a[ai + n:ai + n + k] == b[bi + n:bi + n + k]:
                n += k
            else:
                while n < limit and a[ai + n] == b[bi + n]:
                    n += 1
                break
        return n

    t, n = 0, len(tgt)
    for s, e in spans + [[n, n]]:
        if t < s:                               # unchanged up to the next changed stretch
            source_read(s - t)
            t = s
        while t < e:
            if t < len(src) and src[t] == tgt[t]:   # the source's own bytes in place
                k = same_len(src, t, tgt, t, min(len(src), n) - t)
                if k >= 2:
                    source_read(k)
                    t += k
                    continue
            run = 1
            if t + MIN_RUN <= e and tgt[t:t + MIN_RUN].count(tgt[t:t + 1]) == MIN_RUN:
                run = same_len(tgt, t, tgt, t + 1, e - t - 1) + 1
            if run >= MIN_RUN:
                if t < len(src) and src[t] == tgt[t]:
                    k = same_len(src, t, tgt, t, min(len(src), n) - t)
                    if k >= MIN_RUN:            # run of the source's own value in place
                        source_read(k)
                        t += k
                        continue
                lit.append(tgt[t])              # one byte, then copy it forward
                target_copy(t, run - 1)
                t += run
                continue
            hit = index.get(tgt[t:t + WINDOW])
            if hit is None:
                lit.append(tgt[t])
                t += 1
                continue
            back = 0                            # take back bytes stored as new just before
            while back < len(lit) and hit - back > 0 and src[hit - back - 1] == lit[-1 - back]:
                back += 1
            if back:
                del lit[len(lit) - back:]
            k = back + same_len(src, hit, tgt, t, min(len(src) - hit, n - t))
            if hit - back == t - back:
                source_read(k)
            else:
                source_copy(hit - back, k)
            t += k - back
        # a stretch may run past its end: carry on from wherever t landed
    flush()
    out.extend(struct.pack("<II", zlib.crc32(src), zlib.crc32(tgt)))
    out.extend(struct.pack("<I", zlib.crc32(out)))
    return bytes(out)


def _read_num(p, i):
    n, shift = 0, 1
    while True:
        x = p[i]
        i += 1
        n += (x & 0x7F) * shift
        if x & 0x80:
            return n, i
        shift <<= 7
        n += shift


def apply(src, patch):
    """Apply a BPS patch; raises ValueError when the patch or the source doesn't match."""
    p = bytes(patch)
    if p[:4] != b"BPS1":
        raise ValueError("not a BPS patch")
    if zlib.crc32(p[:-4]) != struct.unpack_from("<I", p, len(p) - 4)[0]:
        raise ValueError("the patch file is damaged (checksum)")
    src_crc, tgt_crc = struct.unpack_from("<II", p, len(p) - 12)
    if zlib.crc32(src) != src_crc:
        raise ValueError("this patch is for a different source file (checksum)")
    i = 4
    ssize, i = _read_num(p, i)
    tsize, i = _read_num(p, i)
    msize, i = _read_num(p, i)
    i += msize
    if len(src) != ssize:
        raise ValueError("source is %d bytes, the patch expects %d" % (len(src), ssize))
    out = bytearray()
    src_rel = tgt_rel = 0
    end = len(p) - 12
    while i < end:
        d, i = _read_num(p, i)
        kind, n = d & 3, (d >> 2) + 1
        if kind == SOURCE_READ:
            out += src[len(out):len(out) + n]
        elif kind == TARGET_READ:
            out += p[i:i + n]
            i += n
        else:
            o, i = _read_num(p, i)
            o = -(o >> 1) if o & 1 else o >> 1
            if kind == SOURCE_COPY:
                src_rel += o
                out += src[src_rel:src_rel + n]
                src_rel += n
            else:
                tgt_rel += o
                for _ in range(n):              # may overlap what it writes (runs)
                    out.append(out[tgt_rel])
                    tgt_rel += 1
    if len(out) != tsize or zlib.crc32(out) != tgt_crc:
        raise ValueError("the result doesn't match the patch's target (size or checksum)")
    return bytes(out)


def stats(patch):
    """{action: (count, bytes)} of a BPS patch, for reports."""
    p, i = bytes(patch), 4
    for _ in range(2):
        _, i = _read_num(p, i)
    m, i = _read_num(p, i)
    i += m
    st = {k: [0, 0] for k in ("SourceRead", "TargetRead", "SourceCopy", "TargetCopy")}
    names = list(st)
    while i < len(p) - 12:
        d, i = _read_num(p, i)
        kind, n = d & 3, (d >> 2) + 1
        st[names[kind]][0] += 1
        st[names[kind]][1] += n
        if kind == TARGET_READ:
            i += n
        elif kind != SOURCE_READ:
            _, i = _read_num(p, i)
    return st


def main(argv):
    if len(argv) != 4 or argv[0] not in ("make", "apply"):
        sys.exit(__doc__)
    a, b = open(argv[1], "rb").read(), open(argv[2], "rb").read()
    out = make(a, b) if argv[0] == "make" else apply(a, b)
    open(argv[3], "wb").write(out)
    print("wrote %s (%d bytes)" % (argv[3], len(out)))


if __name__ == "__main__":
    main(sys.argv[1:])
