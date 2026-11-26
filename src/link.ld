/* Injected code blob for FFTA2 (USA). Loaded by the game's own startup
   autoload into the gap opened by moving the main heap start.  The variables
   (.bss) are not in the blob: they sit right after its reserve, at BSS_ADDR
   (patch.py fills it in), where the same autoload entry has the game's startup
   code zero them (ADR 0017). */
ENTRY(entry_table)
SECTIONS {
  . = 0x02143E20;
  .text : { KEEP(*(.entry)) *(.text*) *(.rodata*) *(.data*) }
  . = BSS_ADDR;
  .bss (NOLOAD) : { bss_start = .; *(.bss*) *(COMMON) bss_end = .; }
  /DISCARD/ : { *(.ARM.*) *(.comment) *(.note*) }
}
