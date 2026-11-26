#!/bin/sh
# Replay the scripted inputs from power-on to the first battle's command menu.
# usage: to_battle.sh ROM OUTDIR STATE
S="w1500"
for i in $(seq 1 320); do S="$S,A4,w22"; done            # new game -> name entry (fills name)
S="$S,X4,w40,UP4,w20,A4,w60"                             # Done -> Yes
for i in $(seq 1 400); do S="$S,A4,w22"; done            # intro scenes
for i in $(seq 1 400); do S="$S,A4,w22"; done            # into first battle
S="$S,sbattle"
SDL_VIDEODRIVER=dummy SDL_AUDIODRIVER=dummy exec .venv/bin/python scripts/run.py "$1" "$2" "$S" --save "$3"
