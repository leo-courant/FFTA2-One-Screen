#!/usr/bin/env python3
"""Quest 19's banner and turn order, before and after ticket 41: preview/bannercut.html.

usage: preview_banner_cut.py
Needs shots/t41/before.png and after.png: scripts/solo.py states/battles/b19.dst "w30,sx,w30,sy"
on the build before ticket 41 (ROM=...) and on the current one (Deck preset, 1280x800)."""
import os, shutil, time
os.makedirs("preview/t41", exist_ok=True)
for n in ("before", "after"):
    shutil.copy("shots/t41/%s.png" % n, "preview/t41/%s.png" % n)
t = int(time.time())
open("preview/bannercut.html", "w").write("""<!doctype html><meta charset=utf-8>
<meta name=viewport content="width=device-width,initial-scale=1"><title>Quest 19 banner</title>
<style>body{background:#16161a;color:#ddd;font:15px/1.5 system-ui;margin:0;padding:24px}
h1{font-size:22px;margin:0 0 6px}p{color:#aaa;max-width:85ch}.frame{overflow-x:auto}
img{image-rendering:pixelated;display:block;outline:1px solid #444;max-width:none}
button{font:inherit;padding:6px 14px;margin-right:8px;background:#2a2a32;color:#ddd;border:1px solid #555;cursor:pointer}
button.on{background:#c9a24a;color:#111}</style>
<h1>Quest 19: banner and turn order (ticket 41)</h1>
<p>Look at the banner's law at the top right, and the turn order at the bottom.
Press 1 for the fixed build, 2 for before.</p>
<p><button data-n=after class=on>1 Now</button><button data-n=before>2 Before</button></p>
<div class=frame><img id=p></div>
<script>
const p=document.getElementById('p'),bs=[...document.querySelectorAll('button')];
p.style.width=1280/devicePixelRatio+'px';
function show(n){p.src='t41/'+n+'.png?t=%d';bs.forEach(b=>b.classList.toggle('on',b.dataset.n==n))}
bs.forEach(b=>b.onclick=()=>show(b.dataset.n));
onkeydown=e=>{if(e.key=='1')show('after');if(e.key=='2')show('before')};show('after');
</script>
""" % t)
print("preview/bannercut.html written")
