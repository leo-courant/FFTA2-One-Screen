# 17: Banner before and after the battle

**What to build:** On the screens around a battle the banner no longer sits on the game's own headings. While placing units and choosing the privilege it stays, clear of the game's headings and hints; on the results and law bonus screens it is hidden. The game's Help window no longer collides with it either.

**Blocked by:** None

**Status:** done, approved by the user (2026-11-24). Preview: http://localhost:8765/prep.html (`scripts/preview_prep.py`)

- [x] Unit placement: banner and the game's "n/5 Unit(s)" heading and B hint do not overlap; the X hint for finishing placement is visible
- [x] Choosing the privilege: banner does not overlap "Select a clan privilege."
- [x] Results and law bonus: no banner, no turn order
- [x] Help (Y) in battle: the help window and the banner do not overlap
- [x] Final check in melonDS, shown to the user as a preview link (Help on Deck and 4:3; placement and the privilege list have no melonDS state, checked with solo.py on all three presets)

**From ticket 10 (2026-11-23):** user decision: keep the banner during preparation but out of the way, hide it afterwards. Captures of each screen: `shots/menus/place.png`, `privpick.png`, `results.png`, `lawbonus.png`, `b_help.png` (catalogue group D and E). The overlaps were first noted in `docs/test-saves.md` ("Seen on the way"). The banner already hides while a speech window is open (`speech_frame` in `src/hook.c`); these screens need their own signal. On these screens SELECT swaps the screens, as in battle. The melonDS route into the second battle (`scripts/melon_play.sh`) passes through placement and the privilege list.

**Note (2026-11-23):** the mod's own picture of each of these screens is in `shots/solo/` (`place.png`, `privpick.png`, `results.png`, `lawbonus.png`, `help.png`), made by `scripts/solo_menus.sh`; use `scripts/solo.py` to check the fix.

**Done (2026-11-23), at the user's request during the menu review:** from "Complete!" on the banner and turn order are not drawn (results, law bonus and what follows). The signal is the word at 0x02124104, which is 2 while a battle is being fought, preparation included, and 1 afterwards; found by comparing memory across test states, its real meaning unknown (`BATTLE_LIVE` in `src/hook.c`). Seen for the tutorial battle only; a lost battle has not been seen. Still open here: placement, privilege list, Help window.

## Built (2026-11-24)

**Finding:** on the Deck and 16:9 presets placement, the privilege list and Help were already clear. The banner had moved to the far right (ticket 07), the B hint was already dropped below it in widescreen (`layout_obj_begin`), and the X "Begin Battle" hint shows bottom right once units are placed (it is not up at 1/5 in the unmodified game either). What was left was **4:3**, where there is no side room:
- placement: the B hint sat on the banner and hid the law box (the drop-below rule only ran in widescreen);
- privilege list: the "Select a clan privilege." heading cut into the banner, and the turn-order strip showed through the translucent list;
- Help: the window covered the banner and strip, which peeked out around it.

**Change (`src/hook.c`):**
- The B-hint rule (a small panel in the top-right corner drops to `hud_bottom + 2`) now applies on every preset. On 4:3 it also fixes the hint covering the privilege box while choosing a target.
- `stage_check` now also tests every game panel and window against the banner (`hud_box`: two boxes, the banner rows and the 4:3 strip). While one covers them (`hud_hit`, last 2 frames), `hud3d_draw` draws neither banner nor turn order. This follows the user's rule "never one layer of panels over another", as the stage already did. `hud_drawn_frame` is still set while hidden, so the B hint stays dropped and can't keep the banner hidden itself.
- The action name bar ("Attack", a full-width window at rows 12..36) is exempt: it runs under the banner rows by design, and on 4:3 under the strip at full width, as approved in ticket 02. Testing banner and strip as one box made the bar hide them during action selection. That was caught by the catalogue comparison and fixed by splitting the box.

**Checks:** `scripts/solo_menus.sh` before/after on Deck, 4:3 and 16:9 (57 captures each). Deck and 16:9 show no layout change, only animation timing. On 4:3 only place, privpick, help and target changed as intended. melonDS: `scripts/melon_state.py states/m_battle1.ml1 shots/t17/m_deck_help.png s:cmd a:1.5` (and `ROM=<4:3 build> SIZE=1024x768` for 4:3; the rig can't read the scratchpad, so put the ROM under `build/`). Pictures in `shots/t17/`; the 4:3 "before" ones come from the build at f51a529.

Not seen: a lost battle (still only the tutorial win for `BATTLE_LIVE`).
