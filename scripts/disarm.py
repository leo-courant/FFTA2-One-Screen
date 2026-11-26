#!/usr/bin/env python3
"""Disassemble a range of the ARM9 binary. usage: dis.py START END [thumb] [file base]"""
import struct
import sys
import capstone

start, end = int(sys.argv[1], 16), int(sys.argv[2], 16)
thumb = len(sys.argv) > 3 and sys.argv[3] == "thumb"
path = sys.argv[4] if len(sys.argv) > 4 else "unpacked/arm9.bin"
base = int(sys.argv[5], 16) if len(sys.argv) > 5 else 0x02000000
d = open(path, "rb").read()
md = capstone.Cs(capstone.CS_ARCH_ARM, capstone.CS_MODE_THUMB if thumb else capstone.CS_MODE_ARM)
md.skipdata = True
for i in md.disasm(d[start - base:end - base], start):
    extra = ""
    if "[pc" in i.op_str and i.mnemonic.startswith("ldr"):
        try:
            off = int(i.op_str.split("#")[1].rstrip("]"), 0)
            pc = (i.address + (4 if thumb else 8)) & ~3
            extra = "   ; =0x%08x" % struct.unpack_from("<I", d, pc + off - base)[0]
        except Exception:
            pass
    print("%08x: %-8s %s%s" % (i.address, i.mnemonic, i.op_str, extra))
