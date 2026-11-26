#!/usr/bin/env python3
"""Write preview/privilege.html from the melonDS captures of the second battle
(shots/melon/t09_battle2*.png, made by scripts/melon_battle2.sh)."""
import os, shutil, time
ITEMS = [("t09_battle2", "Your unit's turn", "Objective in red, then the law (Forbidden: Fire), then the privilege chosen before the battle (Power↑1) in the game's own teal, with a thin rule between the two."),
         ("t09_battle2_d", "An enemy's turn", "The banner stays up while the wolves act.")]
t = int(time.time()); body = ""
for f, ti, de in ITEMS:
    if os.path.exists("shots/melon/%s.png" % f):
        shutil.copy("shots/melon/%s.png" % f, "preview/%s.png" % f)
        body += '<h2>%s</h2><p>%s</p><img src="%s.png?t=%d">' % (ti, de, f, t)
open("preview/privilege.html", "w").write("""<!doctype html><meta charset=utf-8><meta name=viewport content="width=device-width,initial-scale=1"><title>Privilege in the banner</title>
<style>body{background:#16161a;color:#ddd;font:15px system-ui;margin:0;padding:24px}h1{font-size:20px}h2{font-size:16px;margin:28px 0 4px}
p{color:#aaa;max-width:860px;margin:4px 0 12px}img{image-rendering:pixelated;border:1px solid #444;width:960px;max-width:100%%}</style>
<h1>Ticket 09: the privilege in the banner, running in melonDS</h1>
<p>Real captures of the current build at Deck resolution (1280x800), second battle, "A Paw Full of Feathers".
In a battle without a privilege (the tutorial) the banner has only the objective and law boxes, as before.</p>%s""" % body)
print("preview/privilege.html written")
