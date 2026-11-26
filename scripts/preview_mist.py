#!/usr/bin/env python3
"""Preview of ticket 30: preview/mist.html, the story's mist scenes where the story plays them.

usage: preview_mist.py      (after the melonDS captures below)
Real melonDS captures at Deck size, taken with scripts/melon_state.py from states/m_q17.ml1 and
m_q23.ml1 (docs/test-saves.md) on two builds: shots/t30/fin_t30_before (before the ticket) and
shots/t30/fin_ffta2-1screen (now); the two runs land on slightly different moments."""
import os, shutil, time
OUT = "preview/t30"
os.makedirs(OUT, exist_ok=True)
B, A = "shots/t30/fin_t30_before/", "shots/t30/fin_ffta2-1screen/"
SCENES = [("Event 137: talk", A + "a_02.png", B + "a_02.png"),
          ("Event 137: no bubble", A + "a_28.png", B + "a_28.png"),
          ("Event 137: second talk", A + "a_12.png", B + "a_12.png"),
          ("Quest 18's battle", A + "b_2.png", B + "b_2.png"),
          ("Event 135: the flash", A + "q_11.png", B + "q_11.png"),
          ("Quest 24: Complete!", "shots/t30/m6/e_010.png", B + "c_3.png"),
          ("Event 151: farewell", A + "f_03.png", B + "f_03.png")]
for i, (_, a, b) in enumerate(SCENES):
    shutil.copy(a, "%s/%d_a.png" % (OUT, i))
    shutil.copy(b, "%s/%d_b.png" % (OUT, i))
buttons = "".join('<button data-n="%d">%d %s</button>' % (i, i + 1, t) for i, (t, _, _) in enumerate(SCENES))
open("preview/mist.html", "w").write("""<!doctype html><meta charset=utf-8>
<meta name=viewport content="width=device-width,initial-scale=1"><title>Mist scenes</title>
<style>body{background:#16161a;color:#ddd;font:15px/1.5 system-ui;margin:0;padding:24px}
h1{font-size:22px;margin:0 0 6px}p{color:#aaa;max-width:85ch}.frame{overflow-x:auto}
img{image-rendering:pixelated;display:block;outline:1px solid #444;max-width:none}
button{font:inherit;padding:6px 12px;margin:0 6px 6px 0;background:#2a2a32;color:#ddd;border:1px solid #555;cursor:pointer}
button.on{background:#c9a24a;color:#111}</style>
<h1>Story mist scenes (ticket 30)</h1>
<p>Real melonDS pictures at Deck size, reached by winning the battle before each scene. Keys 1-%d pick the
scene; 0 switches to how it was before. Late-story scenes: spoilers.</p>
<p>%s<button data-b=1>0 Before</button></p><div class=frame><img id=p></div>
<script>
const N=%d,p=document.getElementById('p'),bs=[...document.querySelectorAll('[data-n]')],bb=document.querySelector('[data-b]');
let n=0,b=false;p.style.width=1280/devicePixelRatio+'px';
function show(){p.src='t30/'+n+(b?'_b':'_a')+'.png?t=%d';bs.forEach((x,i)=>x.classList.toggle('on',i==n));bb.classList.toggle('on',b)}
bs.forEach((x,i)=>x.onclick=()=>{n=i;show()});bb.onclick=()=>{b=!b;show()};
document.onkeydown=e=>{if(e.key=='0'){b=!b;show()}else if(+e.key>0&&+e.key<=N){n=+e.key-1;show()}};show()
</script>""" % (len(SCENES), buttons, len(SCENES), int(time.time())))
