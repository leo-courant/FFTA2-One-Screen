#!/usr/bin/env python3
"""Ticket 10: the catalogue of dual-screen menus, as two pages.
preview/menus.html       each menu as the mod shows it: one screen, widescreen, from
                         shots/solo/*.png (scripts/solo_menus.sh)
preview/menus_dual.html  the same menus with both of the game's screens, widescreen
                         off, from shots/menus/*.png (scripts/menus_capture.sh)"""
import os, shutil, time

# (id, heading, what the info screen is doing, treatment, [(file, caption)])
GROUPS = [
 ("sheet", "A. The info screen is a sheet for what you have selected",
  "The info screen changes as you move the cursor: a unit's sheet, or an item's stats.",
  "Already handled (ticket 14): SELECT drops the sheet in over the gameplay screen, and item stats appear beside the game's Item Info panel. "
  "The in-battle screens of this kind (last row) get the same overlay, seen so far only in the low-resolution test emulator.",
  [("party", "Party list"), ("unitmenu", "Unit menu"), ("equip", "Change Equipment"), ("fitting", "Shop: Fitting Room"),
   ("shop", "Shop: Buy"), ("sell", "Shop: Sell"), ("itemlist", "Item List"),
   ("b_unitinfo", "In battle: Unit Info"), ("b_status", "In battle: Status"), ("b_items", "In battle: Item List"),
   ("late_unitmenu", "Late save: unit menu")]),
 ("needs", "B. The info screen holds something you need in order to choose",
  "Here the gameplay screen only has the list; what the choice does is on the info screen.",
  "Recommended: show that part automatically beside the list while it is open, as the item stats do, instead of needing SELECT each time.",
  [("jobs2", "Change Jobs: the stat changes (+1, +5) are only on the sheet"),
   ("b_abil", "View Abilities: the abilities and their mastery are only on the info screen"),
   ("late_setabil", "Late save: Set Abilities: the highlighted set's abilities are only on the info screen (ticket 32)"),
   ("late_bazaar", "Late save: Bazaar: the loot each recipe needs, and your grades, are only on the info screen (ticket 33)")]),
 ("clan", "C. The info screen is the clan summary",
  "The same summary (members, quests, talents, gil, date) whatever is selected. Nothing on it depends on the menu.",
  "Recommended: nothing to merge. SELECT already shows the summary when you want it.",
  [("wm", "World map"), ("wm_cursor", "World map: cursor on a quest"), ("main", "Main Menu"), ("system", "System Menu"),
   ("config", "Config"), ("town", "Town menu"), ("pub3", "Pub menu"), ("roster", "Pub: Quest Roster"),
   ("questdetail", "Pub: quest details"), ("p_current", "Pub: Current Quests"), ("p_rumors", "Pub: Rumors"),
   ("shop_sell", "Shop menu"), ("clan2", "Clan Menu"), ("c_quests", "Clan: Quest List"), ("c_report", "Clan: Quest Report"),
   ("c_loot", "Clan: Loot"), ("c_priv", "Clan: Clan Privileges"), ("c_laws", "Clan: Laws"),
   ("late_worldmap", "Late save: world map"), ("late_pubmenu", "Late save: pub menu"), ("late_trials", "Late save: Clan Trials"),
   ("late_trial_detail", "Late save: a clan trial"), ("late_roster", "Late save: Quest Roster"), ("late_shop", "Late save: shop menu"),
   ("late_ivalice", "Late save: map of Ivalice"), ("late_camoa", "Late save: Camoa"), ("late_camoa_town", "Late save: Camoa town menu")]),
 ("prep", "D. Before and after a battle",
  "The info screen is the battle one (objective, law, the unit under the cursor). The banner already carries the objective and law, "
  "but it stays up over the game's own headings here.",
  "Recommended: keep the banner while placing units and choosing the privilege, moved clear of the game's headings; hide it on the results and law bonus screens.",
  [("lawintro", "Law announcement"), ("place", "Unit placement"), ("privpick", "Choosing the privilege"),
   ("results", "Results"), ("lawbonus", "Law bonus")]),
 ("battle", "E. In battle",
  "Covered by the banner and turn order (tickets 07 and 09); SELECT shows the info screen full-size. Shown here for completeness.",
  "No new decision. One thing noticed: the Help window (Y) covers the banner while it is open.",
  [("b2", "Command menu"), ("b_attack2", "Attack: the forecast is on the gameplay screen"), ("b_useitem", "Using an item"),
   ("b_config", "Battle menu (X)"), ("b_law", "View Law"), ("b_help", "Help (Y)")]),
 ("auction", "G. Auctions (late save)",
  "The info screen shows the auction: the areas and champions in the hall, then the round's token list and, while bidding, the bar that fills in real time.",
  "Ticket 28: the bidding bar is what the player needs; the rest are menus over a picture.",
  [("late_camoa_town", "Camoa town menu: Auction House"), ("late_auction", "Auction House"), ("late_emporium", "Token Emporium"),
   ("late_auction_area", "Area up for auction"), ("late_auction_start", "About to begin"), ("late_auction_round", "Round"),
   ("late_auction_bid", "Bidding")]),
 ("later", "H. Later battles (ticket 24)",
  "Story quests 3 to 23 on their own maps (scripts/to_battles.sh): unit placement, then the fight after the first turns. Same kinds as D and E.",
  "Nothing new: the info screen is the battle one.",
  [x for q in (3, 7, 11, 13, 17, 18, 19, 20, 21, 22, 23) for x in (("bq%d_place" % q, "Quest %d: placement" % q), ("bq%d" % q, "Quest %d: fight" % q))]),
 ("blank", "F. The info screen is empty or decoration",
  "Nothing to show.", "Nothing to do.",
  [("save", "Save / Load slots"), ("name", "Name entry"), ("story", "Story scenes")]),
]

