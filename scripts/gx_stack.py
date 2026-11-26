"""For each HUD polygon, recover a heuristic call chain (return addresses found on
the stack that follow a BL) so panels can be told apart by who draws them."""
import sys, struct, collections
sys.path.insert(0, 'scripts')
from emu import boot
emu = boot(sys.argv[1], rom='build/ffta2-1screen.nds', frames=3)
mem = emu.memory
code = bytes(mem.unsigned[0x02000000:0x02122000])
def is_ret(a):
    if not (0x02000008 <= a < 0x02121000) or a & 3: return False
    w = struct.unpack_from('<I', code, a - 4 - 0x02000000)[0]
    return (w >> 24) in (0xEB, 0xFA, 0xFB) or (w & 0x0FFFFFF0) == 0x012FFF30
rows = []
def cb(addr, size):
    r = mem.register_arm9
    pc = r.pc - 8
    if not (0x0204b000 <= pc < 0x020b1000): return
    sp = r.sp & 0xFFFFFFFF
    st = struct.unpack('<96I', bytes(mem.unsigned[sp:sp + 384]))
    chain = [a for a in st if is_ret(a)]
    rows.append((pc, r.lr & 0xFFFFFFFF, chain[:10]))
mem.register_write(0x04000470, cb, 4)   # MTX_TRANS
emu.cycle(False); rows.clear(); emu.cycle(False)
seen = collections.OrderedDict()
for pc, lr, ch in rows:
    seen.setdefault((pc, tuple(ch)), 0); seen[(pc, tuple(ch))] += 1
for (pc, ch), n in seen.items():
    print('T %08x x%-3d %s' % (pc, n, ' '.join('%07x' % a for a in ch)))
