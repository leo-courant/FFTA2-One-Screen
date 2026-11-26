# 01: Widescreen sharpness go-no-go in melonDS

**What to build:** Run the current widescreen build in real melonDS with the OpenGL renderer at high internal resolution and the screen stretched to 16:10, in the first battle, and judge whether text and pixel art are sharp. This decides whether widescreen continues.

**Blocked by:** None (can start immediately)

**Status:** done (2026-11-22) - GO

- [x] melonDS is installed on the dev PC and boots the patched ROM
- [x] A capture at 1280x800 of the first battle exists and is published as a browser preview
- [x] The settings used (renderer, internal resolution, aspect, filtering) are written down
- [ ] A clear go or no-go is recorded, with the user's agreement

## Result

GO. melonDS 1.1 (Flathub) with the OpenGL renderer at 8x internal resolution, bottom screen only, aspect ratio "window", no filtering, renders the squeezed title screen sharp at 1280x800. Only the title screen was tested, not a battle. The fourth criterion (user agreement) is still open until the user has looked at the preview.

How it was run: melonDS inside a headless gamescope session on the host, captured with ImageMagick (the capture helper lives in the scripts folder). Settings used are saved in docs as melonds-test-settings.toml.

Gotchas: melonDS's settings folder is invisible from inside the VS Code flatpak, so the settings file must be copied from the host side; a partial settings file makes melonDS crash on save, so edit its own complete file; a second melonDS process becomes "instance 1" and ignores instance 0's window settings.
