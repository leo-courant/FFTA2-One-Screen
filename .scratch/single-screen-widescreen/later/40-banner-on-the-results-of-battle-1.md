# 40: Banner and turn order on "Complete!" and the law bonus

**What to build:** From "Complete!" on the banner and turn order should be hidden (ticket 17). In the rebuilt `states/s_results.dst` (battle 1) they show on "Complete!" and on the law bonus: the word the mod tests, 0x02124104, stays 2 there. Find a word that really tells a won battle.

**Blocked by:** None. Second batch (found in ticket 26, 2026-11-25).

**Status:** done, approved by the user (2026-11-25). Preview: http://localhost:8765/ending.html (`scripts/preview_ending.py`)

- [x] The banner and turn order are hidden from "Complete!" on in battle 1's and a later battle's ending

## What is known

- The code from before ticket 26, padded to the same size, shows the same on the same state: not a regression of that ticket. Earlier captures (ticket 17) had the word at 1 there; why it differs is not known (the state is made by replaying inputs, with enemy HP written to 0, so the battle may end another way).
- Picture: `shots/solo/lawbonus.png` (2026-11-25).

## Built (2026-11-25)

**The signal:** the byte at 0x0212EF07, the game's own battle outcome: 0 while fought, 1 won, 2 lost. The game's win check (0x02091C6C) sets it when the battle is decided, so the banner and turn order now go at the deciding moment, a little before "Complete!": the closing talk no longer has them flash up between its lines either. `BATTLE_OVER` in `src/hook.c` replaces `BATTLE_LIVE`.

**Why the old word failed:** 0x02124104 is never written from "Complete!" to the after-battle scene in this ending; it is not a battle signal (meaning unknown).

**Cleared in time:** event opcode 0x11 zeroes the byte; all 354 event scripts that open a battle (phase 1 or 8 of opcode 0x23) run it before their first battle phase, checked by walking every script. Resuming a Quick Save also clears it: with the byte set to 2 by hand at the title (as left by a game over), Continue put it back to 0 before the battle was drawn.

**The phase byte** (0x0212EE26, 7 = "Complete!", 0x0A = results and law bonus) was the other candidate. It falls back to 0 between the two, so the banner would have flashed.

**Checks (DeSmuME):**
- battle 1's ending on Deck, 16:9 and 4:3: no banner, no turn order from the win on;
- battle 2 won and lost (game over), battle 20 won up to its closing talk: won or lost by setting the game's own win/loss event flag (0x61B / 0x61A) and ending a turn, so the game's check decides. The banner stays up while the battle is fought;
- `scripts/solo_menus.sh` before/after: 95 of 96 captures identical to the pixel, only the law bonus changed (wanted).

Not checked: melonDS (the change only reads a different byte of main memory); battles won through other win types than "flag" or the tutorial's; chained battles in play (covered by the script check only).

## Review 1 (2026-11-25)

The user: "Complete!" must reach the edge of the screen as it does in the original proportions. (Their second point, the labels written twice at the bottom, is ticket 34, built in the same commit.)

**Built:** the bar is one 256x32 layout piece (phase byte 7, `BATTLE_PHASE`) with the lettering in its texture. `layout_piece` cuts the game's quad at x 216 (flat stripes between lettering and slant), and `still_edges` adds the stripes to the left edge, more to the right, and the slanted end at the right edge (`bar_part`). The lettering stays where it was, centred. The other half of the texture is the failed-quest bar: same shape and flat at the cut; it goes through the same code, not seen in play.

**Checks:** fade-in, battle 1 and 2 on Deck, battle 1 on 16:9 (4:3 is the game's own, untouched).
