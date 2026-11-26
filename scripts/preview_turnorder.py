#!/usr/bin/env python3
"""Ticket 07 preview: the turn order ("stage") as built, per display preset.
usage: preview_turnorder.py     (~1 min; writes preview/turnorder.html + preview/t07/)
Needs build/ffta2-1screen.nds (deck), build/ffta2-16x9.nds (--display 16x9) and
build/t07-4x3.nds (--display 4x3); a melonDS capture shots/melon/t07_stage.png is
added if present (scripts/melon_battle2.sh shots/melon/t07_stage.png).
Pictures are scripts/solo.py captures (the mod's one screen); the video (preview/t07/turnorder.mp4,
needs ffmpeg) is two solo.py runs joined: browsing with L/R, then turns passing with Wait."""
import os, shutil, subprocess, sys, time
P = sys.executable
OUT = "shots/t07"; PV = "preview/t07"
for d in (OUT, PV):
    shutil.rmtree(d, ignore_errors=True); os.makedirs(d)
D = "DOWN,w15"
WAIT = "w150,DOWN,w15,DOWN,w15,A,w60,A,w60,w200"
RUNS = [("build/ffta2-1screen.nds", "s_battle2", "w10,sb2,%s,A,w60,saction,A,w60,UP,w30,A,w60,sforecast,B,w40,B,w40,B,w40,X,w60,smenu" % D, {}),
        ("build/ffta2-1screen.nds", "s_battle2", "w10,%s,%s,%s,%s,senemy" % (WAIT, WAIT, WAIT, WAIT), {}),
        ("build/ffta2-1screen.nds", "p_battle", "w10,sb1", {}),
        ("build/ffta2-16x9.nds", "s_battle2", "w10,s169", {"SCALE": "5"}),
        ("build/t07-4x3.nds", "s_battle2", "w10,s43", {}),
        ("build/ffta2-1screen.nds", "s_battle2", "w10,sbr01" + "".join(",R,w30" + (",sbr%02d" % (i + 2) if i + 2 in (2, 5, 6, 13, 20) else "") for i in range(19)), {})]
