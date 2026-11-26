# 37: Action name bar across the whole width

**What to build:** When an ability or attack is used, its name appears on a dark bar near the top of the battle screen. The user wants that bar to run across the whole width of the wide screen (ticket 24 review, 2026-11-24). Today it keeps the width it has in the game.

**Blocked by:** None. Second batch.

**Status:** done, approved by the user (2026-11-25). Preview: http://localhost:8765/actionbar.html (`scripts/preview_bar.py`)

- [x] The bar runs from edge to edge on every preset, with the name still centred
- [x] Checked with the banner and turn order up (ticket 18 shortened this bar so it ended at the turn order; check whether that still applies after ticket 07's stage turn order) and in melonDS at Deck size

## Notes

- In the unmodified game the bar is not full width either: about 180 of 256 pixels, centred (`shots/t24/battles/b3.png`, top of the gameplay screen). So this is a change of look, not a fault; confirm with the user whether "the whole width" means the screen's full width or the bar widened in proportion, before building.
- Ticket 18 has where the bar is drawn (the "action name bar"); stretching a piece needs whole-texel sampling at the ends (ticket 24, auction backdrop).

## Built (2026-11-25)

**What "the whole width" means:** the note above is wrong. Its picture is a DS-resolution capture of the *squeezed* wide view; 180 px there are the game's whole 256. The bar (window kind "other", 0,12 256x24) fills the 4:3 picture, so on widescreen it runs from screen edge to screen edge, like the bars of tickets 39 and 40.

**Why it was short:** ticket 18's rule widened it only while the turn order was a strip at the top right. Since ticket 07 the turn order stands on the stage at the bottom, so the rule no longer applied. Its width had no effect anyway: the frame doesn't come from the window's width but from 3x3 pieces whose x and width are bytes (0x0204E4AC).

**How:** `window_draw_with` gives the bar the full view and each of the frame's three columns about a third (all columns look the same, ends included, so nothing is visibly stretched and there is no seam; at most 127 for the first two, or the third column's x overflows its byte, seen on 16:9). The name stays centred. In a view too narrow for the stage the bar still ends at the strip (not seen: 320x200 already has room for the stage).

**B hint:** while choosing a target the B hint sat on the bar's rows at the right edge and came out under the dark bar. It now goes right below the bar while the bar is up (`bar_frame`, `bar_bottom`).

**Room:** `window_draw_with` is one Thumb function now (it was inlined three times): blob 32604 (16:9 32628) of 32768, about as before.

**Checks:** (0,12 256x24) was the only window matching the rule in the battle states 3-23, battle 2's menus, story talk, shops, world map and late screens tried. melonDS at Deck size, battle 2 (action menu, target). DeSmuME: battles 3, 13, 20 on Deck, battle 3 on 16:9, 320x200, quest 18's mist map, quest 17 without banner; 4:3 target screen pixel-identical to before. `scripts/solo_menus.sh` before/after: 86 of 96 identical, five differ only at the bar and B hint, five only in cloud drift and idle animation. `test_modpatch.py` passes; `vram_guard.py` silent on battle 2's attack walk.

**Not checked:** the Deck itself; 16:9 in melonDS; `dist/release` not rebuilt (the patcher in `dist/` is).
