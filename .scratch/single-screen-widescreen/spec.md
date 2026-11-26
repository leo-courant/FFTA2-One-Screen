# Spec: FFTA2 single-screen widescreen mod

Status: ready-for-agent

## Problem Statement

Final Fantasy Tactics A2 splits its picture across two DS screens. On a Steam Deck the emulator can only show the second screen as a small off-centre window beside the first, which the player finds ugly and distracting, and the main picture is a 4:3 rectangle with black bars on a 16:10 display.

## Solution

A patched ROM, for the Steam Deck first but usable on any single display an emulator runs on, in which everything needed to play is on the gameplay screen, shown full-screen and centred. In battle a banner carries the objective, the law and any special rules, with the turn order beside it. The info screen remains reachable as a detailed view on a button. The picture fills the Deck's 16:10 display in widescreen, with the map and backdrop continuing into the side areas, the game panels sitting at the screen edges, and optionally a slight zoom-out. Dual-screen menus such as shops, party and equipment are handled so nothing on the info screen is needed blind.

## User Stories

1. As a player, I want the objective visible on the gameplay screen at all times in battle, so that I never need the info screen to know how to win.
2. As a player, I want the law visible at all times in battle, so that I don't break it by accident.
3. As a player, I want special rules visible at all times in battle, so that nothing that constrains me is hidden.
4. As a player, I want to see the turn order on the gameplay screen, so that I can plan around who acts next.
5. As a player, I want the focused unit marked in the turn order, so that I can tell whose turn it is at a glance.
6. As a player, I want long objective or law text to remain readable, so that I am not guessing at cut-off words.
7. As a player, I want to hide and show the banner with a button, so that I can have a clean view of the map when I want one.
8. As a player, I want a button that shows the info screen full-size, so that I can still read details such as an enemy's weaknesses.
9. As a player, I want the picture to fill my Deck's screen without black bars, so that the game uses the whole display.
10. As a player, I want the map to continue into the side areas, so that widescreen shows more of the battlefield rather than empty space.
11. As a player, I want the backdrop to continue into the side areas where there is no map, so that there are no black or striped regions.
12. As a player, I want text and pixel art to stay sharp in widescreen, so that the game does not look stretched or blurred.
13. As a player, I want the game panels to sit at the screen edges in widescreen, so that they do not float in the middle of the map.
14. As a player, I want a slight zoom-out option, so that I see more of the map while the pixel art stays clean.
15. As a player on a 4:3 display, I want a 4:3 version of the patch, so that the game looks right on my screen.
16. As a player, I want shops, the party list and equipment screens to be usable on one screen, so that I can manage my clan without a second display.
17. As a player, I want the banner to appear only when the game is showing its battle HUD, so that it never covers story scenes or menus.
18. As a player, I want every mod control on a single button, so that it is easy to use on a Deck, a keyboard or a phone alike.
19. As a player, I want a short setup guide, so that I know which emulator settings and button mappings the mod expects on my device.
20. As the developer, I want test saves at the world map, in a shop, in the party menu and in a battle with special rules, so that each screen can be checked without replaying the opening.
21. As a player who is not the developer, I want ready-made patch files for common displays, so that I can play without installing a compiler.
22. As a player with an unusual display, I want to build a patch for my own screen size, so that the picture fills it.

## Implementation Decisions

- The mod is a patch applied to the USA ROM by a build script; mod code is written in C, compiled to a blob, and injected as described in ADR 0001.
- A per-frame hook at the end of the game's key update runs all mod logic and reads the game's own pressed/held key state.
- The banner and turn order currently copy rendered tiles and sprites from the info screen (ADR 0002). Under widescreen, HUD that must be crisp is redrawn through the 3D path instead; the info screen stays the source of truth for content.
- Battle HUD presence is detected from the info screen's frame layout, not from game state.
- Widescreen scales the projection inside the SDK's orthographic projection routine (ADR 0003). The view size, zoom and sub-pixel nudge come from the display preset chosen when patching (ADR 0007); there is no switch while playing.
- Side areas: map tiles are drawn beyond the original edge by widening the game's own visibility limit; the backdrop is continued by extending its edge.
- Game panels are re-anchored: left-side panels move to the left edge, right-side panels to the right edge, by the same distance the view was widened.
- Controls (ADR 0006): tap SELECT for the info screen, hold SELECT to switch the banner. No combinations, no in-game remapping; players map their own buttons in the emulator or Steam Input. The game's soft reset (L+R+START+SELECT) is left alone. Spare inputs held in reserve, unchecked: closing the lid, tapping a screen corner.
- Turn order may take visual cues from Triangle Strategy's bar (framed heads in a row, the acting unit emphasised), as long as it stays compact.
- Target: any emulator that draws 3D at high resolution and can show one screen full-size. melonDS on a Steam Deck OLED is the setup that is tested; others are documented as expected to work. DS hardware and flashcarts are not supported and never will be.
- Publishing (only when the user says so, after an audit of the git history for game data): MIT license; README says the project is unaffiliated with Square Enix and Nintendo, players dump their own cartridge, and the repo never links to or hosts ROMs. Published patches hold only the mod's own code and references to the player's ROM, checked automatically for original game bytes on every release. The only game pictures in the repo are a few README examples of the mod's screen. AI-enlarged or AI-extended art made from the game's pictures need not stay private (user, 2026-11-25; until then it was never published).

## Testing Decisions

- Tests check what the player sees: screenshots of the gameplay screen from an emulator run of the built ROM, driven by scripted input from a known save or savestate. They do not assert on internal memory layout.
- The existing headless emulator rig is the regression harness for layout and behaviour at DS resolution. Sharpness and final look can only be judged in melonDS at high resolution, so every widescreen ticket ends with a melonDS capture.
- Every visual result is delivered to the user as a browser preview link.
- Savestates contain the code of the build that made them; each build needs states regenerated or the blob re-injected before testing.

## Out of Scope

- Running on real DS hardware or flashcarts.
- Other regions or revisions of the game.
- Changing game rules, balance, text or art beyond what the HUD needs.
- Touch-screen input support.
- Distributing the ROM or any part of it.
- An in-game settings or button-remapping menu.

## Further Notes

- The first battle is a tutorial that ignores "Wait" until its scripted steps are followed; zeroing enemy HP in memory does not end it.
- The sharpness test (ticket 01) is a go/no-go for widescreen. If it fails, tickets 04 to 08 are dropped and the mod ships 4:3.
