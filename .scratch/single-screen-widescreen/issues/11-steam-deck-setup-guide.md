# 11: Setup guide

**What to build:** A short guide a player follows once: which patch file to pick for their display, which emulator and settings the mod needs, and how to put SELECT on a comfortable button. The Steam Deck section is the tested one; PC and phone sections list what is expected to work.

**Blocked by:** 19, 20 (the guide describes the final controls and the presets)

**Status:** closed by the user (2026-11-25). Written 2026-11-23; the box below is open because no try on the Deck has been reported

- [x] The emulator requirement is stated as a capability (3D at high resolution, one screen shown full-size), with the melonDS settings proven in ticket 01
- [x] Which PC and phone emulators meet it is researched and listed, each marked tested or untested
- [x] Every mod control is listed, with a suggested Deck mapping (for example SELECT on a back paddle through Steam Input)
- [x] Which patch file goes with which display is explained, and how to build one for a custom size
- [ ] The user has followed it on their Deck and confirmed it works

**Changed (user, 2026-11-23):** was "Steam Deck setup guide". The Deck is the user's own target, but others should be able to play on a PC or phone too.

## Written (2026-11-23)

The guide is `docs/setup-guide.md`, written for players: ROM check (size, CRC32, SHA-1, game code A6FE), patch file per display, patching, what the emulator must do, melonDS settings (menu labels checked against the melonDS 1.1 binary), Steam Deck steps, EmuDeck fixes, other emulators, controls, saves, building for another size (`--size 2400x1080` checked: builds a 480x216 view; a portrait size is refused).

Emulator research: `docs/research/ds-emulators.md` (sources cited, nothing run). Should work: melonDS desktop and Android, RetroArch with melonDS DS (desktop only) or DeSmuME, DeSmuME on Windows; NooDS only at 2x 3D (softer); won't work: DeSmuME on macOS (aspect locked), Delta on iOS (native resolution only), melonDS DS on Android/iOS RetroArch (no OpenGL), Lemuroid (no bottom-only layout); DraStic unclear.

Findings that matter for the mod:
- **EmuDeck melonDS** binds Fast Forward to the same button as SELECT (View). Under fast-forward a half-second hold is counted in game frames, so a tap can become a hold. The guide says to unbind it. It also ships Hybrid layout, 5:3 aspect, 3x.
- **EmuDeck RetroArch** sets "Hotkey Enable" to Select; RetroArch blocks game input after 5 frames of it, so the hold never arrives. The guide says to move it.
- EmuDeck's Steam Input chords (View + button) are harmless: the mod ignores SELECT with another button.

Open, for the user's Deck try:
- Game Mode launch options with `-f` and the ROM path, and whether melonDS starts fullscreen at 1280x800.
- Back paddle (L4/R4) to Select through Steam Input: tap and hold both work.
- Whether the Deck's controls reach melonDS without extra Steam Input setup (the research could not settle it from documents).
- Bringing a save from the unpatched game (renaming the .sav) is expected to work, not tried.

Left for ticket 21: the guide says "patch file" without a format, and names Rom Patcher JS, which reads both BPS and xdelta. The README should link the guide.
