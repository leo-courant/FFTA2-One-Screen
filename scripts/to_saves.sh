#!/bin/sh
# Ticket 03: replay from the first battle's command menu (states/p_battle.dst, made
# by to_battle.sh) to the five test situations, on the current build.
# usage: scripts/to_saves.sh            (run from the repo root, ~5 min)
# Writes states/s_worldmap.dst s_shop.dst s_party.dst s_equip.dst s_battle2.dst s_results.dst
# and saves/worldmap.sav (in-game save, slot 1, standing on the world map).
# Segments are separate play.py runs on purpose: each one costs one extra frame
# after loading, and the timings below were found that way.
set -e
P=.venv/bin/python; T=states/tmp_saves; mkdir -p $T saves
rep() { n=$1; s=""; while [ $n -gt 0 ]; do s="$s,$2"; n=$((n-1)); done; echo "$s"; }
play() { $P scripts/play.py "$1" "$2" "$3" $T >/dev/null 2>&1; echo "  $2"; }
A5="A,w60,A,w60,A,w60,A,w60,A,w90"

echo "battle 1 (tutorial)"
# Alulis: Move one tile, Wait, confirm facing
play states/p_battle.dst $T/01.dst "w30,A,w30"
play $T/01.dst $T/02.dst "RIGHT,w10,A,w40,A,w40,A,w60"
play $T/02.dst $T/03.dst "A,w90,w90,w120,w120"
play $T/03.dst $T/04.dst "A,w60,A,w90,w120,A,w90,A,w90,A,w90"
play $T/04.dst $T/05.dst "$(rep 12 A,w80)"
# Black mage: move three tiles toward Klesta, Action > Black Magick > Fire on Klesta
play $T/05.dst $T/06.dst "A,w60,A,w60,A,w40,RIGHT,w10,RIGHT,w10,RIGHT,w10"
play $T/06.dst $T/07.dst "A,w60,DOWN,w10,A,w30,A,w30,A,w30"
play $T/07.dst $T/08.dst "DOWN,w10,A,w30,A,w30,A,w40,A,w40,A,w120,A,w120"
play $T/08.dst $T/09.dst "$(rep 18 A,w90)"       # Cid acts, hints
play $T/09.dst $T/10.dst "$(rep 18 A,w90)"       # ends with Luso's move grid open
# Luso: move next to Cid, then Action > Items > Potion on himself.  Any action by
# Luso makes Klesta flee and the battle end; the HP pokes are not needed for that.
play $T/10.dst $T/11.dst "p02129FE8=1,p0212A104=1,p0212A220=1,p0212A33C=1,RIGHT,w12,RIGHT,w12,RIGHT,w12,UP,w12,A,w70,DOWN,w10,A,w30,A,w30,A,w30,UP,w12,A,w40,A,w150,w120,w120,w120"
play $T/11.dst $T/12.dst "B,w30,DOWN,w10,DOWN,w10,A,w30,A,w30,A,w40,A,w150$(rep 11 A,w90)"
cp $T/12.dst states/s_results.dst                # five presses before the results screen
play $T/12.dst $T/13.dst "$(rep 24 A,w90)"       # Complete!, results, law bonus
echo "story to the world map"
play $T/13.dst $T/14.dst "$(rep 24 $A5)"         # first world map (Targ Wood)
# world map needs ~12-frame presses: cursor right to Wood Village, travel there
play $T/14.dst $T/15.dst "RIGHT12,w60,A12,w120,A12,w120,A12,w120,A12,w120,A12,w120"
play $T/15.dst $T/16.dst "$(rep 16 $A5)"         # pub scene, ends on clan name entry
# clan name: X = Done, Up = Yes; then pub tutorial up to the quest's detail page
play $T/16.dst $T/17.dst "X,w40,UP,w20,A,w90$(rep 16 $A5)"
# accept "A Paw Full of Feathers" (prompt defaults to No), leave the pub
play $T/17.dst states/s_worldmap.dst "A,w60,UP,w20,A,w90$(rep 21 A,w70),A,w90"

echo "menus"
# town menu > Shop > talk > Buy > first category
play states/s_worldmap.dst states/s_shop.dst "A,w60,DOWN,w20,A,w150,A,w90,A,w90,A,w90,A,w90,A,w120"
# X = Main Menu > Unit Info (party list)
play states/s_worldmap.dst states/s_party.dst "X,w60,A,w120,A,w90"
# first unit > Change Equipment
play states/s_party.dst states/s_equip.dst "A,w90,A,w90"
# Main Menu > System Menu > Save > slot 1
play states/s_worldmap.dst - "X,w60,DOWN,w15,DOWN,w15,A,w120,A,w120,A,w120,A,w120,w300,esaves/worldmap.sav"

echo "battle 2 (law + clan privilege)"
# cursor to Muskmallow Field (free cursor: down, down, left, left, up, right), travel
play states/s_worldmap.dst $T/20.dst "DOWN12,w60,DOWN12,w60,LEFT12,w60,LEFT12,w60,UP12,w60,RIGHT12,w60,A12,w150$(rep 14 A,w70,A,w90)"
play $T/20.dst $T/21.dst "$(rep 24 A,w70,A,w90)" # scene, law intro, places 5 units
# X = finish placement (Up = Yes), pick privilege Power^1 (prompt defaults to Back)
play $T/21.dst $T/22.dst "B,w30,B,w30,X8,w60,UP,w20,A,w240,A,w90,UP,w20,A,w150$(rep 13 A,w100)"
play $T/22.dst states/s_battle2.dst "$(rep 16 w150)"   # wolves act; stops on Alulis's command menu
rm -r $T
echo done
