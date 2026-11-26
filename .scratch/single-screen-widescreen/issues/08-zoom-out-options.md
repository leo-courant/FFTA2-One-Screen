# 08: Zoom-out options

**What to build:** Offer the player a slightly zoomed-out view. Produce a side-by-side preview of two or three zoom levels on the Deck's resolution and build the one the user picks.

**Blocked by:** 01, 04, 05, 20

**Changed (user, 2026-11-23):** zoom is a choice made when patching, part of the display preset (ADR 0007), not a switch in the game. "Switchable" below now means "can be picked as a preset option".

**Status:** done, approved by the user (2026-11-23): 3.5x (366x228) is the Deck preset

- [x] Preview page shows the candidate zoom levels
- [x] The chosen level is built and switchable
- [x] No missing map or backdrop at the chosen level

## Result (2026-11-23)

The view is now 320x200 game pixels, chosen because it is exactly 4 screen pixels per game pixel at 1280x800 (ADR 0004), with a sub-pixel nudge. Measured in melonDS: text and panel edges on the 4px grid went from about half to 94-99% horizontally and about 90% vertically. Panels are anchored vertically as well. No other zoom levels were previewed, and the level is not switchable yet.

## Candidates previewed (2026-11-23)

Preview: `scripts/preview_zoom.py` → `preview/zoom.html`. Builds: `patch.py ... --view 366x228` and `--view 426x266` (`build/ffta2-z*.nds`); all 57 menu captures per level with `FIT=1280x800 ROM=... O=shots/t08/<view> scripts/solo_menus.sh` (`solo.py` got `FIT=WxH`: nearest-neighbour enlargement to the display for views that do not divide it); one melonDS capture of the party room per level (`melon_save.sh`, keys `s:1.5 x:3 x:2`, `shots/t08/melon/`).

| View | Zoom on 1280x800 | Game pixels | Edges on the grid in melonDS (across / down) |
| --- | --- | --- | --- |
| 320x200 | 4x (today) | all 4x4 | 98% / 82% |
| 366x228 | 3.5x | 3 and 4 alternate | 80% / 50% |
| 426x266 | 3.005x | nearly all 3x3, soft in melonDS | 80% / 63% |

(Measured with a fractional-period version of `measure_grid.py`: share of colour changes within half a pixel of the best-fitting grid.)

**Main finding:** on a 1280x800 screen 4x is the only zoom between the game's own view and 2x where every game pixel gets the same number of screen pixels (1280 / view width must be whole). 3x would need a 426.67-pixel view; and melonDS renders at 256 x its scale factor first, so a view of 426 never divides evenly there either. Any zoom-out on the Deck therefore gives up the even pixels ADR 0004 was made for. Other displays do have even zoom-outs: 1920x1080 at 4x is 480x270 (the 16:9 preset uses 5x, 384x216), 2560x1440 at 4x is 640x360.

**Faults seen at 366x228 and 426x266** (only worth fixing for a level that is picked): the world map's description box no longer reaches the bottom edge (open). The clan parchment's streaks above and below are fixed (below). The pub's empty speech bubble was a capture moment, not a fault: its text is redrawn when the highlighted option changes, a few frames after the press. No missing map or backdrop in battle, menus or world map; no black edges except the world-map SELECT overlay (a capture limit, as before).

## User review 1 (2026-11-23)

The user's favourite is **3.5x (366x228)**; nothing bothered them in the captures, and they asked to be shown where it looks uneven (added to `preview/zoom.html`: melonDS spots enlarged 3x, flip between 4x and 3.5x). Pictures must be shown at the Deck's real size (1280x800, one screen pixel per display pixel), flipping between levels in place.

Fixed from the same review, at every level:
- **Weather icon outside the world map's globe** (a regression since ticket 18): `sprite_fix` skipped every sprite while the word at 0x0212418C was 2, and that word stays 2 on the world map after a battle. The battle test is now `BATTLE_OBJ`, the pointer at 0x02127D00: non-zero from a battle's opening to the end of its results, 0 on the world map and in its menus, the one word that separated the two across all 57 test screens (memory dumps via `play.py`'s new `DUMP=dir`). `in_battle` uses it too (it also stuck after a battle, which would have hidden the shop's Item Info stats). Both words are in `docs/symbols.tsv`.
- **Clan parchment streaking above and below:** `map_extend` carried the picture's patterned top and bottom rows outwards. Above and below it now fills with the picture's corner texel (the brown beside the sheet; top-left for above, bottom-left for below, both texture coordinates from that corner cell, because the six cells share one texture atlas), so the parchment reads as a sheet lying on the brown.

Checked against a build of the previous commit (all 57 captures): only the world-map screens (icon) and the clan menus (parchment) change; battle captures differ by animation phase only.

## Built: 3.5x is the Deck preset (2026-11-23)

The user chose 3.5x. `patch.py`'s `deck` preset now builds a 366x228 view (ADR 0009; ADR 0004 marked superseded for the Deck; `--view 320x200` gives the even 4x). The nudge stays +3, -3: measured in melonDS on Wood Village with `try_nudge.sh` (now on a 3.5-pixel grid; `measure_grid.py` takes fractional sizes): 3,-3 77% / 53%; 0,0 73% / 44%; -3,3 77% / 45%; 6,-6 72% / 46%. `solo.py` now enlarges to 1280x800 by default (`FIT`), `SCALE=n` for whole multiples. `hook.c`'s built-in defaults follow (366x228, margins 96 / 24).

Fixed on the way (all presets):
- **World map corner flicker:** the place name and the weather icon jumped between the corner globe and their old spot on every other frame, with or without a menu open, so single pictures showed either (the "weather looks off again" report; it also explained the earlier melonDS capture). The world map draws its panels at 30 Hz, so one drawing pass spans the mod's 60 Hz frame boundary, and the globe, which follows its own rectangle from last frame, was only recorded every other pass. Now a panel that followed its own rectangle is recorded again, a frame that drew nothing keeps last frame's list, and the weather icon checks this frame's list as well as last frame's.
- **Place name off its tab** ("Wood Village" above the tab at 3.5x): text lines are judged by their middle, not their top (the name starts 1 px above the tab), and fall back to last frame's panels when placed before their panel is drawn.
- The world map's description box does reach the bottom edge; the earlier note was a misreading of a shrunk picture.

Checked: all 57 solo captures (no black edges except the world-map SELECT overlay, a capture limit; against the build before the flicker fix only the world-map menus and animation phase differ); consecutive frames on the world map with and without the main menu are steady; melonDS at 1280x800: battle 2 (command menu, an enemy turn, unit placement), the world map with and without the main menu (`shots/t08/melon/battle2_deck*.png`, `worldmap_366x228_fix.png`, `menu_deck.png`); the 4:3 preset still matches the unmodified game (ticket 02 method).
