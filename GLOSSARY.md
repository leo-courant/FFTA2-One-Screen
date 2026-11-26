# FFTA2 Single-Screen Mod

A patch for Final Fantasy Tactics A2 (Nintendo DS, USA) that makes the game fully playable on one display in an emulator. The Steam Deck OLED is the tested setup; other single-display devices are expected to work.

## Language

### Screens

**Gameplay screen**:
The DS screen the game uses for the map, units, menus and all input; originally the bottom screen. It is the only screen the player sees in the mod.
_Avoid_: bottom screen, main screen, touch screen

**Info screen**:
The DS screen the game uses for supporting information such as the objective, law and turn order; originally the top screen.
_Avoid_: top screen, sub screen, second screen

**Detailed view**:
The info screen shown full-size in place of the gameplay screen while the player asks for it.
_Avoid_: peek, swap, toggle view

**Overlay**:
Info screen content drawn as a translucent panel in front of the gameplay screen, in menus only (not in story scenes, after-battle dialogue or on the title). Whole-screen on a button, or just the stats beside the game's Item Info panel.
_Avoid_: popup, sheet view

**Dual-screen menu**:
Any non-battle mode where the game splits one task across both screens, such as shops, the party list and equipment.

### Controls

**Mod control**:
An action the mod adds while playing. There are two: show the info screen (detailed view in battle, overlay in menus), on a tap of SELECT, and switch the banner on or off, on a hold of SELECT. Which physical button sends SELECT is set outside the game, in the emulator or the device's own button mapping.
_Avoid_: hotkey, shortcut, binding

### Battle HUD

**Banner**:
The mod's bar across the top of the gameplay screen that carries the objective, the law and the privilege.
_Avoid_: top bar, header, strip

**Objective**:
The win condition text of the current battle, e.g. "Defeat Klesta!".

**Law**:
The judge's rule for the current battle, e.g. "Forbidden: Ranged Weapons".
_Avoid_: rule

**Privilege**:
The clan bonus the player picks before a battle, e.g. "Power↑1"; the info screen lists it under the law. It is the reward side of the law: it holds for the battle as long as the law is not broken.
_Avoid_: special rule, clan ability

**Special rule**:
Any further per-battle condition the game shows on the info screen besides the objective and the law. The only one found is the privilege; say privilege when that is what is meant.

**Turn order**:
The sequence of units about to act, shown by the mod as the stage: four units standing at the bottom of the gameplay screen, the acting unit first on an orange ring, with a row of pips for the coming turns. Browsing ahead with L/R puts a light-blue arrow over the browsed unit.
_Avoid_: timeline, queue

**Pip**:
One coming turn in the turn order's row of small diamonds, blue for an ally's turn and red for an enemy's; the first pip is the acting unit's turn. Read from the info screen's own pip strip.

**Acting unit**:
The unit whose turn it is. Not the same as the browsed unit, the one the player looks at with L/R.

**Game panel**:
A HUD element the original game draws on the gameplay screen itself: the unit status panel with portrait, the command menu, the Config/Help buttons and the height tab.
_Avoid_: widget, window

### Widescreen

**Widescreen**:
Showing the gameplay screen at the display's 16:10 shape with more of the scene visible at the sides, instead of a 4:3 picture with black bars.

**Side area**:
The part of a widescreen picture that lies outside the original 4:3 view, left or right.
_Avoid_: band, margin, bar

**Backdrop**:
The decorative background image behind the battle map, visible wherever the map does not cover the screen.

**Display preset**:
A named display shape the patch is made for, such as the Steam Deck, a 16:9 monitor or plain 4:3. It is chosen when the ROM is patched and fixes how much of the scene is shown, including whether there is widescreen or zoom-out at all; neither can be changed while playing.
_Avoid_: profile, target, resolution setting

**Measured preset**:
A display preset whose pixels have been checked to come out perfectly even on its display. The Steam Deck is the only one so far.

**Zoom-out**:
Showing more of the scene in both directions by drawing everything smaller.
