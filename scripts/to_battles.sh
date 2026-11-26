#!/bin/sh
# Tickets 24 and 38: savestates on later battle maps without travelling there. Walks the road
# into the second battle (quest 2, from states/s_worldmap.dst) and, as that battle is set up,
# swaps in another story quest whole (play.py QUEST: its record, scene row and unit set), so
# the map, scenes, law, objective, enemies and their squares are all that quest's. The party is
# still the early one. (Before ticket 38 only the battlefield bytes were swapped: the enemies
# were quest 2's, off the map.)
# usage: scripts/to_battles.sh [QUEST...]   (repo root; about 25 min, the quests run side by side)
# Writes states/battles/b<Q>_place.dst (unit placement) and b<Q>.dst (the fight, after the
# first turns), and both-screen pictures to shots/t24/battles/.
set -e
P=.venv/bin/python; T=states/battles; O=shots/t24/battles; mkdir -p $T $O
export SDL_VIDEODRIVER=dummy
rep() { n=$1; s=""; while [ $n -gt 0 ]; do s="$s,$2"; n=$((n-1)); done; echo "$s"; }
ROAD="DOWN12,w60,DOWN12,w60,LEFT12,w60,LEFT12,w60,UP12,w60,RIGHT12,w60,A12,w150"
# quest, or quest:S where the battle is chained to the one before it (no arrival on the world
# map): S is the scene script to start with, since its dispatcher starts the after-battle talk
ALL="3 7 11 13 17 18:0 19 20 21 22 23"
WANT="$*"
one() {
    q=${1%%:*}
    # every quest's opening scene is over by 160 presses (A on unit placement only repeats
    # a "party is full" message)
    QUEST=$1 $P scripts/play.py states/s_worldmap.dst $T/b${q}_place.dst \
        "$ROAD$(rep 160 A,w80),w60,sb${q}_place" $O >/dev/null 2>&1
    # B B leaves the unit list, X then Up+A = begin with this party, A then Up+A = the first
    # clan privilege, then the opening turns play by themselves
    $P scripts/play.py $T/b${q}_place.dst $T/b${q}.dst \
        "B,w30,B,w30,X8,w60,UP,w20,A,w240,A,w120,UP,w20,A,w900,sb${q}" $O >/dev/null 2>&1
    echo "  quest $q"
}
for x in $ALL; do
    q=${x%%:*}
    if [ -n "$WANT" ] && ! echo " $WANT " | grep -q " $q "; then continue; fi
    one "$x" &
done
wait
