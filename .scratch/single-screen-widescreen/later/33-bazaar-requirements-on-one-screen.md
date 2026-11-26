# 33: Bazaar: what a recipe needs, on one screen

**What to build:** In the shop's Bazaar (late save: `states/late/l_bazaar.dst`) the gameplay screen lists the recipes with the grades A to E that can be made. Which loot each recipe needs, and the player's grade in each loot kind, are only on the info screen (two rows, one per loot kind, with A to E marks). This is ticket 10's kind B: what you need in order to choose. The user already noted it (ticket 18). Propose a layout and let the user pick, as ticket 16 did for Change Jobs (the info screen's part shown beside the list by itself).

**Blocked by:** None (found in ticket 24). Second batch. The bazaar's crafting menu after choosing a recipe has not been looked at yet: do that first.

**Status:** done, approved by the user (2026-11-26): option A, after two review rounds. Preview: http://localhost:8765/bazaar.html (`scripts/preview_bazaar.py`). Design in ADR 0016

- [x] The screens after choosing a recipe are captured (the crafting menu the user mentioned in ticket 18)
- [x] Options shown to the user as real builds on a preview page, Deck size, flipped in place; the user has chosen (A)
- [x] Built, and the menu captures are unchanged elsewhere

## Findings (ticket 24)

- In melonDS at Deck size (`shots/t24/melon_bazaar.png`, from `saves/late.sav` with `scripts/melon_save.sh`, keys `x:1.5 Down:0.5 x:3 x:1.5 x:1.5 x:1.5 x:1.5 x:3 Down:1 Down:1 Down:1 x:4`; menus open slowly, so the last presses need the longer waits) the recipe list is a window centred on the screen over the shop room, sharp, nothing wrong.
- `scripts/solo.py` shows the list twice side by side: part of it is a 2D layer, which that tool repeats. Use melonDS pictures for this menu.
- The info screen's two rows sit at the top of the info screen, about 256 x 64 px; the space beside the centred window on the Deck is about 55 game pixels a side (366-wide view), so the rows do not fit beside it at full size.

## Findings (2026-11-26)

**A trade, step by step** (states `l_bz_*`, `scripts/to_bazaar.sh`). The recipe list (gameplay screen) shows each recipe's possible grades; the info screen has one row per loot kind the highlighted recipe takes (2 or 3 seen), with the A-E marks all dark. A on a recipe opens the crafting menu: on the gameplay screen a tab bar (Left/Right change the loot kind), the loot of that kind (held, rank in stars) and the loot's description. On the info screen: the rows, and below them a recipe header (the recipe, its A-E grid). Only loot named in white can be sent for the recipe (most is greyed; A on it does nothing). Sending one fills that kind's row and lights the grades it allows; loot of the same rank in every kind draws a line through one grade across the rows, down into the header, which then names the item the trade makes. The game then asks on the gameplay screen whether to send; after Yes the gameplay screen announces the new item and the info screen shows its sheet. B with loot sent asks whether to clear it and go back. So what you need in order to choose (which loot is in, which grade it allows, what you will get) is all on the info screen.

**What draws it.** Info screen: the row bars, icons and grade circles are sprites, the row labels and loot names BG1 (map rows 3-4, 7-8, 11-12), the recipe name BG3 (row 20), the background and the header box BG0. Gameplay screen: all 3D layout objects; several hang from holders without pieces at the screen's middle (128,96). A Yes/No box's marks and cursor are drawn by 0x0204EBE0 at its text lines' stored positions (0x0204CB50/0x0204CD80), not where the mod draws the lines. Trigger: the word at 0x0212EA88 is 5 throughout the bazaar (0 in the 13 other menus compared); after a trade it stays 5 but the info screen has no row labels.

## Built (2026-11-26): two options, Deck view only

Both: while the info screen has bazaar rows, the overlay (ADR 0005) is cut into the rows (24 px each, the info screen's background left out so the gaps are clear) and the header, drawn opaque at 1:1 under the list; the list, and what pops up over it, move up to the tab bar; the description box goes below the view. `bazaar_rows`, `bz_place`, `ov_draw` in `src/hook.c`. A Yes/No box that moves now takes its marks and cursor with it (its lines' stored y moved for the draw, then restored).
- **A** (the build's default): the same on the recipe list (the rows show which kinds a recipe takes; the recipe's description gives way).
- **B** (`--define BZ_LIST=0`): the recipe list keeps its description; the rows come once a recipe is chosen.

16:9 and 4:3 are unchanged (no room under the list; SELECT shows the info screen).

**Room.** The blob was full (32680 of 32768 bytes). Moved to Thumb: `turn_units`, `turn_pips`, `glow_draw`, `dual_frame`, `tex_free`, `rects_new_frame` (each runs once or a few times a frame). The bazaar's placement is a separate Thumb function: anything added inside `layout_obj_begin` grows it by 100-500 bytes. Now 32604.

