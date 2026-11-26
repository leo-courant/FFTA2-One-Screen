# 07: Banner and turn order for the wide layout

**Final state (2026-11-23):**
- Banner: objective / law / privilege boxes against the right edge, sharp (3D, 2-bit text texture); long texts flow onto a second row (at most two on the Deck, three on 4:3). To be replaced by one rotating cell (ticket 23).
- Turn order "stage": four units standing at the bottom centre between the unit panel and the Help bar (4:3: a strip at the top right), whole sprites with their shadows; slot 0 is always the acting unit on an orange ring; a row of pips (blue ally, red enemy) gives the side of each coming turn, the first being the acting unit's; L/R browsing shows a light-blue arrow over the browsed unit and outlines its pip, the other slots following it. Steps aside when a game panel takes the spot.
- Texture memory shared with the game's battle heap, checked every frame (ADR 0008).
- Final melonDS check: `shots/melon/t07_final.png`. Preview and video: `scripts/preview_turnorder.py`.

**What to build:** The banner and turn order are sharp in widescreen and use the extra width: full objective and law text without clipping, and a compact turn-order row with framed heads and the acting unit emphasised, in the spirit of Triangle Strategy.

**Blocked by:** 01

**Status:** done, approved by the user (2026-11-23). Banner layout for long texts continues in ticket 23

- [x] Objective and law text are sharp at 1280x800 in melonDS
- [x] The longest objective and law strings in the game are shown without cut-off words
- [x] The acting unit is obvious at a glance (orange ring, first pip; the user chose "stage")
- [x] Banner on/off still works
- [x] A preview with at least two layout options was shown to the user before finalising

## Progress (2026-11-22)

Done on the existing 2D layer: each banner box is now only as wide as its text plus padding (which also removes the old 104px clipping), the law box follows the objective box directly, and the turn order moved two cells right. Checked in the low-resolution emulator only. Still open: the banner and heads are on a 2D layer, so in widescreen they are about 20% wider than intended and not high-resolution; making them sharp means drawing them through the 3D path. The Triangle Strategy-style turn bar has not been started.

## Result (2026-11-23)

The banner and turn order are now 3D polygons drawn just before the game swaps buffers, from a private texture (free tail of texture bank B at 0x3F000, palettes at 0x3A00 in the texture palette). Text is sharp and correctly proportioned in melonDS at 1280x800. Boxes fit their text. Turn order: unit heads on a translucent dark strip, right-aligned short of the top-right corner, acting unit in a gold frame. The banner and strip hide while a speech window is open. The old 2D banner layer is no longer used.

Open: only one turn-order look was built, so the "two options previewed" criterion is not met; "longest strings" has not been tested against real long text; the texture and palette addresses were chosen because they were empty in two test states, which does not prove the game never uses them; a tutorial pop-up can overlap the strip.

## Update (2026-11-23, later)

At the user's request the banner boxes and the turn-order strip now sit against the right edge. The game's top-right "B" hint is moved below the strip while the banner is showing (checked in the low-resolution emulator only).

## Update (2026-11-23, session 3): second look, long texts, owned texture memory

**Second look (B).** `TURN_STYLE` in hook.c picks the look at build time (`patch.py --define TURN_STYLE=2`):
1 = heads on one dark strip, acting unit on a gold square (as before); 2 = one card per unit in
the game panels' dark blue, the acting unit's card larger (30 px), gold-edged and set apart, the
others a shade darker. Once the user picks, delete the other branch and the switch.

