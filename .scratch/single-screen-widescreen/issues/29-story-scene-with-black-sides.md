# 29: Story scene with black side areas

**What to build:** In the opening story, the scene where the book pulls the hero in (a falling shot with shafts of light) fills the whole wide screen, with no black side areas.

**Blocked by:** None. Found in ticket 06 (2026-11-24).

**Status:** done, approved by the user (2026-11-24): the book scene (melonDS, Deck) and the scene hunt. The in-context check of the mist scenes moved to ticket 30 (later/), at the user's word.

**Direction (user, 2026-11-24):** find every cutscene that falls back to the 4:3 picture, not just this one. Rebuild the missing sides of each background with AI, without stretching the picture. AI pictures go only into the private add-on, as with the map of Ivalice (ticket 24, publishing rules); what the public build shows there is still to be decided.

**Decisions (user, 2026-11-24):**
- Public build: the picture's edge mirrored into the side areas, like the title (ticket 12, ADR 0010), worked out from the player's ROM while the game runs.
- Private build, moving scenes: the AI-made sides move with the scene: a background strip long enough to follow the game's own scrolling. Effects the game draws live (light shafts, sparks) may still stop at the old 4:3 edge.
- Finding every such scene: from the game data. Work out how this scene is drawn, find every story scene in the ROM that draws the same way, reach each by story progress and event flag edits (as for the late save, ticket 24) and capture it.
- Image model: for the first scene, sides made both with LaMa (sandbox, CPU) and with a diffusion model on the user's GPU (the user starts it on the host with a command given to them). The user compares them at Deck size and picks before the rest are made.

