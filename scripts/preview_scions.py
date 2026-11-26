#!/usr/bin/env python3
"""Scion animations on one screen (ticket 26): preview/scions.html, with a video of each.

usage: preview_scions.py videos [K...]   render the videos (solo_scion.py + ffmpeg, ~1 min each)
       preview_scions.py                 write the page
Also uses melonDS captures (scripts/melon_scion.sh): shots/t26/melon (now) and
shots/t26/melon_today (the build before the ticket), and shots/t26/pre_* (other display shapes)."""
import os, shutil, subprocess, sys, tempfile, time
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
NAMES = "Belias Mateus Shemhazai Hashmal Famfrit Adrammelech Cuchulainn Zalera Chaos Zeromus Exodus Ultima Zodiark".split()
END = [776, 774, 834, 770, 772, 777, 775, 779, 775, 774, 881, 772, 832]
OUT = "preview/t26"
os.makedirs(OUT, exist_ok=True)
if sys.argv[1:2] == ["videos"]:
    for k in [int(v) for v in sys.argv[2:]] or range(13):
        with tempfile.TemporaryDirectory(dir="build") as d:
            subprocess.check_call([sys.executable, "scripts/solo_scion.py", str(k), d, "206-%d/2" % END[k]])
            subprocess.check_call(["ffmpeg", "-loglevel", "error", "-y", "-framerate", "30", "-pattern_type", "glob",
                                   "-i", d + "/*.png", "-c:v", "libx264", "-crf", "19", "-pix_fmt", "yuv420p",
                                   "%s/%s.mp4" % (OUT, NAMES[k].lower())])
        print(NAMES[k], flush=True)
    sys.exit()
t = int(time.time())
PAIRS = [("melon_today/b_8", "melon/s0_7", "Belias"), ("melon_today/s12_4", "melon/s12_5", "Zodiark")]


def pic(src, cap):
    name = src.replace("/", "_").replace(".", "_") + ".png"
    shutil.copy("shots/t26/" + src + ".png", OUT + "/" + name)
    return '<figure><img src="t26/%s?t=%d"><figcaption>%s</figcaption></figure>' % (name, t, cap)


before = "".join(pic(a, n + ", before: one screen's half") + pic(b, n + ", now") for a, b, n in PAIRS)
vids = "".join('<figure><video controls muted loop preload=none poster="t26/%s.jpg" src="t26/%s.mp4?t=%d"></video><figcaption>%s</figcaption></figure>'
               % (n.lower(), n.lower(), t, n) for n in NAMES if os.path.exists("%s/%s.mp4" % (OUT, n.lower())))
zoom = pic("p_2x/12_0620", "2x (built): even pixels, 8 game rows spare top and bottom") + \
    pic("pre_t26_208/12_0620", "2.08x: the picture exactly fills the height, pixels uneven")
shapes = pic("pre_ffta2-16x9/12_0620", "16:9 build (2.5x)") + pic("pre_ffta2-4x3/12_0620", "4:3 build (2x on 1024x768)")
open("preview/scions.html", "w").write("""<!doctype html><meta charset=utf-8>
<meta name=viewport content="width=device-width,initial-scale=1"><title>Scions on one screen</title>
<style>body{background:#16161a;color:#ddd;font:15px/1.5 system-ui;margin:0;padding:24px;max-width:1500px}
h1{font-size:22px;margin:0 0 4px}h2{font-size:17px;margin:28px 0 6px}
.g{display:grid;grid-template-columns:repeat(auto-fit,minmax(min(100%%,460px),1fr));gap:14px}
img,video{width:100%%;display:block}figure{margin:0}figcaption{color:#cde}</style>
<h1>Scions on one screen</h1>
<p>The whole two-screen animation as one picture. The sides are the game's own textures carried on; nothing was drawn by AI.</p>
<h2>Videos of all 13</h2><p>From the fast test emulator, which draws at DS resolution; on the Deck it is sharper, as in the stills below. Each starts after the fade from black.</p><div class=g>%s</div>
<h2>Before and now</h2><p>Real melonDS at Steam Deck size. The moments are close, not identical.</p><div class=g>%s</div>
<h2>Your call: 2x or 2.08x</h2><div class=g>%s</div>
<h2>Other display shapes</h2><div class=g>%s</div>""" % (vids, before, zoom, shapes))
print("preview/scions.html written")
