# 06: Game panels sit at the screen edges

**What to build:** In widescreen the unit status panel, command menu, Config/Help buttons and height tab sit against the left or right screen edge instead of floating inward.

**Blocked by:** 01

**Status:** done, approved by the user (2026-11-25). All three checks made, no change needed (2026-11-24); ticket 29 came out of it

- [x] Each named panel touches its screen edge in widescreen
- [x] Panels are unchanged with widescreen off
- [x] Dialogue boxes and centred elements stay centred

## Result (2026-11-22)

Panels slide to their edge as whole units, un-stretched: layout objects (status panel with portrait, height tab, Config/Help bars) are classified by where their pieces sat last frame; windows (COMMANDS) by their own rectangle, and text lines follow the window they sit in. Anything straddling the screen centre is left where it is. The HUD projection is now squeezed about the screen centre (it was being squeezed toward the left edge). Verified in melonDS at 1280x800 in the first battle.

Known gaps: dialogue boxes with a face portrait straddle the centre, so they stay inboard (seen in the story scene); "panels unchanged with widescreen off" is untested because the switch is ticket 02; menus other than the battle HUD have not been looked at.

## Update (2026-11-22, later)

Dialogue boxes: all three window kinds are now anchored, and a window that touches one screen edge slides to that edge together with its face portrait and text. Full-width windows are left alone. Left-side dialogue confirmed in melonDS; right-side dialogue confirmed in the low-resolution emulator only.

## Remaining checks (2026-11-24)

No change to the mod.

**Widescreen off.** Widescreen is now switched off by building with the 4:3 preset (ticket 02, ADR 0007), so the check compares a 4:3 build with the reference build (`patch.py --display 4x3 --no-hooks`, see `docs/test-saves.md`). Ticket 02 already covered the battle HUD and 51 menus; dialogue was missing. Both builds were cold-booted in DeSmuME with the inputs of `scripts/to_battle.sh` (name entry, the opening story scenes, into the first battle), both screens captured every 8 presses, 100 pictures each (`shots/t06/ref`, `shots/t06/m43`). 65 are identical, including all 36 of the story part, with speech windows on both sides. The other 35 differ only by the banner and turn order (on in 4:3 too) and by animation one frame apart (a bird in the forest, the unit sprite on the info screen, one row of a light beam), as ticket 02 found.

**Dialogue at the edges, in melonDS.** Deck preset, melonDS 1.1 OpenGL 8x at 1280x800, `scripts/melon_state.py states/m_story.ml1 shots/t06/deck.png s:n00` followed by twenty `x:1.5 s:nNN`. Speech windows that touch the right edge (top and bottom) and the left edge sit at the real screen edge together with their face portrait and pointer, running off the edge as they do on the DS. This closes the "right-side dialogue confirmed in the low-resolution emulator only" gap.

**Centred elements.** On the road into battle 2 (`scripts/solo.py states/s_worldmap.dst`, the `privpick` walk of `scripts/solo_menus.sh` plus `A,w60,sconfirm`; captures `shots/t06/solo/`): the law announcement, the "select a privilege" heading, its list and description box, and the Yes/Back question all stay in the middle of the wide screen. During unit placement the A hint lies over the bottom of the unit panel; the unmodified game draws it the same way (`shots/t06/ref_place/place.png`).

**Found on the way:** in the opening, the scene where the book pulls the hero in (melonDS capture `shots/t06/deck_n16.png`, 16 presses into `m_story.ml1`) is a 4:3 picture with black side areas. Ticket 29.
