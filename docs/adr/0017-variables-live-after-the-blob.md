# The mod's variables live after the blob, in memory the game never uses

The blob was full (32768 of 32768 bytes) and about 6.4 KB of it was variables: zeros stored in the ROM. Growing the reserve (`BLOB_RESERVE`) lengthens the ARM9 binary, which moves the game's files in the ROM. Every test savestate remembers where those files are, so all of them (DeSmuME and melonDS, more than a hundred) would have had to be made again.

The variables (`.bss`) are now linked at `BLOB_ADDR + BLOB_RESERVE` (0x0214BE20), outside the blob, in a room of `BSS_ROOM` (32 KB). The blob's autoload entry gives that size as its bss size, so the game's own startup code zeroes the room after copying the blob, as it does for its DTCM section's 0x1320 bytes. The heap start literal (`arena_lo_literal`) moves up past the room. The ROM layout is unchanged, so every savestate still loads.

**Why the room is free.** The game makes its RAM heaps (ten NNS expanded heaps, `scripts/heap_free.py`) at fixed addresses from 0x0215B000 up, whatever the heap start literal says: they sit at the same addresses in the unmodified game, with the 32 KB reserve, and with the private build's 48 KB one. Everything between the old heap start (0x02143E20) and 0x0215B000, 94 KB, stayed zero in a cold boot, a battle, the world map, the late states, the auction, the story and the unmodified game. The blob, its variables and their room end at 0x02153E20, which leaves 29 KB of it untouched.

## Consequences

- The blob only holds code, constants and the display settings; 6.4 KB came free (Deck: 26364 bytes before the map art, ticket 36).
- The test rigs (`emu.boot`, `melon_state.py`) used to reset the variables by writing the blob back into a state; they now also zero the room (its size is read from the ROM's autoload entry), so a state behaves as before. `guard_report.py` looks for its record in the room too.
- A big table that starts at zero, or is filled at run time, costs room in RAM, not in the blob (the map art's 16 KB unpacked texture, ticket 36).
- If a future game version or another mod ever used that RAM, the mod would clash with it; `heap_free.py` and a dump of 0x0214BE20-0x0215B000 show it.
- `patch.py` asserts both limits: blob within the reserve, variables within the room.
