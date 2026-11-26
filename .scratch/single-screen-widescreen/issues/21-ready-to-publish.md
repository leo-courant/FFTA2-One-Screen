# 21: Ready to publish

**What to build:** Everything needed so the repo can go public safely, without actually publishing it. The repo goes public only when the user says so.

**Blocked by:** 20 (patch files are made per preset), 27 (the release ships its patcher, and its "no game bytes" check covers that patcher too)

**Status:** closed by the user (2026-11-25): done up to publishing, fresh history in `~/ffta2-mod-public`. Nothing is pushed: that still waits for the user's word, and the public copy needs a sync first (it predates tickets 26, 32, 39)

- [x] A patch file per preset is built in a standard format (xdelta or BPS, whichever passes the check below)
- [x] An automatic check fails a release if the patch file contains any stretch of the original game's bytes
- [x] MIT license file, after confirming the build tools' licenses (the keystone assembler among them) do not constrain it
- [x] README: what the mod does, three or four pictures of the mod's own screen in one folder, and notices that the project is unaffiliated with Square Enix and Nintendo, that players must dump their own cartridge, and that the repo never links to or hosts ROMs
- [x] No other game pictures, game text dumps or game data anywhere in the repo
- [x] The full git history is audited for game data, with the result written down
- [x] Nothing is pushed anywhere until the user says so

**From ticket 27 (2026-11-24):** the release also ships `dist/ffta2-1screen-patcher.py` (`scripts/make_patcher.py`) for ROMs carrying other mods. `scripts/check_no_game_bytes.py ROM FILE...` is the automatic check: run it on every patch file and on the patcher (it decodes the embedded code). The README should carry over "With other mods" from `docs/setup-guide.md`. ADR 0011.

## Built (2026-11-24)

**Release files** (`.venv/bin/python scripts/make_release.py`, about 3 min, writes `dist/release/`, gitignored): `ffta2-1screen-deck.bps`, `-16x9.bps`, `-4x3.bps` (about 20 KB each), `ffta2-1screen-patcher.py` (120 KB), `SHA256SUMS`, `ROM.txt` (size, CRC32 `5826B0B0` and SHA-1 of the ROM the patches expect). BPS, made by our own encoder `scripts/bps.py` (ADR 0012): the mod moves about 73 KB of the game (overlay table, overlay 0, small files) to the end of the ROM, and a generic diff would store it. `bps.py` turns moved stretches into SourceCopy from the player's ROM, runs into TargetCopy and in-place bytes into SourceRead. What's left as new bytes (about 19.5 KB) is the mod's code and header fields.

