# 23: The banner is one cell that rotates through objective, law and privilege

**What to build:** Instead of boxes side by side (and a second row for long texts), the banner is a single cell, as wide as the longest text the game can put in it. When a battle has more than one thing to show (objective, law, privilege), the cell turns through them like a drum: the current text rolls down out of view inside the cell and the next one rolls in from above, as if printed on a wheel turning towards the player. Not a blink or a cut.

**Blocked by:** None (ticket 07 found the limits)

**Status:** done, approved by the user (2026-11-23)

**Outcome:** the one-cell drum below was built and rejected. What shipped instead: the banner keeps its boxes side by side, each trimmed to its text (inked pixels + `BOX_PAD` 5 px each side), no animation (a battle has one objective, at most one law and one privilege); rows only grow when the texts do not fit beside the height tab, and on 4:3 the law fills a row that would otherwise stay empty. Checked with the game's longest texts (`scripts/longest_texts.py`). The checklist below belongs to the rejected design.

- [ ] One cell, its width fixed from the longest text it can hold in the game (so it never changes size between battles or values)
- [ ] With only an objective (no Judge, no privilege) the cell just shows it, no animation
- [ ] The roll animation: text leaves downwards and the next comes in from the top, clipped to the cell; smooth at 60 fps in melonDS
- [ ] It is clear which kind of value is showing (objective / law / privilege): the game's own colours (red box for the objective, parchment for law and privilege) or a small marker; to be settled with the user from a preview
- [ ] Timing settled with the user (how long each value stays, how long the roll takes); the mod control may want to stop or advance it
- [ ] The turn order (stage, bottom centre) and the "B" hint / Attack bar placement still fit around it

## What ticket 07 measured (2026-11-23)

From the game itself (`work/text-widths.tsv`, kept out of git, measured by letting the game draw each text): one objective per battle, at most one law, at most one privilege. Longest: objective 208 px (46 characters), law 121 px (27 characters), privilege 96 px (21 characters); 35 of the 45 longest objectives are over 160 px, a typical short one (16 characters) is 66 px. So a single cell is about 224 px with padding; there are 272 px beside the height tab on the Deck, 208 on 4:3 (where the longest objective does not fit beside the tab).

Notes:
- The text is copied from the info screen into a 2-bit texture (ticket 07: `txt_grp`, `TEXT_TEX` 512x32, objective on line 0, law and privilege on line 1), so the roll is just two textured quads with moving texture coordinates, cut to the cell; no new texture memory needed.
- Clipping inside the cell: shrink the quads and shift their texture coordinates rather than relying on the 3D engine to clip.
- Question for the user: should the cell's width follow the longest text of all three kinds (224 px), or of what this battle has (shorter cells in most battles)?

## 2026-11-23: one-cell drum tried and rejected

Built as described above (commit 0437c20: a single 224 px cell, a four-sided drum turning every 4 s through objective, law and privilege) and reverted the same day. User: "it was much much better before... it is much better with many". What they want instead: keep the boxes side by side (objective, law, privilege); make sure each box can hold the longest string of its kind; and when one kind has more than one value (their example: Fire, then Ice), that box switches between them with an animation, about every 5 s, instead of showing both. Open: ticket 07 measured at most one law and one privilege per battle, so it is unclear when a box would hold more than one value; asked the user.
Kept from the attempt: `BLOB_RESERVE` 0x8000 and the states rebuilt for it.

## 2026-11-23: what the user settled on, built

User: since a battle has one objective and at most one law and one privilege, no animation is needed; the boxes should just be sized well, without the wasted space (the room after the second battle's privilege and a short objective, the extra space around an icon law).
Built: when the text is copied, the mod notes each text's inked pixels (`txt_l`/`txt_r`, from the start of its run); each box is that width plus `BOX_PAD` 5 px each side. The text quads are shifted to start 5 px in and cut at the box edges. Row flow is unchanged (worst-case stretched texts still go onto a second row); on 4:3 the second battle's three boxes now fit on one row. The animation and fixed-width criteria above no longer apply.
Checked with the longest real texts (`scripts/longest_texts.py OUT_STATE`: battle 2 with the longest objective, law and privilege, drawn by the game; preview http://localhost:8765/longest.html): Deck and 16:9 fit on two rows (objective beside the height tab, law + privilege below). 4:3: the objective (218 px boxed) does not fit in the 208 px beside the tab, so row 1 stays empty and the banner takes rows 2-3; the law's first letters are hidden behind the unit portrait's ears. Fixed on the user's word: the row rule now lets the law go alone into a row that would otherwise stay empty above the law + privilege pair; on 4:3 with the longest texts that gives law / objective / privilege on three rows, clear of the portrait. Other cases unchanged (checked: both test battles on 4:3 and Deck, longest texts on Deck and 16:9).
Test-rig note: a state saved right after loading may have the CPU inside the mod's code; it then hangs under another preset's build (different code layout). Run a few frames before saving.