**Checked** (DeSmuME, solo.py; every bazaar screen is 3D): every moment of a trade with both options; the description stays away every frame; `vram_guard.py` silent on five bazaar states and a walk through a whole trade; `scripts/solo_menus.sh` before and after: 92 of 96 identical to the pixel; `bmenu` and `bq13_place` differ in units' animation phase only; `late_bazaar` is this ticket; `buy_info` differs because the build before froze in `s_shop.dst` (below). All three presets build; patcher tests pass.

**Not checked yet:** a recipe with one loot kind, loot names longer than those seen (the row is the info screen's own, so they fit as they do there).

**Found on the way.**
- `states/s_shop.dst` froze with the build from HEAD (and in the menu captures since 2026-11-25: `buy_info` showed the list, not Item Info): D-pad and R did nothing, with widescreen on or off. With this build it plays and Item Info opens. Not followed further: whether a state made by an older build, or a hang the old code could also reach in play.
- States made with `PLAIN=1` in the recipe list show it unsqueezed afterwards (the list builds its projection when it opens): make test states with widescreen on.
- `gx_report.py` finds no polygons while the overlay is up; a test build with `--define BZ_DEBUG=1` draws the rows off screen to see what lies under them.
- A layout object pushed past x 320 (or below the view) is no longer drawn by the game, so its box is empty the next frame: rules that judge by the box must remember the object (as `abil_obj`, `bz_desc`), or it flickers.

## Choice and melonDS check (2026-11-26)

The user chose **A** (rows on the recipe list too); the B switch is gone.

**melonDS** at Deck size, a whole trade from `states/m_shopmenu.ml1` (the late save at the shop menu; any build can start from it), `FPS=60`, steps: `Down:0.4` x3, `x:6 x:2 x:2`, `Down:0.4 Down:0.6`, `x:2.5 x:1.5 x:1.5 x:2`, `Down:0.3` x17, `x:1.5 x:1.5 x:2 Right:1`, `Down:0.3` x11, `x:1.5 Right:1.5`, `Down:0.3` x3, `x:2 Up:0.5 x:3` (captures `shots/t33/melon/final_*.png`, on the preview page under M). Recipe list, crafting menu, each loot sent, the line into the header, the Yes/No box with its marks and cursor, the trade, the new item: as in DeSmuME, sharp, no hairlines. The room's textures are whole after the trade with this build, the build before, and one with the overlay off.

**Fixed after the choice:** after Yes the game removes its panels and shows the room for about a second while the info screen keeps its rows: the rows stayed on screen over the room. Now they are drawn only while the game's list was drawn in the last frames (`bz_list`). Menu captures against the run before this fix: 84 identical, 12 differ in units' animation phase only. Guard silent through a whole trade. Blob 32720 of 32768.

**Found on the way.** melonDS states taken while the overlay is up (in the bazaar) freeze or lose textures when loaded with another build, and even with the same build show the room with missing textures after the trade: `melon_state.py` rewrites the mod's blob into the state, its variables included, so the overlay's bookkeeping is lost while its texture is still in place. Take base states where the overlay is off (`m_shopmenu.ml1`). This is probably also why `s_shop.dst` froze with the build before (DeSmuME's loader does the same).

## Review 1 (user, 2026-11-26): the kind icon's bubble

"Fill out the teal circle, it's missing a bit on the left; rest looks good." The bubble around each row's kind icon is the left end of the row's bar sprite (64x32 at x 0, tile 98): the game draws it from the screen's edge, so its left part never existed. `bz_arc` draws it: a circle of radius 13 about x 6.5 (from the caps above and below the icon), in bands of rows of equal width (2 to 6 px), mirrored, in the sprite's own palette (entries 1 outline, 3-5 shades, 6 fill), so empty, filled and current rows each match; about 30 small flat quads a row. Room: `trail_frame` (Scions, once a frame) is Thumb now. Blob 32752 of 32768.

Checked: DeSmuME at each moment; melonDS, the whole trade again (preview M pictures refreshed); guard silent; menu captures: the bazaar's only changes are the arcs, the rest animation phase. The current kind's glow still stops at the old edge (its sprite starts at x -6, outside the texture).

## Review 2 (user, 2026-11-26): the ring around the current row

The user asked whether the blue selection around the current row is meant to look like that. It is the game's ring around the loot kind being browsed (sprites behind the bar: tile 226, 64x32, along it, and tile 258, a 32x32 circle at x -6), 32 px tall: the 24 px rows cut its top and bottom, and its left part lies off the info screen, outside the completed bubble. Left out of the bazaar's rows now (the compositor skips those two tiles while the rows are up); the tab bar above the list already shows the kind. Room: `unit_pic` is Thumb; the blob is now exactly full (32768 of 32768): the next feature must make room first.

Checked: DeSmuME at every moment (the header's grade letters are sprites near those tiles: they stay), melonDS whole trade, guard silent, menu captures 96 of 96 identical to the run before, presets build, patcher tests pass.
