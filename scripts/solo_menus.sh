#!/bin/sh
# The menus as the mod shows them: one screen, widescreen, 1280x800, into
# shots/solo/NAME.png (or $O; ROM picks the build).  Walks through the menus from the test states
# (docs/test-saves.md) with scripts/solo.py; scripts/preview_menus.py builds the
# page.  usage: scripts/solo_menus.sh      (about 1 min; the walks run side by side)
# *_ov = with the SELECT overlay up, *_info = with the game's Item Info panel up.
P=.venv/bin/python; O=${O:-shots/solo}; mkdir -p $O
D="DOWN,w15"
rep() { n=$1; s=""; while [ $n -gt 0 ]; do s="$s,$2"; n=$((n-1)); done; echo "$s"; }
# RAW=1: plain play.py captures, both screens at DS resolution (the 4:3 preset and the
# unmodified game, ticket 02: ROM=rom/ffta2.nds gives the reference)
# NOSEL=1 also leaves out the SELECT overlay steps: the unmodified game has no overlay, and
# drawing it shifts animation timing, so a comparison with the plain game needs walks without it
# GUARD=1: no pictures; each walk runs under scripts/vram_guard.py instead (ticket 25),
# printing only clashes, each line prefixed with the walk's state
if [ -n "$GUARD" ]; then walk() {
    $P scripts/vram_guard.py "states/$1.dst" "$2" 2>&1 | grep -E "^(frame|  +[A-Z]|Traceback|[A-Za-z]*Error)" | sed "s|^|$1: |"; }
elif [ -n "$RAW" ]; then walk() {
    s=$2; [ -n "$NOSEL" ] && s=$(echo "$2" | sed -E 's/SELECT,w[0-9]+,s[a-z0-9_]+_ov,SELECT,w[0-9]+,//g')
    $P scripts/play.py "states/$1.dst" - "$s" $O > /dev/null 2>&1; }
else walk() { $P scripts/solo.py "states/$1.dst" "$2" $O > /dev/null; }; fi
walk s_worldmap "w10,sworldmap,SELECT,w90,sworldmap_ov,SELECT,w40,X,w60,smain,$D,$D,A,w120,ssystem,$D,$D,A,w120,sconfig,B,w90,UP,w15,UP,w15,A,w120,ssave,B,w120,B,w90,UP,w15,A,w240,sclan,A,w120,squests,B,w90,$D,A,w120,sreport,B,w120,$D,$D,$D,A,w120,sloot,B,w90,$D,A,w120,spriv,B,w90,$D,A,w120,slaws" &
walk s_party "w10,sparty,SELECT,w90,sparty_ov,SELECT,w40,A,w90,sunitmenu,A,w90,sequip,A,w90,sequip_list,B,w90,B,w90,$D,$D,A,w120,sjobs,DOWN,w30,sjobs2,DOWN,w40,sjobs3,SELECT,w90,sjobs_ov,SELECT,w40,B,w90,B,w90,X,w120,A,w60,sitemlist" &
walk s_worldmap "A,w60,stown,A,w150,w150,A,w120,spub,A,w120,scurrent,A,w120,squestdetail,B,w90,B,w90,$D,A,w120,srumors" &
walk s_worldmap "A,w60,DOWN,w20,A,w150,A,w90,A,w90,A,w90,A,w90,sshopmenu,A,w120,sbuy,SELECT,w90,sbuy_ov,SELECT,w40,B,w90,$D,A,w150,ssell,B,w90,$D,A,w150,A,w150,sfitting" &
# the road into the second battle: quest node, 76 presses through the scene (law
# announcement before press 39, unit placement before 60), then the privilege list.
# lawintro: the judge in the circle fades out and back every 31 frames, as in the
# unmodified game, so an empty circle there is a moment of the loop (ticket 35)
walk s_worldmap "DOWN12,w60,DOWN12,w60,LEFT12,w60,LEFT12,w60,UP12,w60,RIGHT12,w60,squest,A12,w150$(rep 39 A,w80),slawintro$(rep 21 A,w80),splace$(rep 16 A,w80),B,w30,B,w30,X8,w60,UP,w20,A,w240,sprivpick" &
walk s_battle2 "w10,sbattle,$D,A,w60,saction,A,w60,starget,UP,w30,A,w60,sforecast,B,w40,B,w40,B,w40,UP,w15,Y,w60,shelp,B,w40,X,w60,sbmenu,A,w90,slaw,B,w90,B,w60,Y,w90,sunitinfo,SELECT,w90,sunitinfo_ov,SELECT,w40,$D,A,w120,sabil,DOWN,w40,sabil2,SELECT,w90,sabil_ov,SELECT,w40,B,w90,$D,A,w120,sstatus" &
# View Abilities: the game's own ability list, opened with A on a category (six abilities
# with a scroll bar; the black mage's three)
walk s_battle2 "w10,B,w40,B,w40,B,w40,UP,w15,Y,w90,$D,A,w120,$D,w40,A,w120,sabil_items_list,RIGHT,w40,DOWN,w40,sabil_items_list2" &
walk s_battle2 "w10,B,w40,B,w40,B,w40,B,w40,LEFT,w30,Y,w90,$D,A,w120,sabil_mage,A,w120,sabil_mage_list" &
# the game's Item Info panel (R), with the stats the mod adds beside it
walk s_shop "w10,R12,w60,sbuy_info" &
walk s_equip "A,w90,R12,w60,sequip_info" &
# end of the tutorial battle (state kept by to_saves.sh)
[ -f states/s_results.dst ] && walk s_results "$(rep 5 A,w90),sresults,A,w90,A,w90,slawbonus" &
wait
# late in the game (ticket 24): the late save's screens (scripts/to_late.sh) and later
# battle maps (scripts/to_battles.sh), each captured as it is
for n in worldmap trials trial_detail pubmenu roster shop bazaar unitmenu setabil ivalice camoa camoa_town auction emporium auction_area auction_start; do
    [ -f states/late/l_$n.dst ] && walk late/l_$n "w10,slate_$n" &
done
# the mod's Item Info stats panel shows up here a few frames in (ticket 32)
[ -f states/late/l_setabil.dst ] && walk late/l_setabil "w90,slate_setabil_w90" &
for q in 3 7 11 13 17 18 19 20 21 22 23; do
    [ -f states/battles/b$q.dst ] && walk battles/b${q}_place "w10,sbq${q}_place" &
    [ -f states/battles/b$q.dst ] && walk battles/b$q "w10,sbq$q" &
done
wait
[ -n "$GUARD" ] || ls $O | wc -l
