# 25: Guard on the video memory the mod borrows

**What to build:** A test-only check that reports when the game uses video memory the mod has borrowed for its own pictures. A clash late in the game should show up as a log line, or as a marker while the user plays, rather than as a broken banner or a corrupted game picture 30 hours in.

**Blocked by:** every ticket in `issues/` (the first batch: today 09, 11, 12, 13, 15, 17, 18, 19, 21, 27). Second batch: don't start it from "work on the next ticket" until the first batch is done, unless the user names it. It does not need ticket 24, but it becomes much more useful once 24's states exist.

**Status:** done (2026-11-24): guard, table, clash test, full run, and the in-play marker (a small red dot, the user's choice). Faults found: ticket 31

- [x] One command (for example `scripts/vram_guard.py STATE [SCRIPT]`) plays a state and reports every frame where the game writes to or draws from a borrowed range: frame, range, and the game's call site. Silent means clean
- [x] The borrowed ranges come from one table that the guard reads, kept next to the definitions in `src/hook.c` (or read from the built blob), so it stays right when addresses move
- [x] Shown to catch a clash on purpose, for example a test build that puts the banner texture where the game keeps a picture
- [x] Run over every current state in `states/` and the walks in `scripts/solo_menus.sh`; results written here
- [x] A patch option for playing (`patch.py --guard`, never in published patches) that shows a small on-screen marker when a clash is detected, so the user can make a savestate there and report it. Decide with the user how it looks
- [x] The comments in `hook.c` and ADRs 0005 and 0008 that say a region is unused say how that was checked

## What the mod borrows (from `src/hook.c`, 2026-11-23; check it again before starting)

- Texture bank B, top `HUD_TEX_SIZE` (0x2000): banner and turn-order texture. Shared with the game's battle texture heap (ADR 0008). The mod checks the heap's free list before writing, so in battle this is guarded already; outside battle it isn't
- Texture palette from 0x3A00: banner and turn-order palettes
- Texture bank A, 0x14000 to 0x1FFFF: the info screen overlay texture (ADR 0005). Its old contents are parked in the main BG bank while the overlay is up
- Main BG bank: 0x06001000 (48 KB backup), plus scratch tables at 0x0600D200 and 0x0600D600
- Texture palette from 0x3C00, 256 entries: overlay palette

The heap start was moved to make room for the mod's code (ADR 0001), so main RAM is safe by construction and not part of this ticket.

## Hints

- Textures are often copied by DMA while a bank is mapped for the CPU, so a CPU write watch (`memory.register_write`) may miss them. The more reliable check is what gets drawn: `scripts/gxtrace.py` already records every polygon and its call site, so flag any polygon not from the mod whose texture or palette address falls in a borrowed range. Do the same for main-engine BG and sprite layers whose tile or map base points into the parked range while the overlay is up (`scripts/vidregs.py`).
- For the in-play marker, the mod can fill a region with a known pattern while it doesn't need it and check the pattern each frame; a change means the game wrote there.

## Result (2026-11-24)

**The guard:** `scripts/vram_guard.py STATE [SCRIPT] [-v]`. It plays a state (play.py steps) and prints a line for each new clash: frame, kind, borrowed tag, bank and offset, and the call site. Repeats are summed at the end. Silent means clean, and the exit status is 1 when anything was reported. `-v` adds the table, the `s<name>` marks and counts of what was seen (game and mod draws and writes, and the most bytes the mod held at once), so you can tell "clean" from "saw nothing".

How it works (details in the script's docstring):
- **Ranges:** `borrowed_vram[]` at the end of `src/hook.c`, after a "BORR" marker, written with the same defines the code uses. The guard reads it from the ROM's blob, so a moved or added range (the private map art adds `MAPA`) is followed without editing the guard.
- **Ownership:** for every borrowed byte, the guard keeps what the game last wrote there and what the mod last wrote there. A draw is a clash when the bytes it reads differ from the reader's own copy. That treats ADR 0008's sharing (the game takes the memory back and the mod stops using it) and the overlay's put-back (the mod writes the game's bytes back) as correct.
- **Writes:** the emulator's write watch on each bank's LCDC window and on main BG space, told apart by program counter (the blob's range = the mod). Check: entering battle 2 changed 41,571 bytes of bank B and the watch saw every one of them. The game uploads with a CPU copy loop (0x01FF84B8), not DMA, so nothing is missed.
- **Draws:** 3D commands from direct port writes, the FIFO and the game's DMA lists (as `gxtrace.py`). Each triangle or quad is followed through the projection, position and texture matrices: off-screen ones count as no draw, and texture rows are narrowed to the ones the polygon samples. Main-engine BG layers (text, affine, extended, bitmap) are checked over their map and the tiles it uses. A layer alpha-blended at weight 0 counts as not shown.
- **Reading banks:** a bank is mapped to the CPU for a moment between frames, then mapped back, so the game never sees it.
- **Cost:** about 20 frames a second. `scripts/vram_guard_all.sh` runs every state (57, 20 s of play each, SELECT tapped and held, 12 at a time, about 5 min) and then the walks in `scripts/solo_menus.sh` (`GUARD=1` mode, about 3.5 min).

**Clash shown on purpose:** `OV_TEX` is now overridable at build time. `patch.py ... --define OV_TEX=0` puts the overlay texture over the shop's 256x256 textures at bank A 0. On `states/s_shop.dst` with SELECT tapped, the guard reports GAME-DRAW from call sites 0x0208CC18 and 0x01FF8628 for every frame the overlay is up. The normal build is silent on the same steps.

**Results of the full run:** the banner, turn order and screen swap are clean in every battle state, and every menu walk is clean. The overlay clashes in four groups of scenes, each confirmed with a picture taken with and without the overlay. Ticket 31 has the details and the options:
1. Story and after-battle dialogue scenes (`intro2`, `t_fall`, `t_prefall`, `s_results`): the game's BG1/BG3 show the overlay's parked copy in BG bank E, and the screen fills with garbage.
2. Late-game pub menus and one opening scene: the pub's texture sheet uses rows inside the overlay texture, giving a band of garbage at the lower right.
3. Title: black for 6 frames as the overlay opens.
4. World map: one tiny quad for 1-2 frames.

Guard bugs found and fixed on the way (false alarms, kept here so nobody brings them back): taking one row span over every polygon of a texture sheet; ignoring the texture matrix (texture-coordinate transform mode 1); counting polygons the mod had pushed off screen; treating a polygon's last texture coordinate as a sampled row; counting palette entry 0 of textures where colour 0 is transparent; checking the mod's draws against palette entries it never filled.

**Comments and ADRs:** ADR 0005 and the overlay comment in `hook.c` now say what was checked and what turned out to be wrong ("the menus do not reference" holds for the early menus only). ADR 0008 and the banner comment say the guard found no clash in any battle state.

**Still open: the in-play marker** (`patch.py --guard`). Not built: the ticket says to decide the look with the user. The plan: in a `--guard` build, the mod fills the parts of its borrowed ranges it is not using with a known pattern, checks it each frame, and shows a small marker when the pattern changes, until the user dismisses it.

## In-play marker (2026-11-24, user: "small dot in a corner")

`patch.py ... --guard` builds a test ROM (never published: `make_release.py` refuses any build containing the "GUARD BUILD" string). While the overlay is up, the mod checks:
1. Before rewriting each band of the overlay texture, that the band still holds what the mod last wrote there (the game wrote into it).
2. One 2 KB slice per frame of the parked copy of bank A, and all of it before it is put back (the game wrote into it).
3. Whether any shown main BG layer reaches the parked copy, through its map, the highest tile it uses, or its bitmap; a layer alpha-blended at weight 0 counts as not shown.

A hit lights a 5x5 red dot in the top-left corner (game pixels 0..5, 2..7, in front of everything) for 10 s. It also writes `guard_info` (after a "GURD" marker): hits, kinds, and first and last frame. `scripts/guard_report.py STATE` reads that record from a melonDS savestate (.ml1) directly, or from a DeSmuME one by playing it. Not seen in play: the game drawing 3D from the borrowed texture (the late pub); `scripts/vram_guard.py` finds that one.

Checked:
- Normal guard build, overlay opened and closed, Item Info up (party, shop, world map, late shop, bazaar, pub, auction) and battle 2: "no clash recorded".
- Test build `--guard --define OV_ANYWHERE=1` (overlay allowed everywhere), overlay opened at frame 120: `intro2` and `t_fall` record kinds 2 and 4 from frame 126, `s_results` kind 4, and `p_story_0` nothing. That is the same as the PC guard's findings.
- How the dot looks: `--define GUARD_DOT_TEST=1` keeps it lit. melonDS captures of battle 1 and the opening story scene are pictures 8 and 9 at http://localhost:8765/guard.html. In battle the dot just touches the top of the "h" on the game's height tab.

Blob: 29,360 bytes with `--guard` and 27,484 without, of 32,768. The normal build carries none of the guard code.
