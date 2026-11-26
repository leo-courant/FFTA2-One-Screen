"""usage: map_art_pack.py [MAP_EXT.png] [OUTDIR]

Step 3 of the map of Ivalice's extended edges (ticket 36, ADR 0018): cut the
bands the wide view can show beyond the map's picture out of the extended
picture (map_ext.png from map_art_outpaint.py: 16 colours, the game's picture
at offset 64, 32; default work/map_art/map_ext.png) and pack them into one
256x128 16-colour texture (DS 4 bits a texel, low nibble = left texel), as
the piece table in src/map_art.c says.  Writes OUTDIR (default work/map_art)
map_art.lz, the texture compressed (LZ as the DS BIOS has it), which
patch.py builds in when it is there.  The art is derived from the game's
picture: it stays in work/ and only ever leaves inside a release's patches.
"""
import os
import re
import sys
from PIL import Image

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
PX, PY = 64, 32
W, H = 256, 128


def pieces():
    src = open(os.path.join(ROOT, "src", "map_art.c")).read()
    body = src[src.index("/* PIECES BEGIN */"):src.index("/* PIECES END */")]
    rows = [tuple(int(v) for v in m.groups()) for m in
            re.finditer(r"\{\s*(-?\d+),\s*(-?\d+),\s*(-?\d+),\s*(-?\d+),\s*(-?\d+),\s*(-?\d+)\s*\}", body)]
    n = int(re.search(r"#define MAP_ART_PIECES (\d+)", src).group(1))
    assert len(rows) == n, "src/map_art.c: %d pieces in the table, MAP_ART_PIECES says %d" % (len(rows), n)
    return rows


def lz_pack(data):
    """LZ10 (DS BIOS): greedy longest match, 3..18 bytes, up to 4096 back."""
    out = bytearray(struct_header(len(data)))
    i, heads = 0, {}
    while i < len(data):
        flag_at = len(out)
        out.append(0)
        for bit in range(8):
            if i >= len(data):
                break
            best, dist = 0, 0
            for j in reversed(heads.get(data[i:i + 3], [])):
                if i - j > 4096:
                    break
                n = 0
                while n < 18 and i + n < len(data) and data[j + n] == data[i + n]:
                    n += 1
                if n > best:
                    best, dist = n, i - j
                    if n == 18:
                        break
            step = best if best >= 3 else 1
            if best >= 3:
                out[flag_at] |= 0x80 >> bit
                out += bytes(((best - 3) << 4 | (dist - 1) >> 8, (dist - 1) & 0xFF))
            else:
                out.append(data[i])
            for k in range(i, i + step):
                heads.setdefault(data[k:k + 3], []).append(k)
            i += step
    out += bytes(-len(out) % 4)
    return bytes(out)


def struct_header(n):
    return (n << 8 | 0x10).to_bytes(4, "little")


def lz_unpack(s):
    n = int.from_bytes(s[:4], "little") >> 8
    d, i = bytearray(), 4
    while len(d) < n:
        flags = s[i]; i += 1
        for bit in range(8):
            if len(d) >= n:
                break
            if flags & 0x80 >> bit:
                a, b = s[i], s[i + 1]; i += 2
                at = len(d) - ((a & 15) << 8 | b) - 1
                for k in range((a >> 4) + 3):
                    d.append(d[at + k])
            else:
                d.append(s[i]); i += 1
    return bytes(d[:n])


def main():
    ext_path = sys.argv[1] if len(sys.argv) > 1 else os.path.join(ROOT, "work", "map_art", "map_ext.png")
    out = sys.argv[2] if len(sys.argv) > 2 else os.path.join(ROOT, "work", "map_art")
    ext = Image.open(ext_path)
    assert ext.mode == "P", "%s: not a 16-colour (palette) picture" % ext_path
    px = ext.load()
    atlas = [[None] * W for _ in range(H)]
    for x0, y0, x1, y1, ax, ay in pieces():
        assert 0 <= ax and ax + x1 - x0 <= W and 0 <= ay and ay + y1 - y0 <= H, "piece outside the texture"
        for y in range(y0, y1):
            for x in range(x0, x1):
                assert atlas[ay + y - y0][ax + x - x0] is None, "pieces overlap in the texture at %d,%d" % (ax + x - x0, ay + y - y0)
                atlas[ay + y - y0][ax + x - x0] = px[PX + x, PY + y] & 15
    data = bytearray()
    for row in atlas:
        row = [v or 0 for v in row]
        for x in range(0, W, 2):
            data.append(row[x] | row[x + 1] << 4)
    packed = lz_pack(bytes(data))
    assert lz_unpack(packed) == bytes(data)
    os.makedirs(out, exist_ok=True)
    open(os.path.join(out, "map_art.lz"), "wb").write(packed)
    print("wrote %s/map_art.lz (%d bytes, %d unpacked)" % (out, len(packed), len(data)))


if __name__ == "__main__":
    main()
