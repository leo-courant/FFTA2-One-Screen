#!/bin/sh
# Ticket 24: late-game save from the world-map state by Action Replay data codes
# (scripts/cheat_save.py), saved in-game, then loaded from the title on a cold boot.
# usage: scripts/late_save.sh NAME   (env CHEATS / FLAGS / POKE passed on; defaults in cheat_save.py) -> saves/NAME.sav,
#        states/late/NAME.dst (world map after loading), shots/t24/NAME_*.png
set -e
N=$1; P=.venv/bin/python; T=states/late; O=shots/t24; mkdir -p $T $O saves
export SDL_VIDEODRIVER=dummy
$P scripts/cheat_save.py states/s_worldmap.dst $T/tmp_$N.dst $CHEATS 2>&1 | grep -E 'writes|poke|flags|progress|auction|refused' || true
# with an auction month set the world map first says the auction houses are open: dismiss it
PRE=""; [ "${AUCTION:-8}" != 0 ] && PRE="w30,A8,w90,"
$P scripts/play.py $T/tmp_$N.dst - "${PRE}X,w60,DOWN,w15,DOWN,w15,A,w120,A,w120,A,w120,A,w120,w300,esaves/$N.sav" $O >/dev/null 2>&1
$P scripts/play.py - $T/$N.dst "isaves/$N.sav,w1500,DOWN,w30,A,w180,A,w120,UP,w20,A,w400,w200,A,w120,UP,w20,A,w600,w300,A,w300,A,w300,w600,B,w90,s${N}_map" $O >/dev/null 2>&1
rm -f $T/tmp_$N.dst
echo "$N done"
