# The mod is applied by a patcher that checks only what it changes

Players who already use another mod (stat or job rebalances, for example) should still be able to add this one. xdelta and BPS patches only apply to the exact file they were made from, so the mod also ships as a patcher of its own (`scripts/modpatch.py`, standard library only). The release embeds one mod description per display preset (`scripts/make_patcher.py`). The description holds the mod's compiled code and, for each change to the game code, the address, the new bytes and a SHA-1 of the original bytes they replace. The patcher refuses only when one of those places no longer holds the original bytes, and then lists every such place by address and by our name from `docs/symbols.tsv`, writing nothing. `scripts/patch.py` builds the same description and applies it with the same code, so the developer build and the players' patcher can't drift apart. On the clean ROM the result is byte for byte what `patch.py` made before (savestates stay valid).

Room for the code after the ARM9 binary is made by moving whatever the ROM's own header and file table say lies there (the overlay table, files, even the ARM7 binary) to the free space at the end, instead of assuming the original layout. The free space must hold only FF or 00 bytes, or the patcher refuses. Another mod may keep unlisted data there.

## Considered

- **Whole-file hash (before):** safe but refuses every modded ROM.
- **Original bytes in the patcher** (`put(addr, data, expect)` as it was): simple, but the release would then carry game bytes, which the publishing rules forbid. Hashes of short instructions are not a way to recover them, and they say nothing new.
- **A generic "smart" patch format** (applying xdelta to a modified file): no such format can check meaning. A clash would silently corrupt the game.

## Consequences

- The release must pass `scripts/check_no_game_bytes.py`, which also decodes the code and bytes embedded in the patcher (base64/hex would hide them from a plain search).
- An ARM9 that differs from the clean one elsewhere is accepted with a note. The mod calls and reads many game routines at run time; a code mod that changes one of them can break the mod in play, and no patch-time check can see that. A code mod that also extends the ARM9 binary, compresses it, or uses the main heap start the mod moves is refused or clashes at run time (`BLOB_RESERVE`, borrowed video memory: ticket 25).
- Order matters: other mods first, this one last. Applying this mod first and a full-file patch after it would undo it or fail.
- `scripts/test_modpatch.py` keeps the cases: clean ROM per preset, wrong game, clashes, applied twice, two rebuilt layouts, junk in the free space, compressed ARM9, and real mods given as xdelta files (`scripts/vcdiff.py` applies them without the xdelta tool).