**Longest texts.** The game's text is in `master/pc.bin` in a one-byte encoding (A-Z = 0x02-0x1B,
a-z = 0x1C-0x35, space 0x01, digits 0x67-0x70, "!" 0x73, "↑" 0x9B, 0x00 ends a string). Laws are a
fixed table at ROM 0x2AA4E00 (longest 27 characters; some laws are icons with short words),
privileges at ROM 0x2AA5600 (longest 19-21 characters), objectives are in the quest event text
(longest found 48 characters). Game texts are not quoted in the repo (publishing rules, ticket 21):
the measured list is `work/text-widths.tsv`, kept out of git. The info screen font is about 5 px per
character: worst case about 28 + 18 + 13 cells of text, against 34 cells beside the height tab.
So the banner now flows: each box goes in the first row with room (row 0 is beside the height
tab, later rows run the full width), the law and privilege together if any row takes both; the
turn order, the game's "B" hint and the "Attack" bar move down under the last row. On the Deck the
worst case is two rows; on the 4:3 preset three. `scripts/banner_stretch.py` makes the test (it
repeats the info screen's own text cells to the longest widths).

The text texture is now 4-colour (2 bits): each box's text uses three colours of one group of four
in the info screen palette (objective 5-7, law 9-11, privilege 13-15), so cells keep their group
(`txt_grp`) and are drawn as one quad per run of same-group cells with that group's 4-entry palette.
512x32 = two lines of 64 cells in 4 KB: objective on line 0, law + privilege on line 1.

**Texture memory is now the mod's own.** FUN_020a0e74 sets up the VRAM areas per scene. In
battle (mode 2) it makes a texture heap at 0x2E000 of size 0x12000, i.e. to the very end of
bank B: unit sprites and effects are allocated from it bottom-up (battle 2 reached about 0x38600),
and the old banner texture at 0x3F000 was its last 4 KB, free only because the heap never filled.
patch.py now shrinks the heap by `HUD_TEX_SIZE` = 0x1800 (instruction at 0x020A0F68, `mov r2,
#0x10800`), and the banner owns 0x3E800-0x3FFFF. Checked: on entering battle 2 the heap reads
base 0x2E000 size 0x10800; over 11,000 frames from the world map through the story scene, unit
placement and several turns, nothing but the mod writes there in battle. The world map loads 644
bytes into 0x3F44C+ each time it is entered (it does not use the battle heap layout); the banner
re-uploads after every scene without the battle HUD, so that cannot leave it stale.
Palette 0x3A00-0x3BFF: never written by the game in any run; the battle table has no area there.
Note for ticket 14: in the menu modes (4-8, 10) the same function gives the game a texture palette
area 0x2E00-0x3FFF, which includes the overlay's palette at 0x3C00. Not seen to clash yet.

Old savestates keep the heap size they were made with (0x12000); a battle entered after loading
them still gets the new size. Uploads now wait for a safe scanline (`ov_safe`), since bank B also
holds the map and unit textures.

Still open: the tutorial pop-up overlap was not reproduced (the first battle's script blocks Action
from `p_battle`); the "Forbidden" heading is not in the banner, so a law reads as a bare word ("Fire").

The gold mark follows whichever head the info screen enlarges: the acting unit normally, the
target in an attack forecast (it can be the last head). Look B enlarges that card wherever it is.
melonDS check (`shots/melon/t07_battle2.png`, battle entered fresh from the in-game save, so with
the smaller heap): text sharp, map and units drawn normally. Preview: `scripts/preview_turnorder.py`
→ http://localhost:8765/turnorder.html.

## Round 3 (2026-11-23): text limits measured, turn order rethought

**Text limits, settled from the game.** A battle has one objective, at most one law, at most one
privilege: the tutorial text says "the law" and "choose the privilege you will use", battles
without a Judge have no law, and the info screen and the battle menu's Law page each hold one
of each (this also answers the question in ticket 09). Widths measured by having the game draw
each text as the objective (`p30` state 30 presses into battle 2's scene, objective string at
0x021CF1D8 swapped before it is drawn; a message ends `c2 00 c1`): every law (71), every
privilege (58), the 45 longest objectives — `work/text-widths.tsv` (game text, kept out of git).
Longest: objective 208 px (46 characters), law 121 px (27 characters),
privilege 96 px (21 characters). With padding:
224 px and 256 px against 272 px beside the height tab, so the Deck banner is at most two rows.

**Turn order.** The user prefers A to B (B removed) but finds A's units off-centre and bland.
The info screen's pip strip (8x8 sprites at y 184, one per coming turn, palette 3 = ally,
4 = enemy; squares for the four shown units, diamonds for 16 more) is now read into `q_side`.
Sprites are uploaded whole (32x32) and drawn by their opaque box, centred. Looks
(`TURN_STYLE`): 1 = A unchanged; 3 = strip+ (side underline/tint, orange disc for the acting
unit, pips for turns 5-20); 4 = stage (bottom centre between the unit panel, which ends at x 124,
and the Help bar, 94 px from the right edge; side-coloured shadows, orange ground ring, pips on
the bottom edge; hidden while a game layout object or window covers it — `stage_check`; falls
back to 3 where the gap is under 91 px, i.e. 4:3). Quads that never overlap share a depth layer
(`hold_layer`). Research notes on Triangle Strategy, FFT (incl. Ivalice Chronicles), FFTA,
Tactics Ogre and Octopath are summarised on the preview page.
Preview: `scripts/preview_turnorder.py` → http://localhost:8765/turnorder.html. Blob is now
~22 KB of the 24 KB reserve.

## Round 4 (2026-11-23): stage chosen, finished

The user picked **stage** ("turn order here is fantastic"), asked that nothing be cut at the bottom,
and moved the banner's long-text handling to ticket 23 (one cell that rolls through its values).
- Each info-screen unit is two sprites: the 32x32 body and a 32x8 strip under it with the feet and
  the ground shadow (shape 1 size 1, same x and palette, 32 rows lower; 64 for the enlarged acting
  unit). Both are copied now (`feet[]`), into a 128x64 head texture, so `HUD_TEX_SIZE` is 8 KB and
  the battle heap 64 KB (ADR 0008 updated).
