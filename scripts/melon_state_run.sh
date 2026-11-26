#!/bin/sh
# Runs INSIDE a headless gamescope session on the host; started by scripts/melon_state.py.
# Boot ROM in melonDS, load savestate slot 1 (ROM.ml1, F1), run the steps, capture OUT.png.
# usage: melon_state_run.sh ROM OUT.png [step ...]
# steps: KEY[:seconds]  press an xdotool key (x = A, z = B, s = X, a = Y, q = SELECT,
#                       1 = L, 2 = R, Return = START, arrows), then wait (default 1 s)
#        hold:KEY:seconds  hold a key down that long
#        s:NAME         capture to OUT_NAME.png (so X with a wait is "s wait:N" or "hold:s:0.1")
#        save           save the state to slot 2 (ROM.ml2)
#        wait:seconds
ROM="$1"; OUT="$2"; shift 2; B="${OUT%.png}"
flatpak run net.kuribo64.melonDS -f "$ROM" > "$B.log" 2>&1 &
i=0; WID=""
while [ $i -lt 40 ] && [ -z "$WID" ]; do sleep 0.5; WID=$(xdotool search --class melonDS 2>/dev/null | tail -1); i=$((i+1)); done
sleep 4                                   # let the game start before loading over it
xdotool key --window "$WID" F1; sleep 5   # load slot 1 (shortcuts only arrive sent to the window); wait out the "State loaded" message
shot() { import -window "$WID" "$1" 2>/dev/null; sleep 0.5; }   # a key pressed right after a capture is lost
for st in "$@"; do
  case "$st" in
    s:*) shot "${B}_${st#s:}.png" ;;
    save) xdotool key --window "$WID" shift+F2; sleep 2 ;;
    wait:*) sleep "${st#wait:}" ;;
    hold:*) k=${st#hold:}; xdotool keydown "${k%%:*}"; sleep "${k#*:}"; xdotool keyup "${k%%:*}"; sleep 0.3 ;;
    *:*) xdotool keydown "${st%%:*}"; sleep 0.08; xdotool keyup "${st%%:*}"; sleep "${st#*:}" ;;
    *) xdotool keydown "$st"; sleep 0.08; xdotool keyup "$st"; sleep 1 ;;
  esac
done
sleep 1; shot "$OUT"
pkill -KILL -x melonDS
