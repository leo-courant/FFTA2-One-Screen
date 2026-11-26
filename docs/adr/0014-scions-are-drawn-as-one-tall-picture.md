# A Scion's animation is drawn once a frame as one tall picture

The 13 Scions are the only thing in the game drawn on both screens at once. The game draws the scene twice, in turns: even frames with the top screen's camera, odd frames with the bottom screen's. Each frame goes through a display capture (12/16 of the new picture plus 8/16 of the last capture, which makes the trails and the glow), and the other screen shows the last capture. On one screen that showed half the creature, at 256x192.

The two cameras are exactly one screen apart, so together they are one 256x384 picture. The mod keeps the game on the even camera (which has its own stored sprite projection, used by nothing else), widens that projection to take in both screens and the side areas, and shows every frame on the gameplay screen (`dual_frame`, `dual_projection` in `src/hook.c`). The view is set by the display preset at the largest half-step scale that fits: 640x400 at 2x on the Deck, 768x432 at 2.5x for 16:9, 512x384 for 4:3 (`patch.py --tall WxH` overrides it).

**Sides.** Every full-screen layer in all 13 (mist, flames, lightning, rain, streaks, flashes) is a quad whose texture the game made to tile, or no texture at all. The quad is enlarged and its texture carried on (`tall_widen`). Nothing had to be made by AI.

**Trails.** Captures are DS resolution in melonDS however sharply it draws 3D. So the live 3D is shown itself, and the last capture is laid over it as a 2D bitmap (BG2) with the game's own two weights: the same sum, with the new part sharp. The captures are of that finished picture, taken in turns into banks C and D 30 times a second, as the game does, so the trails last as long. We considered keeping the game's captured picture (exact, but every pixel 5x4 screen pixels) and dropping the trails (sharp, but a third darker).

**Glow.** Six Scions add a round glow on 2D layer BG3. It needs the one weighted sum the 2D hardware can do, and 2D is not part of the tall view, so it is drawn as translucent 3D rings in the bitmap's own colours. They are translucent where the original adds light, so very bright spots clip a little less.

**Battlefield photograph.** The game zooms out until the whole map fits the 4:3 screen, fades to black and photographs it. The squeeze is off while the screen is black, so the photograph is the game's own.

## Consequences

- All three presets show the Scions this way, the 4:3 one included: a single screen would otherwise show half.
- The other physical screen is blank meanwhile.
- The photograph and the trails stay at DS resolution; the creature and backgrounds are as sharp as the emulator's 3D.
- The mod reads BLDY (0x04000054), which real hardware does not return. melonDS and DeSmuME do; an emulator that does not would show the battlefield smaller and lose the closing white-out.
- The code blob is now always padded to its full reserve, so where the mod's data and the game's overlays sit no longer changes between builds.
