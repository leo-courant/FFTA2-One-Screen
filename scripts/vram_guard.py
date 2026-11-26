#!/usr/bin/env python3
"""Ticket 25: guard on the video memory the mod borrows.

usage: vram_guard.py STATE [SCRIPT] [-v]
  STATE   DeSmuME savestate ("-" boots the ROM cold)
  SCRIPT  play.py steps (w<N>, <KEY><N>, p<addr>=<val>, <step>*<N>; s<name> marks a point
          in the -v log).  Default: w300 (five seconds of play)
Env: ROM (default build/ffta2-1screen.nds).

Plays the state and reports every frame where one side uses the other side's data in the
video memory the mod borrows.  Silent means clean.  Lines go to stderr (DeSmuME swallows
stdout); exit status 1 when anything was reported.

  GAME-DRAW   a game polygon samples a texture or palette there while it holds the mod's data
  GAME-BG     a main-engine BG layer shows tiles or map from there while it holds the mod's data
  GAME-WRITE  the game writes over the mod's data there (the mod's picture or parked copy is lost)
  MOD-DRAW    a mod polygon samples texture or palette bytes the mod wrote and the game changed
  MAPPED      a bank holding the mod's data is handed to an engine the guard does not follow

The borrowed ranges come from the built blob: the table after the "BORR" marker in
src/hook.c (borrowed_vram).  Each byte has two shadows: what the game last wrote there and
what the mod last wrote there (both start as the state's contents).  Writes are caught with
the emulator's write watch on each bank's LCDC window and on main BG space; the program
counter tells the mod (the blob) from the game.  Draws come from the 3D commands (direct
port writes, the FIFO and the game's DMA lists, as scripts/gxtrace.py) and from the
main-engine BG registers.  A draw is a clash when the bytes it reads differ from the
reader's own shadow.  Banks are read by mapping them to the CPU for a moment between
frames, so the emulated game never sees it.

Polygons are followed through the projection and position matrices (gxtrace's model), and
triangles or quads that land wholly off screen are not counted as draws: while the overlay is
up the mod pushes the game's panels off screen.
Limits: texture rows are narrowed by the polygons' texture coordinates, through the texture
matrix when the texture says so (columns are not; normal- and vertex-sourced coordinates
count as the whole texture);
compressed (4x4) textures' palettes are taken as 512 bytes from their base; affine and
the large-bitmap mode (6) is checked over its whole 512 KB; a BG layer counts as shown
unless it is off or alpha-blended at weight 0 (windows and priorities are not followed).  Writes the game makes
while a bank is mapped elsewhere than LCDC or main BG space are not seen (the game only
uploads through those).
"""
import contextlib, io, os, struct, sys
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
os.environ.setdefault("SDL_VIDEODRIVER", "dummy")
import numpy as np
import capstone
import gxdump
import gxtrace
from emu import boot, rom_blob, BLOB_ADDR

# bank: (VRAMCNT register, LCDC offset from 0x06800000, size)
BANKS = {"A": (0x04000240, 0x00000, 0x20000), "B": (0x04000241, 0x20000, 0x20000),
         "C": (0x04000242, 0x40000, 0x20000), "D": (0x04000243, 0x60000, 0x20000),
         "E": (0x04000244, 0x80000, 0x10000), "F": (0x04000245, 0x90000, 0x4000),
         "G": (0x04000246, 0x94000, 0x4000), "H": (0x04000248, 0x98000, 0x8000),
         "I": (0x04000249, 0xA0000, 0x4000)}
LCDC, LSIZE = 0x06800000, 0xA4000
GAME, MOD = 1, 2
BPP = {1: 8, 2: 2, 3: 4, 4: 8, 5: 2, 6: 8, 7: 16}
COLOURS = {1: 32, 2: 4, 3: 16, 4: 256, 5: 256, 6: 8}
KEYNAMES = "A B X Y L R START SELECT UP DOWN LEFT RIGHT".split()


def bank_of(L):
    for b, (_, lo, n) in BANKS.items():
        if lo <= L < lo + n:
            return b, L - lo
    return "?", L


def where(L0, L1):
    b, o = bank_of(L0)
    return "bank %s +0x%05X..0x%05X" % (b, o, o + (L1 - L0) - 1)


