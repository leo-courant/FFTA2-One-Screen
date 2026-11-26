#!/usr/bin/env python3
"""The opening's falling scene (the book pulls the hero in) on the Deck preset, real melonDS
captures, before and after ticket 29: preview/story.html.

usage: preview_story.py
Needs shots/t06/deck_n16.png (before: ticket 06's capture, older build) and
shots/t29/melon/after_n26.png .. after_n28.png, made with
  scripts/melon_state.py states/m_story.ml1 shots/t29/melon/after.png  x:1.5 (x11)  then  x:1.5 s:nNN  for NN = 12..30
(melonDS drops some key presses, so the scene lands on a different press each run: pick the frames)."""
import os, shutil, time

SHOTS = [
    ("t06/deck_n16.png", "Before", "older build (ticket 06's capture): the scene stops at the 4:3 edges"),
    ("t29/melon/after_n27.png", "After", "the same scene: the game's own backdrop continues to the screen edges"),
    ("t29/melon/after_n26.png", "Flash in", "the white flash that opens the scene, now full width"),
    ("t29/melon/after_n28.png", "Flash out", "the flash that ends it, full width"),
]
OUT = "preview/story"
os.makedirs(OUT, exist_ok=True)
t = int(time.time())
srcs = []
for name, _, _ in SHOTS:
    dst = name.replace("/", "_")
    shutil.copy(os.path.join("shots", name), os.path.join(OUT, dst))
    srcs.append("story/%s?t=%d" % (dst, t))
keys = "123456789"[:len(SHOTS)]
btns = "".join('<button data-i=%d%s>%s. %s <small>%s</small></button>' % (i, " class=on" if i == 0 else "", keys[i], s[1], s[2])
               for i, s in enumerate(SHOTS))
open("preview/story.html", "w").write("""<!doctype html><meta charset=utf-8><meta name=viewport content="width=device-width,initial-scale=1">
<title>Falling scene</title>
<style>body{background:#16161a;color:#ddd;font:15px/1.5 system-ui;margin:0;padding:24px}
h1{font-size:22px;margin:0 0 6px}p,li{color:#aaa;max-width:85ch}
.frame{overflow-x:auto}
img.deck{image-rendering:pixelated;display:block;max-width:none;outline:1px solid #444}
.btns{display:flex;gap:8px;margin:12px 0 8px;flex-wrap:wrap}
button{background:#26262c;color:#ddd;border:1px solid #555;border-radius:6px;padding:5px 12px;font:inherit;cursor:pointer;text-align:left}
button small{color:#999}button.on{background:#3a5a8c;border-color:#7aa2e0;color:#fff}button.on small{color:#cde}
#size{color:#9cd}</style>
<h1>The book pulls the hero in: whole screen (ticket 29)</h1>
<p>Real melonDS captures on the Deck preset (OpenGL, 8x), the whole 1280x800 screen, one screen pixel per pixel of
your display (<span id=size></span>). Flip with the buttons or the keys <b>1</b> to <b>%s</b>.</p>
<p>The scene's backdrop is a texture the game itself repeats sideways (it scrolls through it), so the side areas show
the game's own picture carrying on: no mirror, no stretching, no AI. Before and After are a few frames apart
(the hero and the light move), not the same frame. The round glow is a 2D layer and stays a little wide, as all 2D layers do.</p>
<p>(Other story scenes with a full-width mist layer are widened the same way. Their pictures were taken out:
they came from a test setup that showed those scenes on the wrong map; see ticket 29.)</p>
<section><div class=btns>%s</div>
<div class=frame><img class=deck src="%s" data-srcs="%s" alt="falling scene"></div></section>
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
print("preview/story.html written")
