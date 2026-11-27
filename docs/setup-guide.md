# Setup guide

This mod puts all of Final Fantasy Tactics A2 on one screen. You play on what was the DS's
bottom screen, stretched across your whole display, and what the top screen showed reaches you
in two ways: a banner (objective, law, privilege) and turn order during battles, and the top
screen's page whenever you tap SELECT.

You set it up once. The steps are: get your ROM, pick the patch file for your display, patch,
and set up the emulator. The **Steam Deck** is the tested setup. PCs and phones should work
with any emulator that can do the four things listed under [What the emulator must do](#what-the-emulator-must-do).

## 1. Your ROM

You need your own dump of the US cartridge, *Final Fantasy Tactics A2: Grimoire of the Rift*
(game code `A6FE`). This project does not provide ROMs and does not link to them.

Check your file before patching. It must be exactly this:

| | |
| --- | --- |
| Size | 134,217,728 bytes (128 MiB) |
| CRC32 | `5826b0b0` |
| SHA-1 | `7ec7646c527be6af87e3c7ab0ed454f952842001` |

European and Japanese versions will not work, and neither will ROMs that are trimmed. If you
want this mod together with another one (a rebalance, for example), see
[With other mods](#with-other-mods): your ROM won't match these numbers then, and that is fine.

## 2. Pick the patch file for your display

The mod has to know your screen's shape when the ROM is patched. You can't change it in the
game later. Pick by the shape of the area the emulator will show the game in:

| Your display | Patch file | Game picture | Emulator internal resolution |
| --- | --- | --- | --- |
| Steam Deck (1280x800) and other 16:10 screens | `deck` | 366x228 game pixels, about 14% more scene each way than the DS | 8x |
| 16:9 monitors, TVs and laptops (1920x1080 and up) | `16x9` | 384x216 game pixels | 9x |
| Anything else, or if you want the game's own picture | `4x3` | 256x192, exactly the DS screen | any |

- **`deck`** fills a 16:10 screen edge to edge. On the Deck each game pixel is 3.5 screen
  pixels, so pixels alternate between 3 and 4 screen pixels wide. That was a deliberate choice,
  made to get more of the scene on screen.
- **`16x9`** was measured on 1920x1080, where every game pixel comes out exactly 5x5 screen
  pixels. That only happens when the emulator renders at 9x. At 8x some pixels come out a
  little wider than others. Larger 16:9 screens fill completely, just without that exactness.
- **`4x3`** leaves the game's picture untouched, pixel for pixel. You still get the banner,
  turn order and SELECT page. Use it when your emulator can't stretch the bottom screen, can't
  render 3D at a higher resolution, or when you want black bars and the original framing.

Phones in landscape are usually wider than 16:9 (19.5:9 to 20:9), and so are ultrawide
monitors. Two options:
use `16x9` and let the emulator keep that shape (thin bars at the sides), or
[build a patch for your exact size](#building-for-another-size).

## 3. Patch

The patch files are `ffta2-1screen-deck.bps`, `ffta2-1screen-16x9.bps` and
`ffta2-1screen-4x3.bps`, in the BPS format. Apply yours to your ROM with any BPS patcher.
[Rom Patcher JS](https://www.marcrobledo.com/RomPatcher.js/) runs in the browser, on a phone
too; Flips is a common one on PC. The patch carries the checksum of the ROM in step 1. If the patcher reports a checksum mismatch,
your ROM is a different one, and the result won't work: don't use it. Keep the original
ROM: you need it again for other patch files and for updates.

Name the result something like `ffta2-1screen.nds`.

### With other mods

The patch files above only apply to the clean ROM. To combine this mod with another one, use
the patcher script instead. It needs Python 3 and nothing else:

1. Apply the other mod to your clean ROM first, the way that mod says to.
2. Then add this one:

   ```sh
   python3 ffta2-1screen-patcher.py your-modded-ffta2.nds ffta2-1screen.nds --display deck
   ```

   (`--display` takes the same choices as in step 2: `deck`, `16x9` or `4x3`.)

The patcher checks only the places in the game code this mod changes. If the other mod changed
one of them too, the patcher says which ones and writes nothing: the two mods can't be combined.

- **Expected to work:** mods that change only the game's data (unit, job, ability or item
  stats). Tested with *Promise Rewritten* 0.9.7, a rebalance that also changes a few
  instructions of the game code, up to the first battle.
- **May clash:** mods that change screens, menus or text, or that add code of their own.
  Text mods can also get cut off. The banner and the ability list were sized for the game's
  original texts.
- **Not detectable when patching:** this mod uses 64 KB of the game's main memory (from
  0x02143E20, where the game's heap used to start) and some video memory while the game runs.
  Another mod that adds code and uses the same memory would break in play, not when patching.
- Apply this mod **last**, and only once. The patcher refuses a ROM that already has it.

## 4. Set up the emulator

### What the emulator must do

The mod draws its wide picture squeezed into the DS's 256x192 bottom screen, and the emulator
stretches it back out. So every patch except `4x3` needs an emulator that can:

1. **Render 3D at a higher internal resolution** (an OpenGL, Vulkan or "high resolution 3D"
   renderer). At the DS's own resolution the stretched picture looks smeared and wobbly.
2. **Show only the bottom screen.** The game's top screen isn't needed. The mod brings what
   it shows onto the bottom one.
3. **Stretch that screen to fill the display**, with the 4:3 aspect ratio unlocked. Integer
   scaling must be off.
4. **Put SELECT on a button** you can tap and hold comfortably.

### melonDS (tested)

Tested with melonDS 1.1. These are the settings that matter:

| Where | Setting | Value |
| --- | --- | --- |
| Config → Video settings | 3D renderer | OpenGL (Classic) |
| Config → Video settings | Internal resolution | 8x native (2048x1536); 9x for the `16x9` patch |
| Config → Video settings | Improved polygon splitting | on |
| Config → Video settings | OpenGL display | on |
| View → Screen sizing | | Bottom only |
| View → Aspect ratio → Bottom | | Window |
| View | Force integer scaling | off |
| View | Screen filtering | off |
| Config → Emu settings | Boot game directly | on (skips the DS menu, optional) |

Start melonDS in fullscreen (`-f` on the command line, or the "Toggle fullscreen" hotkey
on the General hotkeys tab of Config → Input and hotkeys). Otherwise the window's menu bar takes a strip of the screen
and the picture no longer fits exactly.

### Steam Deck

1. In Desktop Mode, open **Discover**, search for **melonDS** and install it.
2. Copy your patched ROM to the Deck, for example to `~/Emulation/roms/nds/`.
3. Start melonDS from the application menu and enter the settings above. Use 8x and the
   `deck` patch.
4. Map the buttons under **Config → Input and hotkeys → Joystick mappings**. Click a DS
   button there, then press the Deck button you want for it. Suggested:

   | DS | Deck |
   | --- | --- |
   | A, B, X, Y | A, B, X, Y (by label, so the game's prompts match) |
   | L, R | L1, R1 |
   | START | Menu (☰) |
   | SELECT | View (⧉) |
   | D-pad | D-pad |

   Also bind a key or button to **Toggle fullscreen** under the hotkeys.
5. To play from Game Mode, add melonDS to Steam: open Steam in Desktop Mode, choose
   **Games → Add a Non-Steam Game to My Library**, pick melonDS, then in its **Properties →
   Launch options** add `-f` and the ROM's path after what is already there, for example
   `... net.kuribo64.melonDS -f /home/deck/Emulation/roms/nds/ffta2-1screen.nds`.
6. **Put SELECT on a back button.** In Game Mode, open melonDS's controller settings (the
   Steam button → Controller settings), edit the layout, and in the back grip buttons section set
   **L4** (or R4) to the gamepad's **Select / View** button. A back button is easier to hold
   for half a second while you keep your thumbs on the sticks and buttons.

#### If you use EmuDeck

EmuDeck sets up melonDS and RetroArch with its own settings, and some of them get in the
mod's way. Change these (untested; worked out from EmuDeck's own configuration files):

- **melonDS:** apply the settings table above. EmuDeck ships a two-screen "Hybrid" layout, a
  5:3 picture and 3x resolution. Then, in Config → Input and hotkeys, **remove the View button
  from Fast Forward**. EmuDeck puts it on the same button as SELECT, so every SELECT press
  would also fast-forward, and a quick tap could then count as a hold.
- **RetroArch:** EmuDeck makes SELECT RetroArch's "Hotkey Enable" button. RetroArch then cuts
  the game off from your controller once SELECT has been held for 5 frames, so the hold never
  reaches the game. Move Hotkey Enable to another button (Settings → Input → Hotkeys).
- EmuDeck's Steam Input layout uses View plus another button for emulator hotkeys (View + A
  pauses, View + R1 saves a state, and so on). The mod ignores SELECT whenever another button is
  pressed with it, so these don't set it off. A plain tap or hold of View still reaches the
  game as SELECT.

### Other emulators (PC and phones)

Only melonDS 1.1 on Linux at 1280x800 has been tried with the mod. Everything below is
**untested**. It comes from each emulator's own settings and source code
(`docs/research/ds-emulators.md`). If you try one, please report how it went.

| Emulator | Runs on | Expected | Settings |
| --- | --- | --- | --- |
| melonDS 1.1 | Windows, macOS, Linux | should work (tested on Linux) | as in the table above; on macOS only OpenGL (Classic) is available, which is the one you want |
| melonDS (Android) 2.0.1 | Android | should work | OpenGL renderer up to 8x; in the layout editor delete the top screen and set the bottom screen's aspect to "Unrestricted" (or 16:9 with the `16x9` patch) |
| RetroArch with the melonDS DS core | Windows, macOS, Linux | should work | core options: Render Mode "OpenGL (Classic)", Internal Resolution up to 8x, Screen Layout "Bottom Only"; RetroArch: Video → Scaling → Aspect Ratio "Full", Integer Scale off; if the picture stays at DS resolution, the core fell back to software: try RetroArch's "glcore" video driver |
| RetroArch with the DeSmuME core | Windows, macOS, Linux, Android, Steam | should work | core options: internal resolution up to 10x, screen layout "bottom only"; Aspect Ratio "Full", Integer Scale off. This is the core in RetroArch's Steam version. It may be too slow on phones. |
| DeSmuME 0.9.13 | Windows | should work | Config → 3D Settings → GPU Scaling Factor 4 or more; View → LCDs Layout → "One LCD" and "Bottom first"; untick View → "Maintain Aspect Ratio" and "Pad To Integer" |
| NooDS | Windows, macOS, Linux, Android, iOS (sideloaded), RetroArch | may work, softer | Settings → Graphics → "High-Resolution 3D" (2x at most, so expect a softer picture); Screen Layout → "Single Screen" and "Enlarge Bottom", Aspect Ratio 16:10 or 16:9 to match the patch |
| DraStic | Android | unclear | 3D at 2x at most; no first-party information on a bottom-only stretched layout; no longer on Google Play |
| DeSmuME (macOS) | macOS | won't work | always keeps the 4:3 shape; use the `4x3` patch, or melonDS |
| Delta | iOS | won't work | DS games run at native resolution only; use the `4x3` patch |
| RetroArch with melonDS DS | Android, iOS | won't work | no OpenGL renderer in these builds; use the DeSmuME or NooDS core instead |
| Lemuroid | Android | won't work | has no bottom-only layout |

When an emulator offers only fixed aspect ratios, pick the one that matches your patch file:
16:10 for `deck` and 16:9 for `16x9`. "Fill the window" or "Full" stretches to whatever shape
the window has, which is right only when the window has the patch's shape.

## 5. Controls

You play the game with its normal buttons. The mod adds two actions, both on SELECT:

| Do this | In battle | In menus (shops, party, equipment, world map) |
| --- | --- | --- |
| **Tap SELECT** (press and let go) | Shows the game's top screen full size, in place of the battle. Tap again to return. | Shows the top screen's page as a see-through sheet over the menu. The D-pad keeps it up, so you can browse with it showing. A, B, X, Y or START close it. |
| **Hold SELECT** (half a second) | Turns the banner and turn order off, or back on. It switches while you are still holding. | Same |

- The tap happens when you **let go** of SELECT. That's how the mod tells a tap from a hold.
- SELECT pressed **together with any other button** does nothing in the mod. Emulator hotkeys
  that start with SELECT are safe to use.
- The game's soft reset, **L + R + START + SELECT**, still works.
- Some extras show up on their own: the banner during battles, the turn order at the bottom of
  the screen (L/R browses ahead, as in the original), and item stats next to the game's Item
  Info panel (wide patches only).
- Touch controls are not adjusted for the wider picture, so a tap lands where the original
  screen would have been. The game is fully playable with buttons. Use those.

## Saves

- **In-game saves** are stored by the emulator next to the ROM, named after it (for melonDS,
  `ffta2-1screen.sav`). To bring a save from the unpatched game, give it the patched ROM's name.
  The save format is untouched, so this should work. It hasn't been tested yet.
- **Emulator savestates** don't carry over between the unpatched game and the mod, or between
  two different patch files. The mod moves parts of the game around in memory. Switch patch
  files from an in-game save.

## Building for another size

If your display isn't covered by a preset, you can build a ROM for its exact size from this
repository. You need Python 3 and two packages:

```sh
python3 -m venv .venv
.venv/bin/pip install ziglang==0.17.1 keystone-engine==0.9.2
.venv/bin/python scripts/patch.py your-ffta2.nds ffta2-2400x1080.nds --size 2400x1080
```

Use the size of the area the emulator actually draws the game in. That is the screen minus
any bars, notch or on-screen buttons. The script picks how much of the scene to show: as big a
whole-number zoom as still shows at least the DS's 192 rows. It accepts views from 256x192 up to
768x384 game pixels and refuses portrait shapes. Other options:

- `--display deck|16x9|4x3` builds a preset (what the ready-made patch files are).
- `--view WxH` sets the number of game pixels shown yourself, for example `--view 320x200` on
  the Deck for an exact 4x zoom with perfectly even pixels.
- `--nudge X,Y` shifts the picture by a fraction of a pixel. Presets carry measured values. A
  custom size starts at 0,0, which looks fine but may leave slightly uneven pixel edges.
  `docs/test-saves.md`, "Display presets", explains how to measure and tune it.

A ROM built from the repository leaves out one thing the release files have: the extended edges
of the map of Ivalice. That art is made from the game's own map picture, so it isn't in the
repository (`docs/adr/0018-map-of-ivalice-edges-are-ai-extended.md` describes how it is made).
Without it, the map of Ivalice shows the game's flat sea at its far left and right; everything
else is the same. `patch.py` says so when it builds.

For the internal resolution, pick one where the emulator's 3D picture is at least as large as
your display. Higher is sharper if your device keeps up.
