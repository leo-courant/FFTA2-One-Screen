# The bazaar's loot rows go under the list

In the bazaar the gameplay screen has only lists: the recipes, then the loot of one kind. What you need in order to choose is on the info screen: one row per loot kind the recipe takes, with the loot sent for it and the grades that allows, and, once a recipe is chosen, a header with the recipe's grades that names the item the trade makes. The bazaar is not timed, so SELECT could show it, but the user's rule for menus like this (ticket 10, kind B) is that it shows without pressing anything.

The mod cuts the rows and the header from the info screen's overlay texture (ADR 0005) and draws them at 1:1, opaque, under the list, which moves up to the tab bar, as do the boxes that pop up over it; the game's description box (the highlighted loot's flavour text) goes below the view to make room. The user chose this on the recipe list as well (ticket 33, option A), so the rows also tell which loot kinds a recipe takes before it is chosen; option B kept the recipe's description there.

**Fit.** On the Deck's 366x228 view the list ends at 124; three rows of 24 and the 32 px header end at 228. The rows are cut tighter than the info screen spaces them (32 apart), which clips the current kind's glow by a few pixels; the info screen's background layer is left out of those bands, so the gaps are clear rather than teal. 16:9 (216 high) and 4:3 have no such room: they are unchanged, and SELECT shows the info screen there.

**When.** The word at 0x0212EA88 is 5 throughout the bazaar. The rows are drawn while the info screen has row labels (after a trade it shows the new item's sheet instead) and while the game's list was drawn in the last frames: after a trade the panels go and the shop room fills the screen while the info screen still has its rows for a second.

**Placing the panels.** The bazaar's panels hang from holders without pieces at the screen's middle, whose origin lies inside the list, so the general rule would carry them all with it: those holders stay, and the panels under them are placed by their own boxes (`bz_place`). Once the description box is below the view the game no longer draws its pieces, so it is remembered rather than recognised again each frame. A Yes/No box that moves takes its marks and cursor with it: the game draws them at its text lines' stored positions, so those are moved for the draw and put back (`window_draw_with`).

## Consequences

- The loot's description is not shown in the bazaar (SELECT does not show it either: it was on the gameplay screen).
- The room behind shows through the thin gaps between the rows.
- The bubble around each kind icon starts at the info screen's left edge, where the game's art stops; its missing left arc is drawn by the mod in the bar sprite's own palette (`bz_arc`), after the user's review. The ring the game draws around the current row is left out: the rows would cut it on three sides, and the tab bar shows the kind.
- Room in the blob: eight small functions became Thumb (the blob is full) to make space; logic added inside `layout_obj_begin` grows it out of proportion, so the bazaar's is a separate Thumb function.
