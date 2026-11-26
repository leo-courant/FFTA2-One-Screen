#!/bin/sh
# Runs INSIDE a headless gamescope session on the host (see melon_battle.sh):
# load slot 1 of an in-game save in melonDS, then replay a play.py-style script
# (frame counts, as in to_saves.sh) in real time, and capture.
# usage: melon_play.sh ROM SAV OUT.png SCRIPT
# melonDS must run at normal speed for this (TargetFPS = 60.0 in its settings):
# frame-timed presses, such as the world map's, do not survive 4x speed.
# SCRIPT steps: w<N> wait N frames; <KEY><N> hold N frames (default 4), then wait 4;
# s<name> capture to OUT_<name>.png; save: save a melonDS savestate (slot 1, ROM.ml1).
ROM="$1"; SAV="$2"; OUT="$3"; SCRIPT="$4"; B="${OUT%.png}"
cp "$SAV" "${ROM%.nds}.sav"
flatpak run net.kuribo64.melonDS -f "$ROM" > "$B.log" 2>&1 &
sleep 14
WID=$(xdotool search --class melonDS 2>/dev/null | tail -1)
key() { xdotool keydown "$1"; sleep "$2"; xdotool keyup "$1"; sleep "$3"; }
eval "$(xdotool getwindowgeometry --shell "$WID" 2>/dev/null)"
PX=$((200 * ${WIDTH:-1280} / 1280)); PY=$((60 * ${HEIGHT:-800} / 800))   # measured at 1280x800
inlist() {  # true when the "Select data to load." header is on screen
  import -window "$WID" "$B.probe.png" 2>/dev/null || return 1
  set -- $(convert "$B.probe.png" -format "%[fx:int(255*p{$PX,$PY}.r)] %[fx:int(255*p{$PX,$PY}.g)] %[fx:int(255*p{$PX,$PY}.b)]" info: 2>/dev/null)
  [ "${1:-0}" -gt 120 ] && [ "${1:-0}" -lt 170 ] && [ "${2:-255}" -lt 80 ] && [ "${3:-255}" -lt 70 ]
}
i=0; while [ $i -lt 40 ] && ! inlist; do key x 0.1 4; i=$((i+1)); done   # title -> Continue -> slot list
rm -f "$B.probe.png"; sleep 10     # the list takes a while to accept input at normal speed
key x 0.1 5; key Up 0.1 2; key x 0.1 14   # slot 1 -> Load (prompt defaults to Cancel)
key x 0.1 30                               # dismiss "data loaded", world map fades in
secs() { awk "BEGIN{printf \"%.3f\", $1/60}"; }
IFS=,
for step in $SCRIPT; do
  case "$step" in
    "") ;;
    save) xdotool key --window "$WID" shift+F1; sleep 3 ;;   # shortcuts only arrive sent to the window
    w[0-9]*) sleep "$(secs "${step#w}")" ;;
    s*) import -window "$WID" "${B}_${step#s}.png" 2>/dev/null; sleep 0.4 ;;   # a key pressed right after a capture is lost
    *) name=$(echo "$step" | sed 's/[0-9]*$//'); n="${step#$name}"
       case "$name" in A) k=x;; B) k=z;; X) k=s;; Y) k=a;; L) k=1;; R) k=2;; SELECT) k=q;; START) k=Return;;
         UP) k=Up;; DOWN) k=Down;; LEFT) k=Left;; RIGHT) k=Right;; esac
       key "$k" "$(secs "${n:-4}")" 0.067 ;;
  esac
done
sleep 1; import -window "$WID" "$OUT" 2>/dev/null
pkill -KILL -x melonDS
