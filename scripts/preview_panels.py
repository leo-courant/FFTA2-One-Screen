#!/usr/bin/env python3
"""Dialogue windows at the edges and centred windows in the middle, on the Deck preset (ticket 06):
preview/panels.html.

usage: preview_panels.py
Needs shots/t06: melonDS captures from states/m_story.ml1 (deck_nNN.png) and solo.py
captures of the road into battle 2 (solo/*.png); the steps are in ticket 06."""
import os, shutil, time

SHOTS = [
    ("t06/deck_n00.png", "Right, top", "speech window touching the right edge: it and the face sit at the real edge (melonDS)"),
    ("t06/deck_n08.png", "Right, bottom", "the same at the bottom right (melonDS)"),
    ("t06/deck_n09.png", "Left", "speech window touching the left edge, with its pointer (melonDS)"),
    ("t06/solo/lawintro.png", "Law", "the law announcement stays in the middle"),
    ("t06/solo/privpick.png", "Privilege list", "heading, list and description stay in the middle"),
    ("t06/solo/confirm.png", "Confirm", "the Yes/Back question stays in the middle"),
    ("t06/deck_n16.png", "New fault", "the fall into the book: a 4:3 picture with black sides (ticket 29)"),
]
OUT = "preview/panels"
os.makedirs(OUT, exist_ok=True)
t = int(time.time())
srcs = []
for name, _, _ in SHOTS:
    os.makedirs(os.path.join(OUT, os.path.dirname(name)), exist_ok=True)
    shutil.copy(os.path.join("shots", name), os.path.join(OUT, name))
    srcs.append("panels/%s?t=%d" % (name, t))
keys = "1234567890"[:len(SHOTS)]
btns = "".join('<button data-i=%d%s>%s. %s <small>%s</small></button>' % (i, " class=on" if i == 0 else "", keys[i], s[1], s[2])
               for i, s in enumerate(SHOTS))
open("preview/panels.html", "w").write("""<!doctype html><meta charset=utf-8><meta name=viewport content="width=device-width,initial-scale=1">
<title>Dialogue and centred windows</title>
<style>body{background:#16161a;color:#ddd;font:15px/1.5 system-ui;margin:0;padding:24px}
h1{font-size:22px;margin:0 0 6px}p,li{color:#aaa;max-width:85ch}
.frame{overflow-x:auto}
img.deck{image-rendering:pixelated;display:block;max-width:none;outline:1px solid #444}
.btns{display:flex;gap:8px;margin:12px 0 8px;flex-wrap:wrap}
button{background:#26262c;color:#ddd;border:1px solid #555;border-radius:6px;padding:5px 12px;font:inherit;cursor:pointer;text-align:left}
button small{color:#999}button.on{background:#3a5a8c;border-color:#7aa2e0;color:#fff}button.on small{color:#cde}
#size{color:#9cd}</style>
<h1>Dialogue at the edges, centred windows in the middle</h1>
<p>The Deck preset, the whole 1280x800 screen, one screen pixel per pixel of your display (<span id=size></span>).
Pictures 1-3 and 7 are real melonDS captures of the opening story scene; 4-6 come from the fast emulator on the road into the
second battle. Flip with the buttons or the keys <b>1</b> to <b>%s</b>.</p>
<p>Check only, no change to the mod. With the 4:3 preset the opening (name entry, story scenes with speech windows on both
sides, into the first battle) is pixel-identical to the unmodified game, apart from the banner and turn order and animation
one frame apart.</p>
<section><div class=btns>%s</div>
<div class=frame><img class=deck src="%s" data-srcs="%s" alt="game screen"></div></section>
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
print("preview/panels.html written")
