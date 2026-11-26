"""Trace every 3D command the game issues in one frame (direct port writes,
FIFO writes and DMA command lists), run them through a small matrix-stack
model and report each polygon with its screen-space box and call site."""
import struct
import capstone
import gxdump

MD = capstone.Cs(capstone.CS_ARCH_ARM, capstone.CS_MODE_ARM)
REGN = ['r0','r1','r2','r3','r4','r5','r6','r7','r8','sb','sl','fp','ip','sp','lr','pc']

def fx(v):
    return (v - (1 << 32) if v & 0x80000000 else v) / 4096.0

def ident():
    return [[1.0 if i == j else 0.0 for j in range(4)] for i in range(4)]

def mul(a, b):
    return [[sum(a[i][k] * b[k][j] for k in range(4)) for j in range(4)] for i in range(len(a))]

class GX:
    def __init__(self):
        self.mode = 0; self.proj = ident(); self.pos = ident()
        self.pstack = []; self.sstack = []; self.store = {}
        self.polys = []; self.cur = None; self.last = (0.0, 0.0, 0.0)
        self.tex = 0; self.site = 0; self.attr = 0; self.trsite = 0; self.trp = []; self.hist = []; self.dl = None
    def m(self):
        return self.proj if self.mode == 0 else self.pos
    def setm(self, v):
        if self.mode == 0: self.proj = v
        elif self.mode in (1, 2): self.pos = v
    def vtx(self, x, y, z):
        self.last = (x, y, z)
        c = mul([[x, y, z, 1.0]], mul(self.pos, self.proj))[0]
        w = c[3] if c[3] else 1.0
        sx, sy = (c[0] / w + 1) * 128, (1 - c[1] / w) * 96
        if self.cur is not None:
            self.cur['v'].append((sx, sy)); self.cur['raw'].append((x * 4096, y * 4096, z * 4096))
            self.cur.setdefault('tc', []).append(getattr(self, 'tc', (0, 0)))
    def cmd(self, c, p, site):
        # history of matrix commands since the position matrix was last reset or restored
        if self.mode in (1, 2) or c in (0x10,):
            if c in (0x15, 0x16, 0x17, 0x14, 0x12): self.hist = [(c, site, [])]
            elif c in (0x18, 0x19, 0x1A, 0x1B, 0x1C, 0x11, 0x13): self.hist.append((c, site, [x if x < 2**31 else x - 2**32 for x in (p[:16] if c in (0x18, 0x16) else p[:3])]))
        if c == 0x10: self.mode = p[0] & 3
        elif c == 0x11: (self.pstack if self.mode == 0 else self.sstack).append([r[:] for r in self.m()])
        elif c == 0x12:
            st = self.pstack if self.mode == 0 else self.sstack
            n = p[0] & 0x3F if p else 1
            n = n - 64 if n & 0x20 else n
            for _ in range(max(n, 1) if n > 0 else 0):
                if st: self.setm(st.pop())
        elif c == 0x13: self.store[p[0] & 31] = [r[:] for r in self.m()]
        elif c == 0x14:
            if (p[0] & 31) in self.store: self.setm([r[:] for r in self.store[p[0] & 31]])
        elif c == 0x15: self.setm(ident())
        elif c in (0x16, 0x18):
            mm = [[fx(p[r * 4 + k]) for k in range(4)] for r in range(4)]
            self.setm(mm if c == 0x16 else mul(mm, self.m()))
        elif c in (0x17, 0x19):
            mm = [[fx(p[r * 3 + k]) for k in range(3)] + [0.0] for r in range(4)]; mm[3][3] = 1.0
            self.setm(mm if c == 0x17 else mul(mm, self.m()))
        elif c == 0x1A:
            mm = [[fx(p[r * 3 + k]) for k in range(3)] + [0.0] for r in range(3)] + [[0, 0, 0, 1.0]]
            self.setm(mul(mm, self.m()))
        elif c == 0x1B:
            mm = ident(); mm[0][0], mm[1][1], mm[2][2] = fx(p[0]), fx(p[1]), fx(p[2]); self.setm(mul(mm, self.m()))
        elif c == 0x1C:
            self.trsite = site; self.trp = p[:3]
            mm = ident(); mm[3][0], mm[3][1], mm[3][2] = fx(p[0]), fx(p[1]), fx(p[2]); self.setm(mul(mm, self.m()))
        elif c == 0x22:   # TEXCOORD: s, t in texels (12.4 fixed point)
            s16 = gxdump.s16; self.tc = (s16(p[0] & 0xFFFF) / 16, s16(p[0] >> 16) / 16)
        elif c == 0x2B: self.pltt = p[0]   # PLTT_BASE: palette address / 16 (/8 for 4-colour)
        elif c == 0x29: self.attr = p[0]
        elif c == 0x2A: self.tex = p[0]
        elif c == 0x40:
            self.cur = {'v': [], 'raw': [], 'tex': self.tex, 'site': site, 'trsite': self.trsite, 'trp': list(self.trp), 'hist': list(self.hist), 'dl': self.dl, 'attr': self.attr, 'pltt': getattr(self, 'pltt', 0), 'depth': len(self.sstack), 'tr': (self.pos[3][0]*4096, self.pos[3][1]*4096), 'sc': (self.pos[0][0], self.pos[1][1]), 'ptr': (self.proj[3][0], self.proj[3][1]), 'psc': (self.proj[0][0], self.proj[1][1])}
            self.polys.append(self.cur)
        elif c == 0x41: self.cur = None
        elif c == 0x23:
            s = gxdump.s16
            self.vtx(s(p[0] & 0xFFFF) / 4096, s(p[0] >> 16) / 4096, s(p[1] & 0xFFFF) / 4096)
        elif c == 0x24:
            f = lambda v: ((v - 1024) if v & 512 else v) * 64 / 4096
            self.vtx(f(p[0] & 1023), f((p[0] >> 10) & 1023), f((p[0] >> 20) & 1023))
        elif c == 0x25:
            s = gxdump.s16; self.vtx(s(p[0] & 0xFFFF) / 4096, s(p[0] >> 16) / 4096, self.last[2])
        elif c == 0x26:
            s = gxdump.s16; self.vtx(s(p[0] & 0xFFFF) / 4096, self.last[1], s(p[0] >> 16) / 4096)
        elif c == 0x27:
            s = gxdump.s16; self.vtx(self.last[0], s(p[0] & 0xFFFF) / 4096, s(p[0] >> 16) / 4096)
        elif c == 0x28:
            f = lambda v: ((v - 1024) if v & 512 else v) / 8 / 4096
            self.vtx(self.last[0] + f(p[0] & 1023), self.last[1] + f((p[0] >> 10) & 1023), self.last[2] + f((p[0] >> 20) & 1023))

