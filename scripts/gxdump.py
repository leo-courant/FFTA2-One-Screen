"""Capture and decode the 3D command lists the game sends by DMA in one frame."""
import struct
NPAR = {0x00:0,0x10:1,0x11:0,0x12:1,0x13:1,0x14:1,0x15:0,0x16:16,0x17:12,0x18:16,0x19:12,0x1A:9,0x1B:3,0x1C:3,
        0x20:1,0x21:1,0x22:1,0x23:2,0x24:1,0x25:1,0x26:1,0x27:1,0x28:1,0x29:1,0x2A:1,0x2B:1,
        0x30:1,0x31:1,0x32:1,0x33:1,0x34:32,0x40:1,0x41:0,0x50:1,0x60:1,0x70:3,0x71:2,0x72:1}
NAME = {0x10:'MTX_MODE',0x11:'PUSH',0x12:'POP',0x13:'STORE',0x14:'RESTORE',0x15:'IDENT',0x16:'LOAD44',0x17:'LOAD43',
        0x18:'MULT44',0x19:'MULT43',0x1A:'MULT33',0x1B:'SCALE',0x1C:'TRANS',0x20:'COLOR',0x21:'NORMAL',0x22:'TEXCOORD',
        0x23:'VTX16',0x24:'VTX10',0x25:'VTX_XY',0x26:'VTX_XZ',0x27:'VTX_YZ',0x28:'VTX_DIFF',0x29:'POLY_ATTR',
        0x2A:'TEXIMAGE',0x2B:'PLTT_BASE',0x40:'BEGIN',0x41:'END',0x50:'SWAP',0x60:'VIEWPORT'}
def s16(v): return v - 0x10000 if v & 0x8000 else v
def decode(words):
    """Yield (cmd, params) from a packed GX command list."""
    i = 0
    while i < len(words):
        w = words[i]; i += 1
        cmds = [(w >> (8 * k)) & 0xFF for k in range(4)]
        for c in cmds:
            if c == 0 and cmds != [0, 0, 0, 0]:
                continue
            n = NPAR.get(c, 0)
            yield c, words[i:i + n]
            i += n
def capture(emu, frames=1):
    bufs = []
    def cb(addr, size):
        r = emu.memory.register_arm9
        src, ctrl = r.r1, r.r3
        n = ctrl & 0x1FFFFF
        data = bytes(emu.memory.unsigned[src:src + 4 * n])
        bufs.append((src, list(struct.unpack('<%dI' % n, data)), r.lr))
    for a in (0x01ff8480, 0x01ff84c0):
        emu.memory.register_exec(a, cb)
    for _ in range(frames):
        bufs.clear(); emu.cycle(False)
    return list(bufs)
