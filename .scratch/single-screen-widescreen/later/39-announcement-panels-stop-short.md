# 39: Law and objective announcement panels stop short of the right edge

**What to build:** In the unmodified game the law and objective announcement panels run off the right edge of the picture. In the wide presets they are left where they are, so their right end shows as a blunt cut in the middle of the picture: at Deck size at about x 1186 of 1280 (`shots/t35/solo10.png`), in 16:9 likewise. Decide with the user how they should end (carried on to the screen edge, slid to the right, or given a finished end), then build it.

**Blocked by:** None. Second batch (found in ticket 35). Confirm the shape of the change with the user before building.

**Status:** done, approved by the user (2026-11-25): the bars run to the screen edge; the judge and text stay where they are

- [x] The law panel and the objective panel end as decided, on Deck and 16:9; 4:3 unchanged
- [x] The judge stays in the circle (ticket 35) and the slide-in from the right still starts outside the picture
- [x] Menu captures otherwise unchanged

## Leads

- Placement is in `layout_obj_begin` in `src/hook.c`; the panel is not moved by any of its rules today (the judge and circle stay on the 4:3 position).
- The panel slides in from the right, and its slide is animated through its position, so any rule must hold for every frame of it (`shots/t35/in_mod.png` row 3 vs `in_ref.png`).

## Findings (2026-11-25)

- Not a layout object: `layout_obj_begin` never sees the panel (the leads above were wrong). It is sprites in the sprite queue. The bar of both announcements is one entry: an 8x64 texture strip, vertices 0..8 x 0..64, stretched to 240 px (4:3 x 44 to 284 at rest).
- `queue_widen` now finds such a strip (at least `BAR_MIN` 160 px wide, right end at or past 256) and, where it ends before the real right edge, moves only its right end there. During the slide-in it already reaches past the edge, so nothing pops. The whole rule is skipped on 4:3.
- Before/after on the same rebuilt states, with a `--define BAR_MIN=255` build (rule off, same memory layout): 66 frames of both announcements differ only inside the added strip (x 1186 to 1279, y 316 to 417); of the 96 menu captures only `lawintro` and `law` (View Law in the battle menu shows the same bar) differ, in the same strip; 16:9 only right of the old end; 4:3 identical.
- melonDS at 1280x800: both bars in battle 2's opening (slide-in, fade; law with the judge), and View Law.
- All test states rebuilt, `dist` patcher regenerated, `test_modpatch.py` passes.
