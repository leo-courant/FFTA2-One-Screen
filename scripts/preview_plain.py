#!/usr/bin/env python3
"""The plain 4:3 preset next to the unmodified game (ticket 02): preview/plain.html.

usage: preview_plain.py
Needs the captures made as in the ticket's notes:
  shots/t02/orig    RAW=1 NOSEL=1 ROM=build/ffta2-ref.nds  O=shots/t02/orig  scripts/solo_menus.sh
  shots/t02/m43     RAW=1 NOSEL=1 ROM=build/ffta2-4x3.nds  O=shots/t02/m43   scripts/solo_menus.sh
  shots/t02/m43sel  RAW=1         ROM=build/ffta2-4x3.nds  O=shots/t02/m43sel scripts/solo_menus.sh
  shots/t02/bn_ref, bn_4x3   play.py s_battle2 "w10,SELECT40,w30,sbattle_nobanner,..." per ROM
  shots/t02/clan_ref, clan_4x3  play.py s_worldmap through the clan menus with long waits (the
      solo_menus.sh walk is timed for the Deck build and drifts in the plain game; see ticket 02)
Only the gameplay screen (the lower DS screen) is shown: that is what the player sees."""
import os, time
from PIL import Image, ImageChops

OUT = "preview/t02"
os.makedirs(OUT, exist_ok=True)
t = int(time.time())


def screen(d, name):
    return Image.open("shots/t02/%s/%s.png" % (d, name)).convert("RGB").crop((0, 192, 256, 384))


def save(img, key):
    img.save(os.path.join(OUT, key + ".png"))
    return "t02/%s.png?t=%d" % (key, t)


def differ(a, b):
    m = ImageChops.difference(a, b).convert("L").point(lambda v: 255 if v else 0)
    return sum(m.histogram()[255:]), m


def fig(src, cap):
    return '<figure><img src="%s" alt=""><figcaption>%s</figcaption></figure>' % (src, cap)


def pair(da, db, name, title):
    a, b = screen(da, name), screen(db, name)
    n, _ = differ(a, b)
    badge = '<span class="ok">identical</span>' if n == 0 else '<span class="no">%d pixels differ</span>' % n
    return ('<section><h3>%s %s</h3><div class=row>%s%s</div></section>'
            % (title, badge, fig(save(a, "orig_" + name), "Unmodified game"),
               fig(save(b, "m43_" + name), "Mod, 4:3 preset")))


# how many of the menu captures match exactly
CLAN = {n[:-4] for n in os.listdir("shots/t02/clan_ref")}
names = sorted(n[:-4] for n in os.listdir("shots/t02/orig"))
src = lambda n: ("clan_ref", "clan_4x3") if n in CLAN else ("orig", "m43")
same = [n for n in names if differ(*(screen(d, n) for d in src(n)))[0] == 0]

body = ""
body += "<h2>Battle with the banner held off</h2><p>Hold SELECT for half a second: the banner and turn order go away and the picture is the unmodified game's, pixel for pixel.</p>"
body += pair("bn_ref", "bn_4x3", "battle_nobanner", "Muskmallow Field")

body += ("<h2>Menus</h2><p>%d of the %d test pictures are identical to the unmodified game. "
         "The others are battle scenes, where the banner and turn order are on screen or the animation "
         "(leaves, monsters) is a frame or two apart.</p>" % (len(same), len(names)))
for n, title in (("party", "Party room"), ("jobs2", "Change Jobs"), ("equip_info", "Equipment, Item Info"),
                 ("buy_info", "Shop, Item Info"), ("abil_items_list", "View Abilities, the ability list"),
                 ("worldmap", "World map"), ("quests", "Clan menu, Quest List")):
    body += pair(*src(n), n, title)

body += "<h2>What the mod adds on 4:3</h2><p>The banner and turn order in battle; a tap of SELECT for the info screen.</p><div class=row>"
for d, n, cap in (("m43", "battle", "Battle: banner and turn order at the top right"),
                  ("m43", "place", "Unit placement"),
                  ("m43sel", "party_ov", "Party room: SELECT tap, the info screen laid over"),
                  ("m43sel", "buy_ov", "Shop: SELECT tap"),
                  ("m43sel", "unitinfo_ov", "Battle: SELECT tap swaps to the info screen")):
    body += fig(save(screen(d, n), "add_" + n), cap)
body += "</div>"

body += ("<h2>Where the animation differs</h2><p>Left the unmodified game, right the mod; pink marks the pixels that differ. "
         "Only moving things: the mod's per-frame work shifts the animation by a frame or two in the test emulator. Panels and text are identical.</p>")
a, b = screen("orig", "abil"), screen("m43", "abil")
_, m = differ(a, b)
mark = Image.composite(Image.new("RGB", a.size, (255, 0, 200)), a.point(lambda v: v // 3), m)
body += '<div class=row>%s%s</div>' % (fig(save(a, "orig_abil"), "Unmodified game"), fig(save(mark, "mark_abil"), "Differences"))

open("preview/plain.html", "w").write("""<!doctype html><meta charset=utf-8><meta name=viewport content="width=device-width,initial-scale=1">
<title>Plain 4:3 preset</title>
<style>body{background:#16161a;color:#ddd;font:15px/1.5 system-ui;margin:0;padding:24px;max-width:1200px}
h1{font-size:22px;margin:0 0 6px}h2{font-size:18px;margin:40px 0 6px}h3{font-size:15px;margin:22px 0 8px;font-weight:600}
p{color:#aaa;max-width:75ch}.row{display:grid;grid-template-columns:repeat(auto-fit,minmax(min(384px,100%%),1fr));gap:16px}
figure{margin:0}figcaption{color:#bbb;font-size:13px;margin-top:5px}
img{image-rendering:pixelated;border:1px solid #444;display:block;width:100%%;height:auto}
.ok,.no{font-size:12px;font-weight:600;padding:2px 8px;border-radius:9px;margin-left:8px}
.ok{background:#1f4d2e;color:#9fe0b0}.no{background:#4d3a1f;color:#e8c48a}</style>
<h1>The plain 4:3 preset next to the unmodified game</h1>
<p>Gameplay screen only (what a 4:3 display shows), from the test emulator at the DS's own resolution, so these are exact pixels.</p>%s""" % body)
print("preview/plain.html written (%d of %d identical)" % (len(same), len(names)))
