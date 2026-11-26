#!/bin/sh
# Ticket 33: savestates through a bazaar trade, from states/late/l_bazaar.dst (to_late.sh).
# usage: scripts/to_bazaar.sh   (repo root, about 30 s)
# Writes states/late/l_bz_*.dst and both-screen pictures of each to shots/t33/states/.
# Made on the normal build with widescreen on: the recipe list builds its projection when
# it opens, so a state made with PLAIN=1 keeps showing it unsqueezed afterwards.
#
# The route: the first visit shows help pages (A through each).  Only loot named in white
# can be sent for a recipe; for Silver-sheened Armor, Platinum (Metals, 18th), Leucojum
# (Flora, 12th) and Silver Liquid (Philtres, 4th) are all one-star, which makes grade C:
# a Platinum Shield.  Left/Right change the loot kind.
set -e
P=.venv/bin/python; T=states/late; O=shots/t33/states; mkdir -p $O
export SDL_VIDEODRIVER=dummy
play() { $P scripts/play.py "$1" "$2" "$3" $O >/dev/null 2>&1; echo "  $2"; }

# recipe list (Bronze Armor: two loot kinds), and with Silver-sheened Armor (three) highlighted
play $T/l_bazaar.dst $T/l_bz_list.dst "w30,A,w60,A,w60,s_list"
play $T/l_bz_list.dst $T/l_bz_list3.dst "DOWN,w20,DOWN,w30,s_list3"
# its crafting menu, through the help pages
play $T/l_bz_list3.dst $T/l_bz_craft.dst "A,w90,A,w60,A,w60,A,w60,s_craft"
# Platinum sent (and the two help pages after it), then Leucojum
play $T/l_bz_craft.dst $T/l_bz_one.dst "DOWN*17,w20,A,w90,A,w90,A,w120,s_one"
play $T/l_bz_one.dst $T/l_bz_two.dst "RIGHT,w60,DOWN*11,w30,A,w60,RIGHT,w60,s_two"
# Silver Liquid: the line runs down to the header, which names the item; the Yes/Cancel box
play $T/l_bz_two.dst $T/l_bz_ask.dst "DOWN*3,w30,A,w60,s_ask"
# Yes: the new item's sheet on the info screen
play $T/l_bz_ask.dst $T/l_bz_new.dst "UP,w30,A,w150,s_new"
# B with loot sent asks whether to clear it and go back (a second Yes/No box)
play $T/l_bz_two.dst $T/l_bz_clear.dst "B,w60,s_clear"
# Bronze Armor's crafting menu (two kinds; the help pages as for the other)
play $T/l_bz_list.dst $T/l_bz_bronze.dst "A,w90,A,w60,A,w60,A,w60,s_bronze"
