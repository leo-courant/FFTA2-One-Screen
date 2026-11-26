# The widescreen view is 320x200 game pixels so every pixel is exactly 4x4 on the Deck

At a 16:10 view of 307x192 game pixels, each game pixel came out 4.17 screen pixels wide on the Steam Deck's 1280x800 display, so the emulator drew them as an uneven mix of 3, 4 and 5 pixels and portraits looked warped. The view is therefore zoomed out slightly to 320x200, which is exactly 4 screen pixels per game pixel in both directions. Because the emulator samples the picture exactly on the boundary between pixels, the image is also nudged by a fraction of a screen pixel (found by measurement in melonDS 1.1 with the OpenGL renderer at 8x: +3 horizontal, -3 vertical projection units); without the nudge about half of all pixel edges land one pixel early.

## Consequences

- The numbers are tied to a 1280x800 display and to melonDS's sampling. Another resolution or emulator needs its own view size and nudge.
- The view gains 4 game pixels top and bottom as well as 32 each side, so panels are anchored vertically too.

**Superseded for the Deck preset by ADR 0009 (2026-11-23):** the user chose a 366x228 view at 3.5x for more room, accepting uneven pixels. The reasoning here still holds for presets that can be even, and 320x200 is available as `--view 320x200`.
