# 05: Backdrop continues into the side areas

**What to build:** Where the map does not reach, the backdrop fills the side areas by continuing its edge, so there is no black anywhere on screen.

**Blocked by:** 01

**Status:** done, approved by the user (2026-11-25). Second backdrop checked in melonDS at Deck resolution (2026-11-24)

- [x] No black region in either side area in the first battle
- [x] The backdrop's gradient continues without a visible seam
- [x] Checked on at least two different backdrops

## Result (2026-11-22)

The backdrop bands are drawn 128px wider (64 each side). In the first battle there is no black in either side area at any camera position, and the gradient continues without a seam. Only one backdrop has been checked; a second needs a different battle (ticket 03). Static full-screen pictures such as the title screen are a separate problem: see ticket 12.

## Second backdrop (2026-11-24)

No change to the mod. The second battle (Muskmallow Field) has a different backdrop from the first: sky with clouds over a yellow haze, a gradient top to bottom. Checked on the Deck preset (366x228 view, so the side areas are 55 game pixels each and the old 64-pixel widening still covers them; the 228 rows are covered too).

- Fast emulator (`scripts/solo.py states/s_battle2.dst`, camera panned with Move + held D-pad): no black anywhere, the clouds and the haze run on across the old 4:3 edges.
- melonDS 1.1, OpenGL 8x, 1280x800: new base state `states/m_battle2.ml1` (Alulis's command menu), made by `scripts/melon_battle2.sh shots/t05/b2.png save` (new `save` option; `melon_play.sh` has a `save` step). Then

      .venv/bin/python scripts/melon_state.py states/m_battle2.ml1 shots/t05/end.png x:1.5 s:move \
          hold:Right:0.4 wait:1.5 s:right hold:Up:0.4 wait:1.5 s:up hold:Left:0.7 wait:1.5 s:left \
          hold:Down:0.7 wait:1.5 s:down Right:0.4 s:p1 Right:0.4 s:p2 Right:0.4 s:p3 hold:Right:0.7 wait:1.5

  At every map edge the sky and the haze reach both screen edges and the top and bottom rows. No seam at the old 4:3 edges (screen x 192 and 1088): the colour change from one column to the next there is no bigger than anywhere else in the sky (0-4 per pixel, summed over RGB).

Captures in `shots/t05/`; preview `preview/mapedges.html` (shared with ticket 04). Later backdrops come with the late-game saves (ticket 24).