- [x] The scene has no black side area on the Deck preset, checked in melonDS
- [x] The way it is filled is fit for publishing (worked out from the player's ROM while the game runs, as in ticket 12)
- [x] Other scenes drawn the same way are found and fixed with it, or listed here (see Results; five effects could not be played, listed)

**Found (ticket 06, 2026-11-24):** `.venv/bin/python scripts/melon_state.py states/m_story.ml1 OUT.png` with sixteen `x:1.5` steps lands in it (picture `shots/t06/deck_n16.png`; the 15th press is the library with pages flying, the 17th the forest of the first battle). The 4:3 middle is drawn and the sides are black: whatever draws it is not widened by the mod. Not yet known whether it is a 2D layer, a 3D picture like the title (ticket 12's `still_edges`) or something else; `scripts/gxtrace.py` + `scripts/vidregs.py` on a DeSmuME state at that moment will tell. No DeSmuME state is there yet: cold-boot with the inputs of `scripts/to_battle.sh` (the scene comes a little after the library dialogue) and save one with `play.py`.

## How the book scene is drawn (2026-11-24)

DeSmuME state `states/t_fall.dst`: cold boot with the inputs of `scripts/to_battle.sh` up to name entry, then 265 `A4,w22` presses (the scene runs from press 264 to 271; `states/t_flash.dst` is the flash at its end). Captures `shots/t29/`.

- The backdrop is **3D, sent through the sprite queue**, not a layout piece and not a 2D layer: two quads with a 256x256 A3I5 texture (one a little taller than the screen, one a tall strip of light shafts), later a third. Each is one 0xA0-byte queue entry: a ready GX command list (layout written down at `queue_widen` in `src/hook.c`). They are not made by `sprite_queue_add` (0x02034164) but copied into the queue by ITCM code (0x01FFBC70) for the general sprite/effect renderer FUN_02031DBC.
- The texture **wraps** (repeat on S and T) and the quads' texture coordinates span exactly one 256-texel tile and scroll: the art is made to tile sideways. So the side areas can show the game's own picture carrying on, with no mirror and nothing made up.
- The white flash that opens and closes the scene is another queue entry: an untextured quad exactly as wide as the 4:3 picture.
- The round glow is main BG3, a rotated 128x128 256-colour bitmap blended over the 3D. As a 2D layer it is stretched like every 2D layer; left as it is (the "effects drawn live may stop at the old edge" allowance).
- `scripts/solo.py` cannot show this scene (it reports a 2D layer: the glow); use melonDS.

## What was built

`queue_widen` (hook at 0x0208F97C, the one call that draws the sprite queue each frame, into ITCM 0x01FFB390; blob entry slot +64): before the queue goes out, every entry that is an axis-aligned quad of ±2048 vertices, exactly as wide as the 4:3 picture (clip x-scale = 2 x `wide_x`) and centred, is widened to one pixel past the real screen edges:
- wrapping texture: the texture coordinates are carried on by the same amount, so the tiling art continues;
- non-wrapping texture shown exactly once (0..width): wrap + flip bits set, so it is mirrored at its edges like the title (ADR 0010); none seen yet;
- untextured: just widened (the flash).

Checks: melonDS Deck capture after every press through the scene (`shots/t29/melon/after_n26..28.png`): flash in, the fall and flash out all fill 1280x800, no seam at the old 4:3 edges (zoomed). 16:9 build cold-booted into the scene in DeSmuME: sides filled; 4:3 build unchanged. The 57 `solo_menus.sh` captures before/after (`shots/t29/reg_before`, `reg_after`): menus identical, battle captures differ only by animation timing (tree sway, unit frames). `test_modpatch.py` passes.

The 4:3 preset draws nothing extra (`edge_shift()` is 0).

## Still open

- **Other scenes drawn this way:** done, see "Finding the other scenes" below.
- **Private build / AI.** For this scene there is nothing to rebuild: the game's own texture covers the sides. The user agreed (2026-11-24) to keep the LaMa-vs-diffusion comparison for the first scene whose backdrop does not tile. None was found in the story events.
- melonDS: key presses during the library dialogue are dropped at random, so the scene lands on a different press each run (26-28 one run, 16 another): capture after every press and pick.

## Finding the other scenes (2026-11-24, in progress)

Method, all from the player's ROM:
- `scripts/pcbin.py`: reads any file of the game's archive (master/pc.bin) by path through its hash index pc.idx, as the game does (FUN_0201FA3C). The index only checks a path when two paths share a slot, so a made-up path can land on a real file of another name: check the file's header.
- Story scenes are **events** in `ev_all.pak` (folder `event/rom`), one block per event number, indexed by `ev_all_rom.idx` in the same folder (6-byte records, read by FUN_0201FCE4). FUN_02093964(event, battle script) loads one; FUN_020991D4(k) starts its script k. The interpreter is FUN_0209C888: u16 opcode, fixed length per opcode from the table at 0x0211A33C (185 opcodes). `scripts/event_scripts.py --op 38` walks all of them: 1026 events, 1883 scripts, about 297,000 commands.
- Opcode 0x38 plays an effect: kind byte, u16 number, one more byte. Kind 1 = `effect/event/eNNN.efx` (loaded by FUN_02049DAC). The book scene is event 103, script 2, effect e002. The scripts play 182 effect commands: 46 event effects (e001-e048 less a few) and common effects 4 and 7, in 68 events (124 event/script pairs).
- EFX files are chunked records; type 0x52 = texture (format, colours, width, height), 0x5D = a 128x128 bitmap for a 2D layer (the round glow). Event effects with a texture 256 wide: e002, e013, e014, e019 (never played by a script), e022, e025, e047, e048. But a full-screen layer can also be a small texture repeated (event 137: mist over a forest map, 64x64), so every effect-playing event is run, not only these.
- `scripts/play_event.py STATE EVENT OUTDIR` plays any event from `states/t_intro30.dst` (cold boot, 30 presses into the opening, before event 103 loads at press 39): the game's next event load is swapped for EVENT; `SCRIPT=k` also swaps the first script started, for scripts that normally run after a battle. Each frame the sprite queue is checked for quads exactly as wide as the 4:3 picture (what `queue_widen` widens); the first such frame is saved as a state.
- Opcodes 0x61 and 0x63 can also reach the effect code, but they are general commands used thousands of times (fades, waits); story effects are loaded only through 0x38.

### Results (2026-11-24)

All 124 event/script pairs that play an effect were run (`SCRIPT=k scripts/play_event.py states/t_intro30.dst EVENT OUTDIR 400`, 8 at a time, about 25 min; logs and captures in `shots/t29/ev/`, a first pass by event only in `shots/t29/ev1/`). With the hook in place, every capture was also checked for black side areas next to a lit 4:3 middle: none, apart from one night map that simply ends there.

Full-width quads found (all widened by `queue_widen`, no further change needed):
- **Event 103, script 2** (the book, effect e002): 256x256 wrapping backdrop + light-shaft strip + white flashes.
- **Events 135 (script 4), 137 (script 0), 151 (script 0)**: a **mist layer** over a forest/rock map, a 64x64 texture repeated across exactly the 4:3 width (effects e013 and e030). Without the hook the map runs on into the side areas but the mist stops at the old edge; now it covers the screen. DeSmuME check pictures before/after: `shots/t29/mist/`, shown on the preview page (keys 5-9). No melonDS look: these scenes are reached only by the DeSmuME harness.
- Untextured full-width quads (fades to a colour) in events 103, 117, 123, 125, 135, 137, 149, 151, 191, 709, 739: widened too.

Not found anywhere: a non-wrapping one-off picture (the mirror branch of `queue_widen` has not met a real case yet).

Not played (the harness could not reach them; listed for the late-game check, ticket 24/later):
- e007 (event 119 script 5), e014 (event 137 script 1), e020 (events 135, 145, 147), common effects 4 and 7 (events 117, 289, 535, 709, 739, 765-777): their scripts run after a battle or need state the harness does not give, and stay black when started directly. e014 has the same textures as e013 (the mist kit) and e007/e020 only small textures like it, so a full-width mist from them would be caught by the same rule. c_all.efx has no texture wider than 64.
- 33 event/script pairs did not load every effect they name (list from `shots/t29/ev/*.log`, effects loaded vs `scripts/event_scripts.py --op 38`).
- The title loop (attract demo, files `tNNN.efx` in a subfolder of the `titleloop` folder under `effect`) was not checked: its folder name is not known yet, and the archive index cannot confirm guessed paths.

Effects with 256-wide textures that turned out not to be full-width quads: e022 (event 145 script 4), e025 (event 149), e047/e048 (event 875): loaded and played, no full-width quad, no black sides.

Review 1 (user, 2026-11-24): the book and the other mist pictures are good; the event 137 pair looked weird. Cause: that pair was taken 20 frames into a white fade over the mist, and the scene itself shows its forest map only in scraps (patches of water and trees in a dark void). The unmodified game (reference build `--no-hooks`, same harness, `shots/t29/ref137/`) draws it the same way, so the scraps are the game's own. Pictures retaken 60 frames after the saved state (`shots/t29/mist/m_*_60.png`), where the mist is clearly visible.

Review 2 (user, 2026-11-24): event 137 still looks off: two clashing visuals, scraps of map with a sparkling tree and a green "toxic" mist everywhere. Same in the old build, so not the widening, but the harness plays the event out of context (from the opening), so it may not be how the game shows it.

Where the events really come in the story: **system data file 10** (sysdata.pak, entry 10) has 8-byte rows per quest: {quest, battle script, event before the battle, event after}. Row 1 = the tutorial (103/102). Event 137 is the scene before **story quest 18** (story progress 940, place 136, battlefield 182); event 135 = quest 17 (progress 900); 151 = row 25; 145/147/149 = quests 22/23/24; 117/119/123/125 = quests 8/9/11/12; 191 = row 49; 709/739/875 = rows 308/323/391. So the mist scenes are late story missions. Checking one for real means a save at about progress 940 with quest 18 on offer (as the late save of ticket 24 was built), accepting it, travelling to place 136, and capturing in melonDS from that save.

Real check (user asked for it, 2026-11-24), not finished:
- **The scraps were the harness.** Played out of order, event 137 ran on the tutorial battle's map (same tree, rock, mushroom, stream and yellow beast; `shots/t29/ref137/ev137_p160.png` next to `shots/t06/ref/i304.png`), while its camera and the map cells it reveals were made for quest 18's battlefield 182: hence rectangles of missing map and the clash with the mist. Same in the unmodified game, so not the mod. The mist pictures (events 135, 137, 151) came from that setup and were taken off the preview; the widening itself is not in doubt (a full-width repeated layer, whatever the map).
- **Quest 18 is not offered at pubs.** Its record has the 0x80 flag (only 18 and 23-26 have it); at story progress 940 (`PROGRESS=940 AUCTION=0 scripts/late_save.sh q18` -> `saves/q18.sav`) the Quest Roster lists the story quests up to rank 34 (quest 17, at place 114) and then 39. Rows 17 and 18 of sysdata file 10 follow each other, so quest 18 most likely starts by itself after quest 17's battle and its closing scene (event 134).
- Tried and dropped: writing 18 at 0x0212D7E6 (accepting a quest writes its number there, but travelling rewrote it to 16: not simply the accepted list); giving quest 2 quest 18's battlefield and scene row in RAM and walking the battle-2 route (an unrelated scene with a crystal cave and a ruin played instead).
- **What the real check needs:** from `saves/q18.sav`, accept quest 17 at the pub, steer the world-map cursor to place 114 (another region: needs the world-map navigator ticket 24 lacks), win quest 17's battle (level-99 party), let event 134 hand over to quest 18, and capture event 137 in DeSmuME, then in melonDS from an in-game save made just before. New ticket 30 in `later/`.
