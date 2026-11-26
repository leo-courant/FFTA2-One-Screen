#!/usr/bin/env python3
"""PROTOTYPE - throwaway. Mock up single-screen battle HUD variants.

Question: where should the top-screen battle info (objective, law / special
rules, turn order) live on the 256x192 gameplay screen so that all of it is
visible at all times?  Three structurally different variants, composited from
real screenshots, written to one self-contained HTML page with a switcher.

run:  .venv/bin/python prototype/make_hud_prototype.py   (from ~/ffta2-mod)
"""
import base64
import io
from PIL import Image, ImageDraw

CMD = Image.open("shots/intro3/q10.png").convert("RGB")   # command menu open
MOVE = Image.open("shots/intro3/q09.png").convert("RGB")  # choosing a move tile
TOP = CMD.crop((0, 0, 256, 192))
RED = TOP.getpixel((150, 8))
PARCH = TOP.getpixel((150, 60))
PARCH_D = TOP.getpixel((150, 34))
INK = (60, 30, 20)

OBJ_ICON = TOP.crop((0, 0, 28, 16))
OBJ_TEXT = TOP.crop((30, 2, 96, 16))
W_DEFEAT, W_KLESTA = TOP.crop((30, 2, 62, 16)), TOP.crop((63, 2, 96, 16))
LAW_X = TOP.crop((18, 26, 38, 41))
LAW_TEXT = TOP.crop((38, 26, 114, 41))
W_RANGED, W_WEAPONS = TOP.crop((38, 26, 74, 41)), TOP.crop((75, 26, 114, 41))
FORBID = TOP.crop((24, 18, 84, 26))
ACTIVE = TOP.crop((113, 117, 147, 176))
WAITING = [TOP.crop((168, 147, 192, 179)), TOP.crop((198, 147, 224, 179)),
           TOP.crop((228, 147, 254, 179))]
HEADS = [TOP.crop((116, 117, 146, 137)), TOP.crop((170, 148, 190, 166)),
         TOP.crop((200, 148, 222, 166)), TOP.crop((230, 148, 252, 166))]
HTAB = CMD.crop((0, 192, 46, 203))


def bottoms():
    return [CMD.crop((0, 192, 256, 384)), MOVE.crop((0, 192, 256, 384))]


def variant_a(b):
    """Banner: one full-width bar; objective left, law right, turn order under it."""
    d = ImageDraw.Draw(b)
    d.rectangle((0, 0, 127, 15), fill=RED)
    b.paste(OBJ_ICON.crop((0, 0, 28, 16)), (0, 0))
    b.paste(OBJ_TEXT, (30, 1))
    d.rectangle((128, 0, 255, 15), fill=PARCH_D)
    b.paste(LAW_X.crop((0, 0, 20, 15)), (130, 0))
    b.paste(LAW_TEXT, (150, 0))
    d.line((0, 16, 255, 16), fill=INK)
    # turn order: heads strip, right aligned under the bar
    x = 256 - 4 * 26 - 2
    d.rectangle((x - 2, 17, 255, 38), fill=PARCH, outline=INK)
    for i, h in enumerate(HEADS):
        if i == 0:
            d.rectangle((x, 18, x + 25, 37), fill=(240, 160, 20))
        b.paste(h.resize((24, 18), Image.NEAREST), (x + 1, 19))
        x += 26
    b.paste(HTAB, (0, 17))
    return b


def variant_b(b, clean):
    """Sidebar: a dedicated 48px column on the right; map and menus shift left."""
    d = ImageDraw.Draw(b)
    # shift the right-hand HUD (commands, Config/Help) 48px left
    hud = b.crop((176, 76, 256, 192))
    b.paste(clean.crop((176, 76, 208, 192)), (176, 76))
    b.paste(hud, (128, 76))
    d.rectangle((208, 0, 255, 191), fill=PARCH, outline=INK)
    d.rectangle((209, 1, 254, 30), fill=RED)
    b.paste(W_DEFEAT, (215, 2))
    b.paste(W_KLESTA, (215, 16))
    d.rectangle((209, 31, 254, 70), fill=PARCH_D)
    b.paste(FORBID.crop((0, 0, 44, 8)), (210, 33))
    b.paste(W_RANGED, (214, 41))
    b.paste(W_WEAPONS.crop((0, 0, 39, 15)), (212, 55))
    d.line((209, 71, 254, 71), fill=INK)
    y = 74
    d.rectangle((211, y, 252, y + 22), fill=(240, 160, 20))
    b.paste(HEADS[0].resize((30, 20), Image.NEAREST), (217, y + 1))
    y += 26
    for w in WAITING:
        b.paste(w, (220, y))
        y += 30
    return b


