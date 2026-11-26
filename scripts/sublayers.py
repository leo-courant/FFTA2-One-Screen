#!/usr/bin/env python3
"""Render each layer of the info screen (sub engine, mode 0) from a savestate's
video memory: sublayers.py STATE OUT.png   -> BG0..BG3, OBJ and palette-number
maps side by side, plus stats on stdout.  Reference for the hook's own copy."""
import os, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from emu import boot
from PIL import Image, ImageDraw
emu = boot(sys.argv[1], rom="build/ffta2-1screen.nds", frames=4)
m = emu.memory.unsigned
r16 = m.read_short; r32 = m.read_long
vram = bytes(m[0x06200000:0x06220000]); obj = bytes(m[0x06600000:0x06620000])
pal = [r16(0x05000400 + 2 * i) for i in range(256)]; opal = [r16(0x05000600 + 2 * i) for i in range(256)]
rgb = lambda c: ((c & 31) << 3, ((c >> 5) & 31) << 3, ((c >> 10) & 31) << 3)
sheet = Image.new("RGB", (6 * 260, 2 * 196), (255, 0, 255))
disp = r32(0x04001000)
info = []
for b in range(4):
    cnt = r16(0x04001008 + 2 * b)
    cb, sb = ((cnt >> 2) & 15) * 0x4000, ((cnt >> 8) & 31) * 0x800
    im = Image.new("RGB", (256, 192), (40, 0, 40)); pm = Image.new("RGB", (256, 192), (0, 0, 0)); px = im.load(); d = ImageDraw.Draw(pm)
    used = set(); pals = {}
    for ty in range(24):
        for tx in range(32):
            e = vram[sb + 2 * (ty * 32 + tx)] | vram[sb + 2 * (ty * 32 + tx) + 1] << 8
            t, hf, vf, p = e & 1023, e & 1024, e & 2048, e >> 12
            data = vram[cb + t * 32: cb + t * 32 + 32]
            if not any(data): continue
            used.add(t); pals[p] = pals.get(p, 0) + 1
            d.rectangle([tx * 8, ty * 8, tx * 8 + 7, ty * 8 + 7], fill=((p * 67) % 256, (p * 151) % 256, 255 - p * 15))
            for y in range(8):
                for x in range(8):
                    sx, sy = (7 - x if hf else x), (7 - y if vf else y)
                    v = (data[sy * 4 + sx // 2] >> (4 * (sx & 1))) & 15
                    if v: px[tx * 8 + x, ty * 8 + y] = rgb(pal[p * 16 + v])
    sheet.paste(im, (b * 260, 0)); sheet.paste(pm, (b * 260, 196))
    info.append("BG%d cnt=%04x prio=%d char=%d screen=%d: %d cells, %d distinct tiles, palettes %s" % (b, cnt, cnt & 3, (cnt >> 2) & 15, (cnt >> 8) & 31, sum(pals.values()), len(used), dict(sorted(pals.items()))))
im = Image.new("RGB", (256, 192), (40, 0, 40)); px = im.load(); n = 0; opals = {}
shift = 5 + ((disp >> 20) & 3)
SZ = {(0,0):(8,8),(0,1):(16,16),(0,2):(32,32),(0,3):(64,64),(1,0):(16,8),(1,1):(32,8),(1,2):(32,16),(1,3):(64,32),(2,0):(8,16),(2,1):(8,32),(2,2):(16,32),(2,3):(32,64)}
for i in range(127, -1, -1):
    a0, a1, a2 = (r16(0x07000400 + 8 * i + 2 * k) for k in range(3))
    if (a0 & 0x300) == 0x200: continue
    w, h = SZ.get(((a0 >> 14) & 3, (a1 >> 14) & 3), (8, 8))
    x0, y0 = a1 & 511, a0 & 255
    if x0 >= 256: x0 -= 512
    if y0 >= 192: y0 -= 256
    p = a2 >> 12; base = (a2 & 1023) << shift; bpp8 = a0 & 0x2000
    n += 1; opals[p] = opals.get(p, 0) + 1
    for y in range(h):
        for x in range(w):
            sx = w - 1 - x if a1 & 0x1000 else x; sy = h - 1 - y if a1 & 0x2000 else y
            tile = (sy // 8) * (w // 8) + sx // 8
            if bpp8: v = obj[(base + tile * 64 + (sy & 7) * 8 + (sx & 7)) & 0x1FFFF]; c = opal[v]
            else:
                v = (obj[(base + tile * 32 + (sy & 7) * 4 + (sx & 7) // 2) & 0x1FFFF] >> (4 * (sx & 1))) & 15; c = opal[p * 16 + v]
            if v and 0 <= x0 + x < 256 and 0 <= y0 + y < 192: px[x0 + x, y0 + y] = rgb(c)
sheet.paste(im, (4 * 260, 0))
sheet.paste(emu.screenshot().convert("RGB").crop((0, 0, 256, 192)), (5 * 260, 0))
sheet.save(sys.argv[2])
sys.stderr.write("LAY " + "\nLAY ".join(info) + "\nLAY OBJ: %d sprites, palettes %s, objshift %d\n" % (n, dict(sorted(opals.items())), shift))
