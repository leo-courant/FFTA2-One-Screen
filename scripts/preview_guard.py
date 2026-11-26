#!/usr/bin/env python3
"""What the video memory guard found (tickets 25 and 31): preview/guard.html.

usage: preview_guard.py
Needs the captures in shots/t25 (steps in ticket 31): *_none.png / *_ov.png from
scripts/solo.py (SELECT tapped between the two), m_story*.png from
scripts/melon_state.py states/m_story.ml1 (FPS=60, one SELECT tap)."""
import json, os, shutil, time

# (file, before file or None, title, note)
SHOTS = [
    ("results_ov.png", "results_none.png", "After the tutorial battle",
     "The overlay's parked copy shows through the game's own 2D layers and fills most of the screen. "
     "DeSmuME tiles: the garbage repeats in quarters, so its exact pattern is not what melonDS would show"),
    ("intro_ov.png", "intro_none.png", "Opening scene (the book's light)",
     "The same fault: the scene's 2D layers show the parked copy. (The light vertical bands in the normal picture come from the capture tool, not the game)"),
    ("pub_ov.png", "pub_none.png", "Late-game pub menu",
     "Blocky garbage at the right, behind and beside the panel: the pub draws part of its picture "
     "from the memory the overlay borrows. The early-game pub does not"),
    ("pub_fixed.png", "pub_ov.png", "Late-game pub: FIXED",
     "The overlay's picture now lives in the free top of the game's own texture heap, which the pub leaves alone: "
     "the pub's art stays intact behind the panel",
     ("<b>FIXED</b>: the pub with the overlay open on the new build. Press B for how it was",
      "<b>BEFORE</b>: the previous build, garbage at the right. Press B for the fixed build")),
    ("title_ov1.png", "title_none.png", "Title, 1st frame of the overlay",
     "The title picture tears into rows of the half-built overlay for about 6 frames"),
    ("title_ov2.png", "title_none.png", "Title, 4th frame of the overlay", "Still tearing"),
    ("title_ov3.png", "title_none.png", "Title, overlay fully up",
     "The game's picture is gone as designed (panels step aside for the overlay), but the panel itself is noise: "
     "the title's info screen uses a layer type the overlay cannot redraw. Not a memory clash"),
    ("m_story.png", "m_story_none.png", "Opening story scene (real melonDS)",
     "Behind the panel the scene is fine here (this scene's layer is blended away), but the panel is unreadable "
     "for the same reason as on the title. Not a memory clash"),
    ("m_dot_battle.png", "m_battle_nodot.png", "The warning dot: battle (real melonDS)",
     "A test build for playing (patch.py --guard) lights this red dot in the top-left corner for 10 s when it "
     "catches the game and the mod clashing. Make a savestate then; scripts/guard_report.py reads what happened from it",
     ("<b>WITH THE DOT</b> (lit on purpose for this picture). Press B for without",
      "<b>WITHOUT</b>. Press B to see the dot")),
    ("m_dot_story.png", "m_story_none.png", "The warning dot: story scene (real melonDS)",
     "The same dot over a story scene",
     ("<b>WITH THE DOT</b> (lit on purpose for this picture). Press B for without",
      "<b>WITHOUT</b>. Press B to see the dot")),
]
OUT = "preview/t25"
os.makedirs(OUT, exist_ok=True)
t = int(time.time())
data = []
for shot in SHOTS:
    name, before, title, note = shot[:4]
    labels = shot[4] if len(shot) > 4 else ("<b>BROKEN</b>: the same scene with the SELECT overlay open. Press B to go back",
                                            "<b>NORMAL</b>: how the scene looks. Press B (or click) to open the overlay here")
    for f in (name, before):
        if f:
            shutil.copy(os.path.join("shots/t25", f), os.path.join(OUT, f))
    data.append('{a:"t25/%s?t=%d",b:%s,n:%s,la:%s,lb:%s}' % (name, t, '"t25/%s?t=%d"' % (before, t) if before else "null",
                                                          json.dumps(note), json.dumps(labels[0]), json.dumps(labels[1])))
