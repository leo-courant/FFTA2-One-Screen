# 13: Repeatable melonDS capture of the battle HUD

**What to build:** A reliable way to get a melonDS capture of a known game moment (first battle with the command menu open, a story dialogue, later the test saves from ticket 03) on the current build. The present key-press replay depends on timing and lands on a different moment each run.

**Blocked by:** None (can start immediately)

**Status:** done, approved by the user (2026-11-25). Built 2026-11-23

- [x] One command produces a 1280x800 melonDS capture of the first battle's command menu on a freshly built ROM, three runs in a row
- [x] The same works for one story dialogue
- [x] The method is written into the testing notes

## Progress (2026-11-23)

The replay script now watches the capture for the red objective box and stops pressing when it appears, then advances dialogue until the banner stays. It reached the battle HUD in three of four runs. It stops at the tutorial's "Try using the Move command" prompt rather than the open command menu.

**Note from 03 (2026-11-23):** `scripts/melon_save.sh` loads the in-game save `saves/worldmap.sav` in melonDS and captures the world map, shop, party list and equipment screen; it waits for the load screen by pixel, and worked on the first try for all four. The second battle is not reachable this way yet (free-moving map cursor).

**Note (2026-11-23):** `scripts/solo.py` now gives a repeatable, exact picture of the mod's screen from any test state without melonDS (see `docs/test-saves.md`). It may make this ticket unnecessary except for a final sharpness check; the user has not decided that.

## Built (2026-11-23): melonDS savestates brought up to the current build

`scripts/melon_state.py STATE.ml1 OUT.png [steps]` (about 15 s) loads a melonDS savestate and captures. Before loading it writes the build's mod code into the state's main RAM and re-applies the build's ARM9 patches, as `emu.py` does for DeSmuME states, so one state serves every later build and preset. Base states: `states/m_battle1.ml1` (first battle, Shaelan's command menu) and `states/m_story.ml1` (library scene, Luso's speech window with portrait). How-to and gotchas: `docs/test-saves.md`, "melonDS from savestates".

Checks:
- `m_battle1` three runs on the Deck build: same moment each time; only animation phase differs (idle units, cursor).
- `m_story` three runs: identical pictures.
- `m_battle1` on the 4:3 build gives the 4:3 layout, so the code really comes from the ROM given.

Findings:
- melonDS shortcuts (F1 load, Shift+F1 save) only arrive when sent to the window (`xdotool key --window`).
- The state file is `MELN`, then sections of 16-byte header (magic, length, 8 zero bytes); main RAM is the start of `NDSG`, 0x24 bytes into the file, uncompressed.
- `melon_battle.sh`'s probe was still looking for the objective box where it sat before the banner moved to the far right, so it never stopped early. It now probes (752, 28), inside battle 1's box on the Deck preset. It takes `save` / `save:N` to save a base state.
