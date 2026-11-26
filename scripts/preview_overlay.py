#!/usr/bin/env python3
"""Write preview/overlay.html from the melonDS overlay captures (shots/melon/ov_*.png)."""
import os, shutil, time
ITEMS = [("ov_party", "Party: SELECT drops the unit sheet in", "Translucent, in front of the stage. SELECT again, or any confirm/cancel button, puts it away."),
         ("ov_party2", "Party: the sheet follows the selection", "Moving along the unit row with the D-pad updates the sheet (here the second unit)."),
         ("ov_shop_info", "Shop: Item Info (L/R)", "The game's own Item Info panel on the right, and the item's stats from the info screen beside it, shown automatically while the panel is up."),
         ("ov_equip_info", "Equipment: Item Info (L/R)", "Same, in the equipment list. Here the game puts the unit's sheet on the info screen, so the column shown is the unit's stats."),
         ("ov_shop_sel", "Shop: SELECT", "SELECT works in any menu and shows the whole info screen.")]
t = int(time.time()); body = ""
for f, ti, de in ITEMS:
    if os.path.exists("shots/melon/%s.png" % f):
        shutil.copy("shots/melon/%s.png" % f, "preview/%s.png" % f)
        body += '<h2>%s</h2><p>%s</p><img src="%s.png?t=%d">' % (ti, de, f, t)
open("preview/overlay.html", "w").write("""<!doctype html><meta charset=utf-8><meta name=viewport content="width=device-width,initial-scale=1"><title>Info screen overlay</title>
<style>body{background:#16161a;color:#ddd;font:15px system-ui;margin:0;padding:24px}h1{font-size:20px}h2{font-size:16px;margin:28px 0 4px}
p{color:#aaa;max-width:860px;margin:4px 0 12px}img{image-rendering:pixelated;border:1px solid #444;width:960px;max-width:100%%}</style>
<h1>Info screen overlay: the game running in melonDS</h1>
<p>Real captures of the current build at Deck resolution (1280x800), not mock-ups.</p>%s""" % body)
print("preview/overlay.html written")
