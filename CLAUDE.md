# FFTA2 single-screen mod

A ROM patch for Final Fantasy Tactics A2 (DS, USA) that puts the whole game on one widescreen display in an emulator. `GLOSSARY.md` holds the project's words (gameplay screen, info screen, banner, overlay…); use them in code, tickets and replies.

## Working here

- **One ticket per session.** Spec and tickets live in `.scratch/single-screen-widescreen/` (`spec.md`, `issues/NN-*.md`); pick an unblocked `ready-for-agent` ticket, record findings and decisions in the ticket, and record lasting design choices as an ADR in `docs/adr/`.
- **Two batches.** `issues/` is the first batch. `later/` holds the second batch (late-game saves, the memory guard, and what they turn up). "Work on the next ticket" means a ticket from `issues/`: don't start a `later/` ticket until every ticket in `issues/` is done, unless the user names it. Ticket numbers are shared across both folders, so check both before picking a new number.
- **Build:** `.venv/bin/python scripts/patch.py rom/ffta2.nds build/ffta2-1screen.nds [--display deck|16x9|4x3]` compiles `src/hook.c` and injects it (ADR 0001).
- **Applying** is done by `scripts/modpatch.py` (stdlib only), from a mod description `patch.py` builds: the same code players run from `dist/ffta2-1screen-patcher.py` (`scripts/make_patcher.py`), which works on ROMs other mods have changed (ADR 0011). A new patch site needs its `put(addr, new, original)` in `patch.py` and a line in `docs/symbols.tsv` (the name shows in clash messages). After changing either, run `python3 scripts/test_modpatch.py` and keep `scripts/check_no_game_bytes.py` passing on anything meant for publishing.
- **Test:** `scripts/solo.py STATE SCRIPT OUTDIR` gives an exact 1280x800 picture of the mod's screen in seconds, from DeSmuME savestates in `states/`. Use it for previews. For a real melonDS look at a known moment, `scripts/melon_state.py states/m_battle1.ml1 OUT.png` (about 15 s, any build; melonDS states in `states/m_*.ml1`); the older replay rigs (`scripts/melon_*.sh`) are slow and only needed to make new base states. `docs/test-saves.md` explains how the states and saves are rebuilt. `scripts/vram_guard.py STATE [SCRIPT]` reports when the mod and the game use the same video memory at once (silent = clean; `scripts/vram_guard_all.sh` runs every state and menu walk, about 9 min). The ranges it watches are `borrowed_vram[]` at the end of `src/hook.c`: add a line there whenever the mod starts writing video memory somewhere new. `patch.py --guard` makes a test ROM for playing that lights a red dot top left when it catches a clash; `scripts/guard_report.py STATE` reads the details from a savestate made there.
- **One emulator rig at a time on this machine.** Other sessions share it: check `pgrep -x melonDS` before a melonDS run and never `pkill` another session's rig.
- Local git commits are fine. Pushing to a remote, or making anything public, waits for the user's word. Game data and anything derived from it (ROM, `unpacked/`, `work/`, `states/`, `shots/`, `preview/`) stays out of git. Don't quote game texts in tickets or scripts (give lengths or table addresses); the only game pictures allowed are the README's in `docs/pictures/`. `.venv/bin/python scripts/audit_repo.py --tree` (about 3 min) checks the files for game bytes, game text and binaries; without `--tree` it checks the whole history.
- **Release:** `.venv/bin/python scripts/make_release.py` builds `dist/release/` (a BPS patch per preset plus the patcher, ADR 0012) and refuses if any file holds game bytes, or if the map art is missing.
- **Map art:** the map of Ivalice's edges are AI-extended art (ADR 0018), kept in `work/map_art/` (game-derived, never in git). `patch.py` builds it in when `work/map_art/map_art.lz` exists; `scripts/map_art_dump.py`, `map_art_outpaint.py`, `map_art_tear.py` and `map_art_pack.py` make it (ADR 0018 has the steps).
- **Blob room:** the mod's variables live after the blob, not in it (ADR 0017). `patch.py` prints both: code against `BLOB_RESERVE` (nearly full), variables against `BSS_ROOM`. Raising `BLOB_RESERVE` moves the game's files in the ROM and makes every test state unusable; a large zero-initialised table costs only variable room.

## Finding things in the game code

Go in this order:

1. **`docs/symbols.tsv`**: every game address the mod has pinned down (functions, hook sites, RAM words), with our name and what we know. Search it first by address or by name.
2. **`work/decomp/slim/<addr>.c`**: Ghidra's decompile of each ARM9 function, named by its 8-digit address (`FUN_020b3208` → `slim/020b3208.c`). Each file starts with a header: our name and note, the mod's patch sites inside it, its callers, where a pointer to it is stored, and what it calls. Names from `symbols.tsv` are applied in the body (`grid_list_layout_020b3208`), so searching by address still finds them. Read and grep `slim/`. `work/decomp/functions/` is REA's raw output; about 70% of each file is a repeated boilerplate header.
3. **`work/decomp/functions.tsv`** (one line per function, with caller/callee counts) and **`work/decomp/refs.tsv`** (every reference: `call`, `jump`, `pointer`/`table` from Ghidra, and `word` from a scan for function addresses stored anywhere in the binary). Use them for "who calls X" and "where is X used as a callback".
4. **Runtime tracing** when static reading stalls. Most of the project's findings came from it: `scripts/gxtrace.py` + `scripts/gx_report.py` (which call site drew each polygon), `scripts/vidregs.py` (video registers), and py-desmume's `memory.register_write/register_exec` for watches.

When you pin down an address, **add a line to `docs/symbols.tsv`** and rerun `scripts/slim_decomp.py` (about 1 s).

Limits of the index:
- It covers only the ARM9 main binary, loaded at 0x02000800 (`work/arm9_0x02000800.bin`). Overlays (`unpacked/overlays/`) and code that runs from ITCM (0x01FFxxxx, e.g. swap-buffers at 0x01FFB51C) are not in it.
- Calls through a register are invisible statically. A `pointer`/`table`/`word` reference shows where the function's address is stored, and the function that loads it from there is usually the caller.
- `scripts/decomp_index.sh` rebuilds `xrefs.tsv` from a fresh headless Ghidra analysis (about 1 min). Run it only if the decompile itself is redone.

## hook.c rules

- No libgcc: no `/` or `%` on variables (use `sdiv`) and no struct assignment (copy word by word).
- Keep new global variables uninitialised: an initialised one reorders the blob's data and breaks `PLAIN=1` captures.
- VRAM takes 16/32-bit writes only, and byte writes are silently dropped. This also applies to test scripts (`emu.memory.write_short/write_long`).
- Never unmap a texture bank around scanline 215: the whole frame loses it.
- Before moving a widget's pieces one by one, look for the widget's own layout fields (the grid list's cell width and column count, ticket 22).