- The pip row starts with the acting unit's turn (as the user assumed) and shows 18 turns; it sits
  on top of the shadows' lower edge. The stage stands 3 px above the screen's last row: in melonDS
  the bottom row or two fall off the edge (the -3 vertical nudge), which had cut the pips.
- Looks A, B and strip+ are gone (`TURN_STYLE` removed). On 4:3, where the bottom gap is 38 px, the
  same units, ring and pips go in a dark strip at the top right under the banner.
- The blob grew past the ROM gap after the main program (22.4 KB): patch.py now also moves the
  small overlay files that follow it (FAT files 1, 2, …) to the end of the ROM as needed. Checked in
  melonDS: battle 2 entered from the in-game save loads and draws normally
  (`shots/melon/t07_stage.png`). Blob ~22.2 KB of the 24 KB RAM reserve.
Preview: http://localhost:8765/turnorder.html (`scripts/preview_turnorder.py`).

## Round 5 (2026-11-23): browsing with L/R, memory shared instead of reserved

- **L/R browsing** (superseded below: the turn order now holds still while browsing). In the game, L/R walks the turn order on the info screen: the browsed unit is
  enlarged with its turn number, up to three earlier units stand to its left, the pip strip scrolls
  so the browsed turn's pip stays at x 124, and the map cursor and unit panel jump to that unit
  (how the player tells identical-looking units apart). The turn order now reads up to 8 units,
  finds the browsed turn (the pip under the enlarged sprite's middle, `q_mark`), and shows turns
  1-4 while browsing turns 1-3, then one unit before the browsed one and two after it. The ring
  marks the browsed unit and its pip gets an orange outline; the pip row stays anchored at the
  current turn (first pip = acting unit). Units are evenly spaced (23 px).
- **Texture memory shared** (user: "make the right call"; ADR 0008 rewritten). The heap size is no
  longer patched. `tex_free()` walks the heap's free list each frame; the units' half (0x3E000)
  and the banner text's half (0x3F000) are used only while free. Tested by editing the free list:
  units step aside first, then the banner, and both come back when the space is freed.
- melonDS: `shots/melon/t07_stage.png` (landed on the wolves' turn: acting wolf on the ring, red pips).
- The code blob is 23.1 KB of the 24 KB RAM reserve (`BLOB_RESERVE`). Ticket 23 will need more:
  raise the reserve then (all states must be rebuilt, see docs/test-saves.md).
- Browsing goes up to turn 20 in the game.
- **Decision (user):** following the browse mixed up "who is selected" with "whose turn it is". The
  turn order now holds still while browsing: it is refreshed only when the info screen has settled
  on the acting unit (enlarged, leftmost, over the first pip — `browsing` in hud3d_draw; the slide
  between browse steps counts as browsing), otherwise the queue as last shown is kept (`held_*`)
  and nothing is uploaded. The game's map cursor and unit panel show the browsed unit. No pip
  outline any more: the first pip is always the acting unit's turn. Checked every browse step
  (turns 1-20 and back) and a real turn change.

## Round 6 (2026-11-23): browsing shown, separately from whose turn it is

User: "you change the turn order, but the bottom display doesn't reflect the selection". So both are
shown, as two different marks:
- **Whose turn:** slot 0 is always the acting unit, on the orange ring. While browsing, its picture
  stays in the texture (slot 0 is not re-uploaded: `up_from`); if the shared memory was taken
  meanwhile (`slot0_ok` = 0) the units are hidden until the next settled state.
- **Browsed unit:** a light-blue arrow (`CURSOR_COL`) bobbing over it, and its pip outlined in the
  same blue. Slots 1-3 show turns 2-4, or from turn 5 on the unit before the browsed one, the
  browsed one and the one after (clamped at turn 20, the last the info screen shows); a dotted
  gap after slot 0 marks skipped turns. Pitch 22 px + 3 px after slot 0.
- States read from the info screen: settled on the acting unit / settled on a browsed unit /
  moving. "Settled" needs the enlarged unit over its pip **and** every unit at the same place as
  last frame; uploads also wait until the sprite graphics are unchanged for two frames (the game
  swaps a sprite's graphics the frame after moving it, which gave a 2-frame half-drawn unit).
- A guest/AI unit's target and the attack forecast enlarge another unit on the info screen too;
  the arrow then points at it (the stage hides during the forecast anyway).
Checked every frame of the browse clip (R x6, L x6) and the turn-passing clip in
`preview/t07/turnorder.mp4`.
