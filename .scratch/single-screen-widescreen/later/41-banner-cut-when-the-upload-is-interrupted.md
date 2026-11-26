# 41: Banner text cut off and turn order empty after an interrupted upload

**What to build:** In quest 19's fight (`states/battles/b19.dst`, made by `scripts/to_battles.sh`; frames 10 to 60) the banner shows the law cut short, no privilege, and no figures in the turn order, while the info screen has all of it. It stays until the source changes. Found in ticket 38; not a memory clash (`vram_guard.py` is clean, and the heap top is never taken).

**Blocked by:** None. Second batch.

**Status:** done, approved by the user (2026-11-25). Preview: http://localhost:8765/bannercut.html (`scripts/preview_banner_cut.py`)

- [x] Known why the upload stops, and it can no longer be left half done
- [x] Quest 19's fight shows the whole law, privilege and turn order
- [x] Other states' captures unchanged; `vram_guard.py` clean

## Findings so far

- The upload in `hud3d_draw` maps bank B for the CPU (VRAMCNT_B = 0x80), writes text then units, and sets `hud_hash`, so it does not retry. In the state a write-watch on the VRAMCNT registers shows, in one frame, the mod's 0x80 at pc 0x02144966, then the game's own write (return address 0x02004328, an interrupt handler's upload queue, about pc 0x020036B4) followed by a remap to textures (0x8B, about pc 0x02003DD4). Everything the mod writes after that is dropped: the objective and the start of the law arrive, the rest never does. The frame before it, the same upload finished cleanly.
- So the fix is likely either keeping that interrupt off while the bank is mapped (short enough? the writes are 2 KB text and 4 KB units) or checking that the bank is still mapped afterwards and clearing `hud_hash` if not. The blob has about 340 bytes left.
- Why only here: more units on the info screen, so more of the upload queue is busy then. Other states were not searched for it.

## Findings and fix (2026-11-25)

- **Why:** the upload decoded the text and measured the units pixel by pixel with bank B mapped, so it held the bank 50 to 150 scanlines (99 in quest 19), while `ov_safe(16)` allowed for 16. Whenever it was still running at line 192, the game's vblank interrupt (its upload queue, lines 192 to about 209) remapped the bank and the rest was dropped. Not only quest 19: cuts also in b3, b11, b13, b20 and b7_place; many more ran across line 215.
- **Fix in `hook.c`:** (1) the decoding is done with bit operations and one union of the rows per cell or unit, so the bank is held 14 to 31 lines; (2) `ov_safe` also keeps clear of line 192 (the overlay's copies share it), and the upload asks for 34 lines; (3) if the bank was taken anyway, `hud_hash = 1` redoes the upload when the units are at rest, and slot 0 counts as good only after a whole upload. Blob 32496 of 32768 bytes (16x9 preset 32520).
- **Checked** with `scripts/hud_upload.py` (new) on every state in `states/` and `states/battles/` that uploads: no cuts, nothing across 192 or 215. Forcing three cuts in a row: the new build uploads again and ends on the same picture, the old one never retried.
- **Other captures:** the frames of 13 battle states match the old build pixel for pixel, 2 to 5 frames earlier in the fights (fewer dropped frames); one frame of b20 differs, mid-slide of the unit panel. Party, equipment, late shop, bazaar, emporium, roster and unit menu: identical. melonDS battles 1 and 2 (Deck): banner and turn order whole. Quest 19 itself was not run in melonDS (there is no melonDS state for it).
- **Test state:** `s_shop.dst` cannot be saved clean (every frame boundary there is inside the mod), so it crashes on a build whose code has moved. On this build the shop was reached from `s_worldmap.dst` by the `to_saves.sh` route instead: same pictures as before. Rebuild `s_shop.dst` when it is needed.
- **Not this ticket, found on the way:** `patch.py --guard` does not link at HEAD (`__aeabi_uidivmod`: a `%` on a variable in the guard code), so there is no guard test ROM at present; also so before this change.
- **Guard:** `vram_guard_all.sh` silent, exit 0 (states and menu walks); `vram_guard.py` silent on b3, b7, b11, b13, b18, b19, b20. `s_shop.dst`'s part of that run proves nothing (the state crashes, see above).
