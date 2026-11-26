#!/bin/sh
# usage: try_nudge.sh NX NY [PRESET]   (PRESET: deck (default) or 16x9; from the VS Code flatpak)
# Builds that preset with that sub-pixel nudge into build/nudge.nds, captures a
# screen in melonDS at the preset's display size and measures how evenly the game
# pixels sit on the screen-pixel grid (scripts/measure_grid.py).  The screen is Wood
# Village from the in-game save (about 70 s): the title (used for the old 4x Deck view)
# is a still picture made for 256 px that does not lie on the grid of a wider view.
# See docs/test-saves.md, "Display presets".  Do not run while another melonDS rig runs.
cd "$(dirname "$0")/.." || exit 1
R=$PWD; P="${3:-deck}"
case "$P" in
  deck) W=1280; H=800; K=3.497 ;;
  16x9) W=1920; H=1080; K=5 ;;
  *) echo "no display size known for preset $P"; exit 1 ;;
esac
.venv/bin/python scripts/patch.py rom/ffta2.nds build/nudge.nds --display "$P" --nudge "$1,$2" 2>&1 | grep -E "error"
mkdir -p shots/melon
OUT="$R/shots/melon/nudge_${P}_$1_$2.png"
if [ "$P" = deck4x ]; then RUN="$R/scripts/melon_capture.sh $R/build/nudge.nds $OUT 22"; T=60
else RUN="$R/scripts/melon_save.sh $R/build/nudge.nds $R/saves/worldmap.sav $OUT x:8"; T=120; fi
(cd ~ && flatpak-spawn --host sh -c "cd ~; timeout $T gamescope --backend headless -W $W -H $H -w $W -h $H -f -- $RUN >/dev/null 2>&1; pkill -x gamescope; pkill -KILL -x melonDS")
rm -f build/nudge.sav
printf "%s nudge %s %s: " "$P" "$1" "$2"; .venv/bin/python scripts/measure_grid.py "$OUT" $K