btns = "".join('<button data-i=%d%s><span>%d</span> %s</button>' % (i, " class=on" if i == 0 else "", i + 1, s[2])
               for i, s in enumerate(SHOTS))
open("preview/guard.html", "w").write("""<!doctype html><meta charset=utf-8><meta name=viewport content="width=device-width,initial-scale=1">
<title>Overlay clashes</title>
<style>body{background:#16161a;color:#ddd;font:15px/1.5 system-ui;margin:0;padding:24px}
h1{font-size:22px;margin:0 0 6px}p{color:#aaa;max-width:90ch;margin:0 0 8px}
.frame{overflow-x:auto}
img.shot{image-rendering:pixelated;display:block;max-width:none;outline:1px solid #444;cursor:pointer}
.btns{display:flex;gap:8px;margin:12px 0 8px;flex-wrap:wrap}
button{background:#26262c;color:#ddd;border:1px solid #555;border-radius:6px;padding:5px 12px;font:inherit;cursor:pointer}
button span{color:#888;margin-right:4px}button.on{background:#3a5a8c;border-color:#7aa2e0;color:#fff}button.on span{color:#cde}
#ba{margin:4px 0 2px;color:#9cd}#ba b{color:#fff}#ba.before b{color:#f0b060}
#note{color:#ccc;max-width:90ch;margin:0 0 10px;min-height:3em}</style>
<h1>Where the SELECT overlay breaks the picture (ticket 31)</h1>
<p><b>What to look at:</b> each scene opens as it normally looks. Press <b>B</b> to open the SELECT overlay there and see the
fault. The broken pictures are the bug, not a capture problem. The question for you is whether the overlay should simply
be turned off in these scenes (story, after-battle talk, title) and kept for menus only. The pub (3) needs a real fix either way.
Scene 2's normal picture has light bands from the capture tool, not the game.</p>
<p>The guard found these by opening the overlay in scenes no earlier test opened it in. Each picture is the Deck screen, one screen pixel
per display pixel. Pictures 1-7 come from DeSmuME (<code>solo.py</code>), pictures 8-10 from real melonDS. Picture 4 is the pub fix; pictures 9-10 show the warning dot. Pictures 1-2 and 5-8 are scenes where the overlay is now switched off.
Pick with the buttons or <b>1</b>-<b>9</b>, <b>0</b> / <b>&larr;</b> <b>&rarr;</b>; <b>B</b> or a click flips between
<b>with the overlay</b> and <b>without</b> (the same scene a moment earlier, so small differences in units and text are
just time passing).</p>
<div class=btns>%s</div>
<div id=ba></div>
<div id=note></div>
<div class=frame><img class=shot alt="capture"></div>
<script>
const D = [%s], dpr = window.devicePixelRatio || 1;
let cur = 0, before = true;
const im = document.querySelector("img.shot"), ba = document.getElementById("ba"), nt = document.getElementById("note");
function show() {
  const d = D[cur];
  im.src = before ? d.b : d.a;
  im.style.width = (1280 / dpr) + "px"; im.style.height = (800 / dpr) + "px";
  ba.className = before ? "before" : "";
  ba.innerHTML = before ? d.lb : d.la;
  nt.textContent = d.n;
  document.querySelectorAll("button").forEach(b => b.classList.toggle("on", +b.dataset.i === cur));
}
document.querySelectorAll("button").forEach(b => b.addEventListener("click", () => { cur = +b.dataset.i; before = true; show(); }));
im.addEventListener("click", () => { before = !before; show(); });
document.addEventListener("keydown", e => {
  if (e.key === "b" || e.key === "B") { before = !before; show(); }
  else if (e.key === "ArrowRight") { cur = Math.min(cur + 1, D.length - 1); before = true; show(); }
  else if (e.key === "ArrowLeft") { cur = Math.max(cur - 1, 0); before = true; show(); }
  else if (e.key >= "0" && e.key <= "9") { const k = e.key === "0" ? 9 : +e.key - 1; if (k < D.length) { cur = k; before = true; show(); } }
});
show();
</script>""" % (btns, ",".join(data)))
print("preview/guard.html written")
