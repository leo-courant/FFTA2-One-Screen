# 34: Button hints: a second copy of the text pokes out under the frame

**What to build:** On the yellow button-hint bars at the bottom of the screen (Help and Remove Equipment in Change Equipment, Place Unit and Swap Units at unit placement, the sort hint in the clan's quest list, and others) the label looks written twice: a dark copy a little lower than the text, whose bottom row sticks out under the yellow frame. The user noticed it in the ticket 24 review (2026-11-24, pictures from `preview/menus.html`). Find out where it comes from, and make the labels sit cleanly inside their frames if the user wants that.

**Blocked by:** None. Second batch (found in ticket 24's review).

**Status:** done, approved by the user (2026-11-25, asked for in the ticket 40 review). Preview: http://localhost:8765/ending.html keys 6 and 7 (0 = before)

- [x] Checked on the unmodified game, cold-booted (ticket 02's method: `build/ffta2-ref.nds` from `patch.py --display 4x3 --no-hooks`, inputs replayed from boot), and in melonDS at Deck size
- [x] If it is the game's own: shown to the user, who decides whether the mod should clip or move it
- [ ] (not the mod's) If it is the mod's: fixed, and the menu captures are otherwise unchanged

## Findings so far

- The same lower copy is in the widescreen-off capture (`PLAIN=1`, `shots/menus/equip.png`, bottom right) and in `s_equip.dst` run on the no-hooks build. That state still carries the mod's code in RAM, so it is not proof, but it points at the game's own text shadow: a dark 1-pixel drop shadow under each letter, and the label sits on the bar's bottom edge, so the shadow's last row falls below the frame.
- At 3.5x on the Deck the shadow row is 3-4 screen pixels tall, much more visible than on a DS.

## Built (2026-11-25)

**What it is:** the game's own. It draws these labels twice (glyphs_draw 0x0204CDF4, flag bit 0 at +0x20): a copy at (+1,+1) behind the letter, same colours, as a drop shadow. The untouched ROM cold-booted to battle 1 in DeSmuME looks the same as our pictures. Two things made it look wrong:
- DeSmuME (all our previews) rounds the two copies differently because the text sits on half-pixels, so the copy lands 2 rows down and its light pixels show under the letters and inside the H.
- In melonDS the copy lands right, but leaves slivers of light pixels around the letters, and its last row sticks out under the frame.

**Change:** the second copy is not drawn (`label_stub`, hooks at 0x0204CF84 and 0x0204D19C), on widescreen presets only; 4:3 stays as the game has it (ticket 02). Exempt: labels whose layout object sits above row 64, i.e. the world map's place name, which has no frame and needs the heavier outline.

**Checks:** melonDS before/after on battle 2's command menu (clean, inside the frames); all 96 catalogue pictures: the hint labels changed, the rest is animation phase; the place name unchanged; 4:3 unchanged. Blob: 32716 of 32768 (16:9: 32740).
