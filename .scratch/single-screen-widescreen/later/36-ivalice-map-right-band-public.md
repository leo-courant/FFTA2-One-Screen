# 36: Map of Ivalice: the band on the far right (public build)

**What to build:** On the map of Ivalice the map picture stops short of the right edge of the wide screen: a band at the far right shows the map graphics ending (the user, ticket 24 review 2, 2026-11-24, again in this review). Find a way to fill it in the public build.

**Blocked by:** None. Second batch.

**Status:** done, approved by the user (2026-11-26) after one review round. Preview: http://localhost:8765/ivalice.html (`scripts/preview_ivalice.py`). Design in ADR 0018 (the art) and ADR 0017 (the room for it)

**Rule changed (user, 2026-11-25, ticket 26):** enlarged or extended art made by AI from the game's pictures no longer has to stay in the private build. The private build's LaMa map can therefore be considered for the public one; ask the user first, and note that `make_release.py` checks files for game bytes, not for derived art.

- [x] A way to fill the band that the user approves: the private build's LaMa art, in the public build (user's choice, 2026-11-26, over trying the game's own data), right side torn like the left after review 1; approved 2026-11-26
- [x] Holds for all 22 areas the view can reach, on every preset (Deck and 16:9 measured at every area's resting view; 4:3 never sees past the picture and leaves the art out)

## Done (2026-11-26)

- **Room without moving the game's files.** The blob was full and the raw art is 16 KB; the private build's bigger reserve (48 KB) moves the game's files in the ROM, which makes every test state unusable. Instead: the mod's variables (6.4 KB of zeros) now live after the blob, in RAM the game never uses (ADR 0017), and the art is compressed (LZ, the DS BIOS's format: 16384 to 4864 bytes) and unpacked once into the variables. Deck blob 32256 of 32768 (512 bytes left), variables 22796 of 32768. The packed texture is byte-identical to the private build's. Pictures from five states are pixel-identical before and after moving the variables.
- **Free RAM, measured.** `scripts/heap_free.py` finds the game's ten NNS expanded heaps: at fixed addresses from 0x0215B000 in the unmodified game, the public build and the private build alike. 0x02143E20-0x0215B000 stayed zero in every state checked (one stray word in `s_shop.dst`, the state already known to be odd; at 0x0214CE18, not looked into).
- **Reach.** `scripts/map_reach.py` maps the view's corners into the picture's texels over all areas (L/R cycle them on that map). Deck: 40 left, 15 right, 2 below, never above (ticket 24's figures). 16:9: 40 left, 20 right, 2 below, never above. The art covers 48, 24 and 4. Sampling mid-pan gave readings of up to 49 below, 92 left and 195 above, but the saved pictures of those frames show the map at rest: gxtrace misreads the map's transform on some frames, not always with a wrong view size. Pans move between resting positions, so the resting figures stand. A top strip added for an early "3 above" reading on 16:9 (also a misread) was taken out again.
- **The art in the repo.** `scripts/map_art_dump.py`, `map_art_outpaint.py`, `map_art_pack.py` replace the private `work/t24/aitools/` (whose `build_private.sh` no longer builds: its `map_art.c` moved to `src/`). The art stays in `work/map_art/` (git-ignored); `patch.py` builds it in when it is there, `make_release.py` refuses without it. `src/map_art.c` holds the piece table the packer reads. Strip layout of the picture's bottom 44 rows found by gxtrace: picture x 0, 104, 206, 310 from texture (408, 0), (408, 44), (408, 104), (408, 148).
- **Palette slip (no change to the art).** The private art was outpainted with the colours of palette 0x3E20; the map binds 0x34E0 (gxtrace `pltt` 0x34E). The texels were right and the art is stored as the map's 16 colour indices, so the game shows what the user approved; `map_art_dump.py` now reads 0x34E0, so making the art again gives slightly different art.
- **Checks.** melonDS at 1280x800 and 1920x1080 from the new state `states/m_ivalice.ml1` (Camoa and the far west): the art reaches the screen edges as in the test emulator. `vram_guard.py` silent over all 22 areas. The one-time unpack costs about 80 scanlines on the first frame the map shows; the upload keeps to `ov_safe`'s window (lines 217-239). `make_release.py` (into a scratch folder): no game bytes in any patch or the patcher; patches grow by about 6 KB (Deck 32761 bytes, 16:9 31439). `test_modpatch.py` passes after `make_patcher.py`. `dist/release` was not rebuilt.
- **Not from this ticket:** `audit_repo.py --tree` flags three files with game file paths (`issues/29-...md`, `docs/symbols.tsv`, `scripts/event_scripts.py`); they were already in the last commit. To clear before publishing.

## What is known (ticket 24)

- The band is the game's own: its map picture (408 texels wide) fades into sea at its right side, and beyond it the game stretches an 8x8 patch of sea. The 4:3 view never gets there.
- Tried and rejected: mirroring the edge (the fade makes a symmetric dark seam) and sliding the map so the view stays inside the picture (quest markers and the clan's figure are sprites with baked positions and stay behind).
- The private build (`work/t24/aitools/build_private.sh`, `MAP_ART=1`) fills it with LaMa-extended art; that stays private.
- Ideas not yet tried: draw the map a little larger so the view never reaches the fade (then the sprites would need moving, as in `sprite_fix`); repeat a strip of sea texels taken from inside the picture rather than the 8x8 patch; or a darker vignette that makes the end look intended. Show the user pictures before building.

## Review 1 (2026-11-26)

The user: the right side looks weird, it does not follow the lines or the colours; the left side is better because it looks torn, which is acceptable.

- **Right side redone, torn like the left.** LaMa run again with the map's real palette (0x34E0; the first art had 0x3E20) and repainting the picture's last 16 texels on the right (`map_art_outpaint.py ... 2 16`: the game's fade starts about 13 texels from the end, not 8). That continuation is torn into flat sea (colour 1, the left side's) along a ragged edge around picture x 412 with loose specks (`scripts/map_art_tear.py`, which also takes the left side from the first art, unchanged). The right pieces now start at x 392 (40 texels; bottom strips 64 wide to make room in the texture). An untorn continuation (option A) was tried too: no torn edge, and it does not fit in the blob (6664 bytes packed).
- **Fault found: the art lost the depth test where it overlaps the picture.** The pieces were drawn at the map's own depth, and an equal depth loses, so the game's faded end showed through as a dark column above row 256 (below it the art overlaps the game's bottom strips and won). Part of what looked wrong on the right. Now drawn a hair nearer (`MAP_ART_Z`, vertex z 16).
- **Fault found: the art was uploaded into another screen's textures after a boot or state load.** `frame_no` starts near 0, so "map seen at frame 0" looked recent and the art was written into texture memory the world map was drawing from (garbage bottom right of the Targ Wood map in `s_worldmap.dst`; also in the build committed before this review). Now 0 means never seen. The world map is identical to the build before ticket 36 again; `vram_guard.py` flags the old build on `s_worldmap` and is silent on the new one (also on `l_worldmap`, `l_camoa`).
- **Room:** art 5768 bytes packed. `map_art_quad` is Thumb now (its two divisions go through `sdiv`), and so are `stage_check`, `shape` and `pip`: Deck blob 32712 of 32768 (56 bytes left), 16:9 31408. Battle, menu and world-map pictures identical to before (`s_battle2`, `b20`, `s_party`, `s_worldmap`).
- `patch.py --map-art FILE` builds other art (for trying looks); the art's checksum is now part of the compile, since zig's cache did not see an `.incbin`'d file change and kept the old art.
- Previous art kept as `work/map_art/map_ext_v1.png`, `map_art_v1.lz`.
