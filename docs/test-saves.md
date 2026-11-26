# Test saves

Savestates and one in-game save for checking screens beyond the tutorial battle.
All of them are game data and are not in git; rebuild them with one command.

## Rebuild

States hold the game's memory, including where its heap starts, so they must all be rebuilt
whenever `BLOB_RESERVE` in `scripts/patch.py` changes (last time: 0x8000, 2026-11-23, ticket 23), starting
with `p_battle.dst` on the patched ROM.

```
scripts/to_battle.sh build/ffta2-1screen.nds shots/boot states/p_battle.dst   # only if p_battle.dst is missing or the reserve changed, ~3 min
scripts/to_saves.sh                                                 # ~4 min
.venv/bin/python scripts/preview_saves.py                           # preview/index.html, both screens per state
```

`to_saves.sh` replays fixed inputs in headless DeSmuME from `states/p_battle.dst`
(first battle, command menu) on `build/ffta2-1screen.nds`, re-injecting the mod's code
from that ROM after every load (or from `BLOB=` if set). The inputs are listed, with comments, in the script.

| File | Situation |
| --- | --- |
| `states/s_worldmap.dst` | World map, standing on Wood Village; clan named, quest "A Paw Full of Feathers" accepted |
| `states/s_shop.dst` | Wood Village shop, Buy list (item stats on the info screen) |
| `states/s_party.dst` | Main Menu > Unit Info, the party list (unit sheet on the info screen) |
| `states/s_equip.dst` | Change Equipment for the first unit |
| `states/s_battle2.dst` | Second battle (Muskmallow Field), a player unit's command menu; info screen shows objective, law and the privilege |
| `states/s_results.dst` | End of the tutorial battle, five A presses before the results screen (then the law bonus) |
| `states/t_intro30.dst` | 30 presses into the opening, before the library's event (103) loads at press 39. Start point for `scripts/play_event.py`, which makes the game play any event (story scene) in its place, and with `SCRIPT=k` any of its scripts (ticket 29). Cold boot: the `scripts/to_battle.sh` inputs up to name entry, then 30 `A4,w22` presses |
| `states/t_fall.dst`, `states/t_flash.dst` | The opening's falling scene (the book pulls the hero in), and the white flash at its end (ticket 29). Cold boot: the `scripts/to_battle.sh` inputs up to name entry, then 265 `A4,w22` presses (`t_flash`: 6 more presses, then a few frames). The scene builds its projection once, so on another preset cold-boot that build instead of reusing these |
| `states/t_title.dst` | Title screen, New Game highlighted. Made by a cold boot, not by `to_saves.sh`: `scripts/play.py - states/t_title.dst w1500`. A then gives the difficulty menu. In melonDS the title is simply `scripts/melon_capture.sh ROM OUT.png 24` |
| `saves/worldmap.sav` | In-game save, slot 1, same moment as `s_worldmap`. Raw 64 KB save: loads in melonDS and DeSmuME |
| `saves/late.sav`, `states/late/late.dst` | Late-game save built from the world-map state (ticket 24): `scripts/late_save.sh late` (about 1 min) applies the save-data cheat codes, event flags and story progress 1240 listed in `scripts/cheat_save.py`, saves in-game, cold-boots and loads it. Level 99 party, everything owned and mastered, Bazaar, Clan Trials, full Quest Roster, the Ivalice map, auction month = the save's month (auction houses open after a day's travel). Loads in melonDS |
| `states/late/l_auction_mid.dst`, `l_auction_r2.dst`, `l_auction_end.dst` | Auctions (ticket 28): round 1 under way, round 2 at its last bid, round 3 under way. Walked from `l_auction_bid.dst` (A through the help, then A to bid) |
| `states/m_auction.ml1` | melonDS, at Take Part before round 1 of the Camoa auction. `x:3` starts it, six `x:2` pass the help. Taken there and not during bidding: the CPU is then mostly inside the mod's code, and such a state freezes on another build. Window grabs in the rig can be stale by seconds: check a frame counter before calling something a hang |
| `states/late/l_*.dst` | Screens from the late save, made by `scripts/to_late.sh` (about 1 min): worldmap, trials, trial_detail, pubmenu, roster, shop, bazaar, unitmenu, setabil, ivalice, camoa, camoa_town, auction, emporium, auction_area, auction_start, auction_round, auction_bid |
| `states/late/l_bz_*.dst` | Bazaar trade (ticket 33), made by `scripts/to_bazaar.sh` (about 30 s) from `l_bazaar.dst`: list, list3, craft, one, two, ask, clear, bronze, new (route in the script). Made with widescreen on: the recipe list builds its projection when it opens, so a state made with `PLAIN=1` keeps it unsqueezed |
| `states/m_shopmenu.ml1` | melonDS, late save at the shop menu (ticket 33; `build/t28_melon_late.sh` keys `x:1.5 Down:0.5 x:3 x:1.5 x:1.5 x:1.5 x:1.5 x:3`). The bazaar is three Down and A away; the steps of a whole trade are in ticket 33. Taken with the overlay off: a melonDS state taken while the overlay is up does not survive the blob being rewritten into it |
| `states/m_ivalice.ml1` | melonDS, late save on the map of Ivalice with Camoa selected (ticket 36). `2:1.5` (R) cycles the areas; six of them reach the Galerria Deep, the far west. Made by `build/t36_melon_late.sh` (`build/t28_melon_late.sh` with a 3 s pause before Up on the load screen, which the original sometimes misses) with the steps `wait:3 2:2 x:5 wait:4 save`, run in headless gamescope through `flatpak-spawn --host` |
| `states/battles/b<Q>_place.dst`, `b<Q>.dst` | Later battle maps (tickets 24, 38): `scripts/to_battles.sh [QUEST...]` (about 25 min) walks the road into the second battle from `s_worldmap.dst`, and as that battle is set up swaps in another story quest whole (`play.py` `QUEST=N[:S]`: quest, scene row and record at 0x02093A8C), so map, scenes, law, enemies and squares are that quest's. Story quests 3, 7, 11, 13, 17, 18, 19, 20, 21, 22, 23: unit placement, then the fight after the first turns. The party is the early one |
| `states/battles/b17_nojudge.dst` | Quest 17's fight after the law is broken and the judge has left (ticket 42): the info screen's frame is teal (palette 10), with no law or privilege. From `b17.dst`: `w10` and 30 times `A,w40` in `play.py`; it ends on a player's turn. |

