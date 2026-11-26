# 32: Set Abilities: stray side panel, and the set's abilities on one screen

**What to build:** Two things in the unit menu's Set Abilities (reachable with the late save, `states/late/l_setabil.dst`):

1. **Fault:** about 90 frames after Set Abilities opens, the mod shows its Item Info stats panel (ticket 14: the info screen's left column, 128 px, top left) although no Item Info is open. It sits over the game's unit panel (against the user's rule of one layer of panels at most) and is cut at 128 px, so the second column of the highlighted set's abilities is missing. Picture: `shots/solo/late_setabil_w90.png` (catalogue section G).
2. **Decision for the user:** what the list needs. The info screen shows the highlighted set's abilities and their mastery (ticket 10's kind B, like View Abilities). In View Abilities the user chose the game's own ability list (A on a category, ticket 16). In Set Abilities, A on a slot showed the game's help line for the slot in the test emulator, not a list; check in melonDS what A really opens before proposing anything.

**Blocked by:** None (found in ticket 24). Second batch.

**Status:** done, approved by the user (2026-11-25): stats panel no longer in Set Abilities; the set list runs off the right edge; nothing more needed for the set's abilities (the game's own Ability Info, R in the list). Preview: http://localhost:8765/setabil.html (`scripts/preview_setabil.py`)

- [x] The stats panel shows only while the game's Item Info panel is really up (shops, equipment), never in Set Abilities
- [x] What Set Abilities offers on the gameplay screen is checked, and the user has chosen how the set's abilities are shown (or that nothing is needed). Checked in DeSmuME only (no melonDS state in the late save's unit menu); the user chose nothing more (2026-11-25)
- [x] The 57 menu captures (`scripts/solo_menus.sh`) are unchanged apart from Set Abilities

## Findings (ticket 24)

- The trigger is `ITEM_PANEL` in `src/hook.c`: the word at 0x0212E834 (`item_info_panel` in `docs/symbols.tsv`). In Set Abilities it holds 0xF4E0 from the first frame, the same value as with the real Item Info panel open in the shop (`s_shop` + R) and in equipment (`s_equip` + A, R). So the value alone cannot tell them apart: the word probably belongs to a general description/info panel that Set Abilities also uses. Look for a word that tells the menus apart (as `JOBS_LIST` 0x021326D4 and 0x0212E808 == 5 in View Abilities did), e.g. by diffing RAM between `l_setabil` and the shop with Item Info up.
- The panel needs a few dozen frames to appear (the overlay redraws the info screen in bands), so a capture right after loading the state does not show it; the catalogue now has a 90-frame capture as well.

## Findings and fix (ticket 32, 2026-11-24)

- **0x0212E834 is not an Item Info flag.** It is +0xC (size) of slot 26 in the game's resource table at 0x0212E4E8 (47 slots of 0x20 bytes: +0 owner, +8 handle, +0xC size, +0x10 buffer; `res_load` 0x02084AF8 fills a slot, `res_unload` 0x02084D38 empties it; the slot is chosen from the file id by `res_slot_of` 0x02084844). The info screen's sheet pictures are loaded there. Traced with a write watch on the word and an exec watch on `res_load` (args + return chain).
- The party menu's overlay picks the sheets with a switch on its menu mode (overlay code 0x0213DAD0, mode u16 at object +0x5EC, 0..0x16; first sheet's file at +0x605, second at +0x606). Item Info in equipment (modes 0x10, 0x12, 0x13) loads only the item sheet, file 0x1F (slot 26). Set Abilities (modes 3, 4) loads the ability sheet, file 0x1E (slot 25), with file 0x1F as its second sheet. The plain equipment view loads files 0x27 + 0x12. The shop's own overlay loads file 0x1F alone for its Item Info.
- 0x0212E808 (once "== 5 in View Abilities") is slot 25's owner word: 5 while the ability sheet is loaded, in View Abilities and Set Abilities alike.
- **Fix:** `ITEM_PANEL` in `src/hook.c` = item sheet loaded AND ability sheet not loaded (`RES_LOADED(26) && !RES_LOADED(25)`). A RAM diff of the static area across 4 Item-Info-up and 6 other menu captures found no better word (only allocator leftovers), so the sheet pair is the signal.
- **Check:** all 96 `solo_menus.sh` captures, old build vs new, on the same states: only `late_setabil` and `late_setabil_w90` changed among the menus. The other 6 that differed (battle and auction scenes, where the panel is off anyway) were the stale-state effect: the blob's data moved, so states made with the old blob draw wrongly (broken tile stitch, animation drift). All states were rebuilt (`to_saves.sh`, `late_save.sh late`, `to_late.sh`, `to_battles.sh`). After the rebuild, captures drift by replay timing (battle moments, one unit's EXP 60 vs 61), but shop and equipment Item Info still show the stats panel.
- **What Set Abilities offers on the gameplay screen (DeSmuME):** A on a slot opens the game's own list of ability sets (the first A presses after loading `l_setabil` only toggle the help bubble). In that list, R ("Ability Info" on its button hint) opens the game's own view of the highlighted set's abilities with their mastery, on the gameplay screen. That is the same information the info screen shows, one press away, like View Abilities (ticket 16), where the user chose the game's own list. Since the item sheet is loaded alone there, the mod's stats panel shows beside it, over the map, as in equipment Item Info. **Proposal: nothing more is needed.** A melonDS look was not made: there is no melonDS state in the late save's unit menu, and the open-loop walks there are unreliable.

## Review 1 (user, 2026-11-24)

- Approved except the set list (A on a slot): it sat left and short, with its set icons showing outside the window. In the unmodified game the list's window runs from x 39 past the right edge (box 29..264, the set icons beyond 256 out of sight). Its own pieces all lie at x 29..66, so the rule "pieces in the left half slide to the left edge" caught it, and the rule that keeps right-running panels on the right edge (box from x 64) did not apply.
- **Fix:** `layout_obj_begin` gives a root panel that starts inside the picture (2 < x0 < 128) and runs past its right edge (x1 > 258) the right edge's shift, checked before the left/right-half rules. The list now runs off the right edge like the original; steady over consecutive frames.
- **Check:** states rebuilt on the new build, then all 96 `solo_menus.sh` captures taken with the rule on and with it switched off (a `BLOB=` copy whose branch at the rule is made unconditional, so both runs share one data layout): identical. The rule only changes the set list.
- Method worth reusing: to compare two variants of hook.c without stale savestates, build once, rebuild the states, and switch the change off by patching its branch in a copy of the blob (`zig cc -S` with the patch.py flags gives the instructions after the source line's `.loc`).
