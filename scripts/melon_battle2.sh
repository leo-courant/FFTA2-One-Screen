#!/bin/sh
# Capture the second battle (law + privilege) in melonDS from the in-game save.
# usage: scripts/melon_battle2.sh [OUT.png] [save]     (from the VS Code flatpak; ~5 min)
# "save": also save a melonDS savestate at the end (Alulis's command menu) to ROM.ml1,
# the base state states/m_battle2.ml1 for scripts/melon_state.py.
# Env: ROM (default build/ffta2-1screen.nds), SIZE (display, default 1280x800).
# Runs melonDS at normal speed for the duration (the world map cursor needs
# frame-timed presses), then puts the 4x test speed back.  Also leaves
# OUT_cursor/_a/_b/_c/_d.png checkpoints; OUT_d is a wolf's turn.
OUT="${1:-shots/melon/t09_battle2.png}"
rep() { n=$1; s=""; while [ $n -gt 0 ]; do s="$s,$2"; n=$((n-1)); done; echo "$s"; }
# as "battle 2" in to_saves.sh, but with 8-frame cursor presses: xdotool adds a
# couple of frames to each hold, and the cursor overshoots from about 14
SCR="DOWN8,w60,DOWN8,w60,LEFT8,w60,LEFT8,w60,UP8,w60,RIGHT8,w60,scursor,A12,w150$(rep 14 A,w70,A,w90),sa$(rep 24 A,w70,A,w90),sb,B,w30,B,w30,X8,w60,UP,w20,A,w240,A,w90,sc,UP,w20,A,w150$(rep 13 A,w100),sd$(rep 16 w150)"
[ "$2" = save ] && SCR="$SCR,w60,save"
case "$OUT" in /*) ;; *) OUT="$PWD/$OUT";; esac
R=$(cd "$(dirname "$0")/.." && pwd)
ROM="${ROM:-build/ffta2-1screen.nds}"; case "$ROM" in /*) ;; *) ROM="$R/$ROM";; esac
SW="${SIZE%x*}"; SH="${SIZE#*x}"; [ -n "$SIZE" ] || { SW=1280; SH=800; }
cd ~ && flatpak-spawn --host sh -c "
  C=~/.var/app/net.kuribo64.melonDS/config/melonDS/melonDS.toml
  sed -i 's/^TargetFPS = .*/TargetFPS = 60.0/' \$C
  timeout 420 gamescope --backend headless -W $SW -H $SH -w $SW -h $SH -f -- $R/scripts/melon_play.sh $ROM $R/saves/worldmap.sav $OUT '$SCR' >/dev/null 2>&1
  pkill -x gamescope; pkill -KILL -x melonDS
  sed -i 's/^TargetFPS = .*/TargetFPS = 240.0/' \$C"
ls -la "$OUT"
