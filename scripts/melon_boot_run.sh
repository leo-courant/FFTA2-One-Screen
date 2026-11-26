#!/bin/sh
# Runs INSIDE a headless gamescope session on the host (see melon_battle.sh): boot ROM in melonDS
# with an in-game save, run the steps, capture OUT.png; "save" saves a state to slot 1 (ROM.ml1).
# Made for Quick Saves (ticket 30): "x:3 Up:1 x:7 x:4 x:4 x:4 wait:4 save" goes from boot into
# the battle, past its announcements. usage: melon_boot_run.sh ROM SAV OUT.png [step ...]
# steps as in melon_state_run.sh
ROM="$1"; SAV="$2"; OUT="$3"; shift 3; B="${OUT%.png}"
cp "$SAV" "${ROM%.nds}.sav"
flatpak run net.kuribo64.melonDS -f "$ROM" > "$B.log" 2>&1 &
sleep 14
WID=$(xdotool search --class melonDS 2>/dev/null | tail -1)
for st in "$@"; do
  case "$st" in
    s:*) import -window "$WID" "${B}_${st#s:}.png" 2>/dev/null; sleep 0.6 ;;
    save) xdotool key --window "$WID" shift+F1; sleep 3 ;;
    wait:*) sleep "${st#wait:}" ;;
    *:*) xdotool keydown "${st%%:*}"; sleep 0.08; xdotool keyup "${st%%:*}"; sleep "${st#*:}" ;;
  esac
done
import -window "$WID" "$OUT" 2>/dev/null
pkill -KILL -x melonDS
