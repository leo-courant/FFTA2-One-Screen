#!/bin/sh
# Runs INSIDE a headless gamescope session on the host: start melonDS with the
# given ROM, wait, capture its window, quit.  usage: melon_capture.sh ROM OUT.png [SECONDS]
ROM="$1"; OUT="$2"; WAIT="${3:-30}"
flatpak run net.kuribo64.melonDS -f "$ROM" > "${OUT%.png}.log" 2>&1 &
sleep "$WAIT"
WID=$(xdotool search --class melonDS 2>/dev/null | tail -1)
echo "display=$DISPLAY window=$WID"
if [ -n "$WID" ]; then import -window "$WID" "$OUT" 2>&1 | tail -1; else import -window root "$OUT" 2>&1 | tail -1; fi
GAMESCOPE_WAYLAND_DISPLAY="${GAMESCOPE_WAYLAND_DISPLAY:-gamescope-0}" gamescopectl screenshot "${OUT%.png}_gs.png" 2>&1 | tail -1
sleep 2
xdotool windowquit "$WID" 2>/dev/null; sleep 3; pkill -KILL -x melonDS
