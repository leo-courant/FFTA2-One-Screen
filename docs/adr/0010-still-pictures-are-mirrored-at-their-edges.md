# Full-screen still pictures are mirrored at their edges into the side areas

A full-screen still picture (the title screen's background) is exactly 256x192: the game has no more of it to show. In widescreen the mod draws it at its true size in the middle and fills the side areas and the bands above and below with the same picture mirrored at its edge: eight extra quads around the game's own one, sampling the game's texture with texture coordinates running backwards. Everything is computed from the player's ROM while the game runs, so the published patches stay free of game data (the publishing rules, ticket 21). Stretching the picture (what the world-map frame does) distorts it and was rejected; repeating it shows a hard seam; AI outpainting may exist only as a private add-on and never in a published patch (ticket 12).

## Consequences

- The quads are added at the END_VTXS of the layout piece's quad (0x020B0B4C), so they share its texture, palette, vertex colour and matrix, and fade with it.
- A piece is treated as a still only when it is the one piece of a screen-sized layout object, covers 0..256 x 0..192, and is drawn one texel per pixel unflipped. A screen-sized object made of several pieces (the world-map frame) keeps its stretched bars.
- The mirror seams are visible as symmetry on close look; on ornamental art like the title they read as part of the design. Whether a later still (story illustrations, if any) looks right this way has to be judged when one turns up (late-game saves, ticket 24).
- The 4:3 preset draws nothing extra.
