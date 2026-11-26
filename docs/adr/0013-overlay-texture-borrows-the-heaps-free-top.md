# The overlay's texture borrows the free top of the game's texture heap

The SELECT overlay (ADR 0005) needs a 48 KB 256-colour texture. It lived in the upper 48 KB of texture bank A, with bank A's contents parked in the main BG bank while it was up. The memory guard (ticket 25) showed that late-game pub menus draw part of their picture (a 256x512 sheet, rows 320-456) from exactly that memory, so a band of the pub behind the panel turned to garbage (ticket 31).

No other fixed place works. A survey of every menu state, counting only the texture rows the game draws on screen while the overlay is up plus every write it makes meanwhile, found bank A fully used across scenes and bank D written mid-overlay (menu icons load as the cursor moves). But every menu with a heavy picture (party, equipment, shops, pub, emporium, bazaar, auction) sets up the same texture heap as battle (0x2E000-0x3FFFF in bank B, ADR 0008). These menus use only its low part, 9-22 KB, and write nothing above it while the overlay is up.

So when the overlay opens in a scene with a heap, the mod puts its texture in the heap's top 48 KB (0x34000-0x3FFFF), but only if the free list says the game has nothing there and bank B is texture slot 1. Memory the game has freed holds nothing it will draw, so nothing is parked and nothing is put back. Each frame, before writing, the mod checks the free list again; if the game has claimed any of the window, the overlay closes at once (a later tap reopens it once the memory is free). Scenes without a heap (world map, Camoa, the map of Ivalice, the auction hall) keep the bank A place and the parked copy, which the guard found clean there.

We considered splitting the texture into two parts in bank D's undrawn stretches; the survey showed the game writes there mid-overlay. Asking the game's allocator for the memory would have made it truly ours, but an allocation failing later inside the game has unknown effects; a glitch-free close is the safer failure.

## Consequences

- In a heap scene the overlay costs the game nothing and parks nothing; the mod holds about 50 KB instead of 77 KB.
- If a menu ever needs more than the low 24 KB of the heap while the overlay is open, the overlay closes by itself. Not seen in any test state.
- A heap scene whose heap top is already in use falls back to bank A and parking, i.e. to the old behaviour (with the pub's clash, if it is the pub).
- The world map's 1-2-frame quads that sample bank A (ticket 31, group 4) are untouched: the world map has no heap.
