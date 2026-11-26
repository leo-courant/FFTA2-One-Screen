#!/bin/sh
# Rebuild work/decomp/xrefs.tsv: every call / jump / pointer to each ARM9
# function, from a headless Ghidra analysis set up the way REA's decompile was
# (raw binary, ARM:LE:32:v7, base 0x02000800). Takes a few minutes.
# Then run scripts/slim_decomp.py to refresh work/decomp/slim/.
set -e
cd "$(dirname "$0")/.."
T=$HOME/rea-tools
export JAVA_HOME=$T/jdk-25.0.5.1+2
G=$T/ghidra_12.2_PUBLIC
P=work/ghidra-proj
rm -rf "$P"; mkdir -p "$P"
"$G/support/analyzeHeadless" "$PWD/$P" arm9 \
  -import work/arm9_0x02000800.bin \
  -loader BinaryLoader -loader-baseAddr 0x2000800 \
  -processor ARM:LE:32:v7 -cspec default \
  -scriptPath "$PWD/scripts/ghidra" \
  -postScript ExportXrefs.java "$PWD/work/decomp/xrefs.tsv" "$PWD/work/decomp/entries.txt" \
  2>&1 | grep -E 'ExportXrefs|ERROR|created|functions:' || true
test -s work/decomp/xrefs.tsv && wc -l work/decomp/xrefs.tsv
