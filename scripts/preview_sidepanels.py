#!/usr/bin/env python3
"""Write preview/sidepanels.html (ticket 16): Change Jobs with the stat changes beside the
list, and View Abilities, where the game's own ability list does the job.  Pictures from
shots/solo (scripts/solo_menus.sh) and, when present, melonDS captures shots/melon/t16_*.png."""
import os, shutil, time
ITEMS = [("shots/solo/abil_nav_sheet.png", "Moving the cursor: one press per picture",
          "Left to right, top to bottom: start on Potion, then Right, Down, Left, Up, Down, Down, Right, Up. Each single press moves one cell in that direction."),
         ("shots/solo/abil_items_list2.png", "View Abilities: the compact ability list, as built (ticket 22)",
          "Real capture of the build, not a mock-up. Each column is 14 game pixels narrower, the highlight bar is shortened to match, the scroll bar sits right after the second column, and the panel is 28 narrower in all."),
         ("shots/solo/abil_items_list.png", "Cursor in the left column", "The highlight ends before the right-hand column's marker."),
         ("shots/solo/abil_mage_list.png", "The black mage's list", "Progress bars fit inside the shorter highlight."),
         ("shots/solo/abil_longest_test.png", "Test: the widest ability name in the game",
          "\"Thunder Flare Tome\" (87 pixels) put in place of Potion for the test; it still fits inside the highlight. The other garbled names are a side effect of the test, not of the build."),
         ("shots/solo/jobs2.png", "Change Jobs: Thief highlighted (ticket 16, unchanged)",
          "The unit's stats with what the highlighted job changes (+1 Jump, +5 Evasion) sit top left. The Jobs list has moved right to make room."),
         ("shots/melon/t22_abil_list.png", "Final check in melonDS: the compact ability list", "Real melonDS capture at Deck resolution."),
         ("shots/melon/t16_jobs.png", "Final check in melonDS: Change Jobs", "Real melonDS capture at Deck resolution.")]
os.makedirs("preview/sidepanels", exist_ok=True)
t = int(time.time()); body = ""
for src, ti, de in ITEMS:
    if os.path.exists(src):
        name = src.replace("/", "_")
        shutil.copy(src, "preview/sidepanels/" + name)
        body += '<h2>%s</h2><p>%s</p><img src="sidepanels/%s?t=%d" alt="">' % (ti, de, name, t)
open("preview/sidepanels.html", "w").write("""<!doctype html><meta charset=utf-8><meta name=viewport content="width=device-width,initial-scale=1"><title>Side panels</title>
<style>body{background:#16161a;color:#ddd;font:15px/1.5 system-ui;margin:0;padding:24px}h1{font-size:20px}h2{font-size:16px;margin:28px 0 4px}
p{color:#aaa;max-width:75ch;margin:4px 0 12px}img{image-rendering:pixelated;border:1px solid #444;width:960px;max-width:100%%;height:auto;display:block}</style>
<h1>Ticket 16: job changes beside the list, and the ability list</h1>
<p>The mod's one screen at Deck resolution (1280x800). The stats panel in Change Jobs appears by itself while the list is open; SELECT still drops in the whole sheet.</p>%s""" % body)
print("preview/sidepanels.html written")
