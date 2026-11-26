"""usage: map_art_dump.py [STATE] [OUTDIR]

Step 1 of the map of Ivalice's extended edges (ticket 36, ADR 0018): take the
map's picture from a test state on that map (default states/late/l_ivalice.dst)
and write OUTDIR (default work/map_art) map_full.png, the whole 408x300
picture as the game draws it, and map_tex.png, the 16-colour texture it comes
from (its palette is what the extension is brought back to).

The picture is a 512x256 texture at 0 in texture bank A with its palette at
0x3E20 of bank G: a 408x256 piece, and the bottom 44 rows stored as four strips
beside it (gxtrace on the map; palette base 0x34E).  Game data: the output stays in work/.
Next: map_art_outpaint.py.
"""
import os
import sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from emu import boot
from PIL import Image

STATE = sys.argv[1] if len(sys.argv) > 1 else "states/late/l_ivalice.dst"
OUT = sys.argv[2] if len(sys.argv) > 2 else "work/map_art"
# bottom strips: picture x, texture x, texture y, width (44 rows each)
STRIPS = ((0, 408, 0, 104), (104, 408, 44, 104), (206, 408, 104, 104), (310, 408, 148, 98))

os.makedirs(OUT, exist_ok=True)
emu = boot(STATE, rom=os.environ.get("ROM", "build/ffta2-1screen.nds"), frames=120)   # past any fade-in
m = emu.memory
cnt = [m.unsigned[0x04000240 + i] for i in range(7)]
m.write_byte(0x04000240, 0x80); m.write_byte(0x04000246, 0x80)     # banks A and G to the CPU
raw = bytes(m.unsigned[0x06800000:0x06800000 + 512 * 256 // 2])     # 4 bits a texel, low nibble left
tex = bytes(n for b in raw for n in (b & 15, b >> 4))
pal = bytes(m.unsigned[0x06894000 + 0x34E0:0x06894000 + 0x34E0 + 32])
m.write_byte(0x04000240, cnt[0]); m.write_byte(0x04000246, cnt[6])
rgb = []
for i in range(16):
    c = pal[2 * i] | pal[2 * i + 1] << 8
    rgb += [(c & 31) * 255 // 31, (c >> 5 & 31) * 255 // 31, (c >> 10 & 31) * 255 // 31]
t = Image.frombytes("P", (512, 256), tex)
t.putpalette(rgb)
t.save(os.path.join(OUT, "map_tex.png"))
full = Image.new("P", (408, 300))
full.putpalette(rgb)
full.paste(t.crop((0, 0, 408, 256)), (0, 0))
for px, tx, ty, w in STRIPS:
    full.paste(t.crop((tx, ty, tx + w, ty + 44)), (px, 256))
full.convert("RGB").save(os.path.join(OUT, "map_full.png"))
print("wrote %s/map_full.png and map_tex.png" % OUT)
