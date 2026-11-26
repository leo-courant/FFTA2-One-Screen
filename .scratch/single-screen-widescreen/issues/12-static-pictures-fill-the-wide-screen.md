# 12: Static pictures fill the wide screen

**What to build:** Full-screen still images drawn as a single picture (the title screen background, story illustrations and similar) fill the whole 16:10 screen instead of leaving a black side area. The user is open to reconstructing the missing edges with image tools (outpainting) where the game has no more picture to show; simpler options are widening or mirroring the picture's edge.

**Blocked by:** None (can start immediately)

**Status:** done, approved by the user (2026-11-23)

**Changed (user, 2026-11-23):** published patches may only fill these pictures by methods worked out from the player's own ROM while the game runs (widening or mirroring the edge). AI-outpainted pictures are allowed only as a private add-on on the user's machine and are never published or committed to a public repo.

- [x] Title screen has no black area in widescreen, using a method fit for publishing
- [x] If outpainting is done, it is kept out of the published patches (none done)
- [x] Every other full-screen still found so far is listed with how it is handled
- [x] The user has approved the look of at least the title screen via a preview

## Built (2026-11-23)

What was wrong: the title background is one layout object with a single 256x192 piece. The mod's frame rule (`layout_piece`, made for the world-map frame) stretched it to the wide view, and the panel rule in `layout_obj_begin` also slid it 55 px left (its only piece starts at x 0), leaving a 55-column black strip on the right in melonDS. The menu (box 60..210) and the copyright line (one strip 0..256) were slid left the same way.

Fix (ADR 0010):
- `still_edges` (hook at 0x020B0B4C, END_VTXS of the piece's quad, entry slot +60): the still stays at its true size and eight quads around it show the picture mirrored at its edges (texture coordinates running backwards, same texture, colour and matrix). Only for a single piece covering the whole 4:3 picture one texel per pixel; nothing on 4:3.
- `layout_obj_begin`: an object as wide as the 4:3 picture, or centred on it and well clear of both sides (box starts at 32..96 and ends at 160..224, centre within 40 px of the middle: the title menu 60..210, the difficulty menu 70..221), does not slide sideways; it still moves to the top or bottom like other panels.

Checks: all 57 `solo_menus.sh` captures identical to before the change (the first version of the centring rule moved the item description box and the battle forecast; narrowed until none moved). 4:3 preset title and difficulty menu identical pixel for pixel to `patch.py --no-hooks`. 16:9 title filled edge to edge. melonDS capture of the title on the Deck preset: `shots/t12/melon_title_v2.png`.

Full-screen stills found so far and how each is handled:

| Screen | How it is drawn | Handling |
| --- | --- | --- |
| Title background (also behind the difficulty menu) | one 256x192 layout piece | mirrored at its edges (this ticket) |
| Square Enix logo | 3D logo on black | nothing needed: black is the picture; the logo keeps its true width |
| Opening text before name entry | white text on black | nothing needed |
| World-map frame | screen-sized layout object of several pieces | bars stretched to the edges (`layout_piece`, earlier) |
| Menu floors (party room, equipment) | tiled scene layer | repeated sideways (`layer_draw`, ticket 18) |
| Clan parchment | 272x192 map of six cells | edge pixels drawn out (`map_extend`, ticket 18) |
| Fades to white or black | master brightness | cover the whole screen already |

No story illustrations have turned up in the opening or the first two battles; late-game ones would show up with ticket 24's saves.

Test state: `states/t_title.dst` (cold boot, `play.py - states/t_title.dst w1500`), the title with New Game highlighted. `solo.py` draws the title with a dark row where its pieces join (y 737); melonDS has no such row.
