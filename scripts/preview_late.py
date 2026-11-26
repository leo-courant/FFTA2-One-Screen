#!/usr/bin/env python3
"""Write preview/late.html: the screens the late-game save opens (ticket 24), as the mod
shows them on the Deck. Captures: shots/solo_late/<name>.png, made by
    for n in NAMES: scripts/solo.py states/late/l_<n>.dst "w10,s<n>" shots/solo_late
(states from scripts/to_late.sh). One picture at a time at the display's real size;
buttons or number keys flip between them."""
import json, os, shutil, time

ITEMS = [
    ("worldmap", "World map", "The late save loaded: Wood Village. Camoa and the neighbouring areas show faintly around Targ Wood."),
    ("trials", "Clan Trials", "New: the pub's Clan Trials list (opens at this story progress, after the game's own explanation)."),
    ("trial_detail", "A clan trial", "Detail page of a trial."),
    ("pubmenu", "Pub menu", "Now with Clan Trials between Current Quests and Rumors."),
    ("roster", "Quest Roster", "Quests from every part of the game are posted (before: one)."),
    ("shop", "Shop menu", "Bazaar and Sell Loot are new."),
    ("bazaar", "Bazaar", "New: the bazaar's loot list with grades A to E."),
    ("unitmenu", "Unit menu", "Set Abilities is enabled (it was greyed out in the old saves)."),
    ("setabil", "Set Abilities", "New: a level 99 unit's ability sets, every ability mastered."),
    ("ivalice_before", "Map of Ivalice, before", "The previous build: a block missing bottom left and the western lands cut off at the left (the mod had hidden map pieces lying outside the 4:3 picture). On the right, the game's own sea beyond the edge of its map picture."),
    ("ivalice", "Map of Ivalice, fixed", "Now: the whole map is drawn. The band on the right is still the game's sea: its map picture fades out there and the 4:3 view never reaches it. Weather: the globe is empty on this map in the unmodified game too."),
    ("camoa", "Camoa", "A second area's map."),
    ("camoa_town", "Camoa town menu", "In the auction month the town menu gains Auction House; the top screen counts the days left."),
    ("auction", "Auction House", "The auction house and its menu (Enter, Areas, Records)."),
    ("emporium", "Token Emporium", "Tokens bought with clan points before the auction."),
    ("auction_area", "Auction: area", "The area up for auction, with its champion. Fixed: the backdrop and its box now reach both edges (it was left at 4:3 width with black sides, and the champion text had slid off it)."),
    ("auction_start", "Auction: about to begin", "Take part or skip the round."),
    ("auction_round", "Auction round", "What the mod shows: the token list and buttons, a 2D screen, which the emulator stretches about 43% wider. The bidding bar is on the info screen."),
    ("auction_bid", "Auction bidding", "Bidding has started, but the bar that fills in real time with the other clans' avatars is on the info screen, which the mod does not show: the player bids blind. Ticket 28."),
    ("dual:auction_bid", "Auction bidding, both DS screens", "For reference, the two original screens: the bidding bar (top) is what the mod's screen is missing."),
]
t = int(time.time())
items = []
for name, title, text in ITEMS:
    if name.startswith("dual:"):
        # both DS screens side by side at 3x (shots/t24/late/_<name>.png from to_late.sh)
        name = name[5:]
        src = "shots/t24/late/_%s.png" % name
        if not os.path.exists(src):
            continue
        from PIL import Image
        im = Image.open(src)
        pair = Image.new("RGB", (512 + 8, 192), (22, 22, 26))
        pair.paste(im.crop((0, 0, 256, 192)), (0, 0)); pair.paste(im.crop((0, 192, 256, 384)), (264, 0))
        pair.resize((520 * 2, 192 * 2), Image.NEAREST).save("preview/late_%s.png" % name)
        items.append({"src": "late_%s.png?t=%d" % (name, t), "title": title, "text": text})
        continue
    src = "shots/solo_late/%s.png" % name
    if os.path.exists(src):
        shutil.copy(src, "preview/late_%s.png" % name)
        items.append({"src": "late_%s.png?t=%d" % (name, t), "title": title, "text": text})

page = """<!doctype html><meta charset=utf-8><meta name=viewport content="width=device-width,initial-scale=1">
<title>Late-game screens</title>
<style>
:root{--bg:#16161a;--fg:#ddd;--dim:#9a9aa6;--btn:#2a2a33;--on:#c25b2a}
body{background:var(--bg);color:var(--fg);font:15px system-ui;margin:0;padding:16px}
h1{font-size:19px;margin:0 0 6px}p{color:var(--dim);max-width:900px;margin:4px 0 10px}
#bar{display:flex;flex-wrap:wrap;gap:6px;margin:10px 0}
button{background:var(--btn);color:var(--fg);border:0;border-radius:6px;padding:6px 10px;font:inherit;cursor:pointer}
button.on{background:var(--on);color:#fff}
#cap{font-weight:600;margin:6px 0 2px}#txt{margin:0 0 10px}
img{image-rendering:pixelated;display:block;max-width:100%%}
</style>
<h1>Ticket 24: screens the late-game save opens</h1>
<p>Built from your own ROM, no download: the old world-map save with the game's save data filled in (level 99 party, everything owned and mastered) and the story progress moved on, then saved and loaded in the game. Each picture is the mod's screen on the Steam Deck (1280x800, 3.5x), at its real size. The buttons, keys 1-9 and 0, or the arrow keys flip between them.</p>
<div id=bar></div><div id=cap></div><p id=txt></p><img id=pic alt="">
<script>
const items=%s;
const bar=document.getElementById('bar'),pic=document.getElementById('pic');
function show(i){items.forEach((_,j)=>bar.children[j].classList.toggle('on',i===j));
  pic.src=items[i].src;pic.style.width=(1280/window.devicePixelRatio)+'px';
  document.getElementById('cap').textContent=(i+1)+'. '+items[i].title;
  document.getElementById('txt').textContent=items[i].text;}
items.forEach((it,i)=>{const b=document.createElement('button');b.textContent=(i+1)+' '+it.title;b.onclick=()=>show(i);bar.appendChild(b);});
document.addEventListener('keydown',e=>{const k='1234567890'.indexOf(e.key);if(k>=0&&k<items.length)show(k);
  if(e.key==='ArrowRight')show((items.findIndex((_,j)=>bar.children[j].classList.contains('on'))+1)%%items.length);
  if(e.key==='ArrowLeft')show((items.findIndex((_,j)=>bar.children[j].classList.contains('on'))+items.length-1)%%items.length);});
show(0);
</script>
""" % json.dumps(items)
open("preview/late.html", "w").write(page)
print("preview/late.html written (%d pictures)" % len(items))
