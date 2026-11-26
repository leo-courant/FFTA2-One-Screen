# Auctions are laid out again on one screen

While bids are placed the game swaps its screens: the 3D engine draws the bidding field on the info screen, and the gameplay screen gets the 2D token list. The bids are timed, so showing one screen at a time, as SELECT does, is no answer.

The mod keeps the field on the gameplay screen and puts the token list's contents around it. The user picked this layout from three (ticket 28): the field at its own size in the top left corner; each clan's name and token counts beside its lane, since the list is in the order of the lanes; the buttons in the game's own cross below them; the round and Retire in a strip under the field. Nothing is scaled, and nothing is left out.

**Keeping the field.** Overlay 4 makes the swap with bit 15 of POWCNT1, from four places that read the register's address from a literal word each. Once per frame the mod checks those words; when they hold the register's address it makes three of them point at two spare bytes of the overlay (after its last string), which then say whether bidding is on. Being inside the overlay, they survive a savestate whatever build runs next, and go away with the overlay. The fourth place is the Retire question, which takes the bit only while it is up, so it gets a word of its own and the layout stays. No game file is changed.

**The panel.** The overlay's compositor (ADR 0005) redraws the list into a texture, and quads cut from it. Its fills are texels of the list as well, since melonDS shows a plain colour a shade lighter than the same colour in a texture. The list's only sprites are the frames of the first auction's help, so sprites are left out and a frame is drawn around the same part of the panel.

**The field.** One shift of the HUD projection moves everything on it, exactly a corner to a corner: a unit off eats into the nudge (ticket 08) and shows as hairlines. The mod's rules for panels and frames are off during bidding. Titles and bands that run past the field's right edge go behind the panel.

**Cost.** Bands of the texture that did not change are not written again. Writing every frame halved melonDS's speed (87 frames a second on the development machine with the rig uncapped at 240, against 160-198 for the build before); with unchanged bands skipped and two bands a frame it is 138-160, three runs each. The game itself drops no frames either way. Skipping unchanged bands applies to the SELECT overlay too.

**Other displays.** 16:9 is lower, so the buttons are in a flatter cross and the round's two lines share one. 4:3 has no room beside the field: it keeps the field on the gameplay screen, and SELECT lays the list over it.
