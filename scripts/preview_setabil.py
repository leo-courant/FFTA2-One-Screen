#!/usr/bin/env python3
"""Set Abilities without the stray stats panel (ticket 32): preview/setabil.html.

usage: preview_setabil.py
Needs shots/t32 (solo.py captures, 1280x800):
  sa_before.png / sa_after.png  late_setabil_w90 from scripts/solo_menus.sh, old and new build
  sa_list_before.png  sa_list with BLOB= a blob whose ticket-32 placement branch is made unconditional
  sa_list.png, sa_abilinfo.png  scripts/solo.py states/late/l_setabil.dst
      "w60,A8,w120,A8,w120,B8,w90,UP8,w40,A8,w120,DOWN8,w40,ssa_list,R12,w180,ssa_abilinfo" shots/t32
  shop_info.png / equip_info.png  buy_info / equip_info from scripts/solo_menus.sh (new build)"""
import json, os, shutil, time

SHOTS = [
    ("sa_after.png", "Set Abilities, now", "no panel over the unit panel any more: the screen is the game's own"),
    ("sa_before.png", "Set Abilities, before", "the mod's stats panel came up here (cut at 128 px) though no Item Info was open"),
    ("sa_list.png", "A on a slot", "the game's list of ability sets runs off the right edge as in the unmodified game; the set icons stay out of sight"),
    ("sa_list_before.png", "A on a slot, before", "the list was slid left and cut short, with its set icons showing beside it (review 1)"),
    ("sa_abilinfo.png", "then R (Ability Info)", "the game's own view of the highlighted set's abilities and mastery, with the mod's stats panel beside it as in equipment Item Info"),
    ("shop_info.png", "Shop Item Info", "unchanged: the stats panel still shows beside the game's Item Info"),
    ("equip_info.png", "Equipment Item Info", "unchanged: the stats panel still shows here too"),
]
OUT = "preview/t32"
os.makedirs(OUT, exist_ok=True)
t = int(time.time())
srcs = []
for name, _, _ in SHOTS:
    shutil.copy(os.path.join("shots/t32", name), os.path.join(OUT, name))
    srcs.append("t32/%s?t=%d" % (name, t))
btns = "".join('<button data-i=%d%s>%d. %s</button>' % (i, " class=on" if i == 0 else "", i + 1, s[1])
               for i, s in enumerate(SHOTS))
keys = "".join(str(i + 1) for i in range(len(SHOTS)))
html = """<!doctype html><meta charset=utf-8><meta name=viewport content="width=device-width,initial-scale=1">
<title>Set Abilities</title>
<style>body{background:#16161a;color:#ddd;font:15px/1.5 system-ui;margin:0;padding:24px}
h1{font-size:22px;margin:0 0 6px}p{color:#aaa;max-width:85ch}
.frame{overflow-x:auto}
img.deck{image-rendering:pixelated;display:block;max-width:none;outline:1px solid #444}
.btns{display:flex;gap:8px;margin:12px 0 8px;flex-wrap:wrap}
button{background:#26262c;color:#ddd;border:1px solid #555;border-radius:6px;padding:5px 12px;font:inherit;cursor:pointer}
button.on{background:#3a5a8c;border-color:#7aa2e0;color:#fff}
#note{color:#cde;font-weight:600;min-height:1.5em}</style>
<h1>Set Abilities (ticket 32)</h1>
<p>The mod's screen on the Deck preset, 1280x800, one picture pixel per display pixel. Flip with the buttons or the keys
<b>1</b> to <b>%d</b>.</p>
<p id=note></p>
<div class=btns>%s</div>
<div class=frame><img class=deck src="%s" alt="capture"></div>
<script>
const srcs = %s, notes = %s;
const dpr = window.devicePixelRatio || 1, im = document.querySelector("img.deck");
im.style.width = (1280 / dpr) + "px"; im.style.height = (800 / dpr) + "px";
function show(i) {
  if (i >= srcs.length) return;
  im.src = srcs[i]; document.getElementById("note").textContent = "What to look at: " + notes[i];
  document.querySelectorAll("button").forEach(b => b.classList.toggle("on", +b.dataset.i === i));
}
document.querySelectorAll("button").forEach(b => b.addEventListener("click", () => show(+b.dataset.i)));
document.addEventListener("keydown", e => { const i = "%s".indexOf(e.key); if (i >= 0 && e.key) show(i); });
show(0);
</script>""" % (len(SHOTS), btns, srcs[0], json.dumps(srcs), json.dumps([s[2] for s in SHOTS]), keys)
open("preview/setabil.html", "w").write(html)
print("preview/setabil.html written")
