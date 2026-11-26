#!/bin/sh
# Runs INSIDE a headless gamescope session on the host: boot the ROM in melonDS
# (settings: docs/melonds-test-settings.toml: 4x speed, keyboard mapped), replay
# the opening by key presses, and stop as soon as the mod's red objective box is
# on screen (= battle HUD is up).  usage: melon_battle.sh ROM OUT.png [save|save:N]
# "save": also save a melonDS savestate there (slot 1, ROM.ml1), the start of
# scripts/melon_state.py's states (docs/test-saves.md); "save:N": stop after N presses
# into the opening instead (story scenes; about 150 lands in the classroom).
ROM="$1"; OUT="$2"; B="${OUT%.png}"
flatpak run net.kuribo64.melonDS -f "$ROM" > "$B.log" 2>&1 &
sleep 12
WID=$(xdotool search --class melonDS 2>/dev/null | tail -1)
key() { xdotool keydown "$1"; sleep 0.05; xdotool keyup "$1"; sleep "${2:-0.07}"; }
hud() {  # true when the pixel inside the objective box is red
  import -window "$WID" "$B.probe.png" 2>/dev/null || return 1
  set -- $(convert "$B.probe.png" -format "%[fx:int(255*p{752,28}.r)] %[fx:int(255*p{752,28}.g)] %[fx:int(255*p{752,28}.b)]" info: 2>/dev/null)
  echo "$i $*" >> "$B.pixels"
  [ $((i % 60)) -eq 0 ] && cp "$B.probe.png" "$B.p$i.png"
  [ "${1:-0}" -gt 140 ] && [ "${2:-255}" -lt 90 ] && [ "${3:-255}" -lt 90 ]
}
i=0; while [ $i -lt 330 ]; do key x; i=$((i+1)); done      # new game, name entry fills
key s 0.4; key Up 0.3; key x 0.6                            # Done -> Yes
STOP=1400; case "$3" in save:*) STOP=${3#save:} ;; esac
i=0; found=0
while [ $i -lt $STOP ]; do
  key x; i=$((i+1))
  if [ $i -ge 500 ] && [ $((i % 3)) -eq 0 ] && hud; then found=1; break; fi
done
# the HUD flashes up before the tutorial dialogue; advance the dialogue one line
# at a time until the banner is back and stays (banner hides during dialogue)
j=0; settled=0
[ $STOP -lt 1400 ] && j=40
while [ $j -lt 40 ]; do
  sleep 1.2
  if hud; then settled=1; break; fi
  key x; j=$((j+1))
done
echo "presses=$i found=$found extra=$j settled=$settled" > "$B.result"
case "$3" in save*) ;; *) false ;; esac && { sleep 1; xdotool key --window "$WID" shift+F1; sleep 3; }   # shortcuts only arrive sent to the window
sleep 1.5; import -window "$WID" "$OUT" 2>/dev/null
key z 1.2; import -window "$WID" "${B}_b.png" 2>/dev/null
key x 1.2; import -window "$WID" "${B}_c.png" 2>/dev/null
rm -f "$B.probe.png"
pkill -KILL -x melonDS
