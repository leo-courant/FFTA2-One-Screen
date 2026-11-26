# 16: Job changes and ability lists shown beside the list

**What to build:** Where the gameplay screen only has a list and what the choice does is on the info screen, that part of the info screen appears beside the list by itself while the list is open, as item stats do beside Item Info. Two places: Change Jobs (the stat changes of the highlighted job) and View Abilities (the abilities of the highlighted category and their mastery).

**Blocked by:** None

**Status:** done, approved by the user (2026-11-23)

- [x] Change Jobs: the stat column with its +/- changes is visible beside the Jobs list without pressing anything, and follows the highlighted job
- [x] ~~View Abilities (in battle): the ability list for the highlighted category is visible beside the category menu~~ dropped by the user (review round 2): the game's own list after A is used instead, and its panel is fixed for widescreen
- [x] Set Abilities gets the same treatment once a save reaches it, or a note says why not (note below: still not reachable)
- [x] Never more than one layer of panels: nothing the game draws sits under the added panel
- [x] Final check in melonDS, shown to the user as a preview link (Change Jobs `shots/melon/t16_jobs.png`, the ability list `shots/melon/t16_abil_list.png`)

**From ticket 10 (2026-11-23):** user decision: automatic, not SELECT-only. Both screens for each case are in the catalogue (`preview/menus.html`, group B; `shots/menus/jobs2.png`, `b_abil.png`). The Item Info case in ticket 14 / ADR 0005 is the model: it is triggered by one pointer (0x0212E834) and shows a crop of the redrawn info screen; each of these lists needs its own trigger found. Set Abilities did not open for the starting units in the current save. SELECT still gives the whole sheet.

**Note (2026-11-23):** in View Abilities the mod already draws something by mistake: a translucent panel on the left, which looks like the Item Info stats panel being triggered there (`shots/solo/abil.png`). Fix it here. Check the look with `scripts/solo.py` (see `docs/test-saves.md`); the walks to these screens are in `scripts/solo_menus.sh`.

**Update (2026-11-23):** the stray panel in View Abilities is gone. The user did not know what it was for and asked for it to be removed. The Item Info signal (0x0212E834) is also up in View Abilities, so the stats panel beside Item Info is now limited to outside battle scenes (`BATTLE_SCENE`, the word at 0x0212418C: 2 in a battle scene, 1 on the world map and its menus). Side effect: the battle Item List's Item Info no longer gets stats beside it; SELECT still shows the sheet. What this ticket should show beside the abilities list is still to build.

## Built (2026-11-23), as it stands after two review rounds

Preview: `scripts/preview_sidepanels.py` writes `preview/sidepanels.html`.

- **Change Jobs:** the stat column of the info screen (Move to Resistance, with the +/- changes of the highlighted job) is drawn top left, 116x108 game pixels. That is wider than the 90 pixels free beside the Jobs list, so the list slides 28 pixels to the right while the panel is up; its scroll bar still fits on screen. The panel ends just above the portrait. Trigger: the word at 0x021326D4 is 3 while Change Jobs is open (2 and 1 in Change Equipment's two steps, 0 in the other moments compared; `JOBS_LIST` in `src/hook.c`). It uses the overlay of ADR 0005; only the crop and its place are new. Widescreen only: with widescreen off there is no room beside the list, and SELECT gives the sheet. Checked in melonDS (`shots/melon/t16_jobs.png`; keys for `melon_save.sh`: `s:1.5 x:3 x:2.5 Down:0.8 Down:0.8 x:3.5 Down:2`).
- **View Abilities:** the mod adds nothing while a category is only highlighted. Pressing A on a category opens the game's own ability list on the gameplay screen (names, mastery, cursor, scroll bar, L/R to change category), and the cursor already moves in all four directions there. That panel is as wide as the 4:3 picture with its right end outside it, and in widescreen it ended ragged inside the picture; it now slides right until that end is off screen (`layout_obj_begin`: a root panel whose left end is at the old left edge and whose right end is 16 or more pixels past the old right edge).
- `scripts/solo_menus.sh` now also captures `jobs3`, `abil2`, `abil_mage` and the game's list (`abil_items_list`, `abil_items_list2`, `abil_mage_list`).

## Review (user, 2026-11-23)

- Round 1: Change Jobs good. A preview of the highlighted category's abilities above the category menu (first as a blue box across the top, then as names on a light tint standing on the menu) looked odd to the user.
- Round 2: shown the game's own list after A, the user preferred it to abilities floating above the menu, asked for its cut-off right side to be fixed, and asked that the cursor move left/right as well as up/down (it already does). The preview was removed.

## Found on the way

- The overlay may stack at most three quads: each one is drawn 8 depth units nearer and the fourth falls outside the view. Quads that sit side by side must share a layer.
- A panel placement rule has to hold whatever the panel's pieces did last frame. The first try at sliding the Jobs list flipped every other frame, because the list's rule was tested after the general left/right rules and the object also matched its own rectangle from the frame before.
- For a later preview of abilities, if one is ever wanted: the word at 0x0212E808 is 5 while View Abilities is open (0 in the other moments compared); the ability names are on layer 3 of the info screen and their tiles carry the panel's blue fill (colour 0x6603) themselves.
- melonDS replays into the second battle failed four times before one worked: twice because another session's melonDS run was going at the same time (every rig ends with `pkill -KILL -x melonDS`), once because a replay that had lost its melonDS kept running and its own cleanup killed the next one, once because test-emulator captures ran alongside and the frame-timed cursor missed the quest node. One melonDS rig at a time on the machine, nothing heavy beside it, and after a failed run make sure no `melon_play.sh` is left before starting another. The route that worked is the `melon_battle2.sh` script plus `B,w60,B,w60,B,w60,UP,w30,Y,w150,DOWN,w60,A,w200,DOWN,w120,A,w200,RIGHT,w90` with a 570 s limit.
- `PLAIN=1` captures find the widescreen settings by their order in the blob's data; an initialised variable added to `hook.c` can reorder them and break it (it did once here). Keep new variables uninitialised.

## Not done

- **Set Abilities** is still greyed out for the unit tried (Luso) in the test save, so its screens have not been seen and nothing was done for it.
- A category with more than six or seven abilities has not been seen (the black mage has three in the test save); the game's list scrolls, so nothing is expected to be needed.