**The check:** `make_release.py` applies every patch back to the clean ROM (must equal `patch.py`'s build exactly), runs `check_no_game_bytes.py` on every file and on the code and edits inside the patcher, and as a guard builds a naive patch storing every changed 4 KB block, which the check must catch (it does: 2141 stretches, longest 72,916 bytes). Any failure refuses the release and leaves `dist/release/` empty. `check_no_game_bytes.py` got two changes: it skips positions inside a match already grown (it was quadratic on long matches and never finished on the naive patch), and it takes a minimum length.

**Checked with a third-party patcher** (user's OK, 2026-11-24): Rom Patcher JS 3.1.0-b (npm `rom-patcher`, MIT, by its author; installed in `~/rea-tools/rompatcher/`) applied all three `.bps` files, and each result is byte for byte `patch.py`'s build. Its library checks the source ROM: `RomPatcher.validateRom` is true for the clean ROM, and with `requireValidation` it refuses an already-patched ROM ("Invalid input ROM checksum"; `~/rea-tools/rompatcher/validate.js ROM PATCH`). Its command line's `-v` does nothing (it sets `validateChecksum`, the library reads `requireValidation`), so the CLI patches any ROM. Whether the web page blocks or only warns on a mismatch wasn't seen, so the README and setup guide say to stop on a checksum mismatch instead of promising a refusal. Flips not tried.

**Licenses** (checked 2026-11-24): nothing constrains MIT for the repo's own code.
- Shipped files (`.bps`, patcher) hold only the mod's code, compiled by zig (`ziglang` 0.17.1, MIT) with `-ffreestanding -nostdlib`: no library code linked in. The patcher is standard-library Python.
- keystone-engine 0.9.2: the Python binding is BSD-3; the bundled core library is GPL-2.0 (Keystone's own licence). `patch.py` only runs it to assemble a few branch instructions; its output is ours, and we don't redistribute Keystone. Builders install it themselves (README / setup guide).
- py-desmume 0.0.9 (GPL-3.0+), capstone (BSD), numpy (BSD-3 and others), Pillow (MIT-CMU): imported by test and analysis scripts only, never shipped. MIT code may use GPL libraries; the GPL would only matter if we distributed them.
- Ghidra (Apache-2.0) and REA: analysis only; their output (`work/`) stays out of git. `scripts/ghidra/ExportXrefs.java` is ours.
- `LICENSE`: MIT, "Copyright (c) 2026 Leo Courant" (the commit author name), with a line saying it grants nothing for the game.

**README.md:** what the mod does, four pictures of the Deck build in `docs/pictures/` (battle with banner and turn order, SELECT overlay in the party menu, world map, Change Jobs; from `scripts/solo_menus.sh`, 1280x800), the release files, "With other mods" carried over from `docs/setup-guide.md`, building, and the legal notices (unaffiliated, dump your own cartridge, no ROMs or links, no game bytes in releases, MIT). `docs/setup-guide.md` step 3 now names the `.bps` files.

**Repo audit** (`.venv/bin/python scripts/audit_repo.py [--tree]`, under 1 min). Every distinct line of every file version is checked for 16+ bytes found in the ROM, and for 20+ characters of the game's own text (the ROM read through the game's 1-byte text encoding, so quotes are found wherever they are stored). A file with more than 3 quoted game texts fails; a few names in notes pass. Binary files are allowed only under `docs/pictures/`. Current tree: **PASS**. Fixed for that: `.scratch/single-screen-widescreen/text-widths.tsv` (a list of every law and privilege and the 45 longest objectives, with widths) moved to `work/text-widths.tsv` (ignored; `scripts/longest_texts.py` reads it from there), and the quoted longest texts in tickets 07, 23 and `scripts/banner_stretch.py` replaced by their lengths. `CLAUDE.md` now says not to quote game texts.

**History audit** (2026-11-24, all 70 commits, 337 file versions of 112 paths, `29c82c9`..HEAD): no stretch of game bytes anywhere, and no binary file. **Fails on game text in 17 old file versions of 4 paths:** `text-widths.tsv` (in 35 commits, from `4ac170c`), ticket 07 (8 versions), ticket 23 (7 versions) and `scripts/banner_stretch.py` (1 version, in 39 commits). Short quotes that pass (fewer than 4 per file): a quest name, a few item, ability and privilege names, prompts like "Select data to load", and the game's subtitle. Full output: `build/audit-history-full.txt`.

So **the history can't be published as it is.** Two ways, for the user to choose when publishing (neither done):
1. **Publish a fresh history:** the public repo starts from one commit of the cleaned tree. Nothing local changes, and commit hashes in tickets and notes stay valid locally. The development history isn't public.
2. **Rewrite the local history** (`git filter-repo`: drop `text-widths.tsv` from every commit and replace the quotes in old versions of the other three files). This keeps the history, but every commit from `4ac170c` on gets a new hash, so hashes quoted in tickets and notes go stale. It can't be undone without a backup.

Nothing has been pushed; there is no remote.

## Fresh history (user's choice, 2026-11-24)

The public repo is a **separate repository**, `~/ffta2-mod-public` (branch `main`, no remote), holding one commit of this repo's tracked files (`git archive HEAD`). It is separate, not an orphan branch here, so a `git push --all` can never send the old history: its object store holds only that commit's 118 files. `scripts/audit_repo.py` run inside it (whole history, ROM linked in temporarily): PASS.

This repo (`~/ffta2-mod`) stays the working repo with the full history, never pushed. To update the public repo before a push: from here, `git archive HEAD | tar -x -C ~/ffta2-mod-public`, delete there any file deleted here, commit there, and run its audit (`ln -s ~/ffta2-mod/rom rom` first, remove the link after; `.gitignore`'s `rom/` doesn't match a link).

Before the first push: the commit's author email is the one in this repo's git config, a personal address. To publish under GitHub's no-reply address instead: `git -C ~/ffta2-mod-public commit --amend --reset-author` with `user.email` set there first.