# ---- both original screens ----------------------------------------------------
os.makedirs("preview/menus", exist_ok=True)
t = int(time.time())
body = ""
for gid, head, what, treat, items in GROUPS:
    cards = ""
    for f, cap in items:
        src = "shots/menus/%s.png" % f
        if not os.path.exists(src):
            continue
        shutil.copy(src, "preview/menus/%s.png" % f)
        cards += '<figure><img src="menus/%s.png?t=%d" width=256 height=384 alt=""><figcaption>%s</figcaption></figure>' % (f, t, cap)
    body += '<section id="%s"><h2>%s</h2><p>%s</p><p class=rec>%s</p><div class=grid>%s</div></section>' % (gid, head, what, treat, cards)
extra = ""
for f, cap in (("ov_party", "Party list with SELECT"), ("ov_shop_info", "Shop with Item Info"), ("ov_equip_info", "Equipment with Item Info")):
    if os.path.exists("preview/%s.png" % f):
        extra += '<figure><img class=deck src="%s.png?t=%d" alt=""><figcaption>%s</figcaption></figure>' % (f, t, cap)
open("preview/menus_dual.html", "w").write("""<!doctype html><meta charset=utf-8><meta name=viewport content="width=device-width,initial-scale=1">
<title>Dual-screen menus</title>
<style>
body{background:#16161a;color:#ddd;font:15px/1.5 system-ui;margin:0;padding:24px}
h1{font-size:22px;margin:0 0 6px}h2{font-size:17px;margin:44px 0 4px;text-wrap:balance}
p{color:#aaa;max-width:70ch;margin:4px 0}
.rec{color:#e8d9a0}
.grid{display:flex;flex-wrap:wrap;gap:18px;margin-top:14px}
figure{margin:0;width:258px}
figcaption{color:#999;font-size:13px;margin-top:5px}
img{image-rendering:pixelated;border:1px solid #444;display:block}
.deck{width:640px;max-width:100%%;height:auto}
.wide figure{width:auto}
nav{margin:14px 0 0;display:flex;flex-wrap:wrap;gap:6px 18px}
nav a{color:#9cd}
</style>
<h1>Every dual-screen menu found: both original screens</h1>
<p>Each picture is one moment of the game with the info screen above and the gameplay screen below, as the game lays them out
(4:3, widescreen switched off for the capture). The line in yellow under each heading is the proposed treatment.</p>
<p>Set Abilities, the bazaar, auctions and clan trials come from the late save (ticket 24); the later battles from scripts/to_battles.sh.</p>
<nav>%s</nav>
%s
<section class=wide><h2>For reference: how group A looks in the mod today (melonDS, Deck resolution)</h2><div class=grid>%s</div></section>
""" % ("".join('<a href="#%s">%s</a>' % (g[0], g[1]) for g in GROUPS), body, extra))
print("preview/menus_dual.html written")

