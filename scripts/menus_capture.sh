#!/bin/sh
# Ticket 10: capture both screens of the menus reachable from the test states
# (docs/test-saves.md), widescreen off, into shots/menus/NAME.png.  ~3 min.
# usage: scripts/menus_capture.sh     then scripts/preview_menus.py
# Each line: NAME PARENT STEPS; PARENT is a test state (s_*, late/l_* from to_late.sh,
# battles/b* from to_battles.sh) or an earlier NAME.
# Not made here (captured once while replaying to_saves.sh by hand): lawintro,
# place, privpick, results, lawbonus, name, roster, questdetail, story, b_useitem.
T=states/tmp_menus; mkdir -p $T shots/menus
D="DOWN,w15"
while read name parent steps; do
  [ -z "$name" ] && continue
  case "$parent" in s_*|late/*|battles/*) in=states/$parent.dst;; *) in=$T/$parent.dst;; esac
  PLAIN=1 .venv/bin/python scripts/play.py "$in" "$T/$name.dst" "$steps,s$name" shots/menus >/dev/null 2>&1 \
    && echo "  $name" || echo "FAILED $name"
done <<LIST
wm s_worldmap w10
wm_cursor s_worldmap DOWN12,w60,DOWN12,w60,LEFT12,w60,LEFT12,w60,UP12,w60,RIGHT12,w60
main s_worldmap X,w60
system main $D,$D,A,w120
config system $D,$D,A,w120
save system A,w120
town s_worldmap A,w60
pub town A,w150,w150
pub3 pub A,w120
p_current pub3 A,w120
p_rumors pub3 $D,A,w120
shop0 town DOWN,w20,A,w150
shop_sell shop0 A,w90,A,w120,A,w90,$D,A,w120
fitting shop_sell $D,$D,A,w150
sell shop_sell $D,A,w150
shop s_shop w10
clan main $D,A,w120,w120
clan2 clan w1
c_quests clan A,w120
c_report clan $D,A,w120
c_loot clan $D,$D,$D,$D,A,w120
c_priv clan $D,$D,$D,$D,$D,A,w120
c_laws clan $D,$D,$D,$D,$D,$D,A,w120
party s_party w10
unitmenu s_party A,w90
equip s_equip w10
jobs unitmenu $D,$D,A,w120
jobs2 jobs DOWN,w30
itemlist s_party X,w120
b2 s_battle2 w10
b_config b2 X,w60
b_law b_config A,w90
b_items b_config UP,w15,A,w90
b_help b2 Y,w60
b_free b2 B,w60
b_unitinfo b_free Y,w90
b_status b_unitinfo $D,$D,A,w120
b_abil b_unitinfo $D,A,w120
b_action b2 $D,A,w60
b_attack b_action A,w60
b_attack2 b_attack UP,w30,A,w60
late_worldmap late/l_worldmap w10
late_trials late/l_trials w10
late_trial_detail late/l_trial_detail w10
late_pubmenu late/l_pubmenu w10
late_roster late/l_roster w10
late_shop late/l_shop w10
late_bazaar late/l_bazaar w10
late_unitmenu late/l_unitmenu w10
late_setabil late/l_setabil w10
late_ivalice late/l_ivalice w10
late_camoa late/l_camoa w10
late_camoa_town late/l_camoa_town w10
late_auction late/l_auction w10
late_emporium late/l_emporium w10
late_auction_area late/l_auction_area w10
late_auction_start late/l_auction_start w10
late_auction_round late/l_auction_round w10
late_auction_bid late/l_auction_bid w10
bq3_place battles/b3_place w10
bq3 battles/b3 w10
bq7_place battles/b7_place w10
bq7 battles/b7 w10
bq11_place battles/b11_place w10
bq11 battles/b11 w10
bq13_place battles/b13_place w10
bq13 battles/b13 w10
bq17_place battles/b17_place w10
bq17 battles/b17 w10
bq18_place battles/b18_place w10
bq18 battles/b18 w10
bq19_place battles/b19_place w10
bq19 battles/b19 w10
bq20_place battles/b20_place w10
bq20 battles/b20 w10
bq21_place battles/b21_place w10
bq21 battles/b21 w10
bq22_place battles/b22_place w10
bq22 battles/b22 w10
bq23_place battles/b23_place w10
bq23 battles/b23 w10
LIST
rm -r $T