def borrowed_table(blob):
    at = blob.index(b"BORR") + 4
    out = []
    while True:
        tag = blob[at:at + 4]
        if tag == b"\0\0\0\0":
            return out
        s, e = struct.unpack_from("<II", blob, at + 4)
        out.append((tag.decode(), s, e))
        at += 12


def mapping(cnt):
    """What each bank serves, from the VRAMCNT bytes: lists of (address, size, L, bank) for
    main BG space, texture space and texture palette space, plus banks given to other uses."""
    bg, tex, pal, other = [], [], [], []
    for b, (reg, L, n) in BANKS.items():
        c = cnt[b]
        if not c & 0x80:
            continue
        ofs = (c >> 3) & 3
        if b in "AB":
            mst = c & 3
        else:
            mst = c & 7
        if mst == 0:
            continue                                   # LCDC: the CPU's own window
        if b in "ABCD" and mst == 1:
            bg.append((0x06000000 + 0x20000 * ofs, n, L, b))
        elif b in "ABCD" and mst == 3:
            tex.append((0x20000 * ofs, n, L, b))
        elif b == "E" and mst == 1:
            bg.append((0x06000000, n, L, b))
        elif b == "E" and mst == 3:
            pal.append((0, n, L, b))
        elif b in "FG" and mst == 1:
            bg.append((0x06000000 + 0x4000 * (ofs & 1) + 0x10000 * (ofs >> 1), n, L, b))
        elif b in "FG" and mst == 3:
            pal.append((0x4000 * ((ofs & 1) + 4 * (ofs >> 1)), n, L, b))
        else:
            other.append((b, mst))
    return bg, tex, pal, other


def to_L(spans, a0, a1):
    """[a0, a1) in a mapped space -> list of LCDC ranges"""
    out = []
    for base, n, L, _ in spans:
        lo, hi = max(a0, base), min(a1, base + n)
        if lo < hi:
            out.append((L + lo - base, L + hi - base))
    return out