Load a state in a script with `scripts/emu.py` `boot(state, rom="build/ffta2-1screen.nds")`,
or step through one with `scripts/play.py`. Either re-injects the mod's code from the ROM you
give it, so a state made on one display preset runs on a build of any other.

## Seeing the mod's screen: `scripts/solo.py`

`scripts/solo.py STATE SCRIPT OUTDIR` gives the gameplay screen exactly as widescreen shows it,
1280x800, for every `s<name>` step of a `play.py` script, in seconds. The test emulator cannot
show the squeezed picture cleanly, so the script runs four times from the same state, each run
drawing one unsqueezed piece of the wide view (`tile_cfg` in `src/hook.c`), and the pieces are
stitched. Compared with a real melonDS capture of the second battle the picture is the same apart
from colour rounding and animation phase. Use this for previews and layout checks; keep melonDS
for a final look at sharpness. It cannot show 2D layers or the SELECT screen swap (they come out
repeated). `scripts/solo_menus.sh` uses it to capture every menu into `shots/solo/` (about 1 min).

To compare before and after a code change: copy `shots/solo` to `shots/solo_before`, change the
code, run `scripts/solo_menus.sh` again, then `scripts/preview_compare.py NAME:caption ...` writes
`preview/compare.html`. Looking over all the regenerated pictures is the regression check for
anything that touches panel placement. `patch.py` now keeps symbols in `build/hook.elf`, so
`nm build/hook.elf` gives the address of any mod variable for reading it out of the emulator.

## Scion animations: `scripts/solo_scion.py`

`scripts/play_scion.py K OUTDIR` plays Scion K (0-12, Belias to Zodiark) from `states/s_battle2.dst` by
casting Cure with the Scion's ability record; `scripts/solo_scion.py K OUTDIR FRAMES` gives the exact
single-screen picture (`206-770/2` for a range), `scripts/melon_scion.sh K OUT.png` the same in melonDS
(40 s), `scripts/scion_quads.py K` lists the big layers. `scripts/preview_scions.py videos` renders all
13 (about 6 min).

States are saved at a frame where the CPU is outside the mod's code and the blob is padded to a fixed
size, so states keep working when `hook.c` changes (ticket 26). Only a new `BLOB_RESERVE` needs a rebuild.

