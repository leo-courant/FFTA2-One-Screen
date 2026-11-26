# 22: The ability list in View Abilities is more compact

**What to build:** In the game's own ability list (View Abilities, A on a category) the two columns sit closer together and the scroll bar closer to the right-hand column, so the panel is narrower and covers less of the scene, while every ability name in the game still fits.

**Blocked by:** None

**Status:** done, approved by the user (2026-11-23)

- [x] Each column is 14 game pixels narrower: the right-hand column moves 14 left, the scroll bar 28 left, and the panel (anchored to the right screen edge) ends up 28 narrower
- [x] The highlight bar is shortened to the new column width and does not touch the other column's marker
- [x] The longest names still fit inside the highlight: check with `scripts/long_ability_name.py 247` ("Thunder Flare Tome") and `248`
- [x] Cursor in both columns and a scrolled list look right (L/R to another category not captured)
- [x] No other menu changes: regenerate `shots/solo` and compare (docs/test-saves.md)
- [x] Final check in melonDS, shown to the user as a preview link (`shots/melon/t22_abil_list.png`, on the ROM built from the merged master eef6c8c)

**From ticket 16 (2026-11-23):** the user saw the list in widescreen and asked for less empty blue between the columns and before the scroll bar, by whatever amount fits all the names. A mock-up at 14 pixels per column (`shots/mock/t16_compact.png`) was approved for its proportions ("much better").

## Measurements (2026-11-23)

- The ability names are a plain table in the ROM at 0x2A978AC..0x2A995CD, 841 entries, zero-terminated, the game's one-byte text code (space 0x01, A 0x02, a 0x1C, hyphen 0x8D, apostrophe 0x83, colon 0x81, full stop 0x7F). In the `s_battle2` state the table is in memory with "Potion" at 0x0231A072 and "Phoenix Down" at 0x0231A099.
- The 24 longest by character count were drawn by the game and measured (bright pixels, plus 2 for the outline): "Thunder Flare Tome" and "Shadow Shade Tome" 87 px, "Earth Dragon Tome" 83, "Territorial Marking" 81, "Sword of Darkness" 80. Shorter names with wide letters were not all measured; keep a few pixels spare.
- The list as the game lays it out (4:3 pixels): names start at x 23 and 141 (pitch 118), the row marker sits 10 px left of the name, the highlight runs about 106 px from 2 px left of the name, the mastery mark spans name +17 to +75, the scroll bar is at about 276..289. A name needs 87 + margin, about 92, plus 12 for the marker: pitch 104, hence 14 per column.

## What is known about how the list is drawn

- The panel is one root layout object (box about -6,32..289,200 in the test state) that ticket 16 already slides right by 31 px (`layout_obj_begin`, the rule for a panel as wide as the 4:3 picture whose right end lies well outside it). The highlight is a separate object (box 12,78..127,105 with the cursor on the first entry). Names are text lines; `text_line_x` moves text with the rectangle it sits on.
- Not known yet: whether the row markers, the mastery marks ("MASTER", the progress bars) and the scroll bar are pieces of the panel object, child objects, or sprites from prebuilt lists (those have their position baked in; `sprite_fix` is the hook for them). `scripts/gxtrace.py` + `scripts/gx_report.py STATE` list every polygon of a frame by call site and are the quickest way to find out. A state with the list open: play `w10,B,w40,B,w40,B,w40,UP,w15,Y,w90,DOWN,w15,A,w120,DOWN,w40,A,w120` from `states/s_battle2.dst`.
- Shortening the highlight means changing a piece's width (`layout_piece` does this for screen-sized frames through the scratch quad); if the highlight is one textured piece its rounded ends will be squeezed slightly.
- Set Abilities (outside battle) probably uses the same list but has not been reachable in the test save.

## Built (2026-11-23)

- The list is a grid widget of the game that places its own cells (`FUN_020b3208`: cell width at +0x94, cell height +0x96, columns +0x9E, rows +0x9C, the widget's own width, which carries the scroll bar, at +0x20). `list_fix` (hook on the call at 0x020B34C0) sets the cell width from 118 to 104 and takes 28 off the width while the list's panel is on screen. Markers, names, mastery marks, the cursor and the scroll bar all follow by themselves, because the game computes them from those fields. This is why none of the per-piece moves the ticket expected were needed.
- The highlight bar is three pieces a row (6 + 95 + 6 wide) of the cell object; `layout_piece` shortens the middle by 14 and moves the right end.
- The panel slides right by another 28 (59 in all). Slid that far, the game stops drawing the panel's pieces that land beyond x 320, so the panel's box shrinks and the rule that recognised it by its box lost it every third frame (it jumped left for a frame). The panel is now remembered once recognised (`abil_obj`) and tested before the other placement rules.
- Widescreen only; with widescreen off the list is as the game made it.
- Checked with `scripts/solo.py`: cursor in both columns, scrolled list, the black mage's progress bars, and the two widest names written into memory with `play.py` `p` steps ("Thunder Flare Tome" ends 3 pixels inside the highlight). All 57 menu captures regenerated: only the ability list pictures differ.
- `scripts/long_ability_name.py` uses `PLAIN=1`-style 4:3 capture, where the list is not compacted; for a widescreen check write the name with `p<addr>=<val>` steps in a `solo.py` script instead.

Not done: L/R to another category and Set Abilities were not captured.
