#!/usr/bin/env python3
"""Zoom levels side by side at Steam Deck resolution (ticket 08): preview/zoom.html.

usage: preview_zoom.py
Needs, per level (320x200 = the Deck preset, plus builds made with patch.py --view WxH):
  shots/t08/<view>/        ROM=... O=shots/t08/<view> [FIT=1280x800] scripts/solo_menus.sh
  shots/t08/melon/party_<view>.png   melon_save.sh capture of the party room (keys s:1.5 x:3 x:2)"""
import os, shutil, time
from PIL import Image

LEVELS = [
    ("320x200", "4x, before", "every game pixel 4x4 screen pixels", "98% / 82%"),
    ("366x228", "3.5x, the Deck preset now", "game pixels alternate 3 and 4 screen pixels", "77% / 53% (Wood Village)"),
    ("426x266", "3x", "nearly all 3x3; slightly soft in melonDS", "80% / 63%"),
]
SCENES = [
    ("battle", "Battle"), ("place", "Unit placement"), ("party", "Party room"),
    ("worldmap", "World map"), ("buy", "Shop"), ("abil_items_list", "Ability list"),
    ("pub", "Pub (speech)"), ("clan", "Clan menu"),
]
OUT = "preview/t08"
os.makedirs(OUT, exist_ok=True)
t = int(time.time())


def img(src, key):
    shutil.copy(src, os.path.join(OUT, key))
    return "t08/%s?t=%d" % (key, t)


scenes = [("melon_party", "Party room, real melonDS capture", "melon/party_%s.png")] + \
         [(n, title, "%s/" + n + ".png") for n, title in SCENES]
blocks = ""
for key, title, pat in scenes:
    srcs = [img("shots/t08/" + pat % v, "%s_%s.png" % (v, key)) for v, _, _, _ in LEVELS]
    btns = "".join('<button data-i="%d"%s>%s <small>%s</small></button>' % (i, " class=on" if i == 0 else "", v, z)
                   for i, (v, z, _, _) in enumerate(LEVELS))
    blocks += ('<section><h2>%s</h2><div class=btns>%s</div>'
               '<div class=frame><img class=deck src="%s" data-srcs="%s" width=1280 height=800 alt=""></div></section>'
               % (title, btns, srcs[0], "|".join(srcs)))

# where 3.5x is uneven: the same spot at 4x and 3.5x, cut from melonDS captures (the Quest
# Report from the test emulator) and enlarged MAG times so single screen pixels show
MAG = 3
UNEVEN = [
    ("World map description: at 3.5x letters of one width come out 3 or 4 screen pixels wide (look at s, m, l)",
     "melon/worldmap_%s.png", {"320x200": (270, 590, 830, 690), "366x228": (320, 620, 810, 705)}),
    ("Shop description: strokes and outlines alternate thick and thin (the 1 and the H)",
     "melon/shop_%s.png", {"320x200": (150, 510, 560, 610), "366x228": (205, 535, 565, 625)}),
    ("Unit panel: digits and the portrait's outlines",
     "melon/party_%s.png", {"320x200": (0, 640, 420, 800), "366x228": (0, 660, 368, 800)}),
    ("Quest Report grid: squares alternate a pixel wider and narrower (test emulator)",
     "%s/report.png", {"320x200": (0, 0, 520, 240), "366x228": (0, 0, 455, 210)}),
]
uneven = ""
for j, (title, pat, boxes) in enumerate(UNEVEN):
    srcs = []
    for v in ("320x200", "366x228"):
        im = Image.open("shots/t08/" + pat % v).convert("RGB").crop(boxes[v])
        im = im.resize((im.width * MAG, im.height * MAG), Image.NEAREST)
        key = "uneven%d_%s.png" % (j, v)
        im.save(os.path.join(OUT, key))
        srcs.append("t08/%s?t=%d" % (key, t))
    btns = ('<button data-i="0" class=on>320x200 <small>4x</small></button>'
            '<button data-i="1">366x228 <small>3.5x</small></button>')
    uneven += ('<section><h3>%s</h3><div class=btns>%s</div><div class=frame>'
               '<img class=mag src="%s" data-srcs="%s" alt=""></div></section>' % (title, btns, srcs[0], "|".join(srcs)))

