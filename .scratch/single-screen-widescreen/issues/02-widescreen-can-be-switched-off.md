# 02: Plain 4:3 display preset

**What to build:** A patch made with the plain 4:3 display preset shows the game exactly as the unmodified game does on a 4:3 picture, with the banner and the info-screen controls still working.

**Blocked by:** 20

**Status:** done, approved by the user (2026-11-23)

- [x] With the 4:3 preset the picture is identical to the unmodified game's
- [x] The banner and the detailed view / overlay still work

**Changed (user, 2026-11-23):** this was "widescreen can be switched off while playing". The display shape is now chosen when patching (ADR 0007), so there is no switch in the game; a 4:3 display gets its own preset instead.

## Built (2026-11-23)

**Result.** With `--display 4x3` the gameplay screen is the unmodified game's, pixel for pixel, apart from what the mod adds on purpose: the banner and turn order in battle, and the info screen on a SELECT tap. Of the 51 menu test pictures (`scripts/solo_menus.sh`) 33 are identical; the other 18 are battle scenes, where the difference is the banner and turn order, or animation (leaves, monsters, units) one or two frames apart. A battle picture with the banner held off (hold SELECT) is identical, same frame and all. Preview: `scripts/preview_plain.py` → `preview/plain.html`.

**One change was needed:** the stats panel beside the game's Item Info (ticket 14) landed on top of the Item Info box and the unit sheet at 4:3, where there is no side room. It is now widescreen only, like the Change Jobs panel (ticket 16). On 4:3 a SELECT tap gives the whole sheet. Everything else that moves or widens things already did nothing at 4:3: the slides go by `edge_px` (0), the margins are 0 and the patched constants are the game's own values, and the compact ability list (ticket 22) only switches on for a list panel that has been slid to the right edge.

**Controls on 4:3** (`ROM=build/ffta2-4x3.nds scripts/check_select.py states/s_battle2.dst basic|peek|combo|reset`): half-second hold switches the banner, tap swaps the screens in battle, SELECT with other buttons does nothing; same results as on the Deck. The SELECT overlay works in the party room, shop, Change Jobs and on the world map (`shots/t02/m43sel/*_ov.png`).

**How the comparison is made** (written into `docs/test-saves.md`, "Comparing with the unmodified game"):
- `patch.py ... --no-hooks` builds a reference ROM: the same file layout and code blob as a mod build, but no hooks, so the game runs unmodified. The unmodified ROM itself cannot be used with the test states: the mod moves overlays in the ROM, and after a state is loaded the game reads files from the wrong places (screens come out wrong or black).
- `emu.boot` now also undoes code patches a state carries that the ROM lacks (it compares with `STATE_ROM`, default `build/ffta2-1screen.nds`).
- `RAW=1 NOSEL=1 scripts/solo_menus.sh` makes plain both-screen captures without the SELECT steps (the unmodified game has no overlay, and drawing it shifts the timing enough for the scripted walk to drift).
- The world-map walk into the clan menus still drifts in the plain game (a press lands during a transition). Those six menus were walked again with long waits; all identical.

**Fixed on the way:** `scripts/check_select.py` always ran `build/ffta2-1screen.nds` whatever `ROM` said; it now takes `ROM` and refuses to run when `build/hook.elf` (where it reads the mod's variables) is from a different build.

Not checked in melonDS: at 4:3 nothing is squeezed, so the DS-resolution test emulator already shows the exact pixels. The banner during the privilege pick overlaps the heading (`privpick`); that is ticket 17's job.
