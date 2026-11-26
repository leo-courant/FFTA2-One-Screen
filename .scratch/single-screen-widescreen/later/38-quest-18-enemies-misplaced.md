# 38: Later battle maps: enemies off the map (quest 18 and others), and quest 18's white portal

**What to build:** In the quest 18 test state (`states/battles/b18_place.dst`, made by `scripts/to_battles.sh`) the enemies are clearly misplaced: the boss stands above the map near the top edge, off the ground (the user, ticket 24 review, 2026-11-24). Find out whether that is the mod or the test route, and fix whichever it is.

**Blocked by:** None. Second batch.

**Status:** closed by the user (2026-11-25). The test route's fault, no mod change; the banner fault found on the way is ticket 41

- [x] Known whether the mod or the test route causes it: the route
- [x] If the route: `to_battles.sh` sets up later battles so enemies stand where the game puts them, and quests 17-23 are checked again
- [x] If the mod: nothing to fix (no hook.c change)

- [x] Known whether quest 18's portal (top left) should be plain white, and fixed if not
- [x] Every later battle map (quests 3, 7, 11, 13, 17-23) checked for units off the ground, and the catalogue's sections retaken

## Findings so far

- Widescreen off (`PLAIN=1`) the enemies look the same, so the test route is the likelier cause.
- How the route works: it plays the road into quest 2's battle, writes only quest 18's battlefield bytes (+0x22/+0x23) into quest 2's record, and swaps in quest 18's opening scene (event 137) and battle script 18 (`play.py SCENE`). Everything else in the record is still quest 2's, and quest 18 normally starts right after quest 17's battle and closing scene (event 134), not from the world map. Either can leave the enemies' starting places wrong.
- Next steps: copy quest 18's whole 100-byte record into quest 2's slot instead of two bytes; check the other quests with their own battle script (23: script 23) the same way; the real route (ticket 30: `saves/q18.sav`, quest 17 then 18) is the reference.
- The user raised it again with a picture of quest 18's placement screen (2026-11-25): an enemy stands in the air at the upper right, another is hidden behind the banner at the top edge, and the portal at the top left is a pure white shape with a blurred edge. The user is not sure the portal is wrong.
- Checked the same moment in an unmodified build (`patch.py --no-hooks`, Deck layout; `shots/t38/ref18*.png`): the enemy is in the air at the upper right there too, so the cause is not the mod's drawing. That leaves the test route. Quest 18's captures there show only the right edge of the portal, white as well; not enough to judge it, so move the camera left or use the real route.
- The enemies look like quest 2's or a stand-in set (the same beasts and goblin-like unit on most of the eleven maps), which fits the route copying only the battlefield bytes: the units keep another battle's starting squares. Not proven.
- Possible other cases, from the placement captures only: the enemy at the right edge on quest 3, at the top on quests 13 and 23.

## Outcome (2026-11-25)

- **Cause: the route.** The enemies are a unit set named by the quest's scene row (sysdata file 10, u16 +0: 2 for quest 2, 18 for quest 18; 13 and 14 are swapped), which the route never changed, so every map had quest 2's units on quest 2's squares. The record's +0x25/+0x26 (3, 2 only for quests 18 and 23: the mist over the battlefield) were not copied either, nor the law.
- **Fix:** `play.py QUEST=N[:S]` replaces quest, scene row and record at the one place every quest battle starts (0x02093A8C, called from 0x02091DE4), so it is all quest N's. The record pokes and `SCENE` are gone from `to_battles.sh`. Quest 18 is chained to 17's battle (record +3 bit 7, no arrival on the world map): its dispatcher (event 136) queues the after-battle talk, so `18:0` makes the first queued script the battle's (event 137, script 0). Quest 23 is chained too but its own dispatcher queues script 0.
- All eleven battles: every enemy on the ground, each quest's own law and objective, quest 18 has its boss and attendants and the mist. Pictures: section I of http://localhost:8765/menus.html (retaken, both-screen ones too) and http://localhost:8765/battles.html with a button for the old picture. `vram_guard.py` (200 frames) over the 22 states: clean.
- **Portal:** the unmodified build (`--no-hooks`) shows the same plain white oval with a soft edge in the scene where it opens, and the boss steps out of it; nothing to fix. The old state's bare portal was a battle without its boss.
- Found by the now real battles: ticket 41 (quest 19: cut law, no turn-order figures). Ticket 30 can use `QUEST=18:0`: the scene before the battle (event 137) is now reached.
- Not checked: the mist in melonDS (a 2D layer, which `solo.py` can only show with seams); only quest 18's opening scene was compared with the unmodified build.
- The four pan pictures (quests 13 and 19) are from before and still show the old enemies; their captions say so.
- The states the route starts from (`s_worldmap`, `s_shop`) were saved before `save_clean` and had stopped running on the current build; rebuilt with `to_saves.sh`.
