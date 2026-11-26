# 04: Map continues into the side areas

**What to build:** In widescreen the battle map is drawn in the side areas wherever map exists there, with no stripes or missing tiles.

**Blocked by:** 01

**Status:** done, approved by the user (2026-11-25). Verified in melonDS at Deck resolution in battle 1 (2026-11-24)

- [x] No striped or partially drawn map in either side area in the first battle
- [x] Scrolling the camera to each map edge shows no popping at the sides
- [x] Verified in melonDS at high resolution

## Result (2026-11-22)

The game's map-cell visibility test is replaced by one that keeps a margin of extra pixels on each side. In the first battle, panned to all four edges, the side areas show map with no stripes (checked in the DS-resolution emulator, stretched to 16:10). Not yet verified in melonDS at high resolution: that needs a melonDS save inside a battle, which depends on ticket 03.

## melonDS check (2026-11-24)

No change to the mod. Deck preset (366x228 view) in melonDS 1.1, OpenGL 8x, 1280x800, from `states/m_battle1.ml1`:

    .venv/bin/python scripts/melon_state.py states/m_battle1.ml1 shots/t04/end.png x:1.5 s:move \
        hold:Right:0.4 wait:1.5 s:right hold:Up:0.4 wait:1.5 s:up hold:Left:0.7 wait:1.5 s:left \
        hold:Down:0.7 wait:1.5 s:down hold:Right:0.7 wait:1.5

Choosing Move and holding the D-pad drags the camera with the cursor, so the steps above reach all four ends of the map. In every capture both side areas show map wherever the map reaches, and the backdrop beyond it: no stripes, no missing tiles. A second run in short steps with a capture after each (`Right:0.4 s:rN` six times, then `Left:0.4 s:lN` nine times) shows complete map in the side areas in every in-between frame, so nothing pops while the camera moves. Captures in `shots/t04/` (`end_*.png`, `pan_*.png`); preview `scripts/preview_mapedges.py` → `preview/mapedges.html`.

Still only the first battle's map. Later maps come with the late-game saves (ticket 24, second batch), which lists the 04/05/06 re-checks.
