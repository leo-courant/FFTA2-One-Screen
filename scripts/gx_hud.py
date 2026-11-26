import sys, collections
sys.path.insert(0, 'scripts')
from emu import boot
import gxtrace
emu = boot(sys.argv[1], rom='build/ffta2-1screen.nds', frames=3)
gx, unk = gxtrace.trace_frame(emu)
skip = {0x020d5558, 0x020d4fbc, 0x0208cc18, 0x01ff8628}
last = None; n = 0
for p in gx.polys:
    if not p['v'] or p['site'] in skip: continue
    xs = [v[0] for v in p['v']]; ys = [v[1] for v in p['v']]
    rx = [v[0] for v in p['raw']]; ry = [v[1] for v in p['raw']]
    key = (p['site'], round(p['tr'][0]), round(p['tr'][1]))
    print('T %08x d=%d tr=(%.0f,%.0f) sc=(%.2f,%.2f) proj=(%.1f,%.1f;%.2f,%.2f) raw x %.0f..%.0f y %.0f..%.0f -> scr x %.0f..%.0f y %.0f..%.0f nq=%d' % (
        p['site'], p['depth'], p['tr'][0], p['tr'][1], p['sc'][0], p['sc'][1], p['psc'][0], p['psc'][1], p['ptr'][0], p['ptr'][1],
        min(rx), max(rx), min(ry), max(ry), min(xs), max(xs), min(ys), max(ys), len(p['v']) // 4))
