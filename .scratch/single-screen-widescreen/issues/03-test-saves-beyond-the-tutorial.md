# 03: Test saves beyond the tutorial

**What to build:** Get past the tutorial battle and opening story by whatever means work (scripted play, memory edits, or a downloaded save) and keep saves or savestates at: the world map, inside a shop, the party menu, an equipment screen, and a battle that has a special rule.

**Blocked by:** None (can start immediately)

**Status:** done (2026-11-23)

- [x] Each of the five situations has a state that loads on the current build
- [x] A preview page shows both screens for each situation
- [x] How each state was reached is written down so it can be redone

## Result (2026-11-23)

States `states/s_worldmap.dst`, `s_shop.dst`, `s_party.dst`, `s_equip.dst`, `s_battle2.dst` and the in-game save `saves/worldmap.sav`, all rebuilt by `scripts/to_saves.sh` (scripted play, no memory edits needed, no downloaded save). Details and how to redo it: `docs/test-saves.md`. Preview: `scripts/preview_saves.py`.

The "special rule" in `s_battle2` is the clan privilege: the info screen gains a PRIVILEGE line under the law. No other kind of per-battle condition has been seen yet; later quests may add more.
