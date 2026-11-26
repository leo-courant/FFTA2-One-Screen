# 20: Display presets chosen when patching

**What to build:** The patch script takes a display preset (Steam Deck 1280x800, 16:9 monitor, plain 4:3) or a custom width and height, and builds a ROM whose view fits that display. ADR 0007.

**Blocked by:** None (can start immediately). Touches the patch script and the view-size values in the hook; ticket 18 is working in the same files, so start after it lands or merge with care.

**Status:** done, approved by the user (2026-11-25). Merged into master as eef6c8c (2026-11-23)

- [x] Each named preset builds, and the Steam Deck one gives exactly today's picture
- [x] A custom width and height builds and fills that shape
- [x] The 16:9 preset is checked in melonDS at 1920x1080 and has no black areas or missing map
- [x] How to measure and tune a new preset's pixel evenness is written into the testing notes

## Built (2026-11-23)

`scripts/patch.py IN OUT --display deck|16x9|4x3` (default `deck`), `--size WxH` for any display, `--view WxH` to set the view directly (ticket 08's zoom levels), `--nudge X,Y`.

- **Views.** The rule (`view_for`): the largest whole number of screen pixels per game pixel that still shows the game's 192 rows, so every game pixel is the same size. Deck 1280x800 → 320x200 at 4x (unchanged). 16:9 1920x1080 → **384x216 at 5x**, a little more zoomed out than the Deck (216 rows instead of 200). Where the rule would zoom out past 216 rows (1280x720, 1366x768) it keeps 192 rows and accepts uneven pixels (342x192). 2560x1440 → 366x206, 2560x1080 → 512x216. Views from 256x192 to 768x384 are accepted; portrait displays are refused.
- **One source.** Every size that depended on 320x200 now comes from `VIEW_W`/`VIEW_H` and two margins that `patch.py` passes to the compiler: projection multipliers, edge offsets, map-cell culling, backdrop band size, layout-renderer clamps, parchment extension, test-capture tiles. The settings sit in one block, `view_cfg`, after a "VIEW" marker.
- **Deck = today.** Before the settings block was introduced the Deck build was byte-identical to master's. With it, all 51 solo captures match master's pixel for pixel except two, where the bobbing menu pointer is one animation frame apart; the same walk without the SELECT overlay step matches exactly, so it is the overlay's software drawing taking slightly different emulated time, not layout.  After rebasing onto ticket 16: 57 captures, the two that differ (unit placement, privilege pick, both after the long scripted walk into battle 2) differ only in a few pixels of animated foliage and a unit's frame.
- **4:3** builds a 256x192 view with every widened constant back at the game's value; it plays with the banner. Matching the unmodified game exactly is ticket 02.
- **Fixed on the way:** the clan parchment was carried only 8 rows past the old screen; at 216 rows that left thin black strips top and bottom. It now follows the view.
- **16:9 check.** All 51 solo captures (`SCALE=5`, 1920x1080) have no black edges apart from the world-map SELECT overlay, which shows the same on the Deck (a limit of the capture method). melonDS at 1920x1080: Muskmallow Field battle with the whole map, panels at the edges, banner and turn order at the far right; Wood Village fills the screen.
- **Evenness.** The 16:9 preset needs melonDS's internal resolution at **9x**: at 8x a game pixel is 5.33 internal pixels and no nudge gets above 69% of edges on the grid; at 9x it is 6x8 internal, exactly 5x5 on screen, and nudge 3,-3 (same as the Deck) gives 91% / 86%. Notes and the table of presets in `docs/test-saves.md`, "Display presets". The setup guide (ticket 11) and README (ticket 21) must tell 16:9 players to set 9x.

Test rig changes: the test scripts take the mod's code from the ROM they run (no more `build/hook.bin` mismatch when several builds exist); `solo.py` reads the view size from the ROM and lays out its pieces for any size (`SCALE` sets the enlargement); `solo_menus.sh` takes `ROM` and `O`; `melon_save.sh`/`melon_play.sh` probes scale with the window; `melon_battle2.sh` takes `ROM` and `SIZE`; `try_nudge.sh NX NY PRESET` no longer edits `hook.c`; `measure_grid.py IMG PX`.

Not done: other 16:9 sizes (1440p, 4K) are built by the rule but not measured; ultrawide (512 wide) builds but was not looked at.