# ---- the mod's single screen ------------------------------------------------
# (heading, what to know, [(file, caption)])
SOLO = [
 ("A. Sheets for what you have selected",
  "The sheet lives on the info screen. SELECT lays it over the picture; the game's Item Info panel (R) gets the stats beside it. Still wrong (ticket 18): the tiled floor does not reach the sides.",
  [("party", "Party list"), ("party_ov", "Party list, SELECT"), ("unitmenu", "Unit menu"), ("equip", "Change Equipment"),
   ("equip_list", "Equipment: choosing a weapon"), ("equip_info", "Equipment: Item Info"), ("itemlist", "Item List"),
   ("buy", "Shop: Buy"), ("buy_info", "Shop: Item Info"), ("buy_ov", "Shop: Buy, SELECT"), ("sell", "Shop: Sell"),
   ("fitting", "Shop: Fitting Room"), ("unitinfo", "In battle: Unit Info"), ("unitinfo_ov", "In battle: Unit Info, SELECT"),
   ("status", "In battle: Status")]),
 ("B. Lists where what you need is on the info screen (ticket 16)",
  "Today you have to press SELECT to see the stat changes of a job or the abilities in a category. "
  "In View Abilities a stray translucent panel also appears on the left; that is a fault to fix in the same ticket.",
  [("jobs", "Change Jobs"), ("jobs2", "Change Jobs: Thief highlighted"), ("jobs_ov", "Change Jobs, SELECT: the +1 / +5 are here"),
   ("abil", "In battle: View Abilities"), ("abil_ov", "View Abilities, SELECT")]),
 ("C. Menus whose info screen is only the clan summary",
  "Nothing added. SELECT shows the summary (second picture). Still wrong (ticket 18): the weather icon is not on the corner globe, the clan menu and its lists keep black edges, and in Quest Report the highlighted square is away from the cursor.",
  [("worldmap", "World map"), ("worldmap_ov", "World map, SELECT"), ("quest", "World map: cursor on a quest"), ("main", "Main Menu"),
   ("system", "System Menu"), ("config", "Config"), ("town", "Town menu"), ("pub", "Pub menu"), ("current", "Pub: Current Quests"),
   ("questdetail", "Pub: quest details"), ("rumors", "Pub: Rumors"), ("shopmenu", "Shop menu"), ("clan", "Clan Menu"),
   ("quests", "Clan: Quest List"), ("report", "Clan: Quest Report"), ("loot", "Clan: Loot"), ("priv", "Clan: Clan Privileges"),
   ("laws", "Clan: Laws"), ("save", "Save slots")]),
 ("D. Before and after a battle (ticket 17)",
  "The banner is up on all of these and collides with the game's own headings; on the results and law bonus screens it should not be there at all.",
  [("lawintro", "Law announcement"), ("place", "Unit placement"), ("privpick", "Choosing the privilege"),
   ("results", "Results"), ("lawbonus", "Law bonus")]),
 ("E. In battle",
  "As built in tickets 07 and 09. The Help window (Y) covers the banner (ticket 17); the action name bar and the turn order share the same rows (ticket 18).",
  [("battle", "Command menu"), ("action", "Action"), ("target", "Choosing a target"), ("forecast", "Attack forecast"),
   ("help", "Help (Y)"), ("bmenu", "Battle menu (X)"), ("law", "View Law")]),
 ("F. Late in the game: menus with only the clan summary (ticket 24)",
  "From the late save. Nothing to add: the info screen is the clan summary, which SELECT shows.",
  [("late_worldmap", "World map"), ("late_pubmenu", "Pub menu with Clan Trials"), ("late_trials", "Clan Trials"),
   ("late_trial_detail", "A clan trial"), ("late_roster", "Quest Roster"), ("late_shop", "Shop menu with Bazaar"),
   ("late_ivalice", "Map of Ivalice"), ("late_camoa", "Camoa"), ("late_camoa_town", "Camoa town menu"), ("late_unitmenu", "Unit menu")]),
 ("G. Late in the game: two lists that need a decision",
  "Set Abilities: after a moment the mod's Item Info stats panel appears top left by itself (the game's Item Info word is set here too), over the unit panel, "
  "and cut off: the second column of abilities is missing (ticket 32). Bazaar: the recipe list is fine on the gameplay screen (melonDS picture), "
  "but what each recipe needs is on the info screen (ticket 33). The test emulator repeats the bazaar's list, so its picture is from melonDS.",
  [("late_setabil", "Set Abilities, first frames"), ("late_setabil_w90", "Set Abilities, 90 frames later: the stray panel"),
   ("shots/t24/melon_bazaar.png", "Bazaar (melonDS, Deck size)")]),
 ("H. Auctions (ticket 28)",
  "The hall's menus. The round and bidding screens are 2D and come out repeated in this capture; ticket 28 has how they look.",
  [("late_auction", "Auction House"), ("late_emporium", "Token Emporium"), ("late_auction_area", "Area up for auction"),
   ("late_auction_start", "About to begin")]),
 ("I. Later battle maps (ticket 24)",
  "Story quests on their own maps, reached by scripts/to_battles.sh (the party is the early one). Placement, then the fight after the first turns. "
  "Map and backdrop reach both edges on every map; panels sit at the edges. Since ticket 38 the enemies, laws and squares are each quest's own. "
  "Quest 18 and 23: the mist is a 2D layer, so its tiles show as seams here (the test emulator's limit). Quest 19's fight: the law is cut and the turn order's units are missing, a mod fault (ticket 41).",
  [x for q in (3, 7, 11, 13, 17, 18, 19, 20, 21, 22, 23) for x in (("bq%d_place" % q, "Quest %d: placement" % q), ("bq%d" % q, "Quest %d: fight" % q))]
  + [("shots/solo_battles/pan/b%d_%s.png" % (q, d), "Quest %d: Move, D-pad held %s: the camera at the map's edge (older picture, enemies not the quest's)" % (q, d.lower()))
     for q in (13, 19) for d in ("UP", "DOWN", "LEFT", "RIGHT")]),
]
os.makedirs("preview/solo", exist_ok=True)
body = ""
for head, what, items in SOLO:
    cards = ""
    for f, cap in items:
        src = f if "/" in f else "shots/solo/%s.png" % f
        if not os.path.exists(src):
            continue
        f = os.path.splitext(os.path.basename(f))[0] if "/" in f else f
        shutil.copy(src, "preview/solo/%s.png" % f)
        cards += '<figure><a href="solo/%s.png"><img src="solo/%s.png?t=%d" width=640 height=400 alt=""></a><figcaption>%s</figcaption></figure>' % (f, f, t, cap)
    body += '<section><h2>%s</h2><p>%s</p><div class=grid>%s</div></section>' % (head, what, cards)
open("preview/menus.html", "w").write("""<!doctype html><meta charset=utf-8><meta name=viewport content="width=device-width,initial-scale=1">
<title>Menus in the mod</title>
<style>
body{background:#16161a;color:#ddd;font:15px/1.5 system-ui;margin:0;padding:24px}
h1{font-size:22px;margin:0 0 6px}h2{font-size:17px;margin:44px 0 4px;text-wrap:balance}
p{color:#aaa;max-width:75ch;margin:4px 0}
.grid{display:grid;grid-template-columns:repeat(auto-fill,minmax(min(640px,100%%),1fr));gap:18px;margin-top:14px}
figure{margin:0}
figcaption{color:#bbb;font-size:13px;margin-top:5px}
img{image-rendering:pixelated;border:1px solid #444;display:block;width:100%%;height:auto}
a{color:#9cd}
</style>
<h1>Every menu found, as the mod shows it</h1>
<p>One screen, widescreen, at Deck resolution (1280x800; click a picture for full size). These are the current build, faults included.
They are composed from the fast test emulator and match melonDS apart from colour rounding.</p>
<p>The same menus with both of the game's original screens: <a href="menus_dual.html">menus_dual.html</a>.</p>
%s""" % body)
print("preview/menus.html written")
