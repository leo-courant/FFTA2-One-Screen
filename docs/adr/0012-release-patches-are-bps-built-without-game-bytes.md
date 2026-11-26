# Release patches are BPS files built so they hold no game bytes

Players on a clean ROM get one patch file per display preset in the BPS format (`ffta2-1screen-<preset>.bps`), next to the Python patcher for modded ROMs (ADR 0011). `scripts/make_release.py` builds them all and refuses the release if any file, or what the patcher carries encoded, shares a stretch of 16+ bytes with the ROM (`scripts/check_no_game_bytes.py`).

The patches are made by our own encoder, `scripts/bps.py`, not by a generic diff tool. Patching moves the overlay table, overlay 0 and some small files to the end of the ROM (ADR 0001, 0011). A tool that stores every changed byte would put about 73 KB of game data in the patch: the check finds 2141 stretches in such a patch, the longest 72,916 bytes. BPS can copy from anywhere in the player's own ROM (SourceCopy), so `bps.py` stores only what the ROM doesn't have. Moved stretches become copies, runs of one byte value become TargetCopy, and bytes that are the same as the ROM's in place are always read from the ROM. Each patch is about 20 KB, and about 19.5 KB of that is the mod's own code.

## Considered

- **xdelta (VCDIFF):** the other common format for DS patches, and it can copy from the source too. It has more parts to write an encoder for (instruction code table, address caches), and the repo only has a decoder (`scripts/vcdiff.py`). BPS has four actions and is read by the patchers players use (Rom Patcher JS in a browser or on a phone, Flips, beat).
- **IPS:** limited to 16 MB offsets (the ROM is 128 MB) and can't copy, so moved data would be stored.
- **Patches made by Flips or Rom Patcher JS's "create":** whether they copy moved data or store it depends on the tool's matcher. The release check would catch it, but the result can't be controlled.

## Consequences

- BPS checks the source ROM's CRC32, so the `.bps` files only apply to the clean USA dump. Modded ROMs need the patcher.
- `make_release.py` applies every patch back to the clean ROM and requires exactly what `scripts/patch.py` builds. As a guard on the check itself, it also builds a naive patch that stores every changed block, which the check must catch.
- A new kind of change to the ROM (another region moved, for example) is handled by the encoder without changes, as long as the moved bytes are within 1 MB of a changed stretch (`MARGIN` in `bps.py`). Otherwise they would be stored, and the release check would refuse the release.
