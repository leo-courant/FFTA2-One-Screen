#!/bin/sh
# Ticket 24: savestates at the screens the late save opens, from states/late/late.dst
# (made by scripts/late_save.sh late). usage: scripts/to_late.sh   (repo root, about 1 min)
# Writes states/late/l_*.dst and both-screen pictures of each to shots/t24/late/.
set -e
P=.venv/bin/python; T=states/late; O=shots/t24/late; mkdir -p $O
export SDL_VIDEODRIVER=dummy
play() { $P scripts/play.py "$1" "$2" "$3" $O >/dev/null 2>&1; echo "  $2"; }

cp $T/late.dst $T/l_worldmap.dst
# Pub: the first visit at this story progress explains clan titles and opens the Clan Trials list
play $T/late.dst $T/l_trials.dst "A,w60,A,w200,A,w100,A,w100,A,w100,A,w100,A,w100,A,w100,A,w100,A,w100,A,w100,A,w120,s_trials" &
# Shop menu with Bazaar and Sell Loot
play $T/late.dst $T/l_shop.dst "A,w60,DOWN,w20,A,w150,A,w90,A,w90,A,w90,A,w120,A,w120,s_shop" &
# Main Menu > Unit Info > first unit > unit menu (Set Abilities enabled)
play $T/late.dst $T/l_unitmenu.dst "X,w60,A,w120,A,w90,A,w90,s_unitmenu" &
# Camoa Highroad: travelling opens the map of all Ivalice
play $T/late.dst $T/l_ivalice.dst "R8,w60,A,w120,s_ivalice" &
wait
play $T/l_trials.dst $T/l_trial_detail.dst "A8,w150,s_trial_detail" &
play $T/l_trials.dst $T/l_pubmenu.dst "B8,w120,s_pubmenu" &
play $T/l_shop.dst $T/l_bazaar.dst "DOWN,w20,DOWN,w20,DOWN,w20,A,w150,s_bazaar" &
play $T/l_unitmenu.dst $T/l_setabil.dst "w30,DOWN8,w40,A8,w300,A8,w200,A8,w200,A8,w200,A8,w200,A8,w200,s_setabil" &
play $T/l_ivalice.dst $T/l_camoa.dst "w300,A,w120,w300,s_camoa" &
wait
play $T/l_pubmenu.dst $T/l_roster.dst "w30,UP,w30,UP,w30,A,w150,s_roster"
# Auctions (the auction month is set in the save): Camoa's town menu gains Auction House
play $T/l_camoa.dst $T/l_camoa_town.dst "R8,w60,R8,w60,R8,w60,A,w300,s_camoa_town"
play $T/l_camoa_town.dst $T/l_auction.dst "DOWN8,w30,DOWN8,w30,A,w200,A8,w150,s_auction"
play $T/l_auction.dst $T/l_emporium.dst "A8,w150,A8,w150,A8,w150,s_emporium"
play $T/l_emporium.dst $T/l_auction_area.dst "A8,w150,s_auction_area"
play $T/l_auction_area.dst $T/l_auction_start.dst "A8,w150,s_auction_start"
play $T/l_auction_start.dst $T/l_auction_round.dst "A8,w150,s_auction_round"
play $T/l_auction_round.dst $T/l_auction_bid.dst "A8,w150,s_auction_bid"
