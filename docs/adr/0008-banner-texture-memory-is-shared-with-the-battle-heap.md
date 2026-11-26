# The banner's texture memory is shared with the game's battle texture heap

The banner and turn order are textures on 3D quads (ticket 07), so they need texture memory the game is not using at that moment. Textures can only live in the four texture banks, and every emulator reproduces the DS's video memory exactly, so there is none to add. On entering a battle the game (vram_scene_setup, 0x020A0E74, scene mode 2) sets up a texture heap from 0x2E000 to the very end of texture bank B (size 0x12000) and hands out unit sprites and effects from it. The first banner simply used the last 4 KB of that heap, which only worked because the two test battles never filled it.

The heap is a pair of linked lists, free and used, of nodes { prev, next, start, size }; the record is `*(u32 *)0x0212F048` = { start, size, free list, used list }. Both allocators (0x020A23B8 first fit, 0x020A2458 exact fit) carve blocks off the front of the first free block that fits, so the heap fills from the bottom and its top is the last part used (the second battle reaches 0x38600 of 0x40000).

So the mod shares the top `HUD_TEX_SIZE` (8 KB, set in `scripts/patch.py`): the units of the turn order in the lower 4 KB, the banner text in the top 4 KB. Every frame, right before it writes or draws, it checks the free list: it uses each half only while the game has nothing there, and uploads again once the game has let go. The game allocates only on its main loop, and the check and the write happen in the same call of the mod's hook, so the game cannot slip in between.

We first shrank the heap instead (patching its size at 0x020A0F68), which made the memory the mod's alone but took 8 KB from every battle for good. Sharing costs the game nothing.

## Consequences

- In a battle that ever needs the whole heap, the turn order disappears first and the banner text after it, until the game frees the space. Not seen in the two battles tested.
- Other scenes (the world map) put their own data in this memory; the banner uploads again every time the battle HUD comes back, so it is never stale.
- The texture palette at 0x3A00-0x3BFF is outside every area the game's table gives a battle; it is used without a check.
- Checked with `scripts/vram_guard.py` (ticket 25) over every battle test state, including SELECT taps and holds: no game draw from the banner's data, and no banner draw from bytes the game changed, in the texture range or the palette range.
- If the heap record or its nodes are not where expected (no battle heap), the memory counts as free.
