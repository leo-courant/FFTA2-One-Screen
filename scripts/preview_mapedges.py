#!/usr/bin/env python3
"""The battle map in the side areas, panned to each map edge, in real melonDS at Steam Deck
size, first battle (ticket 04) and second battle's backdrop (ticket 05): preview/mapedges.html.

usage: preview_mapedges.py
Needs the captures in shots/t04 and shots/t05, made with scripts/melon_state.py from
states/m_battle1.ml1 and states/m_battle2.ml1 (the steps are in tickets 04 and 05)."""
import os, shutil, time

SHOTS = [
    ("t04/end_move.png", "Battle 1", "Move chosen: the camera where the turn begins"),
    ("t04/end_right.png", "Right", "cursor held right: the map's east end is in view"),
    ("t04/end_up.png", "Then up", "cursor held up: the far corner"),
    ("t04/end_left.png", "Then left", "cursor held left: the west end, map in the left side area"),
    ("t04/end_down.png", "Then down", "cursor held down: the near corner"),
    ("t04/pan_r3.png", "Mid-pan", "a frame taken between short presses while the camera moves"),
    ("t05/end_move.png", "Battle 2", "a second backdrop: sky, clouds and a yellow haze"),
    ("t05/end_right.png", "Right", "the map's east end; haze carries on to the right edge"),
    ("t05/end_up.png", "Then up", "the far end: clouds run on past the old 4:3 edge"),
    ("t05/end_left.png", "Then left", "the west end, sky both sides"),
]
OUT = "preview/mapedges"
os.makedirs(OUT, exist_ok=True)
t = int(time.time())
srcs = []
for name, _, _ in SHOTS:
    os.makedirs(os.path.join(OUT, os.path.dirname(name)), exist_ok=True)
    shutil.copy(os.path.join("shots", name), os.path.join(OUT, name))
    srcs.append("mapedges/%s?t=%d" % (name, t))
keys = "1234567890"[:len(SHOTS)]
btns = "".join('<button data-i=%d%s>%s. %s <small>%s</small></button>' % (i, " class=on" if i == 0 else "", keys[i], s[1], s[2])
               for i, s in enumerate(SHOTS))
open("preview/mapedges.html", "w").write("""<!doctype html><meta charset=utf-8><meta name=viewport content="width=device-width,initial-scale=1">
<title>Map edges</title>
<style>body{background:#16161a;color:#ddd;font:15px/1.5 system-ui;margin:0;padding:24px}
h1{font-size:22px;margin:0 0 6px}p,li{color:#aaa;max-width:85ch}
.frame{overflow-x:auto}
img.deck{image-rendering:pixelated;display:block;max-width:none;outline:1px solid #444}
.btns{display:flex;gap:8px;margin:12px 0 8px;flex-wrap:wrap}
button{background:#26262c;color:#ddd;border:1px solid #555;border-radius:6px;padding:5px 12px;font:inherit;cursor:pointer;text-align:left}
button small{color:#999}button.on{background:#3a5a8c;border-color:#7aa2e0;color:#fff}button.on small{color:#cde}
#size{color:#9cd}</style>
<h1>Map and backdrop in the side areas, at each map edge</h1>
<p>Real melonDS captures of the first two battles on the Deck preset (OpenGL, 8x), the whole 1280x800 screen, one screen pixel per pixel of
your display (<span id=size></span>). Flip with the buttons or the keys <b>1</b> to <b>%s</b>.</p>
<p>Check only, no change to the mod: with the camera pushed to each edge of the map, the side areas show map wherever
there is map, and the backdrop beyond it. No stripes, no missing tiles, nothing popping in or out while the camera moves.
The second battle's backdrop (sky and haze, keys 7 to 0) continues past the old 4:3 edges with no seam and no black.</p>
<section><div class=btns>%s</div>
<div class=frame><img class=deck src="%s" data-srcs="%s" alt="battle map"></div></section>
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
</script>""" % (keys[-1], btns, srcs[0], "|".join(srcs), keys))
print("preview/mapedges.html written")
