#!/usr/bin/env python3
"""Title screen before and after ticket 12, at Steam Deck size: preview/title.html.

usage: preview_title.py
Needs two melonDS captures of the title (scripts/melon_capture.sh inside headless
gamescope at 1280x800, 24 s), one from a build before the change and one after:
  shots/t12/melon_title.png      before
  shots/t12/melon_title_v2.png   after"""
import os, shutil, time

SHOTS = [
    ("melon_title.png", "Before", "background stretched and slid left; black strip on the right; menu and copyright off centre"),
    ("melon_title_v2.png", "After", "picture at its true size, mirrored at its edges into the side areas and the bands above and below"),
]
OUT = "preview/t12"
os.makedirs(OUT, exist_ok=True)
t = int(time.time())
srcs = []
for name, _, _ in SHOTS:
    shutil.copy(os.path.join("shots/t12", name), os.path.join(OUT, name))
    srcs.append("t12/%s?t=%d" % (name, t))
btns = "".join('<button data-i=%d%s>%d. %s <small>%s</small></button>' % (i, " class=on" if i == 1 else "", i + 1, s[1], s[2])
               for i, s in enumerate(SHOTS))
open("preview/title.html", "w").write("""<!doctype html><meta charset=utf-8><meta name=viewport content="width=device-width,initial-scale=1">
<title>Title screen</title>
<style>body{background:#16161a;color:#ddd;font:15px/1.5 system-ui;margin:0;padding:24px}
h1{font-size:22px;margin:0 0 6px}p,li{color:#aaa;max-width:85ch}
.frame{overflow-x:auto}
img.deck{image-rendering:pixelated;display:block;max-width:none;outline:1px solid #444}
.btns{display:flex;gap:8px;margin:12px 0 8px;flex-wrap:wrap}
button{background:#26262c;color:#ddd;border:1px solid #555;border-radius:6px;padding:5px 12px;font:inherit;cursor:pointer;text-align:left}
button small{color:#999}button.on{background:#3a5a8c;border-color:#7aa2e0;color:#fff}button.on small{color:#cde}
#size{color:#9cd}</style>
<h1>Title screen fills the Deck</h1>
<p>Real melonDS captures, the whole 1280x800 Deck screen, one screen pixel per pixel of your display (<span id=size></span>).
Flip with the buttons or the keys <b>1</b> and <b>2</b>.</p>
<p>The game's title picture is exactly 256x192 with nothing beyond it. The mod now shows it unstretched in the middle and
fills the 55 columns each side and the 18 rows above and below with the picture mirrored at its edge, drawn from the
game's own texture while it runs (fine for the published patch). The menu and the copyright line stay centred under the
logo; the difficulty menu after New Game is centred the same way. The 4:3 preset is unchanged, pixel for pixel.</p>
<section><div class=btns>%s</div>
<div class=frame><img class=deck src="%s" data-srcs="%s" alt="title screen"></div></section>
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
document.addEventListener("keydown", e => { const i = "12".indexOf(e.key); if (i >= 0) show(i); });
</script>""" % (btns, srcs[1], "|".join(srcs)))
print("preview/title.html written")
