# The map of Ivalice's edges are AI-extended art, shipped in the release

The map of Ivalice is one 408x300 picture that fades into sea at its left and right ends; beyond it the game stretches an 8x8 patch of sea. The 4:3 view never gets there, but the wide view does: up to 40 texels left of the picture, 20 right of it (16:9; 15 on the Deck) and 2 below it, never above it, over all 22 areas (`scripts/map_reach.py`; pans move between those resting positions). Mirroring the edge left a symmetric dark seam, and sliding the map left its sprites (quest markers, the clan's figure) behind (ticket 24).

The bands are filled with the game's picture extended by LaMa (an image inpainting model), brought back to the map's 16 colours. Since 2026-11-25 the user's publishing rules allow AI art derived from the game's pictures in public releases (ticket 26); in ticket 36 they chose this over trying the game's own data again. It was a private add-on until then (ticket 24).

**Making the art** (maintainer only; the art stays in `work/`, like all game-derived data): `map_art_dump.py` takes the picture from a test state on the map, `map_art_outpaint.py` extends it (LaMa big-lama on the CPU, the picture enlarged 2x: 1x gave blotchy parchment, 4x a flat sea; needs torch, in a separate virtualenv), `map_art_tear.py` puts the left side of one run together with the right side of another and tears the right side into sea, as LaMa's left side looks (the user's review: a torn edge is acceptable, a continuation that does not follow the lines is not), `map_art_pack.py` cuts the pieces listed in `src/map_art.c` into a 256x128 16-colour texture and compresses it (LZ as the DS BIOS has it, 16 KB to 5768 bytes) into `work/map_art/map_art.lz`. `patch.py` builds it in when that file is there and the view is wide.

**In the game** (`src/map_art.c`): the texture is unpacked once into the variables (ADR 0017), the first time the map is shown (about 80 scanlines, once a boot). While the map is on screen it is copied to texture memory 0x26000-0x29FFF, the unused lower part of a texture the map screen does not draw from (checked empty for all 22 areas; `MAPA` in `borrowed_vram`), at a safe moment (`ov_safe`). After the game draws the map's main piece, each piece is drawn as a quad in the same coordinates, so it pans and zooms with the map, a hair nearer than the map (at equal depth the art would lose where it overlaps the picture). The side pieces also cover the picture's own fade: 8 texels on the left, 16 on the right. The art is only uploaded once the map's picture has been drawn: after a boot or a state load the frame counter is near 0, and the texture memory belongs to whatever screen is up.

## Considered

- **The game's own data** (a strip of sea texels from inside the picture, a larger map, a dark vignette): not tried; the user preferred the art they had seen in the private build.
- **A larger reserve for the raw 16 KB texture** (the private build's 48 KB): moves the game's files in the ROM and makes every test savestate unusable. Compressing the art and moving the variables out of the blob (ADR 0017) made it fit in the 32 KB.

## Consequences

- The patches carry about 5 KB of art derived from the game's picture. It is compressed and repainted, so the release check for game bytes passes, but that check does not look for derived art; the user's rule is what allows it.
- Someone building from the repository without the art gets the game's sea at the edges (patch.py says so); `--no-map-art` builds without it on purpose.
- The left side was outpainted with another of the game's palettes (0x3E20 instead of 0x34E0, the one the map uses; ticket 36); it is stored as colour indices and drawn with the map's own palette, and the user accepted it. The right side was made again with the right palette (`map_art_outpaint.py ... 2 16`). Making the whole art again gives a different left side.
- The blob is nearly full again (Deck 32712 of 32768): the next feature has to make room first.
- 4:3 builds leave the art out.
