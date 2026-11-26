# 30: Story mist scenes checked where the story plays them

**What to build:** real captures (DeSmuME, then melonDS at Deck size) of the story scenes with a full-width mist layer, reached the way a player reaches them: event 137 (the scene before story quest 18), event 135 (before quest 17) and event 151 (quest-table row 25). Check that the mist reaches the screen edges (ticket 29's `queue_widen`) and that the scene looks as the game means it to.

**Blocked by:** None (no travelling needed: see the route in "Built").

**Status:** done, approved by the user (2026-11-25). Preview: http://localhost:8765/mist.html (`scripts/preview_mist.py`)

**Why:** ticket 29 could only play these events out of order (`scripts/play_event.py`), which shows them on the wrong battlefield; the user saw the result as "off" (two clashing visuals). See ticket 29, "Real check".

**Route as far as known:** `saves/q18.sav` (story progress 940, `PROGRESS=940 AUCTION=0 scripts/late_save.sh q18`) > pub > Quest Roster > quest 17 (rank 34, 16 entries down) > accept (A, A, Up, A) > world map to place 114 > battle > event 134 > quest 18 > event 137. Quest 18 is not posted at pubs (record flag 0x80).

- [x] Event 137 captured in context, mist to the edges, map whole
- [x] Events 135 and 151 likewise

## Built (2026-11-25)

**Route (no world map):** cold boot of the current build with `saves/worldmap.sav`, road into quest 2 with `play.py QUEST=17` (ticket 38's whole-quest swap), win by event flag 0x61B (ticket 40). The game then chains by itself: closing scene (event 135 script 4) > `quest_setup` 18 called by the game (from 0x02088CD0) > event 137 > quest 18's battle; and from `QUEST=23`: 23 > 24 (event 149) > 25 (event 151) > epilogue. For melonDS: a Quick Save in the battle with the flag set (`saves/q17_won.sav`, `q23_won.sav`) resumed on a cold boot, so the game plays the chain from its own save. `QUEST=24:0` directly falls back to the world map.
- What ticket 29 called "event 135" comes after quest 17's win, not before the battle. Event 151's map really is the first battle's, so its early capture was right.

**Faults found in context (all fixed, Deck and 16:9; 4:3 is as the unmodified game):**
1. The mist sheet of these maps ended at the old side edges: `layer_draw` repeats it, but on maps with clip areas the game culls layer parts against 256x192. The four bounds are patched in place (0x020D50E4..0x020D5130).
2. The mist effect's rotated and 308 px quads (effect 2/3) ended inside the wide view. `quad_grow` (the Scions' `tall_widen`, now per entry) also runs for the normal view: tiling quads covering the old picture are enlarged.
3. Rectangles without mist next to speech bubbles: on these maps the game cuts the mist around the windows on screen, where it placed them; the mod moves them. `mist_holes` moves the rectangles along; the outer borders of the cut pieces (+-128) are carried on.
4. `queue_widen` lost its place after an entry of another length (the portal) and missed what followed (purple flash, event 135's flash): the walk now looks for the next entry word by word.
5. The white cover under quest 24's "Complete!" was a 4:3 rectangle: the cover's corner and size are patched (0x020881B0, 0x020881C0).

**Room and speed:** `map_extend` and `queue_widen` are Thumb now (blob 32612 Deck, 32636 16:9 of 32768). Ordinary sprites leave `queue_widen` first (0.9 lines a frame in battles, 2.3 before; mist maps 5 to 6, 1 to 4 before). `map_extend` leaves at a battle map's first cell: it took 13-15 lines a frame there before; heavy battle 20 draws 729 of 900 frames instead of 632.

**Checks:** melonDS at Deck size from before quest 17's end to quest 18's battle, and from quest 23's end to the epilogue; cold boot in DeSmuME: 4:3 as the unmodified build at five moments of event 137, 16:9 to the edges; 96 menu captures before/after (only animation moments and the mist battles differ); Scions 1, 6 and 12 (two identical, one a frame apart); the book scene in melonDS; `test_modpatch.py` passes; `vram_guard.py` silent on battles 18, 23 and 2.

**Gotchas:** states that descend from `p_battle.dst` carry the 320x200 view's effect projection (the game builds it once, at boot), so full-width effects there look 0.8 of 8192 wide and are not widened; check such effects from a cold boot. `solo.py` can't show effects from the queue (its pieces need their own projection): melonDS, or DeSmuME at DS resolution.

**Not checked:** the Deck itself; 16:9 in melonDS; `dist/release` not rebuilt (the patcher in `dist/` is).

**Found on the way:** tickets 42 and 43.
