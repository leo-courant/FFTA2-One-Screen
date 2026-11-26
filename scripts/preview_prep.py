#!/usr/bin/env python3
"""The banner around a battle (ticket 17): unit placement, the privilege list and the Help
window, on the Deck and 4:3 presets: preview/prep.html.

usage: preview_prep.py
Needs the captures in shots/t17 (the steps are in ticket 17): deck_*.png and 43_*.png from
scripts/solo.py / scripts/solo_menus.sh, 43b_*.png the same 4:3 walks on the build before
the ticket, m_*.png real melonDS captures from states/m_battle1.ml1 (Y = Help)."""
import os, shutil, time

# (file, before file or None, width, height, title, note)
SHOTS = [
    ("deck_place.png", None, 1280, 800, "Deck: placement 1/5",
     "already clear: the n/5 heading top left, the B hint below the banner"),
    ("deck_place2.png", None, 1280, 800, "Deck: placement 5/5",
     "the X Begin Battle hint shows bottom right"),
    ("deck_privpick.png", None, 1280, 800, "Deck: privilege list", "the heading sits left of the banner"),
    ("m_deck_help.png", None, 1280, 800, "Deck: Help (melonDS)", "the Help window sits under the banner"),
    ("43_place.png", "43b_place.png", 1024, 768, "4:3: placement 1/5",
     "the B hint used to sit on the banner and hide the law; now it drops below the turn order"),
    ("43_privpick.png", "43b_privpick.png", 1024, 768, "4:3: privilege list",
     "the heading reaches the banner's corner: banner and turn order step aside while the list is up"),
    ("43_help.png", "43b_help.png", 1024, 768, "4:3: Help",
     "the Help window covers the corner: banner and turn order step aside instead of peeking out"),
    ("m_43_help.png", None, 1024, 768, "4:3: Help (melonDS)", "the same in real melonDS"),
    ("m_43_help_cmd.png", None, 1024, 768, "4:3: before Help (melonDS)", "the banner is back as soon as Help closes"),
    ("43_target.png", "43b_target.png", 1024, 768, "4:3: choosing a target",
     "the same B hint in battle: it used to cover the privilege box"),
    ("43_action.png", "43b_action.png", 1024, 768, "4:3: Action list",
     "unchanged: the action name bar runs under the banner and the turn order by design"),
]
OUT = "preview/t17"
os.makedirs(OUT, exist_ok=True)
t = int(time.time())
data = []
for name, before, w, h, title, note in SHOTS:
    for f in (name, before):
        if f:
            shutil.copy(os.path.join("shots/t17", f), os.path.join(OUT, f))
    data.append('{a:"t17/%s?t=%d",b:%s,w:%d,h:%d}' % (name, t, '"t17/%s?t=%d"' % (before, t) if before else "null", w, h))
btns = "".join('<button data-i=%d%s>%s <small>%s</small></button>' % (i, " class=on" if i == 0 else "", s[4], s[5])
               for i, s in enumerate(SHOTS))
open("preview/prep.html", "w").write("""<!doctype html><meta charset=utf-8><meta name=viewport content="width=device-width,initial-scale=1">
<title>Banner around battles</title>
<style>body{background:#16161a;color:#ddd;font:15px/1.5 system-ui;margin:0;padding:24px}
h1{font-size:22px;margin:0 0 6px}p{color:#aaa;max-width:85ch}
.frame{overflow-x:auto}
img.shot{image-rendering:pixelated;display:block;max-width:none;outline:1px solid #444}
.btns{display:flex;gap:8px;margin:12px 0 8px;flex-wrap:wrap}
button{background:#26262c;color:#ddd;border:1px solid #555;border-radius:6px;padding:5px 12px;font:inherit;cursor:pointer;text-align:left;max-width:30em}
button small{color:#999;display:block}button.on{background:#3a5a8c;border-color:#7aa2e0;color:#fff}button.on small{color:#cde}
#ba{margin:4px 0 8px;color:#9cd}#ba b{color:#fff}#ba.before b{color:#f0b060}</style>
<h1>The banner around a battle (ticket 17)</h1>
<p>On the Deck preset the banner already stays clear of placement, the privilege list and Help; nothing there changed.
On 4:3 there is no side room, so the game's own panels reach the banner's corner: the B hint now drops below the
banner and turn order, and a bigger panel lying on the corner (the privilege heading, Help) makes the banner and turn
order step aside while it is up. Pictures are shown one screen pixel per display pixel. Pick a picture with the buttons or
<b>&larr;</b> <b>&rarr;</b>; where there is a before picture, <b>B</b> or a click on the picture flips to it.</p>
<div class=btns>%s</div>
<div id=ba></div>
<div class=frame><img class=shot alt="capture"></div>
<script>
const D = [%s], dpr = window.devicePixelRatio || 1;
let cur = 0, before = false;
const im = document.querySelector("img.shot"), ba = document.getElementById("ba");
function show() {
  const d = D[cur];
  if (!d.b) before = false;
  im.src = before ? d.b : d.a;
  im.style.width = (d.w / dpr) + "px"; im.style.height = (d.h / dpr) + "px";
  ba.className = before ? "before" : "";
  ba.innerHTML = d.b ? (before ? "<b>BEFORE</b> (the build before this ticket), B for after" : "<b>AFTER</b>, B for before") : "&nbsp;";
  document.querySelectorAll("button").forEach(b => b.classList.toggle("on", +b.dataset.i === cur));
}
document.querySelectorAll("button").forEach(b => b.addEventListener("click", () => { cur = +b.dataset.i; before = false; show(); }));
im.addEventListener("click", () => { before = !before; show(); });
document.addEventListener("keydown", e => {
  if (e.key === "b" || e.key === "B") { before = !before; show(); }
  else if (e.key === "ArrowRight") { cur = Math.min(cur + 1, D.length - 1); before = false; show(); }
  else if (e.key === "ArrowLeft") { cur = Math.max(cur - 1, 0); before = false; show(); }
});
show();
</script>""" % (btns, ",".join(data)))
print("preview/prep.html written")
