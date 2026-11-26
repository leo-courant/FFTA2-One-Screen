# The display shape is chosen when patching, from named presets

To work on displays other than the Steam Deck, the view size, zoom and sub-pixel nudge (ADR 0004) come from a display preset picked when the ROM is patched: Steam Deck 1280x800, 16:9 monitor, plain 4:3, or a custom width and height for those who build from source. Ready-made patch files are made per preset. We chose this over a settings screen inside the game because that would need menu art, somewhere to save the choice and texture memory, and nobody needs to change their display's shape mid-game; it also replaces the run-time widescreen switch once planned (decided with the user on 2026-11-23).

## Consequences

- Only measured presets promise perfectly even pixels; so far that is the Steam Deck. Other presets fill the screen and stay sharp but may show slightly uneven pixel widths until someone measures them with the grid-measuring script.
- Testing has to cover each preset that is published, at least the plain 4:3 one, where the picture must match the unmodified game's.
