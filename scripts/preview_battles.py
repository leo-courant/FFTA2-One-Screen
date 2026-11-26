#!/usr/bin/env python3
"""Page for ticket 38's review: the later battles with their own enemies, next to the old
route's, one screen each (1280x800).  usage: scripts/preview_battles.py
Reads shots/solo/bq*.png (scripts/solo_menus.sh) and the old route's pictures in
work/t38/old_solo/; writes preview/battles.html + preview/battles/. View it at
http://localhost:8765/battles.html."""
import json, os, shutil
OUT = "preview/battles"
os.makedirs(OUT, exist_ok=True)
Q = [3, 7, 11, 13, 17, 18, 19, 20, 21, 22, 23]
NOTE = {18: "Look at: the boss and its two attendants stand on the ground; the white portal is the game's own (the boss covers it). Seams in the mist are the test emulator's, not the mod's.",
        23: "Seams in the mist are the test emulator's.",
        19: "Fight: the law is cut off and the turn order's figures are missing. A mod fault, ticket 41."}
rows = []
for q in Q:
    for part, cap in (("_place", "placement"), ("", "fight")):
        n = "bq%d%s.png" % (q, part)
        new, old = "shots/solo/" + n, "work/t38/old_solo/" + n
        if not os.path.exists(new):
            continue
        shutil.copy(new, "%s/new_%s" % (OUT, n))
        if os.path.exists(old):
            shutil.copy(old, "%s/old_%s" % (OUT, n))
        rows.append((q, "Quest %d, %s" % (q, cap), NOTE.get(q, "") if part == "" or q != 19 else "",
                     "battles/new_" + n, "battles/old_" + n if os.path.exists(old) else ""))
html = """<!doctype html><meta charset=utf-8><meta name=viewport content="width=device-width,initial-scale=1">
<title>Later battles</title><style>
body{background:#16161a;color:#ddd;font:15px/1.5 system-ui;margin:0;padding:24px}
h1{font-size:22px;margin:0 0 6px}p{color:#aaa;max-width:75ch;margin:4px 0}
figure{margin:28px 0;max-width:1280px}img{width:100%;image-rendering:pixelated;display:block}
figcaption{margin:6px 0;color:#eee}button{font:inherit;padding:4px 12px;margin-left:8px}
</style><h1>Later battles</h1>
<p>Each picture is the mod's one screen. The button shows the old test route's picture (stand-in enemies, some off the map).</p>
<div id=x></div><script>
const R=__ROWS__;
R.forEach(([q,cap,note,n,o])=>{const f=document.createElement('figure');let old=false;
const i=new Image();i.src=n;i.alt=cap;const c=document.createElement('figcaption');c.textContent=cap+(note?' — '+note:'');
f.append(c,i);if(o){const b=document.createElement('button');b.textContent='show old';b.onclick=()=>{old=!old;i.src=old?o:n;b.textContent=old?'show new':'show old'};c.append(b)}
document.getElementById('x').append(f)})
</script>"""
open("preview/battles.html", "w").write(html.replace("__ROWS__", json.dumps(rows)))
print("preview/battles.html written: %d pictures" % len(rows))