def variant_c(b):
    """Card: everything in one compact window in the top-right corner."""
    d = ImageDraw.Draw(b)
    x0 = 148
    d.rectangle((x0, 0, 255, 54), fill=PARCH, outline=INK)
    d.rectangle((x0 + 1, 1, 254, 16), fill=RED)
    b.paste(OBJ_ICON.crop((6, 0, 24, 16)), (x0 + 1, 1))
    b.paste(OBJ_TEXT, (x0 + 22, 2))
    d.rectangle((x0 + 1, 17, 254, 32), fill=PARCH_D)
    b.paste(LAW_X.crop((0, 0, 20, 15)), (x0 + 2, 17))
    b.paste(LAW_TEXT, (x0 + 22, 17))
    x = x0 + 3
    for i, h in enumerate(HEADS):
        if i == 0:
            d.rectangle((x - 1, 34, x + 24, 53), fill=(240, 160, 20))
        b.paste(h.resize((24, 18), Image.NEAREST), (x, 35))
        x += 26
    return b


def b64(im):
    buf = io.BytesIO()
    im.save(buf, "PNG")
    return base64.b64encode(buf.getvalue()).decode()


def main():
    clean = MOVE.crop((0, 192, 256, 384))
    variants = [
        ("0", "Today (top screen lost)", "What a single-screen emulator view shows now: none of the top-screen info.", lambda b: b),
        ("A", "Banner", "One bar across the top: objective left, law right. Turn order as a strip of heads underneath. Costs about 16px of map height plus a corner.", variant_a),
        ("B", "Sidebar", "A dedicated 48px column on the right holds everything, with full-size unit sprites. Menus shift left; the map view is 208px wide and never covered.", lambda b: variant_b(b, clean)),
        ("C", "Corner card", "One compact window in the top-right corner. The rest of the map stays untouched, but the corner is always covered.", variant_c),
    ]
    data = []
    for key, name, note, fn in variants:
        ims = [fn(b.copy()) for b in bottoms()]
        for i, im in enumerate(ims):
            im.save("prototype/variant_%s_%d.png" % (key, i))
        data.append((key, name, note, [b64(i) for i in ims]))
    top = b64(TOP)

    js = ",".join('{k:"%s",n:"%s",t:"%s",i:["%s","%s"]}' % (k, n, t, i[0], i[1])
                  for k, n, t, i in data)
    html = """<!doctype html><meta charset=utf-8><title>FFTA2 single-screen HUD prototype</title>
<style>
body{background:#16161a;color:#ddd;font:15px system-ui;margin:0;padding:20px 20px 90px;text-align:center}
h1{font-size:17px;margin:0 0 4px}p{max-width:780px;margin:6px auto;color:#aaa}
.row{display:flex;gap:20px;justify-content:center;flex-wrap:wrap;margin-top:14px}
figure{margin:0}figcaption{color:#888;font-size:12px;margin-top:4px}
img{image-rendering:pixelated;width:768px;max-width:100%%;border:1px solid #444;display:block}
img.small{width:384px}
#bar{position:fixed;bottom:16px;left:50%%;transform:translateX(-50%%);background:#fff;color:#111;
border-radius:999px;padding:8px 14px;box-shadow:0 4px 18px #000a;display:flex;gap:14px;align-items:center;font-weight:600}
#bar button{border:0;background:#111;color:#fff;border-radius:50%%;width:30px;height:30px;cursor:pointer;font-size:16px}
</style>
<h1>PROTOTYPE: where does the top-screen battle info go on a single screen?</h1>
<p>Mock-ups pasted together from real screenshots, not the game running. Use the arrows (or the left/right keys) to flip variants.</p>
<p id=note></p>
<div class=row>
<figure><img id=s0><figcaption>Command menu open</figcaption></figure>
<figure><img id=s1><figcaption>Choosing where to move</figcaption></figure>
</div>
<div class=row><figure><img class=small src="data:image/png;base64,%s"><figcaption>For reference: the original top screen in this battle</figcaption></figure></div>
<div id=bar><button id=prev>&larr;</button><span id=label></span><button id=next>&rarr;</button></div>
<script>
const V=[%s];
function cur(){const k=new URLSearchParams(location.search).get('variant')||'A';const i=V.findIndex(v=>v.k==k);return i<0?1:i}
function show(i){i=(i+V.length)%%V.length;const v=V[i];history.replaceState(null,'','?variant='+v.k);
label.textContent=v.k+' ('+v.n+')';note.textContent=v.t;s0.src='data:image/png;base64,'+v.i[0];s1.src='data:image/png;base64,'+v.i[1]}
prev.onclick=()=>show(cur()-1);next.onclick=()=>show(cur()+1);
addEventListener('keydown',e=>{if(e.key=='ArrowLeft')show(cur()-1);if(e.key=='ArrowRight')show(cur()+1)});
show(cur());
</script>""" % (top, js)
    open("prototype/hud-prototype.html", "w").write(html)
    print("wrote prototype/hud-prototype.html")


if __name__ == "__main__":
    main()
