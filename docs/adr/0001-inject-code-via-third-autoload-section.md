# Inject mod code as a third ARM9 autoload section at the old heap start

The ARM9 binary has no usable free space, so the mod's compiled code is appended as a third startup "autoload" section that the game's own boot code copies to 0x02143E20, the address where the main heap used to start; the heap start constant is moved up by 0x2000 to make room. To let the ARM9 binary grow inside the ROM, the overlay table and overlay 0 are relocated to the end of the ROM. We chose this over overwriting unused strings (only ~200 bytes, proven with the first screen-swap patch), over loading code from the cartridge at runtime, and over adding an overlay, because it needs no knowledge of the game's file or overlay loading functions and gives 8 KB that can be grown by changing one constant.

## Consequences

- Savestates made with a different build contain the old code and heap layout; test states must be regenerated from the same ROM, or the blob re-injected by hand.
- The secure-area checksum in the header is not recomputed, so the ROM is only known to work in emulators.


Update 2026-11-23: the reserve is now 16 KB (heap start moved up by 0x4000), see ADR 0005.
