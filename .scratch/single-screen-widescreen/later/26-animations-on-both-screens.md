# 26: Animations that use both screens

**What to build:** Some moments in the game (the Scions; not the Summoner's spells such as Ifrit: user, 2026-11-25) show their animation across both screens. With only the gameplay screen visible, half of it is lost, and widescreen may break it further. Find every such moment, show the user how each one looks with the mod today, and build the treatment the user picks.

**Blocked by:** every ticket in `issues/` (first batch), and 24 (summons and most such moments need a later save). Second batch: don't start it from "work on the next ticket" until the first batch is done, unless the user names it.

**Status:** done, approved by the user (2026-11-25): 2x kept. The design is in ADR 0014

- [x] A list of the moments that switch to both-screens mode, and how each was found: the 13 Scions, nothing else (Results)
- [x] Each one captured as the mod shows it today, plus both original screens (`shots/t26/ref`, `shots/t26/today`; the page shows before and now for two)
- [x] The user picks a treatment from the preview: option 3 in its Scion form, at 2x (user, 2026-11-25)
- [x] The treatment is built and checked in melonDS at Deck resolution, including how it looks when the animation ends and the battle comes back
- [x] Moments the mod can't fix are written down (Results: none left out; known limits listed)
- [x] Scion animations: whole two-screen picture on one screen; side areas from the game's own tiling textures, the same in every build

## What the code says (static reading, 2026-11-23; nothing checked at run time)

The game has a "3D on both screens" mode, the usual DS method: each frame it swaps which physical screen the 3D engine shows on (POWCNT1 bit 15) and captures the frame (DISPCAPCNT), so the other screen shows the last capture. Each screen gets new 3D every other frame (30 fps).

- `dual3d_start` 0x020F9778 switches it on (`dual3d_state` 0x02131BB8, +0x18 = 1) and starts a task (`dual3d_task` 0x020F8EDC). It is called from FUN_0202443c, which has 12 callers; not yet known which one is a summon
- `dual3d_frame` 0x020F94F8 runs each frame while it is on: +0x14 counts frames (odd/even picks the screen), +0x10 picks one of five variants
- Overlay 4 also writes POWCNT1 (4 places); not looked at

## Likely problems

- The emulator shows one physical screen, so it gets the gameplay view and the info view's captures in turns, or the 3D only every other frame. It may flicker or show half the animation
- Display capture works on the DS's 256x192 picture. In melonDS's high-resolution mode, captured frames may look blurrier than live ones, and with the widescreen squeeze the captured half may come out squeezed
- The mod's own SELECT screen swap uses the same swap bit

## Options to show the user

1. **Leave the mode on and live with it:** only if the captures show it already looks acceptable
2. **Follow the action:** while the mode is on, show whichever screen the animation is on (via the mod's existing screen swap)
3. **One taller view:** turn the mode off and draw the whole scene once per frame with a camera that sees both screens' views, scaled to fit the wide screen. No capture, 60 fps, sharp in melonDS. Most work, but likely the best look
4. **Director (user's idea, 2026-11-23):** during each animation, decide moment by moment which screen to show, like a camera operator cutting between two cameras. Option 2 is the simplest version of this. Questions to settle with the user:
   - **Who decides:** an automatic rule, a hand-made table per animation (animation id, then which screen from which frame on), or both: the rule by default, with the table overriding it where the rule picks badly. Both is the likely answer, since there are more animations than anyone wants to tune by hand
   - **The rule:** show the screen where the action is. Candidates: the 3D engine's polygon count for each screen's frame (register 0x04000604, read at the swap-buffers hook; whichever rises above its starting level has the effect), or which of the two cameras the effect's position is in
   - **No ping-pong:** a minimum hold before switching again (about half a second) so the picture doesn't flicker between screens
   - **How it switches:** a hard cut, or a quick slide up/down, since the top screen sits above the bottom one
   - **60 fps for the chosen screen:** once a screen is picked, the game could be made to draw only that camera every frame, with no capture. Sharp and smooth, but the game's own logic may count on the odd/even frames, so check that first
   - **Finding the animation id:** the caller of `dual3d_start` and the variant at `dual3d_state`+0x10 are the first places to look

## Scion animations (user, 2026-11-24)

The Scion animations take both screens as one tall picture. For these the user expects option 3 to go much further: zoom out a lot more than the normal view, so the whole two-screen picture fits on the one screen, and use AI to extend the background animation into the side areas this leaves.

- **How much zoom:** the two screens together are 256x384 DS pixels. To fit the Deck's 800 rows, that is about 2.1 screen pixels per DS pixel (the normal view is 3.5, ADR 0009), so the picture is about 533 of the 1280 columns wide. About 370 columns on each side need background that the game never drew. At exactly 2x (768 rows, a 16-row bar top and bottom) the pixels stay even; 2.08x fills the height but the pixels come out uneven. Show the user both
- **Turning off the alternating frames:** as in option 3, draw both cameras' views in one frame (or one camera that sees both), so the Scion is sharp and at 60 fps rather than built from low-resolution captures
- **AI background:** first find how the background animation is made. If it is moving or tiled textures, or colour cycling, extend the source texture or tiles once, so the animation still runs as the game drives it, rather than AI-extending every frame (slow, and the frames would not match each other, so it would shimmer). Extend frame by frame only where the background really is a sequence of different pictures
- **Publishing rule (changed by the user, 2026-11-25: AI-extended art made from the game's pictures need not stay private any more; it was not needed here):** AI-extended art is a private add-on only, never committed to the public repo or put in a published patch (ticket 12, `ffta2-publishing-rules`). Use the private add-on pipeline from ticket 24: `#ifdef` hooks in `hook.c`, data and tools in git-ignored `work/`, a private build via `patch.py --reserve`, LaMa outpainting in the sandbox (ticket 12 notes: 2x worked best for the map of Ivalice). The public build needs its own answer for the side areas without AI: the game's own background widened or mirrored, or plain dark sides
- **Texture memory:** Scion scenes are probably heavy on effects, and extended background art needs room. Check free space in these scenes first; ticket 25's guard should run on them
- **Finding them:** Scions appear in story battles, so ticket 24's late save (story progress at 0x0212D714) is the place to start. Each Scion animation gets its own capture in the preview

## How to find the moments

- Watch `dual3d_state`+0x18 (or writes to DISPCAPCNT) while replaying every state and the walks in `scripts/solo_menus.sh`; log the frame and the caller's return address
- To catch the rest during the user's playthrough, extend ticket 25's on-screen marker to light up when the mode starts, so the user can make a savestate there
- A Summoner's spells need a unit with the job; ticket 24's save should have one

## Results (2026-11-25)

**What uses both screens.** Only effects 0x152-0x15E: `effect_load` (0x020242F0) returns -1 for them, and `effect_play` starts the mode for -1 and for nothing else. They are `effect/magic/m338.efx` to `m350.efx`, with sound files `sumn_*` (names at 0x0211E4B4): Belias, Mateus, Shemhazai, Hashmal, Famfrit, Adrammelech, Cuchulainn, Zalera, Chaos, Zeromus, Exodus, Ultima, Zodiark; abilities 0x289-0x295. Overlay 4 (the other place that swaps screens) is the auction house; it never captures (ticket 28).

**How ticket 29 did it for cutscenes** (the user asked): no AI there either. The book scene's backdrop is a texture that tiles, so the game's own art was carried on. The AI route was only ever used for the map of Ivalice (tickets 24 and 36). The Scions' backgrounds turned out to be the same kind: in all 13, every quad that covers the old picture has a wrapping, unflipped texture or none (`scripts/scion_quads.py K` lists them).

**Playing one:** `scripts/play_scion.py K OUTDIR` (DeSmuME: Cure's ability record is swapped at lookup), `scripts/solo_scion.py K OUTDIR FRAMES` (the mod's exact picture), `scripts/melon_scion.sh K OUT.png` (real melonDS; `SCION=K` in `melon_state.py` pokes the record). Reference build: `patch.py --no-hooks` with the Deck preset (the 4:3 one hangs on these states). The animation is the Scion's own; the caster and the damage are Cure's, so the ordinary route (an accessory and the smash gauge) was not played.

**Faults of the old build** (all gone): half the creature, the halves not meeting, a 256x192 picture, the battlefield photograph too small, a black area on the right while the camera zooms out (the backdrop's zoomed width was not patched), banner and turn order on top of the fade.

**Checks.** All 13 in DeSmuME frame by frame: no one-frame flash, and the length is within 3 frames of the unmodified game (the first glow version ran Zodiark 244 frames long; the rings are kept cheap for that reason). melonDS at 1280x800: the finished build for Belias, Adrammelech, Exodus and Zodiark, the other nine on builds before the last fixes (glow speed, the glow's first frame, polygon ID). 16:9, 4:3 and 2.08x builds in DeSmuME. Guard clean (Belias, Zodiark). 96 menu captures: differences only from rebuilt states landing on other frames. `test_modpatch.py` and the release checks pass.

**Traps found.** The glow code writes BLDCNT and DISPCNT in mid-frame (a tear, and a flash when a glow starts); the game's polygon IDs go round 0x21-0x3F, so a translucent polygon of the mod's must use another; the sprite projection at 0x027E1274 is built once at boot, so states from a build with another view carry a stale one (the mist looked inset in the reference pictures for that reason).

**Limits.** The trails and the battlefield photograph stay at DS resolution. A Scion whose parts the game parks off the sides now shows them entering earlier. Not checked on the Deck itself or in a late battle with a big map (the zoom fits any map by construction, `camera_fit_map`).

**Test rig.** The blob is always padded to its reserve and `play.py` saves states only at frames where the CPU is outside the mod's code (`save_clean` in `emu.py`): states now survive changes to `hook.c`. All `s_*`, `late/*` and `battles/*` states rebuilt this way. Seen on the way: ticket 40.