def trace_frame(emu):
    mem = emu.memory
    gx = GX()
    pending = {'c': None, 'p': [], 'site': 0}
    fifo = {'cmds': [], 'need': 0, 'p': [], 'site': 0}
    in_dma = {'on': False}
    unknown = set()

    ALIAS = {'sb': 'r9', 'sl': 'r10', 'fp': 'r11', 'ip': 'r12'}

    def value_at_write(addr=0):
        r = mem.register_arm9
        pc = r.pc - 8
        raw = bytes(mem.unsigned[pc:pc + 4])
        for ins in MD.disasm(raw, pc):
            if ins.mnemonic.startswith('stm'):
                base, lst = ins.op_str.split(',', 1)
                base = base.strip().rstrip('!')
                regs = [x.strip() for x in lst.strip().strip('{}').split(',')]
                b = getattr(r, ALIAS.get(base, base)) & 0xFFFFFFFF
                idx = (addr - b) // 4
                if '!' in ins.op_str.split(',')[0]:
                    idx = len(regs) + idx if idx < 0 else idx
                if 0 <= idx < len(regs):
                    return getattr(r, ALIAS.get(regs[idx], regs[idx])) & 0xFFFFFFFF, pc
                unknown.add((pc, 'stm idx %d' % idx)); return None, pc
            if ins.mnemonic.startswith('str') and not ins.mnemonic.startswith('strh') and not ins.mnemonic.startswith('strb'):
                reg = ins.op_str.split(',')[0].strip()
                if reg in REGN:
                    return getattr(r, reg if reg not in ('sb','sl','fp','ip') else {'sb':'r9','sl':'r10','fp':'r11','ip':'r12'}[reg]) & 0xFFFFFFFF, pc
            unknown.add((pc, ins.mnemonic + ' ' + ins.op_str))
        return None, pc

    def flush():
        if pending['c'] is not None and len(pending['p']) >= gxdump.NPAR.get(pending['c'], 0):
            gx.cmd(pending['c'], pending['p'], pending['site'])
            pending['c'] = None; pending['p'] = []

    def port_cb(addr, size):
        if in_dma['on']:
            return
        v, pc = value_at_write(addr)
        if v is None:
            return
        c = (addr & 0x1FF) >> 2
        need = gxdump.NPAR.get(c, 0)
        if pending['c'] != c or len(pending['p']) >= max(need, 1):
            flush(); pending['c'] = c; pending['p'] = []; pending['site'] = pc
        pending['p'].append(v)
        if len(pending['p']) >= need:
            flush()

    def fifo_cb(addr, size):
        if in_dma['on']:
            return
        v, pc = value_at_write(addr)
        if v is None:
            return
        flush()
        f = fifo
        if not f['cmds']:
            f['cmds'] = [(v >> (8 * k)) & 0xFF for k in range(4)]
            f['p'] = []; f['site'] = pc
            while f['cmds'] and gxdump.NPAR.get(f['cmds'][0], 0) == 0:
                c = f['cmds'].pop(0)
                if c: gx.cmd(c, [], pc)
            return
        f['p'].append(v)
        while f['cmds'] and len(f['p']) >= gxdump.NPAR.get(f['cmds'][0], 0):
            c = f['cmds'].pop(0); n = gxdump.NPAR.get(c, 0)
            if c: gx.cmd(c, f['p'][:n], f['site'])
            f['p'] = f['p'][n:]

    def dma_cb(addr, size):
        r = mem.register_arm9
        if (r.r2 & 0xFFFFFFFF) != 0x04000400:
            return
        flush()
        n = r.r3 & 0x1FFFFF
        data = bytes(mem.unsigned[r.r1:r.r1 + 4 * n])
        # display list: where it lives and who asked for it (return addresses on the stack)
        sp = r.sp & 0xFFFFFFFF
        st = struct.unpack('<64I', bytes(mem.unsigned[sp:sp + 256]))
        gx.dl = (r.r1 & 0xFFFFFFFF, n, [a for a in st if 0x01FF8000 <= a < 0x02122000 and not a & 3][:12])
        for c, p in gxdump.decode(list(struct.unpack('<%dI' % n, data))):
            gx.cmd(c, p, r.lr & 0xFFFFFFFF)
        gx.dl = None

    for a in range(0x04000440, 0x040005CC, 4):
        mem.register_write(a, port_cb, 4)
    for a in range(0x04000400, 0x04000440, 4):
        mem.register_write(a, fifo_cb, 4)
    for a in (0x01ff8480, 0x01ff84c0):
        mem.register_exec(a, dma_cb)
    emu.cycle(False)
    gx.polys.clear(); unknown.clear()
    emu.cycle(False)
    flush()
    return gx, unknown
