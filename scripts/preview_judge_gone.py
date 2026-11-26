#!/usr/bin/env python3
"""Preview of ticket 42: preview/judgegone.html, the banner and turn order after the judge has left.

usage: preview_judge_gone.py      (~1 min; uses the shared melonDS rig)
melonDS at Deck size on quests 17 and 23 (states/m_q17.ml1, m_q23.ml1: the law broken, the
judge gone), with the current build and the one from before (BEFORE, default
build/t42-old.nds); then the 16:9 and 4:3 presets from states/battles/b17_nojudge.dst."""
import os, shutil, subprocess, sys, time
ROOT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..")
os.chdir(ROOT)
BEFORE = os.environ.get("BEFORE", "build/t42-old.nds")
OUT = "preview/t42"
os.makedirs(OUT, exist_ok=True)
if subprocess.run(["pgrep", "-x", "melonDS"], stdout=subprocess.DEVNULL).returncode == 0:
    sys.exit("melonDS is running (another session's rig?): try again later")


def melon(state, name, rom):
    # melonDS runs on the host, which cannot see a sandboxed /tmp: capture into shots/
    out = "shots/t42/page_%s.png" % name
    env = dict(os.environ, ROM=rom)
    subprocess.run([sys.executable, "scripts/melon_state.py", state, out], env=env, check=True, stdout=subprocess.DEVNULL)
    shutil.copy(out, os.path.join(OUT, name + ".png"))


def solo(rom, name, extra):
    d = "shots/t42/page_" + name
    env = dict(os.environ, ROM=rom, **extra)
    subprocess.run([sys.executable, "scripts/solo.py", "states/battles/b17_nojudge.dst", "w40,sshot", d],
                   env=env, check=True, stdout=subprocess.DEVNULL)
    shutil.copy(os.path.join(d, "shot.png"), os.path.join(OUT, name + ".png"))


for q in ("q17", "q23"):
    melon("states/m_%s.ml1" % q, q + "_after", "build/ffta2-1screen.nds")
    if os.path.exists(BEFORE):
        melon("states/m_%s.ml1" % q, q + "_before", BEFORE)
solo("build/ffta2-16x9.nds", "p16_after", {"SCALE": "5"})
solo("build/ffta2-4x3.nds", "p43_after", {"FIT": "1280x960"})

SCENES = [("q17", "Quest 17 (Deck, melonDS)", 1280), ("q23", "Quest 23 (Deck, melonDS)", 1280),
          ("p16", "Quest 17 on 16:9 (1920x1080)", 1920), ("p43", "Quest 17 on 4:3 (1280x960)", 1280)]
buttons = "".join('<button data-n="%d">%d %s</button>' % (i, i + 1, t) for i, (_, t, _) in enumerate(SCENES))
open("preview/judgegone.html", "w").write("""<!doctype html><meta charset=utf-8>
<meta name=viewport content="width=device-width,initial-scale=1"><title>After the judge leaves</title>
<style>body{background:#16161a;color:#ddd;font:15px/1.5 system-ui;margin:0;padding:24px}
h1{font-size:22px;margin:0 0 6px}p{color:#aaa;max-width:85ch}.frame{overflow-x:auto}
img{image-rendering:pixelated;display:block;outline:1px solid #444;max-width:none}
button{font:inherit;padding:6px 12px;margin:0 6px 6px 0;background:#2a2a32;color:#ddd;border:1px solid #555;cursor:pointer}
button.on{background:#c9a24a;color:#111}button:disabled{opacity:.4;cursor:default}</style>
<h1>Banner and turn order after the judge leaves (ticket 42)</h1>
<p>The law has been broken and the judge has gone, so the battle has no law or privilege left. The banner
now keeps the objective and the turn order stays at the bottom; before, both disappeared for the
rest of the battle. Keys 1-4 pick the screen; 0 switches to how it was before (melonDS screens only).</p>
<p>%s<button data-b=1>0 Before</button></p><div class=frame><img id=p></div>
<script>
const S=%s,p=document.getElementById('p'),bs=[...document.querySelectorAll('[data-n]')],bb=document.querySelector('[data-b]');
let n=0,b=false;
function show(){const q=S[n][0][0]=='q';if(!q)b=false;p.src='t42/'+S[n][0]+(b?'_before':'_after')+'.png?t=%d';
p.style.width=S[n][1]/devicePixelRatio+'px';
bs.forEach(x=>x.classList.toggle('on',x.dataset.n==n));bb.classList.toggle('on',b);bb.disabled=!q}
bs.forEach(x=>x.onclick=()=>{n=+x.dataset.n;show()});bb.onclick=()=>{b=!b;show()};
onkeydown=e=>{if(e.key=='0'){if(S[n][0][0]=='q'){b=!b;show()}}else if(e.key>='1'&&e.key<=''+S.length){n=e.key-1;show()}};show();
</script>
""" % (buttons, str([[s[0], s[2]] for s in SCENES]).replace("'", '"'), time.time()))
print("preview/judgegone.html -> http://localhost:8765/judgegone.html")
