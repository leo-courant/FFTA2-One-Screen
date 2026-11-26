# 15: In-battle sheets checked in melonDS

**What to build:** The sheets the game puts on the info screen during a battle (Unit Info, Status, View Abilities, Item List from the battle menu) are readable on the gameplay screen through the SELECT overlay, checked at Deck resolution and fixed where they are off.

**Blocked by:** None

**Status:** done, approved by the user (2026-11-25). Checked 2026-11-23, no mod change needed

- [x] Unit Info, Status and the battle Item List each captured in melonDS with the overlay up
- [x] The overlay closes cleanly back to the battle, banner and turn order return
- [x] SELECT does the same thing on these screens every time (overlay, never the screen swap)
- [x] Anything found wrong is fixed or written up

**From ticket 10 (2026-11-23):** user decision. On these screens the info screen's battle frame is replaced by a blue sheet, so the mod treats them as menus and SELECT gives the overlay; seen working in the low-resolution emulator only (`shots/menus/s_unitinfo.png`). Reach them from `states/s_battle2.dst`: B (free cursor), Y (Unit Info), then the Unit Menu; X then Item List. In melonDS: `scripts/melon_battle2.sh` gets to the same command menu.

**Note (2026-11-23):** `scripts/solo_menus.sh` already walks to these screens and captures them as the mod shows them (`shots/solo/unitinfo.png`, `unitinfo_ov.png`, `status.png`, `abil_ov.png`); the overlay looks right there. What is left for this ticket is the look in real melonDS and closing behaviour.

## Checked (2026-11-23)

In real melonDS on the Deck preset (366x228), from `states/m_battle1.ml1` (first battle; the sheets are the same as in battle 2). Captures in `shots/t15/`, preview `preview/sheets.html`.

Routes for `scripts/melon_state.py` (always with `FPS=60`, see below):
- Unit Info: `z:1 z:1 z:1 a:2`, then `q:1.5` for the overlay
- View Abilities: Unit Info, then `Down:1 x:2`; Status: Unit Info, then `Down:1 Down:1 x:2`
- Item List: `z:1 z:1 z:1 s wait:2 Up:1 x:2` (`s` = X; `s:NAME` is a capture, not "X then wait")

Results:
- All four sheets (Unit Info, View Abilities, Status, Item List): SELECT gives the translucent overlay, sharp at 3.5x. SELECT counted without captures in between: 5 presses = open, 6 = closed, on Item List, Unit Info and Status. Never the screen swap.
- D-pad with the overlay up keeps it and the overlay follows the game's cursor (Item List, Shortsword → Broadsword).
- Closing: SELECT closes it; back in battle the banner and turn order return.
- DeSmuME, frame-exact, battle 2 Item List (`s_battle2.dst`): the mod's `menu` signal stays 1 for 200 frames, each 6-frame tap toggles `ov_manual`, B clears it.

Not faults, written up:
- **B closes the overlay and the game also gets the B** (one step back: from Unit Info + overlay, one B lands on the free cursor). Same as the overlay outside battle (ticket 14, approved); the mod doesn't swallow keys. Left as is unless the user wants B to only close the overlay.
- **The Item List sheet for a Shortsword looks half empty** (no ability rows, only Attack 22): that is the game's own info screen for that item, the same in DeSmuME.

Test-rig fault found and fixed: melonDS's test config runs at 240 FPS. The rig's key press (0.08 s plus xdotool's overhead) then lasts about 20-40 game frames, around the 30-frame SELECT hold limit (ticket 19), so some taps counted as holds (banner toggled, nothing visible in a menu) and the overlay seemed to open and close at random. `melon_state.py` now takes `FPS=60` (sets melonDS's TargetFPS for that run and puts the old line back). Use it whenever a step presses SELECT. A key pressed right after a capture is still sometimes lost even with a 0.5 s wait (two in one run here): don't trust a capture sequence that tests a key straight after a capture; count presses with no captures in between instead.
