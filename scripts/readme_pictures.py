#!/usr/bin/env python3
"""The README's and the catalogue's before -> after pictures, and the Scion clip.

usage: readme_pictures.py readme|catalogue|clip|all

Each picture is the unmodified game on a drawn DS (both screens at 2x, with the hinge between
them, so it is plain the game used to be split) next to the Deck build's one screen at 1280x800,
with an arrow between. Captures first (none of them go in git; build/ is ignored):

  pictures   O=build/cat/after scripts/solo_menus.sh
             RAW=1 NOSEL=1 ROM=build/ffta2-ref.nds O=build/cat/before scripts/solo_menus.sh
             (build/ffta2-ref.nds: patch.py ... --display 4x3 --no-hooks, see docs/test-saves.md)
  clip       ROM=build/ffta2-ref.nds scripts/play_scion.py 0 build/belias/before 206,208,...,774
             scripts/solo_scion.py 0 build/belias/after 206-776/2

Writes docs/pictures/*.png (README), docs/pictures/catalogue/*.png (docs/catalogue.md) and
docs/pictures/belias.webp, plus build/belias/belias.mp4 (to upload through GitHub's editor).
The only game pictures the repository may hold are these (audit_repo.py allows docs/pictures/).
"""
import os, subprocess, sys
from PIL import Image, ImageDraw

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CAT = os.path.join(ROOT, "build", "cat")
CLIP = os.path.join(ROOT, "build", "belias")
PICS = os.path.join(ROOT, "docs", "pictures")

README = {"battle": ("battle", "battle"), "info-overlay": ("party", "party_ov"),
          "change-jobs": ("jobs2", "jobs2"), "world-map": ("worldmap", "worldmap")}
BEZEL, HINGE, EDGE, ARROW = (74, 77, 82), (43, 45, 49), (98, 102, 108), (136, 136, 136)
B, G, GAP = 12, 32, 120                  # bezel, hinge height, room for the arrow
DS_W, DS_H = 512 + 2 * B, 384 * 2 + 2 * B + G
W, H = DS_W + GAP + 1280, DS_H


def catalogue():
    out = {}
    for line in CATALOGUE_LIST.strip().splitlines():
        name, before, *after = line.split()
        out[name] = (before, after[0] if after else before)
    return out


# docs/catalogue.md shows these (its own order and captions): name, before, after if different
CATALOGUE_LIST = """
action action
forecast forecast
help help
battle-menu bmenu
law law
unit-sheet unitinfo unitinfo_ov
ability-list abil_mage_list
status status
privilege privpick
placement place
results results
law-bonus lawbonus
later-battle bq18
story-in-battle bq22
equipment equip
item-info equip_info
item-list itemlist
main-menu main
clan clan
quests quests
world-map-sheet worldmap worldmap_ov
town town
pub pub
quest-details questdetail
shop shopmenu
buying buy_info
fitting-room fitting
map-of-ivalice late_ivalice
bazaar late_bazaar
auction-house late_auction
later-town late_camoa_town
clan-trials late_trials
token-emporium late_emporium
"""


def ds(before):
    """Both screens (a 256x384 capture, top over bottom) at 2x on a drawn DS: a bezel round
    them and the hinge between, so the split is obvious."""
    s = before.convert("RGB").resize((512, 768), Image.NEAREST)
    im = Image.new("RGBA", (DS_W, DS_H), BEZEL + (255,))
    d = ImageDraw.Draw(im)
    d.rectangle((0, B + 384, DS_W - 1, B + 384 + G - 1), fill=HINGE + (255,))
    for y in (B + 384 + 9, B + 384 + G - 10):
        d.line((B, y, DS_W - B - 1, y), fill=EDGE + (255,), width=2)
    im.paste(s.crop((0, 0, 512, 384)), (B, B))
    im.paste(s.crop((0, 384, 512, 768)), (B, B + 384 + G))
    return im


def pair(before, after, bg=(0, 0, 0, 0)):
    im = Image.new("RGBA", (W, H), bg)
    im.paste(ds(before), (0, 0))
    im.paste(after.convert("RGB"), (DS_W + GAP, (H - 800) // 2))
    d = ImageDraw.Draw(im)
    cx, cy = DS_W + GAP // 2, H // 2
    d.rectangle((cx - 36, cy - 9, cx + 8, cy + 9), fill=ARROW + (255,))
    d.polygon([(cx + 8, cy - 28), (cx + 40, cy), (cx + 8, cy + 28)], fill=ARROW + (255,))
    return im


def pictures(table, outdir):
    os.makedirs(outdir, exist_ok=True)
    for name, (b, a) in table.items():
        pair(Image.open(os.path.join(CAT, "before", b + ".png")),
             Image.open(os.path.join(CAT, "after", a + ".png"))).save(
            os.path.join(outdir, name + ".png"), optimize=True)
        print(os.path.relpath(os.path.join(outdir, name + ".png"), ROOT))


def clip(first=300, last=700):
    """Belias from game frame `first` to `last` (captures every 2nd frame): an animated WebP
    for the README (half size, 15 fps, see-through round the pictures) and an MP4."""
    frames = range(first, last, 2)
    load = lambda side, f: Image.open(os.path.join(CLIP, side, "0_%04d.png" % f))
    web = [pair(load("before", f), load("after", f)).resize((W // 2, H // 2), Image.LANCZOS)
           for f in frames[::2]]
    out = os.path.join(PICS, "belias.webp")
    web[0].save(out, save_all=True, append_images=web[1:], duration=67, loop=0, quality=55, method=6)
    print(os.path.relpath(out, ROOT), os.path.getsize(out) // 1024, "KB")
    tmp = os.path.join(CLIP, "mp4")
    os.makedirs(tmp, exist_ok=True)
    for i, f in enumerate(frames):
        pair(load("before", f), load("after", f), (13, 17, 23, 255)).convert("RGB").save(
            os.path.join(tmp, "%04d.png" % i))
    mp4 = os.path.join(CLIP, "belias.mp4")
    subprocess.check_call(["ffmpeg", "-loglevel", "error", "-y", "-framerate", "30", "-i",
                           os.path.join(tmp, "%04d.png"), "-vf", "scale=1280:-2:flags=lanczos",
                           "-c:v", "libx264", "-crf", "28", "-preset", "slow", "-pix_fmt", "yuv420p",
                           "-movflags", "+faststart", mp4])
    print(os.path.relpath(mp4, ROOT), os.path.getsize(mp4) // 1024, "KB")


if __name__ == "__main__":
    what = sys.argv[1] if len(sys.argv) > 1 else "all"
    if what in ("readme", "all"):
        pictures(README, PICS)
    if what in ("catalogue", "all"):
        pictures(catalogue(), os.path.join(PICS, "catalogue"))
    if what in ("clip", "all"):
        clip()
