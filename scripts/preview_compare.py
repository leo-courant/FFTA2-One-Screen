#!/usr/bin/env python3
"""Before/after page of the mod's screen: preview/compare.html.
usage: preview_compare.py NAME:caption ...   (pictures shots/solo_before/NAME.png and
shots/solo/NAME.png; copy shots/solo to shots/solo_before before changing the code)"""
import os, shutil, sys, time
os.makedirs("preview/compare", exist_ok=True)
t = int(time.time()); body = ""
for arg in sys.argv[1:]:
    name, _, cap = arg.partition(":")
    for d in ("solo_before", "solo"):
        shutil.copy("shots/%s/%s.png" % (d, name), "preview/compare/%s_%s.png" % (d, name))
    body += ('<section><h2>%s</h2><div class=row>'
             '<figure><img src="compare/solo_before_%s.png?t=%d" alt=""><figcaption>Before</figcaption></figure>'
             '<figure><img src="compare/solo_%s.png?t=%d" alt=""><figcaption>Now</figcaption></figure></div></section>') % (cap or name, name, t, name, t)
open("preview/compare.html", "w").write("""<!doctype html><meta charset=utf-8><meta name=viewport content="width=device-width,initial-scale=1">
<title>Before and after</title>
<style>body{background:#16161a;color:#ddd;font:15px/1.5 system-ui;margin:0;padding:24px}h1{font-size:22px;margin:0 0 6px}
h2{font-size:16px;margin:36px 0 8px}p{color:#aaa;max-width:75ch}
.row{display:grid;grid-template-columns:repeat(auto-fit,minmax(min(480px,100%%),1fr));gap:16px}
figure{margin:0}figcaption{color:#bbb;font-size:13px;margin-top:5px}
img{image-rendering:pixelated;border:1px solid #444;display:block;width:100%%;height:auto}a{color:#9cd}</style>
<h1>The mod's screen, before and after</h1>
<p>One screen, widescreen, at Deck resolution. All menus as they are now: <a href="menus.html">menus.html</a>.</p>%s""" % body)
print("preview/compare.html written")
