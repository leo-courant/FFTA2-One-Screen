#!/usr/bin/env python3
"""The law and objective announcement bars, lengthened (ticket 39): preview/bars.html.

usage: preview_bars.py
Needs solo.py captures (1280x800) of one walk on two builds: shots/t39/on (the mod) and
shots/t39/off (patch.py --define BAR_MIN=255, rule off): a45.png objective, c56.png law up."""
import os, shutil, time
OUT = "preview/t39"
os.makedirs(OUT, exist_ok=True)
t = int(time.time())
figs = ""
for name, shot, title in (("obj", "a45", "Objective bar"), ("law", "c56", "Law bar")):
    for d, label in (("on", "now"), ("off", "before")):
        shutil.copy("shots/t39/%s/%s.png" % (d, shot), "%s/%s_%s.png" % (OUT, name, d))
        figs += '<figure><img src="t39/%s_%s.png?t=%d"><figcaption>%s, %s</figcaption></figure>' % (name, d, t, title, label)
open("preview/bars.html", "w").write("""<!doctype html><meta charset=utf-8>
<meta name=viewport content="width=device-width,initial-scale=1"><title>The two bars</title>
<style>body{background:#16161a;color:#ddd;font:15px/1.5 system-ui;margin:0;padding:24px}h1{font-size:20px;margin:0 0 4px}
.g{display:grid;grid-template-columns:repeat(auto-fit,minmax(min(100%%,480px),1fr));gap:12px;max-width:1320px}
img{width:100%%;display:block}figure{margin:0}figcaption{color:#cde}</style>
<h1>The two bars shown when a battle starts</h1>
<p>Left: now, the bar runs to the screen edge. Right: before. Nothing else on the screen changed.</p>
<div class=g>%s</div>""" % figs)
print("preview/bars.html written")
