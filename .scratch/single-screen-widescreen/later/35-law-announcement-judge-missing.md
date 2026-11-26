# 35: Law announcement: the judge is missing from the circle

**What to build:** When a battle's law is announced, the panel with the law (heading plus the law's name) has a circle at its left end. In the unmodified game the judge stands inside that circle (`shots/menus/lawintro.png`, widescreen off). In the mod the circle is empty (`shots/solo/lawintro.png`; the user's ticket 24 review, 2026-11-24). Put the judge back in the circle.

**Blocked by:** None. Second batch (found in ticket 24's review).

**Status:** done (approved by the user 2026-11-25; no mod change)

- [x] The judge shows in the circle on every preset (Deck, 16:9, 4:3), in melonDS at Deck size
- [x] Checked on a second battle's announcement (battle 2 route in `scripts/solo_menus.sh`, or `states/battles/` from `scripts/to_battles.sh`)
- [x] The menu captures are otherwise unchanged (no code change)

## Leads

- The judge is most likely a sprite (sprite queue, FUN_02034164) with its position baked in, like the weather icon and the world-map quest markers. `sprite_fix` in `src/hook.c` moves sprites with the panel they sit on, but it returns at once in battle (`BATTLE_OBJ`) and only looks at panels near the top (`r->y1 <= 48`); this panel is lower down in a battle. So the judge stays where the panel was or is hidden, while the panel's right end is stretched to the screen edge.
- Find the judge with `scripts/gxtrace.py` + `scripts/gx_report.py` on the law announcement (the battle-2 walk in `solo_menus.sh` stops there as `lawintro`).

## Findings (2026-11-25)

**The judge was never missing.** While the announcement is up the judge loops: appears small and solid, grows, fades out completely, starts over. One loop is 31 frames (about half a second). The review capture `shots/solo/lawintro.png` was taken on a frame at the end of a fade; `shots/menus/lawintro.png`, the picture it was compared with, happened to be taken on a solid one.

- Unmodified game (`--no-hooks` build, own walk from `s_worldmap`): same loop. The 4:3 build's circle is pixel-identical to it (0 of 2080 pixels differ, two frames later) on 14 sampled frames across two loops.
- Deck and 16:9: the judge follows the circle through the whole loop (`solo.py`, every 4 frames over a loop), because this panel is not moved at all. The leads above (sprite left behind, panel stretched to the edge) did not hold.
- The whole opening, every 4 frames from the press before to after the panel closes: the judge slides in with the panel and goes with it, as in the unmodified game. Nothing about the law appears again in the first 600 frames after the privilege is picked.
- Second battle: quest 11's scene in quest 2's slot (`SCENE=123:0@2`, announcement after press 42), same loop. Also melonDS at 1280x800, battle 2 from `saves/worldmap.sav`: fading and solid captures of the same announcement.
- Preview: `scripts/preview_judge.py`, a half-speed loop of the mod beside the unmodified game.

Found on the way, not touched: the panel's right end (ticket 39).