notes = "".join("<li><b>%s</b> (%s): %s; pixel edges on the grid in melonDS, across / down: %s</li>" % l for l in LEVELS)
open("preview/zoom.html", "w").write("""<!doctype html><meta charset=utf-8><meta name=viewport content="width=device-width,initial-scale=1">
<title>Zoom levels</title>
<style>body{background:#16161a;color:#ddd;font:15px/1.5 system-ui;margin:0;padding:24px}
h1{font-size:22px;margin:0 0 6px}h2{font-size:17px;margin:34px 0 8px}p,li{color:#aaa;max-width:85ch}
.frame{overflow-x:auto}
img.deck,img.mag{image-rendering:pixelated;display:block;max-width:none;outline:1px solid #444}
h3{font-size:15px;font-weight:600;margin:26px 0 8px;color:#ccc}
.btns{display:flex;gap:8px;margin-bottom:8px;flex-wrap:wrap}
button{background:#26262c;color:#ddd;border:1px solid #555;border-radius:6px;padding:5px 12px;font:inherit;cursor:pointer}
button small{color:#999}button.on{background:#3a5a8c;border-color:#7aa2e0;color:#fff}button.on small{color:#cde}
.warn{color:#e8c48a}#size{color:#9cd}</style>
<h1>Zoom levels at Steam Deck size</h1>
<p><b>Decided (2026-11-23): 366x228, 3.5x, is now the Steam Deck preset.</b> Its pictures below are from the final build.</p>
<p>Each picture is the whole Deck screen, 1280x800, shown one screen pixel per pixel of your display
(<span id=size></span>). Flip between levels with the buttons, or press <b>1</b>, <b>2</b>, <b>3</b> to switch every picture at once.
The first picture is a real melonDS capture; the others come from the fast test emulator, enlarged to 1280x800 the way an emulator does.</p>
<ul>%s</ul>
<p class=warn>Fixed: the world map's place name and weather icon flickered between the corner globe and their old spot on
every other frame (with or without a menu open), so any single picture could catch either; they now stay on the globe.
The place name ("Wood Village") now sits on its tab at 3.5x. The clan parchment no longer streaks above and below.
The empty pub speech bubble was a capture moment, not a fault.</p>
<h2>Where 3.5x is uneven</h2>
<p>At 3.5x a game pixel gets 3 or 4 screen pixels, alternating. These spots are enlarged %dx so single screen pixels show; flip
between 4x and 3.5x to compare. At real size it takes a close look to notice.</p>
%s
<h2>The whole screen at each level</h2>
%s
<script>
const dpr = window.devicePixelRatio || 1;
document.querySelectorAll("img.mag").forEach(im => im.addEventListener("load", () => {
  im.style.width = (im.naturalWidth / dpr) + "px"; }));
document.querySelectorAll("img.deck").forEach(im => { im.style.width = (1280 / dpr) + "px"; im.style.height = (800 / dpr) + "px"; });
document.getElementById("size").textContent = dpr === 1 ? "your display shows it at exactly Deck size"
  : "your display scale is " + dpr + "x, so the pictures are sized down to stay one-to-one";
function show(sec, i) {
  const im = sec.querySelector("img.deck, img.mag"), srcs = im.dataset.srcs.split("|");
  if (i >= srcs.length) return;
  im.src = srcs[i];
  sec.querySelectorAll("button").forEach(b => b.classList.toggle("on", +b.dataset.i === i));
}
document.querySelectorAll("section").forEach(sec => sec.querySelectorAll("button").forEach(b =>
  b.addEventListener("click", () => show(sec, +b.dataset.i))));
document.addEventListener("keydown", e => { const i = "123".indexOf(e.key);
  if (i >= 0) document.querySelectorAll("section").forEach(sec => show(sec, i)); });
</script>""" % (notes, MAG, uneven, blocks))
print("preview/zoom.html written")
