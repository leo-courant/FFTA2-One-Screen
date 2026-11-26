# 19: Tap SELECT for the info screen, hold it for the banner

**What to build:** Every mod control is on one button. A tap of SELECT shows the info screen (detailed view in battle, overlay in menus) and a hold of about half a second switches the banner on or off. L+SELECT is gone. The game's soft reset (L+R+START+SELECT) still works. ADR 0006.

**Blocked by:** None (can start immediately). Touches the same key-handling code as other hook work, so merge with care if another ticket is in progress.

**Status:** closed by the user (2026-11-25). Built 2026-11-23, checked with `scripts/check_select.py`; no try on the Deck has been reported

- [x] Tap SELECT opens and closes the detailed view in battle and the overlay in menus, as before
- [x] Holding SELECT switches the banner and does not also open the info screen
- [x] The overlay's existing behaviour (D-pad keeps it, A/B/X/Y/START close it) is unchanged
- [x] L+R+START+SELECT still resets the game
- [x] The hold length is one tunable value

## Built (2026-11-23)

- `frame_hook` counts the frames SELECT is down (`sel_frames`; the hook runs once per 60 Hz frame, measured in battle, party, shop and world map states). At `HOLD_FRAMES` (30 = half a second) the banner switches at once, while still held, so the player sees it happen; letting go after that does nothing. Letting go earlier is a tap: overlay outside battle, screen swap in battle, as before.
- Any other button held with SELECT (or a D-pad press during the hold) spoils the press: neither the tap nor the hold fires. This keeps the soft reset clean and makes slips harmless. The start of a press is taken from the held bits, not the game's "pressed" bits, so key repeat cannot restart the count.
- The game's soft reset (`soft_reset_combo` 0x0201ED70) needs held == exactly L+R+START+SELECT for 10 checks in a row; the mod never changes the key words, so it is untouched. Verified: held 1 s in battle 2 and in the party menu, the game goes back to the boot logos. (Held for only 10 frames it did not fire in the test; a real press lasts longer.)
- L+SELECT is gone; `KEY_L` is no longer used.
- `scripts/check_select.py STATE basic|peek|combo|reset` reruns all the checks (one case per process). Results on s_party, s_shop and s_battle2: tap toggles overlay / swap on release; 40-frame hold toggles the banner at frame 30 with no overlay or swap; 25-frame hold is a tap; D-pad keeps the overlay, A and B close it; L/R/A/DOWN with SELECT do nothing. `solo.py` capture confirms a hold hides banner + turn order and a second hold brings them back.
- Not checked in melonDS (input logic only, nothing drawn differently).
