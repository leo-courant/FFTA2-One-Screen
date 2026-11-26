#!/usr/bin/env python3
"""The mod on top of another mod (ticket 27): preview/mods.html.

usage: preview_mods.py
Needs shots/t27: clean_deck.png and promise-rewrit.png (scripts/solo.py on the first-battle
states that scripts/to_battle.sh made from build/t27/ok_*.nds) and tests.txt (the output of
python3 scripts/test_modpatch.py with the Promise Rewritten xdelta)."""
import html
import os
import shutil
import time

SHOTS = [
    ("promise-rewrit.png", "With Promise Rewritten", "the rebalance applied first, then this mod with the "
     "players' patcher: Alulis has 71/71 HP and 107/107 MP"),
    ("clean_deck.png", "Clean game", "the same moment on the clean ROM, for comparison: 92/92 HP, 10/45 MP"),
]
OUT = "preview/t27"
os.makedirs(OUT, exist_ok=True)
t = int(time.time())
srcs = []
for name, _, _ in SHOTS:
    shutil.copy(os.path.join("shots/t27", name), os.path.join(OUT, name))
    srcs.append("t27/%s?t=%d" % (name, t))
tests = html.escape(open("shots/t27/tests.txt").read())
btns = "".join('<button data-i=%d%s>%d. %s <small>%s</small></button>' % (i, " class=on" if i == 0 else "", i + 1, s[1], s[2])
               for i, s in enumerate(SHOTS))
open("preview/mods.html", "w").write("""<!doctype html><meta charset=utf-8><meta name=viewport content="width=device-width,initial-scale=1">
<title>With other mods</title>
<style>body{background:#16161a;color:#ddd;font:15px/1.5 system-ui;margin:0;padding:24px}
h1{font-size:22px;margin:0 0 6px}h2{font-size:17px;margin:24px 0 6px}p{color:#aaa;max-width:85ch}
.frame{overflow-x:auto}
img.deck{image-rendering:pixelated;display:block;max-width:none;outline:1px solid #444}
.btns{display:flex;gap:8px;margin:12px 0 8px;flex-wrap:wrap}
button{background:#26262c;color:#ddd;border:1px solid #555;border-radius:6px;padding:5px 12px;font:inherit;cursor:pointer;text-align:left}
button small{color:#999}button.on{background:#3a5a8c;border-color:#7aa2e0;color:#fff}button.on small{color:#cde}
pre{background:#1e1e24;border:1px solid #333;border-radius:6px;padding:12px;overflow-x:auto;font-size:12.5px;line-height:1.45;color:#ccc}</style>
<h1>The mod on top of another mod</h1>
<p>The first battle at Steam Deck size, one screen pixel per display pixel. Flip with the buttons or the keys <b>1</b> and <b>2</b>.
The other mod is <i>Promise Rewritten</i> 0.9.7, a rebalance for FFTA2 USA that changes a big data file and five
instructions of the game code, none of them a place this mod changes. Both ROMs were played from power-on to this
battle with the same key presses.</p>
<div class=btns>%s</div>
<div class=frame><img class=deck src="%s" data-srcs="%s" alt="first battle"></div>
<h2>Patcher tests</h2>
<p>The players' patcher (one Python file, nothing else needed) run on each case. Two "rebuilt" ROMs with the
files laid out differently also played to the first battle, pixel-identical to the clean build.</p>
<pre>%s</pre>
<script>
const dpr = window.devicePixelRatio || 1;
document.querySelectorAll("img.deck").forEach(im => { im.style.width = (1280 / dpr) + "px"; im.style.height = (800 / dpr) + "px"; });
function show(i) {
  const im = document.querySelector("img.deck"), srcs = im.dataset.srcs.split("|");
  if (i >= srcs.length) return;
  im.src = srcs[i];
  document.querySelectorAll("button").forEach(b => b.classList.toggle("on", +b.dataset.i === i));
}
document.querySelectorAll("button").forEach(b => b.addEventListener("click", () => show(+b.dataset.i)));
document.addEventListener("keydown", e => { const i = "12".indexOf(e.key); if (i >= 0 && e.key) show(i); });
</script>""" % (btns, srcs[0], "|".join(srcs), tests))
print("preview/mods.html written")
