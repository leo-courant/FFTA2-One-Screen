# 18: Widescreen layout faults from the menu review

**What to build:** The remaining places where the widescreen picture differs from how the game lays the screen out, found when the user reviewed the menu catalogue (`preview/menus.html`) on 2026-11-23.

**Blocked by:** None

**Status:** done, approved by the user (2026-11-25). Built 2026-11-23

- [x] World map: the weather icon sits inside the corner globe, as in the game
- [x] Party, equipment and Fitting Room: the tiled floor continues into the side areas
- [x] Clan menu and its lists: no black side areas
- [x] Clan > Quest Report: the highlighted square is under the cursor figure
- [x] Battle: the action name bar ("Attack") and the turn order do not sit on each other
- [x] Each fix shown to the user as it looks in the mod (`scripts/solo.py`): approved 2026-11-25

## How each was done

- **Weather icon.** An animated sprite queued by FUN_02034164 with a finished screen matrix. A hook right after a sprite is queued (`sprite_fix`, 0x02034C5C) moves any sprite whose anchor lies on a small moved panel at the top of the screen the same way as that panel. Only rain has been seen. Checked in melonDS (`shots/melon/t18_worldmap.png`).
- **Tiled floor.** FUN_020d4be0 draws the scene's picture layers (clouds in battle); in these menus the layer is four fixed 128px quads that fill the old screen exactly. `layer_draw` (called in its place, 0x020D60C0) draws such a sheet twice more, one screen to either side, by changing the layer's scroll offset at +0xC. The pattern repeats every 128px so the copies join up. Moving the matrix instead does nothing: the routine sets its own.
- **Clan menu.** The parchment is a "map" like the battle maps (FUN_0208cafc), but one fixed picture of 272x192 in six cells, so there is nothing more to show. `map_extend` (end of that routine, 0x0208CE08) draws the picture's outermost row or column of pixels on out to the screen edge: the dark table the parchment lies on carries on. Applies only to a map exactly 192 rows high and narrower than the wide view. No outpainting was needed.
- **Quest Report.** The board, the cursor figure, the highlighted square and the quest nodes are four separate top-level objects. The board is now treated as a *ground* (a top-level object that covers the old screen and is bigger than it): where its own edge shows inside the wide picture it slides out to the real edge, and objects that touch no screen edge, and holders without pieces, go where it went. On the world map the ground is the brown table, which does not move, so nothing changes there. Scrolling the board could not be tested: the save has two quests, both in column a.
- **Action name bar.** While the turn order is up, a full-width window on its rows runs from the real left edge to where the turn order starts, text centred in what is left (`window_draw_with`).

## Found on the way

- **0x0212418C is not "battle scene".** It is 1 on the world map and its top menus and 2 in everything entered from there, including the party room, the shop and the clan lists. The check added in the previous session to keep the stats panel out of battle's View Abilities had therefore also removed it from the shop and equipment Item Info. Replaced by `in_battle`: set when the battle HUD is seen on the info screen, cleared when that word is 1 again.
- **Layout tracking ran out of slots.** 16 slots for objects; the Quest Report draws more than twenty, so objects were forgotten every frame and never placed. Now 48. One visible effect: the pub quest detail's B hint sits at the screen edge.
- **Code space.** The mod's code no longer fit in 0x4000 bytes; `BLOB_RESERVE` is 0x6000. All states were rebuilt (`to_battle.sh` on the patched ROM, then `to_saves.sh`); `p_story*`, `p_after1` and `intro*` are stale.
- Not checked in melonDS: these are all position changes, checked with `scripts/solo_menus.sh` (all 51 captures compared with before).

## Fixed already (2026-11-23, same review)

How the mod decides where a panel goes was reworked (`layout_obj_begin` in `src/hook.c`):
- Panels are drawn as trees. A child (a list row with its cursor, icon and name) now always moves with its parent. Before, each child was judged on its own, by coordinates relative to its parent, so rows stayed behind when their panel slid to the edge (Change Equipment, View Abilities).
- Top or bottom is now judged from the object's real position on screen. Before it used positions relative to the object, which pushed the attack forecast's target panel 46 pixels down, hid the Config hint in battle, and moved bottom panels up instead of down.
- A label without pieces of its own follows the moved panel it sits on (the world map's area name on the corner globe).
- Pieces the game parks just outside the 4:3 picture are kept out of the side areas (the list cursor dot in the pub's quest lists, which the game never shows).

## For later in the game (user, 2026-11-23)

Weapon crafting (the bazaar) has a menu whose requirements the user believes are on the info screen. It is not reachable with the current save; when a later save exists, add it to the catalogue and decide its treatment like the kind B menus of ticket 10 (ticket 16).
