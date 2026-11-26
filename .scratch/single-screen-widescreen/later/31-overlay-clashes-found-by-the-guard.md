# 31: Overlay clashes found by the memory guard

**What to build:** Fix the places where the SELECT overlay (ADR 0005) and the game use the same video memory at the same time, as found by `scripts/vram_guard.py` (ticket 25). How to fix them is the user's call; options are below.

**Blocked by:** 25 (the guard). Second batch.

**Status:** done (2026-11-24): groups 1 and 3 by offering the overlay in menus only (user's choice), group 2 by moving the overlay texture into the free top of the game's texture heap (ADR 0013); group 4 (world-map quads, 2-4 frames) noted only

- [x] The user picks a fix for groups 1 and 3: turn the overlay off outside menus
- [x] A fix for group 2 (late-game pub): ADR 0013
- [x] `scripts/vram_guard_all.sh` is silent for these states afterwards (or each remaining line is explained here)
- [x] Each fixed scene shown to the user with the overlay up (`scripts/solo.py`; DS-resolution captures for the 2D-layer cases, which `solo.py` repeats)

## What the guard found (2026-11-24)

Each state was played for 20 s with SELECT tapped at frame 120 (`scripts/vram_guard_all.sh`). Every group below was checked with a picture: the same moment with and without the overlay.

1. **Story and after-battle dialogue scenes: the screen fills with garbage while the overlay is up.** States `intro2`, `t_fall`, `t_prefall`, `s_results`, probably `t_flash` (its picture caught a black frame). The overlay parks bank A's old contents in main-engine BG bank E at 0x06001000 (`OV_BACKUP`). These scenes show main BG1 (tiles from 0x06002260) and BG3 (a 256-colour bitmap from 0x06000000), blended over the 3D picture. The game keeps both layers empty, so they normally show nothing. With the parked copy in them, stripes of bank A's bytes cover most of the gameplay screen. In the book scenes the game also writes into the parked copy (from frame 247 to 337, call site 0x01FF857C), so bank A is restored wrong when the overlay closes. No draw from the wrong bytes was seen afterwards. In the other story states (`p_story*`), BG3 is blended at weight 0, so it shows nothing even with the parked copy in it.
2. **Late-game pub menus: garbage in a band at the lower right of the pub behind the overlay.** States `late/l_pubmenu`, `l_roster`, `l_trials`, `l_trial_detail`, `q18_pub`, `q18_acc`, `q18_roster`, `q18_sel`; also `t_intro40`, an opening scene that draws the same rows of the same sheet (x 105..273, y 123..136). The pub's 256x512 texture sheet at bank A 0 (call site 0x0208CC18) is drawn with rows 320-328, which lie inside the overlay texture (0x14000+). On screen this is x 138..250, y 138..171 of the 256x192 viewport, partly under the translucent overlay panel and partly in the right side area; a `solo.py` capture shows it as blocky garbage at the right. In the DS-resolution capture it is hard to see under the panel. The early-game pub (`s_worldmap` walks) does not use those rows.
3. **Title: the picture goes black for 6 frames when the overlay opens.** States `t_title`, `t_diff`, `boot1500`. The title picture (256x256, 256 colours, from 0x11780) runs into the overlay texture. For the first frames it shows the half-built overlay, until the game's panels are pushed off screen (ticket 14), and that hides the title picture anyway.
4. **World map: one 4x2-pixel quad for 1-2 frames** (`s_worldmap` frame 208, `late/q2as18`, `late/q18_acc18`): a board piece that samples rows 107-144 of the world-map texture at 0x10000. Probably not visible.

Clean: every battle state (banner, turn order, SELECT screen swap), the menus in the ticket 10/14 walks (`GUARD=1 scripts/solo_menus.sh`), shops, party, equipment, the map of Ivalice, auctions, Camoa.

Preview: http://localhost:8765/guard.html (`scripts/preview_guard.py`, from `shots/t25`: `solo.py` on `s_results`, `intro2`, `late/l_pubmenu`, `t_title` with SELECT tapped between the two shots; real melonDS `melon_state.py states/m_story.ml1 ... wait:1 q:3` with FPS=60). The pictures also show a fault that is not a memory clash: on the title and in the opening story scene (melonDS) the overlay panel itself is unreadable noise. The info screen there uses layer types the compositor does not redraw (ADR 0005, "Not handled").

## Options (for the user)

- **Offer the overlay only where it is useful:** menus, where the info screen describes the selection (ticket 14). Story scenes, battle results and the title would ignore a SELECT tap. This removes groups 1 and 3 and is the smallest change.
- **Park the copy in main RAM instead of BG bank E:** 48 KB more code reserve (states rebuilt again), and group 1 goes away wherever the overlay stays allowed.
- **Check before borrowing, as the banner does (ADR 0008):** refuse the overlay, or use a smaller area, when a shown BG layer or a drawn texture reaches the borrowed memory. This is general, but it needs the same kind of tracking the guard does, inside the mod.
- **Group 2 needs room elsewhere in texture memory,** or an overlay texture that avoids rows the scene draws. The pub draws only a band of its sheet, so the free part of bank A depends on the scene.

## Fix for groups 1 and 3 (2026-11-24, user: "turn it off outside menus")

**The rule:** `info_screen_is_menu()` in `hook.c`: the overlay is offered only while the info screen uses mode 0 and every shown layer is a 16-colour tile layer (no BGxCNT bit 7). Surveyed over all 57 states:
- Every menu passes: world map, party, equipment, shops, pubs, auctions, bazaar, Camoa, Set Abilities, clan trials.
- No story scene (`p_story*`, `intro2`, `t_fall`, `t_flash`, `t_prefall`, `t_prebook`, `t_intro40`, `q2as18_go`), the after-battle dialogue (`s_results`) or the title (`t_title`, `t_logo`, `t_diff`, `boot1500`) passes. All of them show a 256-colour picture layer on the info screen.

The rule is also exactly what the compositor can draw, so the overlay can no longer come out as noise. Outside a menu a SELECT tap does nothing (no overlay, no screen swap), and an open overlay closes if a menu gives way to a scene. The Jobs and Item Info side panels go through the same switch; they only appear in menus anyway.

**Checked:**
- `scripts/check_select.py` (basic and peek). In the world map and party menus a tap opens the overlay and B or A closes it. In battle 2 a tap swaps the screens. In `p_story_0` and on `t_title` a tap does nothing. The banner hold works in all of them.
- All 44 menu captures of `scripts/solo_menus.sh` are pixel-identical to the previous ones (`shots/t31` vs `shots/solo`), including the Jobs panel, Item Info panels and every overlay shot. The 13 that differ are battle screens taken before later banner work, and the switch was already off in battle.
- `scripts/vram_guard_all.sh`: all story, dialogue and title lines are gone, and the walks are clean. What remains is group 2 (the late pub and its menus) and group 4 (world-map board pieces for 1-2 frames, now also one frame in `late/l_camoa` at the closing tap, with a vertex behind the eye so no screen box).

## Fix for group 2 (2026-11-24, user: "fix the pub")

**Survey** (scratch tool on the guard's classes): over 34 menu states, the guard counted only the texture rows the game draws on screen while the overlay is up, plus every write it makes in banks B and D meanwhile.
- Bank A: used across scenes (the late pub alone draws 0x14000-0x1C7FF).
- Bank D: written mid-overlay as the cursor moves (menu icons).
- Bank B: every menu with a picture-heavy scene has the game's texture heap (record at 0x0212F048, 0x2E000-0x3FFFF) and uses only its low 9-22 KB. In all of those, the game neither draws from nor writes to the top while the overlay is up.

**Change** (ADR 0013): `ov_set(1)` puts the texture at 0x34000 (bank B, the heap's top 48 KB) when the scene has a heap, bank B is slot 1 and the free list covers the window. Nothing is parked then. Otherwise it uses bank A and parks its contents as before. While the overlay is up, the frame hook checks the free list before writing; if the game has claimed any of the window, the overlay closes. The table gains `OVTH`. The guard build's parked-copy checks run only when something is parked.

**Checked:**
- `scripts/vram_guard_all.sh`: all 57 states and the walks are silent except group 4's world-map quads (2-4 frames, no heap there).
- The pub and its menus are clean, and the mod holds about 50 KB instead of 77 KB.
- `check_select.py` peek in the world map, late pub and shop.
- Guard build in the pub: no clash recorded.
- 54 of 57 menu captures are identical to the previous build. The 3 that differ are battle screens without the overlay (a fading emblem on the law screen and terrain shading in the ability list: animation phase).
- Simulated claim: in the pub, the overlay opens at 0x34000 unparked. After shrinking the heap's free block, it closes within 2 frames. With the block free again, a tap reopens it there; with the heap full, a tap opens it in bank A, parked.
- Before/after picture: picture 4 at http://localhost:8765/guard.html.
