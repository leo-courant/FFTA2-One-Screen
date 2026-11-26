#!/usr/bin/env python3
"""Build work/decomp/slim/: the REA decompile made cheap for agents to read.

For every function in work/decomp/functions/ it writes slim/<8-digit addr>.c
(so FUN_020b3208 -> slim/020b3208.c) with:
  - REA's long per-file "limitations" header dropped (~70% of the bytes);
  - a short header: range, our name and note from docs/symbols.tsv, mod hook
    sites inside it, who calls it, where a pointer to it is stored, what it calls;
  - names from docs/symbols.tsv applied in the body (FUN_020b3208 becomes
    grid_list_layout_020b3208, DAT_0212e834 becomes item_info_panel_0212e834),
    so the address is still in every name and still greppable.

Also writes work/decomp/functions.tsv (one line per function) and
work/decomp/refs.tsv (all references: Ghidra's plus a scan of the binary for
words equal to a function entry, which finds pointer tables Ghidra missed).

Inputs: work/decomp/decompile-index.json + functions/ (REA), work/decomp/xrefs.tsv
(scripts/decomp_index.sh), work/arm9_0x02000800.bin, docs/symbols.tsv.
"""
import bisect, json, os, re, shutil, struct, sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
D = os.path.join(ROOT, "work", "decomp")
BASE = 0x02000800


def h8(a):
    return "%08x" % a


