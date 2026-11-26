# Widescreen by squeezing the 3D projection, which ties the mod to melonDS

A DS game can only output 256x192, so widescreen is done by scaling the game's orthographic projection (every one goes through a single SDK routine) so the 3D picture is squeezed horizontally, and relying on the emulator to render 3D at several times DS resolution and stretch the screen to 16:10. This makes melonDS with its OpenGL renderer and aspect-ratio setting a requirement; on anything rendering at DS resolution the picture is visibly soft, because one column in six is lost. We accepted that because the target is a Steam Deck OLED, not DS hardware. If melonDS cannot produce a sharp result, widescreen is dropped and the mod ships as a sharp 4:3 picture with the banner (decided with the user on 2026-11-22).

## Consequences

- Anything drawn on the DS's 2D layers (the current banner, the whole info screen) is stretched about 20% wider and cannot gain resolution; HUD that must stay crisp has to be drawn through the 3D path.
- The game only draws map and backdrop inside the original 4:3 view, so the side areas need their own fixes.
