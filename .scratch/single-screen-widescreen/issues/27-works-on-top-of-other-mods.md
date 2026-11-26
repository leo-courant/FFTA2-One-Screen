# 27: The mod applies on top of other mods

**What to build:** A player who already has a mod that changes the game's data (unit, job or item stats, for example) can still add this mod. The patcher checks only the bytes it changes, not the whole ROM, and says clearly what clashes when it can't apply. Players get a way to apply it that works on an already-modified ROM, because xdelta and BPS patches only apply to the exact file they were made from.

**Blocked by:** None (can start immediately). Touches `scripts/patch.py`, like ticket 21: if 21 is in progress, merge with care.

**Status:** done, approved by the user (2026-11-25). Built 2026-11-24

- [x] `patch.py` accepts a ROM that isn't the clean USA dump, as long as every place it changes still holds the original bytes. The whole-file SHA-1 check stays as a "clean ROM" message, not a refusal
- [x] When something clashes, the patcher says where and what it was expecting (game address, and our name from `docs/symbols.tsv`) and changes nothing
- [x] The way `patch.py` makes room is checked against modified ROMs: it moves the overlay table, overlay 0 and some small files to the end of the used area, and appends the mod's code after the ARM9 binary. A ROM rebuilt by another tool may be laid out differently, or the other mod may have used the same space; detect that instead of assuming the original layout
- [x] A patcher players can run without a compiler: the prebuilt mod code plus the checks, for each display preset (ticket 20). It holds no original game bytes (see below)
- [x] Tested on top of at least one real stat mod for FFTA2 USA, and on a ROM where the same bytes were changed on purpose (it must refuse cleanly)
- [x] The README (ticket 21) says which kinds of mods are expected to work: data-only mods. Mods that change screens, menus or text, or that add their own code, may clash; text mods may also get cut off, because the banner and the ability list were sized against the original text (ticket 22)
- [x] Order is documented: apply the other mod first, then this one

## Notes

- **Publishing rule:** published files hold no original game bytes (ticket 21, `ffta2-publishing-rules`). Today `put(addr, data, expect)` in `patch.py` compares against original bytes stored in the script. A published patcher must store a hash of each expected stretch instead, and the automatic check from ticket 21 must cover the patcher too.
- The mod also takes 32 KB from the game's main memory pool (`BLOB_RESERVE`) and borrows video memory (ticket 25). Another code mod doing the same would clash at run time, not at patch time. Out of scope here beyond saying so in the README.

## Built (2026-11-24)

Design in ADR 0011. What is where:
- `scripts/modpatch.py`: the apply step, standard library only. It reads a *mod description*: the mod's code, and for each change to the game code the address, new bytes, SHA-1 of the original bytes and our name from `docs/symbols.tsv`. It refuses a wrong game (game code A6FE), an ARM9 that is compressed, has a moved parameter block or a changed end (another code mod), a ROM that already has this mod, and any place whose bytes don't match. All clashes are listed at once (address, name, what is there now), and nothing is written. The expected bytes can't be shown because they are game bytes; the message says "not the game's original N bytes". To make room it moves whatever the header and file table place after the ARM9 binary (any of the overlay table, files, ARM7, file tables, banner) to the end of the used area, and refuses if that space isn't all FF/00.
- `scripts/patch.py`: same CLI. It compiles, assembles the `put()` list into a description (`--json` writes it), and applies it through `modpatch.apply`. **Byte-identical** to the old patcher on the clean ROM for deck, 16x9, 4x3 and `--no-hooks`, so all savestates stay valid.
- `scripts/make_patcher.py` → `dist/ffta2-1screen-patcher.py` (120 KB, gitignored): modpatch.py with all three presets embedded (`MODS = json.loads('...')`), then runs the check below.
- `scripts/check_no_game_bytes.py ROM FILE...`: fails on any shared stretch of 16+ bytes, also inside the base64 code and hex edits of a description or patcher. Stretches that are mostly one byte value don't count (indentation spaces matched ROM padding). Positive controls (64 game bytes raw, and hidden in a blob) are caught.
- `scripts/test_modpatch.py [XDELTA...]`: 13 cases, run with the plain system `python3`: each preset on the clean ROM (deck identical to `patch.py`), other game, two clashes (`hook_entry`, `layout_clip_checks` named), an ARM9 byte changed elsewhere (applies with a note), applied twice, overlay table moved, ARM7 binary right after ARM9 (files 0-7 and the overlay table moved away), junk in the free space, compressed ARM9, and real mods as xdelta files.
- `scripts/vcdiff.py`: an xdelta3/VCDIFF decoder (no xdelta tool on this machine) to put other mods on test ROMs.

**Real mod:** *Promise Rewritten* 0.9.7 (rebalance; xdelta from the NGPlus GitLab mirror, project `ngplus-net/homepage/mods/final-fantasy-tactics-a2-promise-rewritten`, `releases/FFTA2-Promise-Rewritten_0.9.7.rar`; kept locally in `build/t27/thirdparty/`, ffhacktics.com refuses automated downloads). It changes file 19 (a big data archive), 43 header bytes and five ARM9 words at 0x020B9094-0x020BAC44, none a mod site. Applied with the players' patcher (note: ARM9 differs), played from power-on to the first battle with `scripts/to_battle.sh`: works, banner and turn order fine, Alulis 71/71 HP 107/107 MP instead of 92/92 10/45. The two rebuilt layouts reached the same battle pixel-identical to the clean build. Pictures: `shots/t27/`.

**Players' text:** `docs/setup-guide.md`, new section "With other mods" (order, what is expected to work, what may clash, run-time memory use). Ticket 21's README should carry it over.

Not done here: the patch files in a standard format (ticket 21), and a patcher for players without Python, e.g. phones (a web page could run the same description; not asked yet).