def clip(parts):
    n = [0]; steps = []
    def shots(frames, every):
        for _ in range(frames // every):
            steps.append("w%d" % every); n[0] += 1; steps.append("s%04d" % n[0])
    def key(k):
        steps.append(k); n[0] += 1; steps.append("s%04d" % n[0])
    parts(shots, key)
    return "w10," + ",".join(steps)
def browse(shots, key):
    shots(48, 4)
    for k in "RRRRRRLLLLLL":
        key(k); shots(32, 4)
def turns(shots, key):
    shots(40, 4)
    for t in range(6):
        shots(150, 8); key("DOWN"); shots(12, 4); key("DOWN"); shots(12, 4); key("A"); shots(56, 4); key("A"); shots(56, 4)
        shots(200, 8)
for d in ("vid_a", "vid_b"):
    shutil.rmtree(os.path.join(OUT, d), ignore_errors=True)
RUNS += [("build/ffta2-1screen.nds", "s_battle2", clip(browse), {"_dir": "vid_a"}),
         ("build/ffta2-1screen.nds", "s_battle2", clip(turns), {"_dir": "vid_b"})]
procs = [subprocess.Popen([P, "scripts/solo.py", "states/%s.dst" % st, sc, os.path.join(OUT, env.get("_dir", ""))],
                          env=dict(os.environ, ROM=rom, **{k: v for k, v in env.items() if k != "_dir"}),
                          stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL) for rom, st, sc, env in RUNS]
if any(p.wait() for p in procs):
    sys.exit("a capture failed")
from PIL import Image
for f in ("b2", "enemy", "b1"):
    im = Image.open("%s/%s.png" % (OUT, f)); im.crop((460, 600, 1000, 800)).resize((1080, 400), Image.NEAREST).save("%s/%s_zoom.png" % (OUT, f))
seq = os.path.join(OUT, "vid"); shutil.rmtree(seq, ignore_errors=True); os.makedirs(seq)
frames = [os.path.join(OUT, d, f) for d in ("vid_a", "vid_b") for f in sorted(os.listdir(os.path.join(OUT, d)))]
frames += frames[-1:] * 20                     # hold the end
for i, f in enumerate(frames):
    os.symlink(os.path.abspath(f), os.path.join(seq, "%05d.png" % i))
subprocess.check_call(["ffmpeg", "-loglevel", "error", "-y", "-framerate", "15", "-i", os.path.join(seq, "%05d.png"),
                       "-c:v", "libx264", "-pix_fmt", "yuv420p", "-crf", "16", "-preset", "slow", "-movflags", "+faststart",
                       os.path.join(PV, "turnorder.mp4")])
for f in os.listdir(OUT):
    if f.endswith(".png"):
        shutil.copy(os.path.join(OUT, f), os.path.join(PV, f))
if os.path.exists("shots/melon/t07_stage.png"):
    shutil.copy("shots/melon/t07_stage.png", os.path.join(PV, "melon.png"))
t = int(time.time())
img = lambda f, cap: '<figure><img src="t07/%s.png?t=%d"><figcaption>%s</figcaption></figure>' % (f, t, cap)
row = lambda *figs: "<div class=row>%s</div>" % "".join(figs)
melon = row(img("melon", "melonDS 1.1, OpenGL, 1280x800, second battle entered from the in-game save")) if os.path.exists(os.path.join(PV, "melon.png")) else "<p>(no melonDS capture yet)</p>"
html = """<!doctype html><meta charset=utf-8><meta name=viewport content="width=device-width,initial-scale=1"><title>Turn order stage</title>
<style>body{background:#16161a;color:#ddd;font:15px system-ui;margin:0;padding:24px}h1{font-size:20px}h2{font-size:17px;margin:34px 0 4px}
p{color:#aaa;max-width:920px}.row{display:flex;gap:12px;flex-wrap:wrap}figure{margin:0 0 12px;flex:1 1 420px;max-width:960px}
img{image-rendering:pixelated;border:1px solid #444;width:100%%}figcaption{color:#999;font-size:13px;margin-top:4px}b{color:#fff}</style>
<h1>Ticket 07: turn order "stage", as built</h1>
<p>Units are now whole: each one is two sprites on the info screen (body, and feet with the ground shadow), and both are copied.
The pip row starts with the acting unit's turn and shows the next 18 turns (blue ally, red enemy); it sits on top of the shadows' lower edge.</p>
<h2>In motion</h2>
<p>Test-emulator capture at 1280x800. First Alulis's turn and browsing with R three times and L back: the game's map cursor and unit panel move to the browsed unit (Otz, Tsark, Cid), and so does the light-blue arrow in the turn order, while Alulis keeps the first slot and the orange ring (whose turn it is).
Then turns end with Wait, one after another (shown at about 2x between turns): each time the queue moves on, the next unit stands on the orange ring, until the wolves act and the red pips come to the front.</p>
<video src="t07/turnorder.mp4?t=%d" controls autoplay loop muted playsinline style="width:100%%;max-width:1280px;border:1px solid #444"></video>
<h2>Close-ups</h2>%s
<h2>Browsing with L/R (turn 1, 2, 5, 6, 13, 20)</h2>
<p>Two marks: the <b>orange ring</b> is whose turn it is (always the first slot), the <b>light-blue arrow</b> is the unit you browsed to with L/R (its pip is outlined in the same blue). Browsing past turn 4, the other three slots follow the arrow (the unit before, the browsed one, the one after) and a dotted gap after the first slot shows turns were skipped. The game's map cursor and unit panel jump to the browsed unit too.</p>%s%s%s
<h2>Deck (1280x800)</h2>%s%s
<h2>Attack forecast: the stage steps aside for the game's panels</h2>%s
<h2>16:9 (1920x1080) and 4:3 (too narrow at the bottom: the same units in a strip at the top right)</h2>%s
<h2>melonDS</h2>%s
""" % (t, row(img("b2_zoom", "your turn: Alulis on the orange ring, first pip is hers"), img("enemy_zoom", "a few turns later"), img("b1_zoom", "first battle")),
       row(img("br01", "no browsing: Alulis's turn"), img("br02", "R: browsing turn 2 (Otz on the panel and under the map cursor)")),
       row(img("br05", "browsing turn 5"), img("br06", "browsing turn 6")),
       row(img("br13", "browsing turn 13"), img("br20", "browsing turn 20, the last the game shows")),
              row(img("b2", "your turn"), img("enemy", "a few turns later")), row(img("action", "choosing an action"), img("menu", "battle menu")),
       row(img("forecast", "forecast"), img("b1", "first battle")),
       row(img("169", "16:9"), img("43", "4:3")), melon)
open("preview/turnorder.html", "w").write(html)
print("preview/turnorder.html written")
