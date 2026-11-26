# 43: Thin vertical line in some speech bubbles

**What to build:** Some speech bubbles show a one-pixel dark vertical line about 20 px from their rounded end, in melonDS at Deck size. The unmodified game at the same moment shows none. Remove it.

**Blocked by:** None. Second batch (found in ticket 30, 2026-11-25; the build before that ticket has it too).

**Status:** done, approved by the user (2026-11-26). Preview: http://localhost:8765/hairline.html (`scripts/preview_hairline.py`)

- [x] No line inside speech bubbles at Deck size

Where: `states/m_t30b.ml1`, two presses of A (bubble bottom left). It may be the seam between two pieces of the bubble at the 3.5x scale (not looked into).

## Findings and fix (2026-11-26)

**What the line is:** not a dark stroke but a crack: the map shows through it (its colour changes down the line with the scenery behind; melonDS, x 395 of 1280 in that capture). The bubble is drawn as pieces (`window_frame_draw`, 3x3 pieces of the window). Each piece is placed by a matrix translation to its corner and then drawn as a quad of its own width, under the game's 2D projection (`ui_draw_pass` 0x020840a0, `G3_OrthoW` with 1 unit = 1 game pixel: 32 clip units per pixel across, 42.67 down). The hardware rounds the translation and the width separately (each product is cut to whole clip units). In the plain game a pixel is exactly 32 units, so nothing is lost. The Deck squeeze makes it 22.38 units: the right edge of one piece (corner + width) and the left edge of the next (its own corner) can then differ by one clip unit, about 1/22 of a game pixel. At melonDS's 8x resolution that sliver covers a column of sample points often enough to show. Letters are drawn the same way, and some had the same slivers inside their strokes.

**Fix:** `ortho_whole` (end of `src/hook.c`, called by `ortho_hook` in place of `ortho_fix`) multiplies that one projection by 128 after the squeeze: x, y, z and w alike, so positions, depths and their order are unchanged (the game uses z-buffering: swap-buffers argument 1). A pixel across is then `wide_x` clip units (32 x wide_x / 4096 x 128), a whole number, so corner + width and the next corner come out equal. Down, the rounding is 128 times finer. It applies only to the 2D projection with its origin top left (x scale +32.0, translation -1/+1, w 1.0 before the squeeze), only when squeezed (not on 4:3 or the plain game), and also in the test rig's tile path, so `solo.py` draws what the release draws.
- Not the sprites' centred projection (same scale, x mirrored). The sprite queue multiplies the current projection into each entry's matrix, and `queue_widen` (ticket 39's law bar) reads those entries expecting w = 1.0. A first version scaled both, and the law bar stopped short again.
- `ortho_whole` is in its own section (`.text.zlast`), after every other function, and is Thumb. No function moved, so melonDS test states saved inside the mod's code still run. `states/m_q17.ml1` has a return address into `layer_draw` on its stack, and froze on a build where only `ortho_fix` grew. Remaking `m_q17.ml1` / `m_q23.ml1` while the game is outside the mod's code (as `save_clean` does for DeSmuME) would make them robust; not done here.
- Blob 32680 of 32768 bytes (Deck), 84 more than before; 88 left.

**Checks:**
- melonDS at Deck size, `m_t30b.ml1`: the line is gone (before: one lone column inside the bubble on every run that reached it; now none). 16:9 preset (1920x1080): bubble clean. 4:3: unchanged (no squeeze).
- melonDS before/after, `m_q17`, `m_q23`, `m_battle1`, `m_story`, `m_auction`, `m_t30f`: the same pictures (banner, turn order, panels, speech windows, auction); all run (where the old build also moves).
- `scripts/solo_menus.sh`, old build and new (`TMPDIR` outside /tmp, which is nearly full): 65 of 96 captures identical to the pixel, no warnings from the rig. Remaining differences are sub-pixel and limited to the fast rig's 1x pictures: portraits, the world-map parchment, the menus' diamond floor and some glyph rows sample one DS row differently where the finer vertical rounding moves an edge by under 1/40 pixel, plus animation phase (units, the judge's fade), since the blob's size changed. No panel appears, vanishes or changes order; the law bar reaches the right edge.
- `dist` patcher regenerated (`make_patcher.py`: no game bytes); `python3 scripts/test_modpatch.py`: all passed.