class Guard:
    def __init__(self, emu, blob, verbose=False):
        self.emu, self.mem, self.m = emu, emu.memory, emu.memory.unsigned
        self.blob_lo, self.blob_hi = BLOB_ADDR, BLOB_ADDR + len(blob)
        self.verbose = verbose
        self.table = borrowed_table(blob)
        self.frame = 0
        self.tracked = np.zeros(LSIZE, bool)
        self.tag = np.zeros(LSIZE, np.uint8)            # index into self.table + 1
        self.content = np.zeros(LSIZE, np.uint8)
        self.gshadow = np.zeros(LSIZE, np.uint8)
        self.mshadow = np.zeros(LSIZE, np.uint8)
        self.modwrote = np.zeros(LSIZE, bool)           # bytes the mod has written at least once
        self.writer = bytearray(LSIZE)
        self.dirty = set()                              # 32-byte chunks written this frame
        self.game_sites = {}                            # chunk -> (pc, lr) of the game's first write this frame
        self.events = {}                                # (kind, tag, site) -> [first, last, count]
        self.remapping = False
        self.stats = {"game draws": 0, "mod draws": 0, "game writes": 0, "mod writes": 0, "max bytes held by the mod": 0}
        self.cnt = self.read_cnt()
        self.bg_entries = [(t, s, e) for t, s, e in self.table if s < LCDC]
        self.watch_writes()
        self.gx_init()

    # ---- memory --------------------------------------------------------------
    def read_cnt(self):
        return {b: self.m[reg] for b, (reg, _, _) in BANKS.items()}

    def read_L(self, L0, L1):
        """bytes of [L0, L1) (one bank), mapping the bank to the CPU for the moment"""
        b, _ = bank_of(L0)
        reg = BANKS[b][0]
        old = self.m[reg]
        self.remapping = True
        self.mem.write_byte(reg, 0x80)
        data = bytes(self.m[LCDC + L0:LCDC + L1])
        self.mem.write_byte(reg, old)
        self.remapping = False
        return np.frombuffer(data, np.uint8)

    def track(self, L0, L1, idx):
        new = ~self.tracked[L0:L1]
        if not new.any():
            return
        now = self.read_L(L0, L1)
        sl = slice(L0, L1)
        self.content[sl] = np.where(new, now, self.content[sl])
        self.gshadow[sl] = np.where(new, now, self.gshadow[sl])
        self.mshadow[sl] = np.where(new, now, self.mshadow[sl])
        self.tag[sl] = np.where(new, idx, self.tag[sl])
        self.tracked[sl] = True
        self.mem.register_write(LCDC + L0, self.on_lcdc, L1 - L0)

    def watch_writes(self):
        for i, (t, s, e) in enumerate(self.table):
            if s >= LCDC:
                self.track(s - LCDC, e - LCDC, i + 1)
            else:
                self.mem.register_write(s, self.on_bg, e - s)
        self.resolve_bg()
        self.mem.register_write(0x04000240, self.on_cnt, 10)

    def resolve_bg(self):
        """main-BG-space entries -> the banks mapped there now; track those bytes too"""
        bg = mapping(self.cnt)[0]
        self.bg_map = bg
        for i, (t, s, e) in enumerate(self.table):
            if s < LCDC:
                for L0, L1 in to_L(bg, s, e):
                    self.track(L0, L1, i + 1)

    def on_cnt(self, addr, size):
        if self.remapping:
            return
        self.cnt = self.read_cnt()
        self.cnt_changed = True

    def who(self):
        r = self.mem.register_arm9
        pc = (r.pc - 8) & 0xFFFFFFFF
        return (MOD if self.blob_lo <= pc < self.blob_hi else GAME), pc, r.lr & 0xFFFFFFFF

    def mark(self, L, size):
        w, pc, lr = self.who()
        self.stats["mod writes" if w == MOD else "game writes"] += 1
        self.writer[L:L + size] = bytes([w]) * size
        c = L >> 5
        self.dirty.add(c)
        if (L + size - 1) >> 5 != c:
            self.dirty.add((L + size - 1) >> 5)
        if w == GAME and c not in self.game_sites:
            self.game_sites[c] = (pc, lr)

    def on_lcdc(self, addr, size):
        if not self.remapping:
            self.mark(addr - LCDC, size)

    def on_bg(self, addr, size):
        for L0, _ in to_L(self.bg_map, addr, addr + size):
            if self.tracked[L0]:
                self.mark(L0, size)

    # ---- 3D commands -----------------------------------------------------------
    def gx_init(self):
        self.md = capstone.Cs(capstone.CS_ARCH_ARM, capstone.CS_MODE_ARM)
        self.insn = {}
        self.uses = {}            # (tex, pltt, site) -> [[tmin, tmax] per primitive group]
        self.g_tex = self.g_pltt = 0
        self.g_t = None
        self.mtx_mode = 0
        self.model = gxtrace.GX()                    # projection / position matrices (gxtrace's model)
        self.clip = None
        self.last_v = (0.0, 0.0, 0.0)
        self.texm = [[1.0 if i == j else 0.0 for j in range(4)] for i in range(4)]
        self.cur = None
        self.fifo = {"cmds": [], "p": [], "site": 0}
        self.pending = {"c": None, "p": [], "site": 0}
        for a in range(0x04000440, 0x040005CC, 4):
            self.mem.register_write(a, self.on_port, 4)
        self.mem.register_write(0x04000400, self.on_fifo, 0x40)
        for a in (0x01FF8480, 0x01FF84C0):
            self.mem.register_exec(a, self.on_dma)

    def value_at_write(self, addr):
        r = self.mem.register_arm9
        pc = (r.pc - 8) & 0xFFFFFFFF
        ins = self.insn.get(pc)
        if ins is None:
            raw = bytes(self.m[pc:pc + 4])
            d = list(self.md.disasm(raw, pc))
            ins = self.insn[pc] = (d[0].mnemonic, d[0].op_str) if d else ("", "")
        mn, ops = ins
        alias = {"sb": "r9", "sl": "r10", "fp": "r11", "ip": "r12"}
        reg = lambda n: getattr(r, alias.get(n, n)) & 0xFFFFFFFF
        if mn.startswith("stm"):
            base, lst = ops.split(",", 1)
            wb = "!" in base
            base = base.strip().rstrip("!")
            regs = [x.strip() for x in lst.strip().strip("{}").split(",")]
            idx = (addr - reg(base)) // 4
            if wb and idx < 0:
                idx += len(regs)
            return (reg(regs[idx]) if 0 <= idx < len(regs) else None), pc
        if mn.startswith("str") and not mn.startswith(("strh", "strb")):
            n = ops.split(",")[0].strip()
            return (reg(n) if n in ("r0 r1 r2 r3 r4 r5 r6 r7 r8 r9 r10 r11 r12 sb sl fp ip lr".split()) else None), pc
        return None, pc

    def texmtx(self, c, p):
        """texture matrix commands (MTX_MODE 3), as gxtrace's model: new matrix on the left"""
        fx = lambda v: (v - (1 << 32) if v & 0x80000000 else v) / 4096.0
        I = [[1.0 if i == j else 0.0 for j in range(4)] for i in range(4)]
        if c == 0x15:
            self.texm = I
            return
        if c in (0x16, 0x18):
            n = [[fx(p[r * 4 + k]) for k in range(4)] for r in range(4)]
        elif c in (0x17, 0x19):
            n = [[fx(p[r * 3 + k]) for k in range(3)] + [0.0] for r in range(4)]
            n[3][3] = 1.0
        elif c == 0x1A:
            n = [[fx(p[r * 3 + k]) for k in range(3)] + [0.0] for r in range(3)] + [[0.0, 0.0, 0.0, 1.0]]
        elif c == 0x1B:
            n = I
            n[0][0], n[1][1], n[2][2] = fx(p[0]), fx(p[1]), fx(p[2])
        elif c == 0x1C:
            n = I
            n[3][0], n[3][1], n[3][2] = fx(p[0]), fx(p[1]), fx(p[2])
        else:
            return
        if c in (0x16, 0x17):
            self.texm = n
        else:
            a = self.texm
            self.texm = [[sum(n[i][k] * a[k][j] for k in range(4)) for j in range(4)] for i in range(4)]

    def vertex(self, c, p):
        """screen position (x, y in 256x192 viewport pixels, or None behind the eye)"""
        s16 = gxdump.s16
        x, y, z = self.last_v
        if c == 0x23:
            x, y, z = s16(p[0] & 0xFFFF) / 4096, s16(p[0] >> 16) / 4096, s16(p[1] & 0xFFFF) / 4096
        elif c == 0x24:
            f = lambda v: ((v - 1024) if v & 512 else v) * 64 / 4096
            x, y, z = f(p[0] & 1023), f((p[0] >> 10) & 1023), f((p[0] >> 20) & 1023)
        elif c == 0x25:
            x, y = s16(p[0] & 0xFFFF) / 4096, s16(p[0] >> 16) / 4096
        elif c == 0x26:
            x, z = s16(p[0] & 0xFFFF) / 4096, s16(p[0] >> 16) / 4096
        elif c == 0x27:
            y, z = s16(p[0] & 0xFFFF) / 4096, s16(p[0] >> 16) / 4096
        elif c == 0x28:
            f = lambda v: ((v - 1024) if v & 512 else v) / 8 / 4096
            x, y, z = x + f(p[0] & 1023), y + f((p[0] >> 10) & 1023), z + f((p[0] >> 20) & 1023)
        self.last_v = (x, y, z)
        if self.clip is None:
            self.clip = gxtrace.mul(self.model.pos, self.model.proj)
        m = self.clip
        cx = x * m[0][0] + y * m[1][0] + z * m[2][0] + m[3][0]
        cy = x * m[0][1] + y * m[1][1] + z * m[2][1] + m[3][1]
        w = x * m[0][3] + y * m[1][3] + z * m[2][3] + m[3][3]
        if w <= 0:
            return None
        return (cx / w + 1) * 128, (1 - cy / w) * 96

    def gx_cmd(self, c, p, site):
        if 0x10 <= c <= 0x1C:
            if c == 0x10:
                self.mtx_mode = p[0] & 3
            if self.mtx_mode == 3 and c != 0x10:
                self.texmtx(c, p)
            else:
                self.model.cmd(c, p, site)
                self.clip = None
        elif c == 0x2A:
            self.g_tex = p[0]
        elif c == 0x2B:
            self.g_pltt = p[0]
        elif c == 0x22:
            s16 = lambda v: (v - 0x10000 if v & 0x8000 else v) / 16
            S, T = s16(p[0] & 0xFFFF), s16((p[0] >> 16) & 0xFFFF)
            if (self.g_tex >> 30) == 1:              # TexCoord source: (S T 1/16 1/16) x texture matrix
                m = self.texm
                T = S * m[0][1] + T * m[1][1] + (m[2][1] + m[3][1]) / 16
            elif self.g_tex >> 30:                   # normal or vertex source: not followed
                T = None
            self.g_t = T
        elif c == 0x40:
            # a primitive group: its type and, per vertex, the t coordinate and screen position
            if (self.g_tex >> 26) & 7:
                self.cur = [p[0] & 3, []]
                self.uses.setdefault((self.g_tex, self.g_pltt, site), []).append(self.cur)
            else:
                self.cur = None
        elif 0x23 <= c <= 0x28:
            if self.cur is not None:
                self.cur[1].append((self.g_t, self.vertex(c, p)))
            else:
                self.vertex(c, p)

    @staticmethod
    def prim_spans(group, out):
        """add to out {(tmin, tmax): screen box} per triangle or quad of a primitive group that
        reaches the screen; (1, 0) = the whole texture; box = [x0, y0, x1, y1] in the 256x192
        viewport (None when a vertex is behind the eye)"""
        kind, vs = group
        size, step = ((3, 3), (4, 4), (3, 1), (4, 2))[kind]
        for i in range(0, max(1, len(vs) - size + 1), step):
            v = vs[i:i + size]
            if len(v) < size:
                break
            pos = [q for _, q in v]
            box = None
            if all(q is not None for q in pos):
                xs = [q[0] for q in pos]
                ys = [q[1] for q in pos]
                if max(xs) <= 0 or min(xs) >= 256 or max(ys) <= 0 or min(ys) >= 192:
                    continue                          # off screen: samples nothing
                if max(xs) - min(xs) < 0.5 and max(ys) - min(ys) < 0.5:
                    continue                          # degenerate (a scaled-away piece)
                box = [min(xs), min(ys), max(xs), max(ys)]
            ts = [t for t, _ in v]
            key = (1, 0) if any(t is None for t in ts) else (min(ts), max(ts))
            old = out.get(key, 0)
            if old == 0 or old is None or box is None:
                out[key] = box if old == 0 else None
            else:
                out[key] = [min(old[0], box[0]), min(old[1], box[1]), max(old[2], box[2]), max(old[3], box[3])]

    def flush(self):
        pd = self.pending
        if pd["c"] is not None and len(pd["p"]) >= gxdump.NPAR.get(pd["c"], 0):
            self.gx_cmd(pd["c"], pd["p"], pd["site"])
            pd["c"] = None
            pd["p"] = []

    def on_port(self, addr, size):
        c = (addr & 0x1FF) >> 2
        if c not in (0x10, 0x15, 0x16, 0x17, 0x18, 0x19, 0x1A, 0x1B, 0x1C, 0x22, 0x23, 0x24, 0x25, 0x26,
                     0x27, 0x28, 0x2A, 0x2B, 0x40):
            return
        v, pc = self.value_at_write(addr)
        if v is None:
            return
        pd, need = self.pending, gxdump.NPAR.get(c, 0)
        if pd["c"] != c or len(pd["p"]) >= max(need, 1):    # a new command (parameters come one write each)
            pd["c"], pd["p"], pd["site"] = c, [], pc
        pd["p"].append(v)
        if len(pd["p"]) >= need:
            self.gx_cmd(c, pd["p"], pd["site"])
            pd["c"] = None

    def on_fifo(self, addr, size):
        v, pc = self.value_at_write(addr)
        if v is None:
            return
        f = self.fifo
        if not f["cmds"]:
            f["cmds"] = [(v >> (8 * k)) & 0xFF for k in range(4)]
            f["p"] = []
            f["site"] = pc
            while f["cmds"] and gxdump.NPAR.get(f["cmds"][0], 0) == 0:
                c = f["cmds"].pop(0)
                if c:
                    self.gx_cmd(c, [], pc)
            return
        f["p"].append(v)
        while f["cmds"] and len(f["p"]) >= gxdump.NPAR.get(f["cmds"][0], 0):
            c = f["cmds"].pop(0)
            n = gxdump.NPAR.get(c, 0)
            if c:
                self.gx_cmd(c, f["p"][:n], f["site"])
            f["p"] = f["p"][n:]

    def on_dma(self, addr, size):
        r = self.mem.register_arm9
        if (r.r2 & 0xFFFFFFFF) != 0x04000400:
            return
        n = r.r3 & 0x1FFFFF
        src = r.r1 & 0xFFFFFFFF
        words = struct.unpack("<%dI" % n, bytes(self.m[src:src + 4 * n]))
        site = r.lr & 0xFFFFFFFF
        for c, p in gxdump.decode(list(words)):
            self.gx_cmd(c, p, site)

    # ---- one frame -----------------------------------------------------------------
    def report(self, kind, idx, L0, L1, site, extra=""):
        tag = self.table[idx - 1][0] if idx else "?"
        key = (kind, tag, site)
        ev = self.events.get(key)
        if ev:
            if ev[1] != self.frame:
                ev[1] = self.frame
                ev[2] += 1
            return
        self.events[key] = [self.frame, self.frame, 1]
        print("frame %5d  %-10s %s  %s  %s%s" % (self.frame, kind, tag, where(L0, L1), site, extra),
              file=sys.stderr)

    def runs(self, mask, L0):
        """[(start, end)] of True runs in mask (offset L0)"""
        idx = np.flatnonzero(np.diff(np.concatenate(([0], mask.view(np.int8), [0]))))
        return [(L0 + a, L0 + b) for a, b in zip(idx[::2], idx[1::2])]

    def end_frame(self):
        self.frame += 1
        if getattr(self, "cnt_changed", False):
            self.cnt_changed = False
            self.resolve_bg()
        # writes: settle the shadows
        if self.dirty:
            chunks = sorted(self.dirty)
            spans = []
            for c in chunks:
                if spans and c == spans[-1][1] and bank_of(c << 5)[0] == bank_of(spans[-1][0] << 5)[0]:
                    spans[-1][1] = c + 1
                else:
                    spans.append([c, c + 1])
            for c0, c1 in spans:
                L0, L1 = c0 << 5, min(c1 << 5, LSIZE)
                now = self.read_L(L0, L1)
                w = np.frombuffer(bytes(self.writer[L0:L1]), np.uint8)
                tr = self.tracked[L0:L1]
                sl = slice(L0, L1)
                g = (w == GAME) & tr
                mo = (w == MOD) & tr
                held = self.content[sl] != self.gshadow[sl]          # the mod's data was there
                lost = g & held & (now != self.content[sl])
                for a, b in self.runs(lost, L0):
                    pc, lr = self.game_sites.get(a >> 5, (0, 0))
                    self.report("GAME-WRITE", int(self.tag[a]), a, b, "pc %08x lr %08x" % (pc, lr))
                self.gshadow[sl] = np.where(g, now, self.gshadow[sl])
                self.mshadow[sl] = np.where(mo, now, self.mshadow[sl])
                self.modwrote[sl] |= mo
                self.content[sl] = np.where(tr, now, self.content[sl])
                self.writer[L0:L1] = bytes(L1 - L0)
            self.dirty.clear()
            self.game_sites.clear()
        modheld = self.tracked & (self.content != self.gshadow)
        self.stats["max bytes held by the mod"] = max(self.stats["max bytes held by the mod"], int(modheld.sum()))
        # the mod only relies on what it wrote itself (e.g. the overlay palette up to the colours
        # it has filled in): its draws are checked against those bytes
        gamechg = self.modwrote & (self.content != self.mshadow)
        bg, tex, pal, other = mapping(self.cnt)
        # 3D draws
        for (t, pltt, site), spans in self.uses.items():
            mine = self.blob_lo <= site < self.blob_hi
            self.stats["mod draws" if mine else "game draws"] += 1
            bad = gamechg if mine else modheld
            seen = {}
            prims = {}
            for group in spans:
                self.prim_spans(group, prims)
            for (tmin, tmax), box in sorted(prims.items()):
                for kind, (L0, L1) in self.tex_ranges(t, pltt, tmin, tmax, tex, pal):
                    m = bad[L0:L1]
                    if m.any():
                        a, b = self.runs(m, L0)[0]
                        k = (kind, a, b)
                        seen[k] = box if k not in seen or box is None or seen[k] is None else [
                            min(seen[k][0], box[0]), min(seen[k][1], box[1]),
                            max(seen[k][2], box[2]), max(seen[k][3], box[3])]
                        seen.setdefault(("rows",) + k, (tmin, tmax))
            for k, box in seen.items():
                if k[0] == "rows":
                    continue
                kind, a, b = k
                tmin, tmax = seen[("rows",) + k]
                self.report(("MOD-DRAW" if mine else "GAME-DRAW"), int(self.tag[a]), a, b,
                            "site %08x" % site, "  (%s, teximage %08x, rows %s, on screen %s)" % (
                                kind, t, "all" if tmin > tmax else "%g-%g" % (tmin, tmax),
                                "?" if box is None else "x %d..%d y %d..%d of 256x192" % (box[0], box[2], box[1], box[3])))
        self.uses.clear()
        self.cur = None
        # main-engine BG layers
        if modheld.any():
            for name, L0, L1 in self.bg_ranges(bg):
                m = modheld[L0:L1]
                if m.any():
                    a, b = self.runs(m, L0)[0]
                    self.report("GAME-BG", int(self.tag[a]), a, b, name)
            for b, mst in other:
                _, L, n = BANKS[b]
                if modheld[L:L + n].any():
                    a, e = self.runs(modheld[L:L + n], L)[0]
                    self.report("MAPPED", int(self.tag[a]), a, e, "bank %s mode %d" % (b, mst))

    def tex_ranges(self, t, pltt, tmin, tmax, tex, pal):
        fmt = (t >> 26) & 7
        w, h = 8 << ((t >> 20) & 7), 8 << ((t >> 23) & 7)
        addr = (t & 0xFFFF) * 8
        r0, r1 = 0, h
        if tmin <= tmax:
            # texels sampled: rows floor(tmin) .. ceil(tmax) - 1 (a coordinate on an edge is a
            # texel boundary), at least one row
            lo = int(tmin // 1)
            hi = max(lo + 1, -int(-tmax // 1))          # exclusive
            if (t >> 17) & 1:                         # repeat in t
                if hi - lo <= h:
                    a0, a1 = lo % h, (hi - 1) % h + 1
                    if a0 < a1:
                        r0, r1 = a0, a1
            else:
                r0, r1 = max(0, min(lo, h - 1)), max(1, min(hi, h))
        out = []
        if fmt == 5:
            a0, a1 = addr + (r0 // 4) * w, addr + -(-r1 // 4) * w
            out += [("texels", x) for x in to_L(tex, a0, a1)]
            ia = 0x20000 + (addr & 0x1FFFF) // 2 + (0x10000 if addr >= 0x40000 else 0)
            out += [("4x4 index", x) for x in to_L(tex, ia + (r0 // 4) * w // 2, ia + -(-r1 // 4) * w // 2)]
        else:
            row = w * BPP[fmt] // 8
            out += [("texels", x) for x in to_L(tex, addr + r0 * row, addr + r1 * row)]
        if fmt != 7:
            base = pltt * (8 if fmt == 2 else 16)
            n = 0x200 if fmt == 5 else COLOURS[fmt] * 2
            skip = 2 if fmt in (2, 3, 4) and (t >> 29) & 1 else 0   # colour 0 transparent: never shown
            out += [("palette", x) for x in to_L(pal, base + skip, base + n)]
        return out

    def bg_ranges(self, bg):
        """(name, L0, L1) for every enabled main-engine BG layer's map and tiles"""
        m = self.m
        disp = m.read_long(0x04000000)
        mode = disp & 7
        out = []
        bld, alpha = m.read_short(0x04000050), m.read_short(0x04000052)
        for n in range(4):
            if not (disp >> (8 + n)) & 1 or (n == 0 and disp & 8):
                continue
            if (bld >> 6) & 3 == 1 and (bld >> n) & 1 and alpha & 31 == 0:
                continue                                # alpha-blended at weight 0: shows nothing
            cnt = m.read_short(0x04000008 + 2 * n)
            cbase = 0x06000000 + ((disp >> 24) & 7) * 0x10000 + ((cnt >> 2) & 15) * 0x4000
            mbase = 0x06000000 + ((disp >> 27) & 7) * 0x10000 + ((cnt >> 8) & 31) * 0x800
            size = cnt >> 14
            affine = (n == 3 and mode in (1, 2, 3, 4, 5)) or (n == 2 and mode in (2, 4, 5))
            ext = (n == 3 and mode in (3, 4, 5)) or (n == 2 and mode == 5)
            name = "BG%d (BG%dCNT %04x)" % (n, n, cnt)
            spans = []                                   # (what, start, end) in BG space
            if n == 2 and mode == 6:                     # large bitmap: the whole 512 KB is out of reach
                spans.append(("bitmap", 0x06000000, 0x06080000))
            elif ext and (cnt >> 7) & 1:                 # bitmap layer: 8 or 16 bits per pixel
                w, h = ((128, 128), (256, 256), (512, 256), (512, 512))[size]
                bbase = 0x06000000 + ((cnt >> 8) & 31) * 0x4000
                spans.append(("bitmap", bbase, bbase + w * h * (2 if (cnt >> 2) & 1 else 1)))
            else:
                if affine and not ext:                   # 8-bit map entries, 8bpp tiles
                    side = (128 << size) // 8
                    mlen = side * side
                    maps = [m[mbase + i] for i in range(mlen)] if mlen <= 0x4000 else list(range(256))
                    tb = 64
                elif ext:                                # 16-bit map entries, 8bpp tiles
                    side = (128 << size) // 8
                    mlen = side * side * 2
                    maps = [m.read_short(mbase + i) & 0x3FF for i in range(0, mlen, 2)]
                    tb = 64
                else:                                    # text
                    mlen = (0x800, 0x1000, 0x1000, 0x2000)[size]
                    maps = [m.read_short(mbase + i) & 0x3FF for i in range(0, mlen, 2)]
                    tb = 64 if (cnt >> 7) & 1 else 32
                spans.append(("map", mbase, mbase + mlen))
                tiles = sorted(set(maps))
                run = [tiles[0], tiles[0]]
                for t in tiles[1:] + [None]:
                    if t is not None and t == run[1] + 1:
                        run[1] = t
                        continue
                    spans.append(("tiles", cbase + run[0] * tb, cbase + (run[1] + 1) * tb))
                    if t is not None:
                        run = [t, t]
            for what, a0, a1 in spans:
                for L0, L1 in to_L(bg, a0, a1):
                    out.append((name + " " + what, L0, L1))
        return out


def main():
    args = [a for a in sys.argv[1:] if a != "-v"]
    verbose = "-v" in sys.argv[1:]
    if not args:
        sys.exit(__doc__)
    state = args[0]
    script = args[1] if len(args) > 1 else "w300"
    rom = os.environ.get("ROM", "build/ffta2-1screen.nds")
    blob = rom_blob(rom)
    with contextlib.redirect_stdout(io.StringIO()):
        emu = boot(None if state == "-" else state, rom=rom, frames=1)
    from desmume.controls import Keys, keymask
    keys = {k: getattr(Keys, "KEY_" + k) for k in KEYNAMES}
    g = Guard(emu, blob, verbose)
    if verbose:
        for t, s, e in g.table:
            print("borrowed %s 0x%08X..0x%08X" % (t, s, e - 1), file=sys.stderr)

    def cyc(n):
        for _ in range(n):
            emu.cycle(False)
            g.end_frame()

    def do(step):
        if step[0] == "w" and step[1:].isdigit():
            cyc(int(step[1:]))
        elif step[0] == "s":
            if verbose:
                print("frame %5d  mark %s" % (g.frame, step[1:]), file=sys.stderr)
        elif step[0] == "p":
            a, v = step[1:].split("=")
            emu.memory.write_short(int(a, 16), int(v, 16))
        else:
            name = step.rstrip("0123456789")
            n = int(step[len(name):] or 4)
            emu.input.keypad_add_key(keymask(keys[name]))
            cyc(n)
            emu.input.keypad_rm_key(keymask(keys[name]))
            cyc(4)

    for step in script.split(","):
        step = step.strip()
        if not step:
            continue
        if "*" in step:
            s, n = step.split("*")
            for _ in range(int(n)):
                do(s)
                cyc(20)
        else:
            do(step)
    for (kind, tag, site), (f0, f1, n) in g.events.items():
        if n > 1:
            print("           %-10s %s  %s  again until frame %d (%d frames)" % (kind, tag, site, f1, n),
                  file=sys.stderr)
    if verbose:
        print("frames %d, %d clash kinds; " % (g.frame, len(g.events))
              + ", ".join("%s %d" % kv for kv in g.stats.items()), file=sys.stderr)
    sys.exit(1 if g.events else 0)


if __name__ == "__main__":
    main()
