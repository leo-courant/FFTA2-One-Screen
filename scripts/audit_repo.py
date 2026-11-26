#!/usr/bin/env python3
"""Audit the git repository, every version of every file in its whole history, for game
data before it goes public (ticket 21, publishing rules).

usage: .venv/bin/python scripts/audit_repo.py [--tree]      (~1 min; needs rom/ffta2.nds)
       --tree   check only the files on disk git would take (tracked or new, not ignored)

Three tests on each file version (git blob):
  bytes     a stretch of 16+ bytes also found in the ROM (scripts/check_no_game_bytes.py)
  text      the game's own text: the ROM is read through the game's 1-byte text encoding
            (A=0x02, a=0x1C, 0=0x67, space 0x01) and each file is searched for stretches of
            TEXT_MIN+ characters found there.  A few names in notes are expected; many
            hits in one file means a text dump
  binary    pictures and other non-text files, which the rules allow only under
            docs/pictures/ (README examples of the mod's own screen)
Exit 1 if any version of any file fails, with the commits and paths it appears under.
"""
import bisect
import os
import subprocess
import sys
import time
from collections import defaultdict

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
sys.path.insert(0, HERE)
import check_no_game_bytes as check                 # noqa: E402

TEXT_MIN = 20           # characters of game text that count as quoting the game
NAMES_OK = 3            # at most this many quoted game texts per file pass (names in notes)
PICTURES = "docs/pictures/"


def git(*args, data=None):
    return subprocess.run(["git", "-C", ROOT] + list(args), input=data, capture_output=True, check=True).stdout


def blobs(tree_only):
    """{blob sha: set of (commit, path)} for every file version to check."""
    out = defaultdict(set)
    if tree_only:                                   # the files on disk git would see
        for path in git("ls-files", "-co", "--exclude-standard").decode().splitlines():
            if os.path.isfile(os.path.join(ROOT, path)):
                out["file:" + path].add(("tree", path))
        return out
    for commit in git("rev-list", "--all").decode().split():
        for line in git("ls-tree", "-r", commit).decode().splitlines():
            meta, path = line.split("\t", 1)
            mode, kind, sha = meta.split()
            if kind == "blob":
                out[sha].add((commit[:7], path))
    return out


def game_text_table():
    t = bytearray(256)                              # everything else -> 0 (a break)
    t[0x01] = ord(" ")
    for i in range(26):
        t[0x02 + i] = ord("A") + i
        t[0x1C + i] = ord("a") + i
    for i in range(10):
        t[0x67 + i] = ord("0") + i
    t[0x73], t[0x8D] = ord("!"), ord("-")
    return bytes(t)


def plain_text_table():
    keep = {0x20, 0x21, 0x2D} | set(range(0x30, 0x3A)) | set(range(0x41, 0x5B)) | set(range(0x61, 0x7B))
    return bytes(b if b in keep else 0 for b in range(256))


def is_binary(data):
    if b"\x00" in data:
        return True
    try:
        data.decode("utf-8")
    except UnicodeDecodeError:
        return True
    return False


def main():
    tree_only = "--tree" in sys.argv
    rom = open(os.path.join(ROOT, "rom", "ffta2.nds"), "rb").read()
    where = blobs(tree_only)
    shas = sorted(where)
    data = {s: open(os.path.join(ROOT, s[5:]), "rb").read() for s in shas if s.startswith("file:")}
    objs = [s for s in shas if s not in data]
    contents = git("cat-file", "--batch", data="".join(s + "\n" for s in objs).encode()) if objs else b""
    i = 0
    for sha in objs:                                # parse `cat-file --batch` output
        nl = contents.index(b"\n", i)
        size = int(contents[i:nl].split()[2])
        data[sha] = contents[nl + 1:nl + 1 + size]
        i = nl + 2 + size
    print("%d file versions (%d paths) in %s" % (len(shas), len({p for v in where.values() for _, p in v}),
          "the current tree" if tree_only else "%d commits" % len({c for v in where.values() for c, _ in v})))

    problems = defaultdict(list)                    # sha -> findings
    for sha in shas:
        paths = {p for _, p in where[sha]}
        if is_binary(data[sha]) and not all(p.startswith(PICTURES) for p in paths):
            problems[sha].append("binary file (%d bytes)" % len(data[sha]))

    # Versions of a file repeat most of their lines, so each distinct line is searched once
    # and hits are given to every file version holding that line.  A stretch is only found
    # within a line: game bytes or text in a text file don't contain newlines.
    lines = {}                                      # line -> index
    owners = []                                     # index -> shas
    for sha in shas:
        if is_binary(data[sha]):
            continue                                # reported as binary already, or a picture
        for line in set(data[sha].split(b"\n")):
            if len(line) >= 16:
                k = lines.setdefault(line, len(lines))
                if k == len(owners):
                    owners.append([])
                owners[k].append(sha)
    order = sorted(lines, key=lines.get)
    print("%d distinct lines, %d KB" % (len(order), sum(map(len, order)) // 1024))

    def search(hay, table, min_len):
        """search every distinct line at once in `hay`; report hits per file version"""
        t0 = time.time()
        joined, starts = bytearray(), []
        for line in order:
            starts.append(len(joined))
            joined += line.translate(table) if table else line
            joined += b"\n"                         # 0x0A: neither a letter nor a run
        hits = check.shared_stretches(hay, bytes(joined), min_len)
        per = defaultdict(list)
        for s, n, rs in hits:
            k = bisect.bisect_right(starts, s) - 1
            for sha in owners[k]:
                per[sha].append(bytes(joined[s:s + n]))
        print("  %d hit(s), %.0f s" % (len(hits), time.time() - t0))
        return per

    print("bytes: searching the ROM for shared stretches of %d+ bytes..." % check.MIN)
    for sha, found in search(rom, None, check.MIN).items():
        if any(p.startswith(PICTURES) for _, p in where[sha]):
            continue                                # README pictures are allowed game pictures
        problems[sha].append("%d stretch(es) of game bytes, e.g. %r" % (len(found), found[0][:40]))

    print("text: searching the game's text for %d+ characters..." % TEXT_MIN)
    game_text = rom.translate(game_text_table())
    for sha, found in search(game_text, plain_text_table(), TEXT_MIN).items():
        quoted = sorted({f.decode("ascii", "replace").strip("\x00 ").replace("\x00", "·") for f in found})
        if len(quoted) > NAMES_OK:
            problems[sha].append("%d quoted game texts, e.g. %s" % (len(quoted), "; ".join(quoted[:4])))
        else:
            print("  ok, %d short quote(s) in %s: %s" % (len(quoted), sorted({p for _, p in where[sha]})[0],
                                                       "; ".join(quoted)))

    if not problems:
        print("PASS: no game data found")
        return
    print("FAIL: %d file version(s)" % len(problems))
    for sha, msgs in sorted(problems.items(), key=lambda kv: sorted(where[kv[0]])[0][1]):
        paths = sorted({p for _, p in where[sha]})
        commits = sorted({c for c, _ in where[sha]})
        print("  %s (%s, in %d commit(s): %s)" % (", ".join(paths), "disk" if sha.startswith("file:") else "blob " + sha[:8], len(commits),
                                                         " ".join(commits[:6]) + (" ..." if len(commits) > 6 else "")))
        for m in msgs:
            print("      " + m)
    sys.exit(1)


if __name__ == "__main__":
    main()
