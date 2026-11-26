# Mod controls are a tap and a hold of SELECT, with no in-game remapping

The game can only read the DS's 12 buttons, whatever device the emulator runs on; a Steam Deck back paddle is invisible to it unless the emulator or Steam Input makes it send one of those 12. The game uses SELECT only as part of the soft reset (L+R+START+SELECT), found by checking every place its code reads the buttons, so SELECT is the one free button. The user wanted no two-button controls, so the mod's two controls share it: a tap shows the info screen, a hold of about half a second switches the banner. The info screen therefore appears when SELECT is let go rather than when it is pressed. Mapping physical buttons to SELECT is left to the emulator or Steam Input; an in-game remap menu could only shuffle the same 12 buttons and would cost texture memory the game barely has (decided with the user on 2026-11-23).

## Considered options

- L+SELECT for the banner (the earlier control): instant, one paddle on the Deck through Steam Input, but two buttons on a keyboard or phone.
- A modified emulator with an extra button: works on the Deck only, and every other player would need our build.

## Consequences

- Outside battle, a tap shows the info screen only in menus. In story scenes, after-battle dialogue and on the title it does nothing (ticket 31, the user's choice on 2026-11-24). The hold for the banner works everywhere.
- A third control has no free button. The spares held in reserve, not yet checked: the emulator's "close lid" key (the game would have to be kept from sleeping) and a tap in a screen corner (the game already uses touch, and widescreen moves where a tap lands).
- Story scripts and some text-box settings are data the check did not read; one of them could still test SELECT.