## Display presets

`scripts/patch.py IN OUT --display deck|16x9|4x3` (ADR 0007; `deck` is the default), or
`--size WxH` for any display. The Deck preset's view is set by hand: 366x228 at 3.5x (ADR 0009).
For other displays the script picks the view, the game pixels shown, as the largest whole number
of screen pixels per game pixel that still shows the game's 192 rows: 1280x800 would give 320x200
at 4x, 1920x1080 gives 384x216 at 5x.
Where that would zoom out past 216 rows (1280x720, 1366x768) it keeps 192 rows and the pixels
come out uneven. `--view WxH` sets the view directly (for trying zoom levels, ticket 08). Every
size that depends on it (projection, side margins, culling, the parchment, layout clamps) comes
from that one value; see "display preset" near the top of `src/hook.c`.

Checking a preset:

- `ROM=build/ffta2-16x9.nds O=shots/solo169 SCALE=5 scripts/solo_menus.sh` captures every
  menu as that preset shows it (`solo.py` reads the view size from the ROM; without `SCALE` it
  enlarges to `FIT`, default 1280x800, the way the emulator does). Look for black
  rows or columns at the picture's edges; a script that counts black edge pixels per picture
  is the quickest first pass. The SELECT overlay on the world map shows black sides in every
  preset: a limit of the method (2D layer), not a fault.
- melonDS at the display's size: `scripts/melon_save.sh` and `scripts/melon_battle2.sh`
  (`ROM=... SIZE=1920x1080`) run inside `gamescope -W/-H` of that size; the probe that finds the
  save list scales with the window.

### Pixel evenness and the nudge

melonDS samples the picture exactly on the boundary between screen pixels, so even with a
whole-number scale about half the game-pixel edges can land one screen pixel early. The fix is
a sub-pixel nudge of the whole picture, in projection units (one screen pixel is 8192/W
horizontally and 8192/H vertically, W x H the display). Only measured nudges promise even
pixels; a new preset starts at 0,0.

The emulator's internal resolution matters as much as the nudge. melonDS renders the 3D picture
at 256x192 times its scale factor S and then scales that to the display, so a game pixel is
256*S/VIEW_W internal pixels wide and 192*S/VIEW_H tall. When those are whole numbers that scale
evenly to the display, edges can line up; when not, some game pixels come out a screen pixel
wider than others whatever the nudge. The 16:9 preset (384x216) needs S = 9 (6 x 8 internal
pixels per game pixel, then exactly 5 x 5 on screen); at the usual 8 it measured at most 69%
across. A 320x200 view on the Deck is not exact at 8 either, but close enough (94-99%). The Deck
preset's 366x228 cannot be even on a 1280x800 display at all (ADR 0009).

| Preset | View | Display | melonDS scale | Nudge | Measured on grid (x / y) |
| --- | --- | --- | --- | --- | --- |
| deck | 366x228 | 1280x800 | 8 | 3, -3 | 77% / 53% on a 3.5-pixel grid (Wood Village); 0,0 gave 73% / 44% |
| (`--view 320x200`) | 320x200 | 1280x800 | 8 | 3, -3 | 94-99% / about 90% (title screen) |
| 16x9 | 384x216 | 1920x1080 | 9 | 3, -3 | 91% / 86% (Wood Village); at 8x, 69% across at best |
| 4x3 | 256x192 | any | any | 0, 0 | the game's own picture |

1. Set melonDS's `ScaleFactor` (in its `melonDS.toml`, host side) to suit the view, and put it
   back to 8 afterwards: the other melonDS scripts expect 8.
2. `scripts/try_nudge.sh NX NY PRESET` builds `build/nudge.nds` with that nudge, captures a
   screen in melonDS at the preset's size (Wood Village from the
   save otherwise, about 70 s, because the title is a still picture that does not lie on a wider
   view's grid) and prints, per axis, how many
   colour changes fall on each phase of the K-pixel grid (`scripts/measure_grid.py IMG K`).
3. Good is one phase with well over 90% horizontally (the Deck measures 94-99%) and about 90%
   vertically. Two big phases next to each other mean edges straddle the sampling boundary:
   move the nudge by about half a screen pixel on that axis and measure again. Captures from
   the save can land on a slightly different moment; compare runs whose change counts are
   similar.
