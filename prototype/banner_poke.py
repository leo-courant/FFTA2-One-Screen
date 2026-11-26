#!/usr/bin/env python3
"""PROTOTYPE - throwaway. Emulate the banner patch by poking video memory from
Python every frame, to check the look and whether the game fights back."""
import sys
sys.path.insert(0, "scripts")
from emu import boot
from desmume.controls import Keys, keymask
emu = boot("states/intro3.dst"); m = emu.memory.unsigned
r16, r32 = m.read_short, m.read_long
def w16(a, v): emu.memory.write_short(a, v & 0xFFFF)
def w32(a, v): emu.memory.write_long(a, v & 0xFFFFFFFF)
SUB_TXT, SUB_FRM = 0x0620C000, 0x06204000
SUB_TMAP, SUB_FMAP = 0x06200800, 0x06200000
CH, MAP = 0x06008000, 0x0600F800

def banner():
    # palettes: main rows 12,13 = frame pals 13,14 ; rows 14,15 = text pal + bar colour
    for i in range(16):
        w16(0x05000000 + 2 * (12 * 16 + i), r16(0x05000400 + 2 * (13 * 16 + i)))
        w16(0x05000000 + 2 * (13 * 16 + i), r16(0x05000400 + 2 * (14 * 16 + i)))
        c = r16(0x05000400 + 2 * i)
        w16(0x05000000 + 2 * (14 * 16 + i), c)
        w16(0x05000000 + 2 * (15 * 16 + i), c)
    w16(0x05000000 + 2 * (14 * 16 + 4), r16(0x05000400 + 2 * (14 * 16 + 7)))   # red
    w16(0x05000000 + 2 * (15 * 16 + 4), r16(0x05000400 + 2 * (13 * 16 + 14)))  # parchment
    # text tiles 0..127 with transparent -> index 4
    for o in range(0, 128 * 32, 4):
        w = r32(SUB_TXT + o)
        z = ~(w | w >> 1 | w >> 2 | w >> 3) & 0x11111111
        w32(CH + o, w | z * 4)
    for o in range(0, 256 * 32, 4):
        w32(CH + 0x2000 + o, r32(SUB_FRM + o))
    def cell(r, c, v): w16(MAP + 2 * (r * 32 + c), v)
    def frm(r, c): 
        e = r16(SUB_FMAP + 2 * (r * 32 + c)); p = e >> 12
        return ((12 if p == 13 else 13) << 12) | (256 + (e & 0x3FF))
    def txt(r, c, pal): return (pal << 12) | (r16(SUB_TMAP + 2 * (r * 32 + c)) & 0x3FF)
    for r in range(2):
        for c in range(3): cell(r, c, frm(r, c))
        for c in range(3, 16): cell(r, c, txt(r, c, 14))
        for c in range(3): cell(r, 16 + c, frm(3 + r, 2 + c))
        for c in range(13): cell(r, 19 + c, txt(3 + r, 5 + c, 15))
    for r in range(2, 32):
        for c in range(32): cell(r, c, 0x0200)
    w16(0x0400000A, 0x1F08)

import os
os.makedirs("shots/poke", exist_ok=True)
log = []
def run(n, key=None):
    if key: emu.input.keypad_add_key(keymask(key))
    for _ in range(n):
        emu.cycle(False)
        log.append((r16(0x0400000A), r32(0x04000000)))
        banner()
    if key: emu.input.keypad_rm_key(keymask(key))
banner(); run(3); emu.screenshot().save("shots/poke/p1.png")
run(4, Keys.KEY_A); run(60); emu.screenshot().save("shots/poke/p2.png")
run(4, Keys.KEY_DOWN); run(30); run(4, Keys.KEY_A); run(120); emu.screenshot().save("shots/poke/p3.png")
print("map row0", ["%04x" % r16(MAP+2*c) for c in range(8)], "tile15 %08x" % r32(CH+0x15*32+8), "pal14", ["%04x" % r16(0x05000000+2*(224+i)) for i in range(6)], "BLD %04x %04x" % (r16(0x04000050), r16(0x04000052)), "WIN %04x %04x" % (r16(0x04000048), r16(0x0400004a)))
print("BG1CNT/DISPCNT seen before re-poke:", sorted(set(log)))
