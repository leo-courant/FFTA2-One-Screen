# 09: Special rules in the banner

**What to build:** Whatever the game shows on the info screen as a special rule for a battle is also shown on the gameplay screen at all times.

**Blocked by:** 03

**Status:** done, approved by the user (2026-11-25). One law per battle, answered from the game (2026-11-24)

- [x] A battle with a special rule shows it on the gameplay screen
- [x] Battles without one show no empty slot
- [x] The glossary entry for Special rule is updated with what it actually is

**Note from 03 (2026-11-23):** `states/s_battle2.dst` has a PRIVILEGE line (clan privilege, "Power↑1") under the law on the info screen. That is the only extra condition seen so far. See `docs/test-saves.md`.

## Result (2026-11-23)

The special rule is the clan privilege: the bonus picked before the battle, listed on the info screen under the law. The banner now has a third box for it, after the law, on the same parchment with a thin rule between the two; its text keeps the game's own teal. With no privilege (the tutorial battle) there is no box and the banner is as before. Glossary: new entry Privilege; Special rule now points to it.

The three boxes share the 32 text cells of the banner texture, about the width free beside the height tab; if the texts are longer than that together, the privilege gives way first, then the law.

Checked: second battle in melonDS at 1280x800 (`scripts/melon_battle2.sh`, new: battle 2 now has a melonDS route), on a player's turn and on an enemy's; tutorial battle in the low-resolution emulator only (`states/p_battle.dst`).

Open: only one privilege has been seen ("Power↑1"). A battle with no law but a privilege, a longer privilege name, or a second extra line on the info screen have not been met; a line below the privilege would not be picked up.

**Question from the user (2026-11-23):** what if a battle forbids more than one thing? Not answered from the game yet. As far as I recall FFTA2 gives each battle a single law, but that is from memory, not checked in the ROM. Today the banner reads one law line (info screen text rows 3-4) and one privilege line (rows 6-7); a second law line would not be shown, and long law names compete with the privilege for the banner's 32 text cells. To settle it: look for a battle whose info screen has more than one FORBIDDEN line, or find where the game stores a battle's law and see whether it holds one or several.

## Answer: one law per battle (2026-11-24)

Checked in the game code and in memory, not from recall:

- **A battle holds one law.** It is a single byte, event variable 0x172 (RAM 0x0212D9A6): 10 in the tutorial battle, 1 in battle 2. A memory diff of the two battles found it. The law announcement screen (`law_announce`, 0x020DB480) is the only code that writes it, and it writes one value. The only code that reads it is the info screen's setup (`info_law_priv_setup`, 0x02098E10). That setup passes exactly one law message (14000 + law) and one privilege message (15000 + privilege) to the routine that draws them (0x020A9C48). There is no list and no second law slot.
- **The game has 71 laws** (message list at ROM 0x2AA4F4E, entry 0 unused), and each one forbids one category. One law names three elements in a single line: it is still one law and one line, and it is among the 71 laws whose widths ticket 07 measured.
- **No law, but a privilege:** the info screen hides the law and the privilege separately (bits 13 and 14 of the battle word). Each line has its own drawing routine, and neither is given a position, so the privilege should stay on rows 6-7 when there is no law. I have not met such a battle yet. To test the banner in that case, I cleared the law heading and law text on the info screen (rows 2-4) in `s_battle2` and took a solo capture: the banner shows the objective and the privilege with no empty slot between them.

So the banner's single law box is all the game can ever need. The rest of this ticket's open note still stands: only one privilege has been seen ("Power↑1"), and a longer privilege name and a battle with no law have not been met in play.

New lines in `docs/symbols.tsv`: `battle_law`, `battle_privilege_var`, `law_announce`, `info_law_priv_setup`, `info_law_priv_post`, `info_law_line_draw`, `info_privilege_line_draw`.