4. Put the winning pair in `PRESETS` in `scripts/patch.py` and note it there as measured.
   Add the preset's display size to `try_nudge.sh` if it is new.

Do not run two melonDS rigs at once (they share the speed setting and kill each other's melonDS).

## Menu catalogue

`scripts/menus_capture.sh` walks the menus from the test states and saves both screens of each to
`shots/menus/`, with widescreen switched off (`PLAIN=1` for `scripts/play.py`) so the low-resolution
capture is pixel-exact; `scripts/preview_menus.py` builds `preview/menus_dual.html` from them (and `preview/menus.html`, the same menus as the mod shows them, from `shots/solo/`). About 3 min.

## melonDS from the in-game save

`scripts/melon_save.sh ROM SAV OUT.png [key[:seconds] ...]` (run inside headless
gamescope like `melon_battle.sh`) copies the save next to the ROM, loads slot 1 and
presses the given keys before capturing. About 45 s per capture. Sequences that work:

- world map: no keys
- shop: `x:1.5 Down:0.5 x:3 x:1.5 x:1.5 x:1.5 x:1.5 x:2`
- party: `s:1.5 x:3 x:2`
- equipment: `s:1.5 x:3 x:2 x:2 x:2`

The second battle has its own script, `scripts/melon_battle2.sh [OUT.png]` (about 5 min, run
from the VS Code flatpak). The world map cursor moves freely and accelerates with how long a
direction is held, so the 4x test speed cannot hit the quest node; the script switches melonDS
to normal speed, replays the `to_saves.sh` inputs in real time through `scripts/melon_play.sh`
(8-frame cursor presses, since each key press costs a couple of extra frames and the cursor
overshoots from about 14), and switches the speed back. In melonDS a key pressed straight after a screenshot is lost (the script pauses after each capture), and menus open more slowly than in the test emulator, so walking through many menus this way is unreliable; use `solo.py` for that. Do not start a second run while one is
going: both would edit the speed setting and kill each other's melonDS.

## melonDS from savestates: `scripts/melon_state.py`

The repeatable way to see a known moment in real melonDS on the current build (ticket 13), about
15 s a capture, run from the VS Code flatpak:

    .venv/bin/python scripts/melon_state.py states/m_battle1.ml1 shots/x/battle.png
    .venv/bin/python scripts/melon_state.py states/m_story.ml1 shots/x/story.png x:1.5 s:next

It loads a melonDS savestate (slot 1, F1) and captures after the given steps (`KEY[:seconds]`,
`hold:KEY:seconds`, `wait:seconds`, `s:NAME` for extra captures; keys as in
`docs/melonds-test-settings.toml`: x = A, z = B, s = X, a = Y, q = SELECT, 1/2 = L/R). Env: `ROM`
(default the Deck build), `SIZE` (gamescope display, default 1280x800), `SAVE=path.ml1` (save a
new state after the steps: how a state further on is made), `FPS=60` (run at real speed for this capture:
needed whenever SELECT is pressed, since at the test config's 240 FPS a key press lasts about the 30 frames
that make a SELECT hold). `s:NAME` is a capture, so X followed by a wait is `s wait:N`.

A melonDS state holds main RAM and with it the mod code of the build that made it, so before
loading, the script writes the build's blob into the state at 0x02143E20 and re-applies every
ARM9 word the build patches, as `emu.py` does for DeSmuME states (`MELN` header, then the `NDSG`
section; main RAM starts 0x24 bytes into the file). A state therefore works on any later build,
including other presets; like the DeSmuME ones it must be remade when `BLOB_RESERVE` changes.

| State | Moment |
| --- | --- |
| `states/m_battle1.ml1` | First battle, Shaelan's command menu open (Move highlighted) |
| `states/m_story.ml1` | Opening story scene, a speech window with portrait |
| `states/m_battle2.ml1` | Second battle (Muskmallow Field: law, privilege, sky backdrop), Alulis's command menu open |

Making a base state: `scripts/melon_battle.sh ROM OUT.png save` replays the opening and saves
slot 1 (`ROM.ml1`) when the battle HUD is up; `save:N` stops after N presses into the opening
instead. Step on from there with `melon_state.py` and `SAVE=`. `scripts/melon_battle2.sh OUT.png save`
(about 5 min) does the same for the second battle from `saves/worldmap.sav`; copy `ROM.ml1` to
`states/m_battle2.ml1`.

In battle, choosing Move and holding the D-pad drags the camera with the cursor to the map's
edges: `x:1.5 hold:Right:0.4 wait:1.5 s:right` and so on (tickets 04, 05).

Gotchas: melonDS shortcuts (F1, Shift+F1) only arrive when sent to its window
(`xdotool key --window`); plain `xdotool key` reaches the game but not the shortcuts. melonDS
shows "State loaded from slot 1" for a few seconds; the script waits it out (turning `ShowOSD`
off would change melonDS's real settings on this machine). Captures of the same state differ only
in animation phase (idle units, the cursor). The script refuses to start while any melonDS runs.

## How the game gets past the opening

- Tutorial battle: the tutorial accepts Move + Wait for Alulis, wants Fire from the
  black mage, and then gives Luso a free turn. Any action by Luso (the script uses a
  Potion on himself) makes Klesta flee and the battle ends. No memory edits are needed.
- World map: needs presses of about 12 frames; 4-frame presses are ignored there.
  A on a town opens Pub / Shop.
- Prompts that default to "No": accepting a quest, finishing unit placement, choosing
  the clan privilege, loading a slot. All need Up before A.
- Unit placement before a battle is finished with X, not START.
- Only one emulator instance per Python process; a second one crashes.

## After changing the code reserve

`BLOB_RESERVE` in `scripts/patch.py` moves the game's heap start, so states made with another value cannot run the new build. Regenerate with `to_battle.sh` then `to_saves.sh`. The dialogue states `p_story_*.dst` predate the 16 KB reserve and have no replay script. The in-game save is unaffected.

## Seen on the way (not fixed here)

- (Fixed in ticket 17: the banner is hidden from "Complete!" on, and stays clear of
  placement, the privilege list and Help; the X hint for finishing placement shows.)
- The load-game screen leaves black side areas in melonDS.

## Comparing with the unmodified game

The test states were made with a mod build, so the unmodified ROM cannot run them: the mod moves
overlays inside the ROM and the game then loads files from the wrong places. Build a reference
ROM with the same layout and no hooks, and capture both (ticket 02):

    .venv/bin/python scripts/patch.py rom/ffta2.nds build/ffta2-ref.nds --display 4x3 --no-hooks
    RAW=1 NOSEL=1 ROM=build/ffta2-ref.nds O=shots/t02/orig scripts/solo_menus.sh
    RAW=1 NOSEL=1 ROM=build/ffta2-4x3.nds O=shots/t02/m43  scripts/solo_menus.sh

`RAW=1` gives both screens at DS resolution through `play.py`; `NOSEL=1` leaves out the SELECT
overlay steps. `scripts/preview_plain.py` builds `preview/plain.html`. Battle scenes differ by the banner
and by animation a frame or two apart; the clan-menu walk can drift in the plain game, so walk it
again with longer waits before calling a difference real.

## Story scenes after a battle (ticket 30)

- `saves/q17_won.sav`, `saves/q23_won.sav`: Quick Saves in quests 17 and 23 with the "battle won" flag (0x61B, `p0212D7F6=810`) set, so the battle is won when the turn ends (Wait). Made by cold-booting with `worldmap.sav`, the road with `QUEST=17` (or 23), waiting for a player turn, then the poke and X, Down, A, Up, A (Quick Save) and `e<file>`. From the title: Continue, Up, A, then A through objective, law and message.
- `states/m_q17.ml1`, `m_q23.ml1`: the same in melonDS at the command menu (`scripts/melon_boot_run.sh`); Down, Down, A wins. Further on: `m_t30b.ml1` (event 137, talk), `m_t30c.ml1` / `m_t30d.ml1` (quest 24, "proceed?" / fight; `POKE=0212D7F6=810 scripts/melon_state.py` wins it), `m_t30f.ml1` (event 151, farewell). `m_q17.ml1` was saved with a return address into the mod's `layer_draw` on the stack: it freezes on any build where code before `layer_draw` moved (ticket 43); remake it, with `m_q23.ml1`, at a moment outside the mod's code when that happens.
- The game builds the projection its effects use once, at boot: states descending from `p_battle.dst` still have the 320x200 view's. For effects that fill the screen, start from a cold boot.

