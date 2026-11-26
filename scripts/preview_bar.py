#!/usr/bin/env python3
"""Preview of ticket 37: preview/actionbar.html, the action name bar edge to edge.

usage: preview_bar.py      (~30 s)
Captures with the current build and with the one from before (BEFORE, default
build/t37_before.nds).  MELON=file adds a melonDS capture of the same screen as battle 2's."""
import os, shutil, subprocess, sys, time
ROOT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..")
os.chdir(ROOT)
BEFORE = os.environ.get("BEFORE", "build/t37_before.nds")
OUT = "preview/t37"
os.makedirs(OUT, exist_ok=True)
# key, state, script, caption
SCENES = [("attack", "states/battles/b3.dst", "w22,sx", "Enemy ability, forecast up"),
          ("target", "states/s_battle2.dst", "w10,DOWN,w15,A,w60,A,w100,sx", "Choosing a target: B hint below the bar"),
          ("action", "states/s_battle2.dst", "w10,DOWN,w15,A,w60,sx", "Action menu"),
          ("longname", "states/battles/b20.dst", "w150,sx", "Later battle, wide banner")]
for key, st, script, _ in SCENES:
    for tag, rom in (("after", None), ("before", BEFORE)):
        if rom and not os.path.exists(rom):
            continue
        d = "shots/t37/%s_%s" % (key, tag)
        env = dict(os.environ, **({"ROM": rom} if rom else {}))
        subprocess.run([sys.executable, "scripts/solo.py", st, script, d], env=env, check=True, stdout=subprocess.DEVNULL)
        shutil.copy(d + "/x.png", "%s/%s_%s.png" % (OUT, key, tag))
items = [(k, c, True) for k, _, _, c in SCENES]
if os.environ.get("MELON"):
    shutil.copy(os.environ["MELON"], OUT + "/melon_after.png")
    items.append(("melon", "melonDS, choosing a target", False))
buttons = "".join('<button data-n="%d">%d %s</button>' % (i, i + 1, c) for i, (_, c, _) in enumerate(items))
open("preview/actionbar.html", "w").write("""<!doctype html><meta charset=utf-8>
<meta name=viewport content="width=device-width,initial-scale=1"><title>Action name bar</title>
<style>body{background:#16161a;color:#ddd;font:15px/1.5 system-ui;margin:0;padding:24px}
h1{font-size:22px;margin:0 0 6px}p{color:#aaa;max-width:85ch}.frame{overflow-x:auto}
img{image-rendering:pixelated;display:block;outline:1px solid #444;max-width:none}
button{font:inherit;padding:6px 12px;margin:0 6px 6px 0;background:#2a2a32;color:#ddd;border:1px solid #555;cursor:pointer}
button.on{background:#c9a24a;color:#111}</style>
<h1>Action name bar (ticket 37)</h1>
<p>Look at the dark bar with the action's name near the top: it reaches both screen edges. Number keys pick the
screen; 0 switches to how it was before.</p>
<p>%s<button data-b=1>0 Before</button></p><div class=frame><img id=p></div>
<script>
const S=%s,p=document.getElementById('p'),bs=[...document.querySelectorAll('[data-n]')],bb=document.querySelector('[data-b]');
let n=0,b=false;p.style.width=1280/devicePixelRatio+'px';
function show(){if(!S[n][1])b=false;p.src='t37/'+S[n][0]+(b?'_before':'_after')+'.png?t=%d';
bs.forEach(x=>x.classList.toggle('on',x.dataset.n==n));bb.classList.toggle('on',b);bb.disabled=!S[n][1]}
bs.forEach(x=>x.onclick=()=>{n=+x.dataset.n;show()});bb.onclick=()=>{b=!b;show()};
onkeydown=e=>{if(e.key=='0'){b=!b;show()}else if(e.key>='1'&&e.key<=''+S.length){n=e.key-1;show()}};show();
</script>
""" % (buttons, str([[k, int(h)] for k, _, h in items]).replace("'", '"'), time.time()))
print("preview/actionbar.html -> http://localhost:8765/actionbar.html")
