#!/usr/bin/env python3
"""How well do game-pixel edges in a capture sit on an even grid?
usage: measure_grid.py IMG [PX]  -> share of colour changes on the best-fitting grid, per axis.
PX is screen pixels per game pixel: 4 for a 320x200 view at 1280x800, 5 for the 16:9 preset at
1920x1080, a fraction such as 3.497 (1280/366) for the Deck preset.  A change counts as on the grid
when it lies within half a screen pixel of a grid line; with a whole PX that is exactly the
dominant phase."""
import sys
from PIL import Image
im = Image.open(sys.argv[1]).convert('RGB'); w, h = im.size
k = float(sys.argv[2]) if len(sys.argv) > 2 else 4.0
px = im.load()
cx = [x for y in range(40, h - 40, 19) for x in range(1, w) if px[x, y] != px[x - 1, y]]
cy = [y for x in range(40, w - 40, 31) for y in range(1, h) if px[x, y] != px[x, y - 1]]


def on_grid(changes):
    best = 0
    for i in range(80):
        ph = k * i / 80
        best = max(best, sum(1 for c in changes if min((c - ph) % k, k - (c - ph) % k) < 0.5))
    return best / max(1, len(changes))


print('x on-grid %.0f%% | y on-grid %.0f%%' % (100 * on_grid(cx), 100 * on_grid(cy)))
