#!/usr/bin/env python3
"""Preview of ticket 43: preview/hairline.html, the speech bubble without the crack.

usage: preview_hairline.py      (~1 min; uses the shared melonDS rig; nothing else heavy
                                 should run meanwhile, or the rig's key presses come too late)
melonDS at Deck size from states/m_t30b.ml1 (event 137, two presses of A: a bubble bottom
left), with the current build and the one from before (BEFORE, default build/t43_before.nds),
each whole and enlarged 4x around the place the crack was."""
import os, shutil, subprocess, sys, time
from PIL import Image
ROOT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..")
os.chdir(ROOT)
BEFORE = os.environ.get("BEFORE", "build/t43_before.nds")
OUT = "preview/t43"
os.makedirs(OUT, exist_ok=True)
os.makedirs("shots/t43", exist_ok=True)
if subprocess.run(["pgrep", "-x", "melonDS"], stdout=subprocess.DEVNULL).returncode == 0:
    sys.exit("melonDS is running (another session's rig?): try again later")
CROP = (330, 585, 500, 800)


def melon(name, rom):
    # melonDS runs on the host, which cannot see a sandboxed /tmp: capture into shots/
    out = "shots/t43/page_%s.png" % name
    for _ in range(3):
        subprocess.run([sys.executable, "scripts/melon_state.py", "states/m_t30b.ml1", out, "x:1.5", "x:1.5"],
                       env=dict(os.environ, ROM=rom), check=True, stdout=subprocess.DEVNULL)
        im = Image.open(out).convert("RGB")
        if im.getpixel((300, 745)) == (195, 154, 97):      # the bubble is up
            break
    im.save(os.path.join(OUT, name + ".png"))
    c = im.crop(CROP)
    c.resize((c.width * 4, c.height * 4), Image.NEAREST).save(os.path.join(OUT, name + "_zoom.png"))


melon("after", "build/ffta2-1screen.nds")
melon("before", BEFORE)
open("preview/hairline.html", "w").write("""<!doctype html><meta charset=utf-8>
<meta name=viewport content="width=device-width,initial-scale=1"><title>Bubble hairline</title>
<style>body{background:#16161a;color:#ddd;font:15px/1.5 system-ui;margin:0;padding:24px}
h1{font-size:22px;margin:0 0 6px}h2{font-size:17px;margin:24px 0 6px}p{color:#aaa;max-width:85ch}
.frame{overflow-x:auto}img{image-rendering:pixelated;display:block;outline:1px solid #444;max-width:none}
.pair{display:flex;gap:16px;flex-wrap:wrap}.pair div{flex:none}
button{font:inherit;padding:6px 12px;margin:0 6px 6px 0;background:#2a2a32;color:#ddd;border:1px solid #555;cursor:pointer}
button.on{background:#c9a24a;color:#111}</style>
<h1>Speech bubble without the hairline (ticket 43)</h1>
<p>Real melonDS pictures at Deck size, from the talk in event 137. Before, a one-pixel line ran down
the bubble about a fifth of the way from its rounded end: the map showing through a crack between
two pieces of the bubble. 0 switches between now and before.</p>
<p><button data-b=0 class=on>Now</button><button data-b=1>0 Before</button></p>
<h2>Enlarged 4x where the line was</h2>
<div class=pair><div>Before<img src="t43/before_zoom.png?t=%(t)d"></div><div>Now<img src="t43/after_zoom.png?t=%(t)d"></div></div>
<h2>The whole screen</h2><div class=frame><img id=p></div>
<script>
const p=document.getElementById('p'),bs=[...document.querySelectorAll('[data-b]')];let b=0;
p.style.width=1280/devicePixelRatio+'px';
function show(){p.src='t43/'+(b?'before':'after')+'.png?t=%(t)d';bs.forEach((x,i)=>x.classList.toggle('on',i==b))}
bs.forEach((x,i)=>x.onclick=()=>{b=i;show()});document.onkeydown=e=>{if(e.key=='0'){b=1-b;show()}};show()
</script>""" % {"t": int(time.time())})
print("preview/hairline.html")
