# 42: Banner and turn order gone once the judge has left

**What to build:** After the law is broken and the judge leaves, the banner and the turn order no longer show for the rest of the battle, though the info screen still shows the objective and the turn order there (teal, without law and privilege). Find out why, and show what is left (objective, turn order).

**Blocked by:** None. Second batch (found in ticket 30, 2026-11-25).

**Status:** done, approved by the user (2026-11-26). Preview: http://localhost:8765/judgegone.html (`scripts/preview_judge_gone.py`)

- [x] Known why they are hidden
- [x] Objective and turn order shown after the judge has left

Seen in DeSmuME and melonDS on quest 17 (the law is broken in the opening turns) and quest 23; `states/m_q17.ml1` is such a moment, but it also has the win flag set. Not a change of ticket 30 (not compared with older builds).

## Findings and fix (2026-11-26)

**Why:** `battle_hud_present` in `src/hook.c` tells a battle by the info screen's frame: its top-left BG0 cells must be exactly 0xE001, 0xE002, 0xE004 (the "!" objective badge). Once the judge has left, the game redraws the same frame cells in palette 10 instead of 14 (0xA001, 0xA002, 0xA004: the teal look). The check failed, so `hud3d_draw` returned before the banner and turn order for the rest of the battle. Nothing else changes for the mod there: the BG palettes, the turn-order sprites (y 97-152) and the pips (y 184, palettes 3/4) are as before; the objective text moves from palette 0 to palette 1 (same glyph cells), and the law and privilege rows of BG1 are empty.

**Fix:** the check accepts palette 14 or 10 on the same three cells. Law and privilege have no text, so the banner shows the objective box alone (the layout already drops empty boxes); the turn order is unchanged. The text is still coloured from BG palette row 0, so the objective looks as it did before the judge left (red box, light text), not teal. Blob 32596 of 32768 bytes (Deck).

**State:** `states/battles/b17_nojudge.dst` (from `b17.dst`: `w10` and 30 times `A,w40`; the opening has the law broken by a steal, the judge leaves, and it ends on a player's turn). Documented in `docs/test-saves.md`.

**Checks:**
- DeSmuME, `solo.py` on `b17_nojudge.dst`: objective and turn order on Deck, 16:9 and 4:3 (4:3: the dark strip under the banner).
- melonDS at Deck size, `states/m_q17.ml1` and `m_q23.ml1`: objective and turn order (before: neither).
- `scripts/solo_menus.sh`, old build and new: 90 of 96 captures identical to the pixel. The 6 others (`abil`, `abil2`, `abil_ov`, `status`, `unitinfo` from `s_battle2`, `bq13_place`) differ only in units' animation phase on the map; banner, panels and turn order identical. Those screens have the palette-14 frame, where the check answers as before; the blob is 8 bytes shorter, which moves timing.
- `vram_guard.py` on `b17_nojudge.dst` (300 frames): silent.

Not checked: a battle where the judge leaves while a dialogue box or "Complete!" is up (the existing rules for those apply unchanged).
