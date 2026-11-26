#!/usr/bin/env python3
"""Build preview/index.html from screenshots.
usage: preview.py "Title" "intro text" IMG::caption [IMG::caption ...]
Images are copied into preview/ so the page is served by the local preview server."""
import html, os, shutil, sys, time
title, intro, items = sys.argv[1], sys.argv[2], sys.argv[3:]
out = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "preview")
os.makedirs(out, exist_ok=True)
figs = []
for n, it in enumerate(items):
    path, _, cap = it.partition("::")
    name = "img%02d_%s" % (n, os.path.basename(path))
    shutil.copy(path, os.path.join(out, name))
    figs.append('<figure><img src="%s?t=%d"><figcaption>%s</figcaption></figure>' % (name, time.time(), html.escape(cap)))
open(os.path.join(out, "index.html"), "w").write("""<!doctype html><meta charset=utf-8><title>%s</title>
<style>body{background:#16161a;color:#ddd;font:15px system-ui;margin:0;padding:24px;text-align:center}
h1{font-size:18px}p{color:#aaa;max-width:760px;margin:8px auto 20px}
.row{display:flex;gap:24px;justify-content:center;flex-wrap:wrap}
figure{margin:0 0 20px}figcaption{color:#aaa;font-size:13px;margin-top:6px;max-width:512px}
img{image-rendering:pixelated;width:512px;max-width:100%%;border:1px solid #444}</style>
<h1>%s</h1><p>%s</p><div class=row>%s</div>""" % (html.escape(title), html.escape(title), html.escape(intro), "".join(figs)))
print("preview/index.html written")
