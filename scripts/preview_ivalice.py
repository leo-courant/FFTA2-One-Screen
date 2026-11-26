"""Ticket 36 preview: preview/ivalice.html, the map of Ivalice's edges before and
after, on the Deck and 16:9 presets, and in melonDS.  Local page only (preview/
and shots/ are not in git).  Pictures: shots/t36/ (solo.py and melon_state.py on
states/late/l_ivalice.dst and states/m_ivalice.ml1; "before" is the same build
with --no-map-art, or the previous build for the Deck)."""
import json
import os
import shutil
import time

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
os.chdir(ROOT)
t = int(time.time())
items = []
for src, title, text in [
    ("b_vs_cur_deck", "Right edge, close up: previous | now", "Left half: the art you reviewed (the right side ran on in streaks, with a dark column where the game's own fade showed through). Right half: now. The parchment, its colours and the grid lines carry on past the picture's end, then the map tears into sea, as on the left side."),
    ("deck_new/e", "Deck, Camoa: previous", "The first version."),
    ("opt_b_deck/e", "Deck, Camoa: now", "Torn right edge; no column at the picture's end any more."),
    ("deck_new/w", "Deck, the Galerria Deep: previous", "The left side you accepted."),
    ("opt_b_deck/w", "Deck, the Galerria Deep: now", "The same torn left side (only the picture's last 8 texels now draw over the game's fade, as they always should have)."),
    ("t36_16x9/e", "16:9, Camoa: previous", ""),
    ("opt_b_169/e", "16:9, Camoa: now", "16:9 sees a little further right, so more sea shows past the tear."),
    ("t36_16x9/w", "16:9, the Galerria Deep: previous", ""),
    ("opt_b_169/w", "16:9, the Galerria Deep: now", ""),
    ("m_deck_b_east", "Real melonDS, Deck, Camoa: now", "melonDS at 1280x800 (states/m_ivalice.ml1)."),
    ("m_deck_b", "Real melonDS, Deck, the Galerria Deep: now", ""),
    ("m_16x9_b_east", "Real melonDS, 16:9, Camoa: now", "melonDS at 1920x1080."),
    ("m_16x9_b", "Real melonDS, 16:9, the Galerria Deep: now", ""),
]:
    name = "ivalice_%s.png" % src.replace("/", "_")
    shutil.copy("shots/t36/%s.png" % src, "preview/" + name)
    items.append({"src": "%s?t=%d" % (name, t), "title": title, "text": text})
html = open("preview/late.html").read()
a = html.index("const items=") + len("const items=")
b = html.index("\n", a) - 1          # the whole line: the template's texts contain ";"
assert html[b] == ";"
html = html[:a] + json.dumps(items) + html[b:]
# each picture at its own size (16:9 ones are 1920 wide; the template assumes 1280)
html = html.replace("pic.style.width=(1280/window.devicePixelRatio)+'px';",
                    "pic.onload=()=>{pic.style.width=(pic.naturalWidth/window.devicePixelRatio)+'px'};")
html = html.replace("<title>Late-game screens</title>", "<title>Map of Ivalice edges</title>")
h1 = html.index("<h1>")
p_end = html.index("</p>", h1) + 4
html = html[:h1] + ("<h1>Ticket 36: the map of Ivalice to the screen's edges (review 1)</h1><p>The right side redone after "
       "your review: torn like the left. Each picture is the mod's screen at its real size. "
       "Step through with the buttons or the arrow keys: each \"previous\" is followed by its \"now\".</p>") + html[p_end:]
open("preview/ivalice.html", "w").write(html)
print("preview/ivalice.html")
