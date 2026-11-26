#!/usr/bin/env python3
"""Preview of tickets 40 and 34: preview/ending.html, battle endings without banner and turn order,
"Complete!" to both screen edges, and the button-hint labels without their second copy.

usage: preview_ending.py      (after scripts/to_saves.sh; ~1 min)
Captures battle 1's ending (states/s_results.dst) with the current build and with the one
from before (BEFORE, default build/t40_before.nds), and battle 2's: the game's own "battle
won" event flag 0x61B is set and Alulis waits, so the game's win check ends the battle."""
import os, shutil, subprocess, sys, time
ROOT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..")
os.chdir(ROOT)
BEFORE = os.environ.get("BEFORE", "build/t40_before.nds")
OUT = "preview/t40"
os.makedirs(OUT, exist_ok=True)


def solo(state, script, prefix, rom=None):
    env = dict(os.environ)
    if rom:
        env["ROM"] = rom
    d = "shots/t40/page_" + prefix
    subprocess.run([sys.executable, "scripts/solo.py", state, script, d], env=env, check=True, stdout=subprocess.DEVNULL)
    for f in os.listdir(d):
        shutil.copy(os.path.join(d, f), os.path.join(OUT, prefix + "_" + f))


B1 = "w5,A,w90,A,w90,scomplete,A,w90,A,w90,sresults,A,w90,A,w90,slaw"
WIN = "p0212D7F6=810"                           # event flag 0x61B at 0x0212D734 + 0xC3, bit 3
B2 = "w10,slive," + WIN + ",DOWN,w15,DOWN,w15,A,w40," + ",".join(["A,w100"] * 4) + ",scomplete," + \
    "A,w100,A,w100,sresults,A,w100,A,w100,A,w60,slaw"
solo("states/s_results.dst", B1, "b1after")
if os.path.exists(BEFORE):
    solo("states/s_results.dst", B1, "b1before", BEFORE)
solo("states/s_battle2.dst", B2, "b2after")
# hint labels: whole screens, with before
for st, script, n in (("states/s_battle2.dst", "w10,shint", "h1"), ("states/battles/b20_place.dst", "w10,shint", "h2")):
    solo(st, script, n + "after")
    if os.path.exists(BEFORE):
        solo(st, script, n + "before", BEFORE)

SCENES = [("b1", "complete", "Battle 1: Complete!"), ("b1", "results", "Battle 1: results"), ("b1", "law", "Battle 1: law bonus"),
          ("b2", "live", "Battle 2: still fighting"), ("b2", "complete", "Battle 2: Complete!"),
          ("h1", "hint", "Labels: battle menu"), ("h2", "hint", "Labels: placement"),
          ("b2", "results", "Battle 2: results"), ("b2", "law", "Battle 2: law bonus")]
buttons = "".join('<button data-n="%d">%d %s</button>' % (i, i + 1, t) for i, (_, _, t) in enumerate(SCENES))
open("preview/ending.html", "w").write("""<!doctype html><meta charset=utf-8>
<meta name=viewport content="width=device-width,initial-scale=1"><title>Battle endings</title>
<style>body{background:#16161a;color:#ddd;font:15px/1.5 system-ui;margin:0;padding:24px}
h1{font-size:22px;margin:0 0 6px}p{color:#aaa;max-width:85ch}.frame{overflow-x:auto}
img{image-rendering:pixelated;display:block;outline:1px solid #444;max-width:none}
button{font:inherit;padding:6px 12px;margin:0 6px 6px 0;background:#2a2a32;color:#ddd;border:1px solid #555;cursor:pointer}
button.on{background:#c9a24a;color:#111}</style>
<h1>Battle endings and button labels (tickets 40, 34)</h1>
<p>1 and 5: the Complete! bar reaches both screen edges. 6 and 7: the button labels at the bottom (Config, Help,
Place Unit) have one clean copy inside their frames. Keys 1-9 pick the screen; 0 switches to how it was before,
where there is a before.</p>
<p>%s<button data-b=1>0 Before</button></p><div class=frame><img id=p></div>
<script>
const S=%s,p=document.getElementById('p'),bs=[...document.querySelectorAll('[data-n]')],bb=document.querySelector('[data-b]');
let n=0,b=false;p.style.width=1280/devicePixelRatio+'px';
function show(){if(!/^(b1|h)/.test(S[n][0]))b=false;p.src='t40/'+S[n][0]+(b?'before_':'after_')+S[n][1]+'.png?t=%d';
bs.forEach(x=>x.classList.toggle('on',x.dataset.n==n));bb.classList.toggle('on',b);bb.disabled=!/^(b1|h)/.test(S[n][0])}
bs.forEach(x=>x.onclick=()=>{n=+x.dataset.n;show()});bb.onclick=()=>{b=!b;show()};
onkeydown=e=>{if(e.key=='0'){b=!b;show()}else if(e.key>='1'&&e.key<=''+S.length){n=e.key-1;show()}};show();
</script>
""" % (buttons, str([list(s[:2]) for s in SCENES]).replace("'", '"'), time.time()))
print("preview/ending.html -> http://localhost:8765/ending.html")
