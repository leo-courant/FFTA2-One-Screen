# The Steam Deck preset shows 366x228 game pixels at 3.5x, accepting uneven pixels

The Deck preset's view is 366x228 game pixels: 3.5 screen pixels per game pixel at 1280x800, showing about 14% more of the scene across and down than the 320x200 of ADR 0004. On a 1280-pixel-wide display, 4x is the only zoom between the game's own view and 2x where every game pixel gets the same number of screen pixels, so this view gives up the even pixels ADR 0004 was made for: game pixels alternate 3 and 4 screen pixels wide and tall. The user compared 4x, 3.5x and 3x at real Deck size, including enlarged melonDS spots where 3.5x is uneven (letters of one width drawn 3 or 4 pixels wide, outlines alternating thick and thin), and chose 3.5x for the extra room (2026-11-23, ticket 08).

## Consequences

- Measured in melonDS (OpenGL 8x, Wood Village): 77% of pixel edges across and 53% down sit on the best-fitting 3.5-pixel grid, against 98% / 82% at 4x. The nudge of ADR 0004 (+3, -3) is still the best of those tried.
- The even 4x view remains one option away: `patch.py --view 320x200`.
- The fast test captures (`scripts/solo.py`) enlarge the view to 1280x800 with nearest-neighbour by default, which shows the same 3-and-4 pattern as the emulator.
