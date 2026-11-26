#!/usr/bin/env python3
"""Ticket 03 preview: load each test state on the current build, screenshot both
screens, and write preview/index.html (melonDS captures from shots/melon/t03_*.png
are shown for the gameplay screen where they exist).  usage: preview_saves.py"""
import os, shutil, subprocess, sys, time
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
if len(sys.argv) > 1:      # child: one emulator per process (a second instance crashes)
    from emu import boot
    emu = boot("states/s_%s.dst" % sys.argv[1], rom="build/ffta2-1screen.nds", frames=30)
    im = emu.screenshot().convert("RGB")
    im.crop((0, 0, 256, 192)).save("preview/t03_%s_info.png" % sys.argv[1])
    im.crop((0, 192, 256, 384)).save("preview/t03_%s_game.png" % sys.argv[1])
    sys.exit(0)
SITS = [("worldmap", "World map", "Standing on Wood Village after the opening; clan named, first quest accepted."),
        ("shop", "Shop", "Buy list, first category. The info screen holds the item's stats."),
        ("party", "Party menu", "Unit Info: the unit list. The info screen holds the selected unit's sheet."),
        ("equip", "Equipment screen", "Change Equipment for Luso. The info screen holds the stat comparison."),
        ("battle2", "Battle with a special rule",
         "Second battle, “A Paw Full of Feathers”. Besides objective and law the info screen now has a third line: PRIVILEGE Power↑1.")]
os.makedirs("preview", exist_ok=True)
rows = []
for key, title, note in SITS:
    subprocess.run([sys.executable, __file__, key], check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    melon = "shots/melon/t03_%s.png" % key
    if os.path.exists(melon):
        shutil.copy(melon, "preview/t03_%s_melon.png" % key)
        game = ('<figure><img class=deck src="t03_%s_melon.png?t=%d"><figcaption>Gameplay screen, melonDS at Deck resolution '
                '(loaded from the in-game save; one menu step further in than the state)</figcaption></figure>' % (key, time.time()))
    else:
        game = ('<figure><img class=ds src="t03_%s_game.png?t=%d"><figcaption>Gameplay screen, state as loaded '
                '(DS-resolution test capture: the picture is squeezed here, not how it looks on the Deck)</figcaption></figure>' % (key, time.time()))
    rows.append('<section><h2>%s</h2><p>%s <code>states/s_%s.dst</code></p><div class=row>%s'
                '<figure><img class=ds src="t03_%s_info.png?t=%d"><figcaption>Info screen (from the state)</figcaption></figure></div></section>'
                % (title, note, key, game, key, time.time()))
open("preview/index.html", "w").write("""<!doctype html><meta charset=utf-8><meta name=viewport content="width=device-width,initial-scale=1">
<title>Ticket 03: test saves</title>
<style>body{background:#16161a;color:#ddd;font:15px system-ui;margin:0;padding:24px}
h1{font-size:20px}h2{font-size:16px;margin:28px 0 4px}p{color:#aaa;max-width:860px;margin:4px 0 12px}
code{color:#9cd}.row{display:flex;gap:20px;flex-wrap:wrap;align-items:flex-start}
figure{margin:0}figcaption{color:#999;font-size:12px;margin-top:6px;max-width:512px}
img{image-rendering:pixelated;border:1px solid #444;max-width:100%%}.deck{width:640px}.ds{width:512px}</style>
<h1>Ticket 03: test saves beyond the tutorial</h1>
<p>Five situations, each kept as a savestate that loads on the current build. Both screens are shown for each one.
The world map is also kept as an in-game save (<code>saves/worldmap.sav</code>, slot 1) that loads in melonDS.</p>
%s""" % "".join(rows))
print("preview/index.html written")
