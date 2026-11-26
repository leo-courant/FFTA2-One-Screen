# 14: Info screen content laid over the gameplay screen in menus

**What to build:** In dual-screen menus where one screen describes what is selected on the other (party list, equipment, shop), show that information on the gameplay screen itself as an overlay, sharp at 4x like the banner, so the detailed view is not needed there. Preview: `scripts/preview_overlay.py` writes `preview/overlay.html` from melonDS captures.

**Blocked by:** None

**Status:** done, approved by the user (2026-11-23)

- [x] Party list shows the selected unit's sheet on the gameplay screen
- [x] Equipment screen shows the stat comparison on the gameplay screen
- [x] Shop shows the selected item's stats on the gameplay screen
- [x] The overlay follows the selection without visible lag or slowdown
- [x] Final check in melonDS for each menu

## Decision recorded (user, 2026-11-23)

Where a menu has "one screen shows information about the item selected on the other", overlay it on the gameplay screen if we can, rather than relying on the detailed view.

## Findings (2026-11-23)

- In every menu state the gameplay screen is drawn entirely in 3D; its 2D layers are unused. The info screen is four 16-colour tile layers plus sprites, no extended palettes (`scripts/vidregs.py STATE`).
- A 2D copy onto the gameplay screen's free layers would be easy but comes out stretched and soft in widescreen (ADR 0003), which the user already rejected for the banner. The overlay therefore has to go through the 3D path: copy from the info screen into a texture and draw quads, as the banner does.
- Texture memory is the constraint. Banks A, B and D are textures and look nearly full in all test states: the largest all-zero stretch is 16 KB (bank B +0x6000, zero in all five states; not yet proven unused). A whole 256x192 sheet needs 48 KB at 256 colours. Non-zero does not prove in use, so finding the game's texture allocator may free more.
- What fits today without more memory: text and numbers only (the info screen's text layer is 16-colour tiles, same format as a 16-colour texture), drawn over panels the mod draws itself. 16 KB holds 256x128 pixels of text. Icons, the background art and sprites would need the extra memory.
- Cost: copying tiles is cheap; only redo it when the source tile map changes (hash, as the banner does).

## Decisions (user, 2026-11-23)

- Party: the whole sheet drops in on a button, translucent like the shop's list panel.
- Item stats: not overlaid all the time; they appear together with the game's own Item Info panel (L/R), so abilities and stats are seen at once.

## Built (2026-11-23)

- SELECT outside battle shows the whole info screen as a translucent panel over the gameplay screen (party, equipment, shop, world map). It is a peek: the D-pad keeps it up and it follows the selection; SELECT again or A/B/X/Y/START puts it away. In battle SELECT still swaps screens.
- While the game's Item Info panel is up, the stats part of the info screen is shown beside it automatically: the item's stat block in the shop, the unit's stat column in equipment.
- Opacity and backdrop dimming are the constants `OV_ALPHA` (25 of 31) and `OV_DIM` in `src/hook.c`.
- How it works and its limits: ADR 0005. Checked in melonDS (captures `shots/melon/ov_*.png`).

Open points:
- In equipment, Item Info makes the game put the unit sheet on the info screen, not the weapon comparison, so the stats shown beside the panel are the unit's, not the weapon's change.
- The game's own windows (unit menu, help text) draw in front of the overlay.
- The Item Info detection is one pointer at 0x0212E834 found by comparing memory in the shop and equipment; other screens with an Item Info panel are untested.

## Review round 2 (user, 2026-11-23)

- Rule from the user: never more than one layer of panels over another. While the whole-screen overlay (SELECT) is showing, everything the game draws with its HUD projection is pushed off screen (`hud_hidden` in `ortho_fix`): portrait and HP/MP bubble in the party menu, the item list in the shop, button hints.
- The game's Item Info box ran off the right side of the 4:3 picture and showed a ragged end in widescreen; panels that start mid-screen and run off one side now stay attached to that side (`layout_obj_begin`).
