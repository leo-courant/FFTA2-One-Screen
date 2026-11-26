#!/bin/sh
# Runs INSIDE a headless gamescope session on the host (see melon_battle.sh):
# boot the ROM in melonDS with an in-game save, load slot 1, press further keys,
# capture.  usage: melon_save.sh ROM SAV OUT.png [key[:seconds] ...]
# keys are xdotool names as mapped in docs/melonds-test-settings.toml
# (x = A, z = B, s = X, arrows); seconds = wait after the press (default 1.5).
ROM="$1"; SAV="$2"; OUT="$3"; shift 3
cp "$SAV" "${ROM%.nds}.sav"
flatpak run net.kuribo64.melonDS -f "$ROM" > "${OUT%.png}.log" 2>&1 &
sleep 14
WID=$(xdotool search --class melonDS 2>/dev/null | tail -1)
key() { xdotool keydown "$1"; sleep 0.08; xdotool keyup "$1"; sleep "${2:-1.5}"; }
eval "$(xdotool getwindowgeometry --shell "$WID" 2>/dev/null)"
PX=$((200 * ${WIDTH:-1280} / 1280)); PY=$((60 * ${HEIGHT:-800} / 800))   # measured at 1280x800
inlist() {  # true when the "Select data to load." header is on screen
  import -window "$WID" "${OUT%.png}.probe.png" 2>/dev/null || return 1
  set -- $(convert "${OUT%.png}.probe.png" -format "%[fx:int(255*p{$PX,$PY}.r)] %[fx:int(255*p{$PX,$PY}.g)] %[fx:int(255*p{$PX,$PY}.b)]" info: 2>/dev/null)
  [ "${1:-0}" -gt 120 ] && [ "${1:-0}" -lt 170 ] && [ "${2:-255}" -lt 80 ] && [ "${3:-255}" -lt 70 ]
}
i=0; while [ $i -lt 20 ] && ! inlist; do key x 1.5; i=$((i+1)); done   # title -> Continue -> slot list
rm -f "${OUT%.png}.probe.png"
key x 1.5; key Up 0.5; key x 4   # slot 1 -> Load (prompt defaults to Cancel)
key x 8                           # dismiss "data loaded", world map fades in
for k in "$@"; do key "${k%%:*}" "$(case $k in *:*) echo ${k#*:};; *) echo 1.5;; esac)"; done
sleep 1; import -window "$WID" "$OUT" 2>/dev/null
pkill -KILL -x melonDS