def main():
    idx = json.load(open(os.path.join(D, "decompile-index.json")))
    funcs = {}
    for f in idx["functions"]:
        if not f["address"].startswith("0x"):
            continue
        a = int(f["address"], 16)
        rng = [(int(r["start"], 16), int(r["end"], 16)) for r in (f.get("body") or {}).get("ranges") or []]
        funcs[a] = {"name": f["name"], "path": f.get("relative_path"), "ranges": rng}

    syms = {}
    for line in open(os.path.join(ROOT, "docs", "symbols.tsv")):
        if line.startswith("#") or line.startswith("address\t") or not line.strip():
            continue
        a, kind, name, note = (line.rstrip("\n").split("\t") + [""] * 4)[:4]
        syms[int(a, 16)] = (kind, name, note)
    for a, (kind, name, _) in syms.items():
        if kind == "func" and a not in funcs and not 0x01FF8000 <= a < 0x02000000:
            print("warning: symbols.tsv func %s is not a function entry in the decompile" % h8(a), file=sys.stderr)

    # body ranges, for "which function contains this address"
    spans = sorted((s, e, a) for a, f in funcs.items() for s, e in f["ranges"])
    starts = [s for s, _, _ in spans]

    def owner(addr):
        i = bisect.bisect_right(starts, addr) - 1
        if i >= 0 and spans[i][0] <= addr <= spans[i][1]:
            return spans[i][2]
        return None

    refs = set()   # (target, from, from_func or None, kind)
    xf = os.path.join(D, "xrefs.tsv")
    if not os.path.exists(xf):
        sys.exit("missing %s: run scripts/decomp_index.sh first" % xf)
    for line in open(xf):
        t, fr, ff, kind = line.rstrip("\n").split("\t")
        if t == "target":
            continue
        refs.add((int(t, 16), int(fr, 16), None if ff == "-" else int(ff, 16), kind))
    seen = {(t, fr) for t, fr, _, _ in refs}
    data = open(os.path.join(ROOT, "work", "arm9_0x02000800.bin"), "rb").read()
    for off in range(0, len(data) - 3, 4):
        w = struct.unpack_from("<I", data, off)[0]
        t = w & ~1
        if t in funcs and (t, BASE + off) not in seen:
            fr = BASE + off
            refs.add((t, fr, owner(fr), "word"))

    callers, callees = {}, {}
    for t, fr, ff, kind in refs:
        callers.setdefault(t, []).append((fr, ff, kind))
        if ff is not None and kind in ("call", "jump"):
            callees.setdefault(ff, set()).add(t)

    def label(a):
        s = syms.get(a)
        if s and s[0] == "func":
            return "%s_%s" % (s[1], h8(a))
        return "FUN_" + h8(a)

    def some(items, n=30):
        items = list(items)
        more = " ... +%d more (grep refs.tsv)" % (len(items) - n) if len(items) > n else ""
        return " ".join(items[:n]) + more

    def rename(m):
        pre, hexa = m.group(1), m.group(2)
        a = int(hexa, 16)
        s = syms.get(a)
        if s is None or (pre == "FUN_") != (s[0] == "func"):
            return m.group(0)
        return "%s_%s" % (s[1], hexa.lower().zfill(8))

    name_re = re.compile(r"\b(FUN_|DAT_|_DAT_|PTR_DAT_)([0-9a-fA-F]{7,8})\b")
    head_re = re.compile(r"^// (rea decompile_all|name:|address:|body:|range:|non_contiguous:|provider:|analysis_profile:|limitations:|pseudocode:)")

    out = os.path.join(D, "slim")
    shutil.rmtree(out, ignore_errors=True)
    os.makedirs(out)
    sites = {a: s for a, s in syms.items() if s[0] == "site"}
    rows = []
    for a in sorted(funcs):
        f = funcs[a]
        if not f["path"] or not os.path.exists(os.path.join(D, f["path"])):
            continue
        body = [l for l in open(os.path.join(D, f["path"])).read().split("\n") if not head_re.match(l)]
        while body and not body[0].strip():
            body.pop(0)
        end = max(e for _, e in f["ranges"]) if f["ranges"] else a
        hdr = ["// %s  0x%s-0x%s (%d bytes)" % (label(a), h8(a), h8(end), end - a + 1)]
        s = syms.get(a)
        if s and s[0] == "func" and s[2]:
            hdr.append("// note: " + s[2])
        mine = [(sa, ss) for sa, ss in sites.items() if owner(sa) == a]
        for sa, ss in sorted(mine):
            hdr.append("// mod patches 0x%s: %s - %s" % (h8(sa), ss[1], ss[2]))
        cs = sorted(callers.get(a, []))
        calls = sorted({ff for fr, ff, k in cs if k in ("call", "jump") and ff is not None})
        loose = [fr for fr, ff, k in cs if k in ("call", "jump") and ff is None]
        ptrs = [(fr, ff) for fr, ff, k in cs if k not in ("call", "jump")]
        if calls:
            hdr.append("// called by: " + some(label(c) for c in calls))
        if loose:
            hdr.append("// called from code outside any function at: " + some("0x" + h8(x) for x in loose))
        if ptrs:
            hdr.append("// pointer to it at: " + some(
                "0x%s%s" % (h8(fr), "(in %s)" % label(ff) if ff else "") for fr, ff in ptrs))
        if callees.get(a):
            hdr.append("// calls: " + some(label(c) for c in sorted(callees[a])))
        text = name_re.sub(rename, "\n".join(hdr) + "\n\n" + "\n".join(body))
        open(os.path.join(out, h8(a) + ".c"), "w").write(text)
        rows.append((a, end, label(a), len(calls) + len(loose), len(ptrs), len(callees.get(a, ())),
                     (s[2] if s and s[0] == "func" else "")))

    with open(os.path.join(D, "functions.tsv"), "w") as fo:
        fo.write("address\tend\tname\tcallers\tpointers\tcallees\tnote\n")
        for a, end, lab, nc, np_, ne, note in rows:
            fo.write("0x%s\t0x%s\t%s\t%d\t%d\t%d\t%s\n" % (h8(a), h8(end), lab, nc, np_, ne, note))
    with open(os.path.join(D, "refs.tsv"), "w") as fo:
        fo.write("target\tfrom\tfrom_func\tkind\n")
        for t, fr, ff, kind in sorted(refs):
            fo.write("0x%s\t0x%s\t%s\t%s\n" % (h8(t), h8(fr), "0x" + h8(ff) if ff else "-", kind))
    words = sum(1 for r in refs if r[3] == "word")
    print("slim: %d functions, %d refs (%d found only by the word scan)" % (len(rows), len(refs), words))


if __name__ == "__main__":
    main()
