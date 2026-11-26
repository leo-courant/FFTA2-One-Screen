# 10: Decide the treatment of each dual-screen menu

**What to build:** Catalogue every dual-screen menu (shops, party list, equipment, world map and any others found), show the user both screens for each, and agree per menu whether the detailed view is enough or content must be merged onto the gameplay screen. Produces decisions and follow-up tickets, not code.

**Blocked by:** 03

**Status:** done; decisions made by the user (2026-11-23)

- [x] Preview page with both screens for every menu found
- [x] A decision per menu is recorded
- [x] Follow-up tickets are written for menus that need merging

**Note from 03 (2026-11-23):** states for the world map, shop, party list and equipment screen exist (`docs/test-saves.md`); `scripts/preview_saves.py` already renders both screens for each. Also seen and not yet captured: pub menu and quest list, clan name entry, save/load slots, unit placement, clan-privilege list.

**Note (2026-11-23):** user's standing preference for these menus: overlay the info screen's content on the gameplay screen where possible (ticket 14). World map frame now reaches the screen edges and the backdrop covers the taller view (no black bar in party/equipment).

## Result (2026-11-23)

Catalogue: `preview/menus.html` (`scripts/preview_menus.py`), 47 moments with both screens each, taken with widescreen off so the DS-resolution captures are pixel-exact (`PLAIN=1` in `scripts/play.py`). `scripts/menus_capture.sh` remakes the ones reachable from the test states; the rest were taken once while replaying the `to_saves.sh` route.

The menus fall into six kinds by what the info screen is doing. Decisions (user, 2026-11-23):

| Kind | Menus | Decision |
| --- | --- | --- |
| A. Sheet for the selection | Party list, unit menu, Change Equipment, Fitting Room, shop Buy and Sell, Item List; in battle: Unit Info, Status, Item List | As built in ticket 14 (SELECT overlay; item stats beside Item Info). The in-battle ones get a melonDS check: ticket 15 |
| B. Needed in order to choose | Change Jobs (stat changes), View Abilities (ability list) | Shown automatically beside the list: ticket 16 |
| C. Clan summary, same whatever is selected | World map, Main Menu, System Menu, Config, town menu, pub and its lists, quest details, shop menu, Clan Menu and its lists | Nothing to merge; SELECT shows the summary |
| D. Before and after a battle | Law announcement, unit placement, choosing the privilege, results, law bonus | Banner stays during preparation, clear of the game's headings; hidden on results and law bonus: ticket 17 |
| E. In battle | Command menu, targeting, battle menu, View Law, Help | Already covered by tickets 07 and 09; Help window overlap goes into ticket 17 |
| F. Empty or decoration | Save/Load slots, name entry, story scenes | Nothing |

Found on the way:
- In placement and on the privilege list the battle frame is on the info screen, so SELECT swaps the screens there; on the in-battle sheets (kind A) it gives the overlay.
- The attack forecast (hit chance, damage) is on the gameplay screen; nothing needed.
- Not reached with the current save: Set Abilities (does not open for the starting units), bazaar, auctions, clan trials. They need a later save; Set Abilities is carried in ticket 16.

## Update (2026-11-23, later)

The user wants previews to show the mod's single screen, not both DS screens (mostly: "what I care about 80% of the time is how the mod looks"). `preview/menus.html` now shows every menu as the mod draws it, widescreen at 1280x800, made with the new `scripts/solo.py` (`scripts/solo_menus.sh`, about a minute); the both-screens version moved to `preview/menus_dual.html`. Seen in the solo pictures and not known before:
- View Abilities in battle shows a stray translucent panel on the left (the Item Info stats panel triggering there). Into ticket 16.
- The clan menu and its lists keep black side areas. Not ticketed yet.
