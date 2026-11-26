#!/usr/bin/env python3
"""Preview of ticket 33: preview/bazaar.html, the bazaar's loot rows on the one screen.

usage: preview_bazaar.py      (~1 min)
Every moment of a trade (states/late/l_bz_*.dst, scripts/to_bazaar.sh) with the current
build and the one from before (BEFORE, default build/t33_head.nds), from scripts/solo.py at
the Deck's size (every bazaar screen is 3D, which solo.py shows exactly); and melonDS
captures of a whole trade, where there are some (MELON, default shots/t33/melon/final_*.png,
made from states/m_shopmenu.ml1 with the steps in the ticket).  The user chose option A
(the rows on the recipe list too) over B (rows once a recipe is chosen) on 2026-11-26."""
import json, os, shutil, subprocess, sys, time
ROOT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..")
os.chdir(ROOT)
P = sys.executable
BEFORE = os.environ.get("BEFORE", "build/t33_head.nds")
OUT = "preview/t33"
os.makedirs(OUT, exist_ok=True)
subprocess.run([P, "scripts/patch.py", "rom/ffta2.nds", "build/ffta2-1screen.nds"],
               check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
ROMS = {"before": BEFORE, "a": "build/ffta2-1screen.nds"}
MELON = os.environ.get("MELON", "shots/t33/melon/final")
MELON_OF = {"list": "_list", "craft": "_craft", "one": "_one", "two": "_two", "ask": "_ask", "new": ""}

MOMENTS = [
    ("list", "Recipe list", "Bronze Armor highlighted: it takes two loot kinds."),
    ("list3", "Recipe with three kinds", "Silver-sheened Armor takes Metal, Flora and Philtre."),
    ("craft", "Crafting menu", "The recipe chosen: nothing sent yet."),
    ("one", "One loot sent", "Platinum sent as the Metal: its row lights the grades one-star loot allows (B, C, D)."),
    ("two", "Two sent", "Leucojum as the Flora: both rows meet at grade C."),
    ("ask", "Send?", "Silver Liquid as the Philtre: the line runs down to the header, which now names the item it makes."),
    ("clear", "Back out?", "B with loot sent asks whether to clear it."),
    ("bronze", "Two-kind recipe", "Bronze Armor's crafting menu: two rows, room left below."),
    ("new", "After the trade", "The new item's sheet is on the info screen (SELECT shows it); nothing is added here."),
]
procs = []
for v, rom in ROMS.items():
    for m in MOMENTS:
        d = "shots/t33/page_%s" % v
        procs.append(subprocess.Popen([P, "scripts/solo.py", "states/late/l_bz_%s.dst" % m[0], "w30,s" + m[0], d],
                                      env=dict(os.environ, ROM=rom), stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL))
    for p in procs:
        p.wait()
    procs = []
    for m in MOMENTS:
        shutil.copy("shots/t33/page_%s/%s.png" % (v, m[0]), "%s/%s_%s.png" % (OUT, m[0], v))
for k, suffix in MELON_OF.items():
    if os.path.exists(MELON + suffix + ".png"):
        shutil.copy(MELON + suffix + ".png", "%s/%s_m.png" % (OUT, k))
HAS_M = [m[0] in MELON_OF and os.path.exists("%s/%s_m.png" % (OUT, m[0])) for m in MOMENTS]

VARIANTS = [("a", "Now"), ("m", "Now in melonDS"), ("before", "Before")]
mb = "".join('<button data-m="%d">%d %s</button>' % (i, i + 1, m[1]) for i, m in enumerate(MOMENTS))
vb = "".join('<button data-v="%s">%s %s</button>' % (v, k, t) for (v, t), k in zip(VARIANTS, "amz"))
open("preview/bazaar.html", "w").write("""<!doctype html><meta charset=utf-8>
<meta name=viewport content="width=device-width,initial-scale=1"><title>Bazaar on one screen</title>
<style>body{background:#16161a;color:#ddd;font:15px/1.5 system-ui;margin:0;padding:24px}
h1{font-size:22px;margin:0 0 6px}p{color:#aaa;max-width:90ch;margin:0 0 10px}.frame{overflow-x:auto}
img{image-rendering:pixelated;display:block;outline:1px solid #444;max-width:none}
button{font:inherit;padding:6px 12px;margin:0 6px 6px 0;background:#2a2a32;color:#ddd;border:1px solid #555;cursor:pointer}
button.on{background:#c9a24a;color:#111}#note{color:#ddd;min-height:1.5em}</style>
<h1>Bazaar: what a recipe needs, on the one screen (ticket 33)</h1>
<p>Option A, as chosen: the info screen's loot rows (which loot you sent for each kind, and the
grades that allows) and its recipe header (which names the item you will get) are shown at their own
size under the list, which moves up to the tab bar; the game's description box gives way to them, on
the recipe list too. Keys 1-9 pick the moment; A = now (DeSmuME, exact), M = the same moment in
melonDS (a separate run through the same trade, where captured), Z = before. Pictures are the Deck's
screen, 1280x800, one screen pixel per pixel.</p>
<p>%s</p><p>%s</p><p id=note></p><div class=frame><img id=p></div>
<script>
const M=%s,H=%s,p=document.getElementById('p'),note=document.getElementById('note'),
ms=[...document.querySelectorAll('[data-m]')],vs=[...document.querySelectorAll('[data-v]')];
let m=0,v='a';
function show(){if(v=='m'&&!H[m])v='a';p.src='t33/'+M[m][0]+'_'+v+'.png?t=%d';p.style.width=1280/devicePixelRatio+'px';note.textContent=M[m][2];
ms.forEach(x=>x.classList.toggle('on',x.dataset.m==m));vs.forEach(x=>x.classList.toggle('on',x.dataset.v==v))}
ms.forEach(x=>x.onclick=()=>{m=+x.dataset.m;show()});vs.forEach(x=>x.onclick=()=>{v=x.dataset.v;show()});
onkeydown=e=>{const k=e.key.toLowerCase();if(k>='1'&&k<=''+M.length){m=k-1;show()}
else if(k=='a'||k=='m'){v=k;show()}else if(k=='z'){v='before';show()}};show();
</script>
""" % (mb, vb, json.dumps([list(m) for m in MOMENTS]), json.dumps(HAS_M), time.time()))
print("preview/bazaar.html -> http://localhost:8765/bazaar.html")
