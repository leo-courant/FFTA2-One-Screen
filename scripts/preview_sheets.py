#!/usr/bin/env python3
"""In-battle sheets with the SELECT overlay, in real melonDS at Steam Deck size (ticket 15):
preview/sheets.html.

usage: preview_sheets.py
Needs the captures in shots/t15, made with scripts/melon_state.py from states/m_battle1.ml1
at FPS=60 (the steps are in ticket 15)."""
import os, shutil, time

SHOTS = [
    ("f3.png", "Unit Info", "Y on a unit, then SELECT: the unit sheet over the battle"),
    ("a_abil_ov.png", "View Abilities", "the ability list's sheet; the game's own list stays underneath"),
    ("f5.png", "Status", "Status opens Buffs/Debuffs; SELECT shows the unit sheet the game keeps on the info screen"),
    ("e_ov1.png", "Item List", "Shortsword: the game's sheet really is this empty (no abilities, only Attack 22)"),
    ("e_ov2dn.png", "Item List, D-pad", "Down with the overlay up: it stays and follows the cursor (Broadsword)"),
    ("f6.png", "Back in battle", "SELECT closes it, B backs out: banner and turn order are back"),
]
OUT = "preview/t15"
os.makedirs(OUT, exist_ok=True)
t = int(time.time())
srcs = []
for name, _, _ in SHOTS:
    shutil.copy(os.path.join("shots/t15", name), os.path.join(OUT, name))
    srcs.append("t15/%s?t=%d" % (name, t))
btns = "".join('<button data-i=%d%s>%d. %s <small>%s</small></button>' % (i, " class=on" if i == 0 else "", i + 1, s[1], s[2])
               for i, s in enumerate(SHOTS))
keys = "".join(str(i + 1) for i in range(len(SHOTS)))
open("preview/sheets.html", "w").write("""<!doctype html><meta charset=utf-8><meta name=viewport content="width=device-width,initial-scale=1">
<title>Battle sheets</title>
<style>body{background:#16161a;color:#ddd;font:15px/1.5 system-ui;margin:0;padding:24px}
h1{font-size:22px;margin:0 0 6px}p,li{color:#aaa;max-width:85ch}
.frame{overflow-x:auto}
img.deck{image-rendering:pixelated;display:block;max-width:none;outline:1px solid #444}
.btns{display:flex;gap:8px;margin:12px 0 8px;flex-wrap:wrap}
button{background:#26262c;color:#ddd;border:1px solid #555;border-radius:6px;padding:5px 12px;font:inherit;cursor:pointer;text-align:left}
button small{color:#999}button.on{background:#3a5a8c;border-color:#7aa2e0;color:#fff}button.on small{color:#cde}
#size{color:#9cd}</style>
<h1>Battle sheets with the SELECT overlay</h1>
<p>Real melonDS captures of the first battle on the Deck preset, the whole 1280x800 screen, one screen pixel per pixel of
your display (<span id=size></span>). Flip with the buttons or the keys <b>1</b> to <b>%d</b>.</p>
<p>No change to the mod was needed: on all four sheets SELECT gives the overlay (never the screen swap), the same way every
press, and it closes cleanly. B closes the overlay and the game takes the B as well (one step back), as in the menus
outside battle.</p>
<section><div class=btns>%s</div>
<div class=frame><img class=deck src="%s" data-srcs="%s" alt="battle sheet"></div></section>
<script>
const dpr = window.devicePixelRatio || 1;
document.querySelectorAll("img.deck").forEach(im => { im.style.width = (1280 / dpr) + "px"; im.style.height = (800 / dpr) + "px"; });
document.getElementById("size").textContent = dpr === 1 ? "your display shows it at exactly Deck size"
  : "your display scale is " + dpr + "x, so the picture is sized down to stay one-to-one";
function show(i) {
  const im = document.querySelector("img.deck"), srcs = im.dataset.srcs.split("|");
  if (i >= srcs.length) return;
  im.src = srcs[i];
  document.querySelectorAll("button").forEach(b => b.classList.toggle("on", +b.dataset.i === i));
}
document.querySelectorAll("button").forEach(b => b.addEventListener("click", () => show(+b.dataset.i)));
document.addEventListener("keydown", e => { const i = "%s".indexOf(e.key); if (i >= 0 && e.key) show(i); });
</script>""" % (len(SHOTS), btns, srcs[0], "|".join(srcs), keys))
print("preview/sheets.html written")
