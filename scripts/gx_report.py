import sys, collections
sys.path.insert(0, 'scripts')
from emu import boot
import gxtrace
import os
emu = boot(sys.argv[1], rom=os.environ.get('ROM', 'build/ffta2-1screen.nds'), frames=3)
gx, unk = gxtrace.trace_frame(emu)
print('T polys', len(gx.polys), 'unknown', list(unk)[:6])
by = collections.OrderedDict()
for p in gx.polys:
    if not p['v']: continue
    xs = [v[0] for v in p['v']]; ys = [v[1] for v in p['v']]
    t = p['tex']
    by.setdefault(p['site'], []).append((min(xs), max(xs), min(ys), max(ys), 8 << ((t >> 20) & 7), 8 << ((t >> 23) & 7), (t >> 26) & 7, (t & 0xffff) * 8))
for site, l in by.items():
    print('T site %08x  n=%d' % (site, len(l)))
    for b in l[:int(sys.argv[2]) if len(sys.argv) > 2 else 8]:
        print('T      box x %.0f..%.0f y %.0f..%.0f  tex %dx%d fmt%d @%05x' % b)
