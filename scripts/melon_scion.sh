#!/bin/sh
# A Scion's animation in real melonDS (ticket 26): casts Scion K from states/m_battle2.ml1 and
# captures the two-screen part at about the given seconds. usage: melon_scion.sh K OUT.png [NAME...]
# (from the VS Code flatpak, about 50 s; ROM, SIZE as for melon_state.py). OUT_0.png, OUT_1.png...
# are taken one after another (about 0.7 s apart) from just before the Scion to after it.
K=$1; OUT=$2; N=${3:-18}
STEPS="Down:0.4 x:0.8 Down:0.4 x:0.8 x:0.8 x:1 x:1.8 x:${LEAD:-4.5}"
i=0; while [ $i -lt $N ]; do STEPS="$STEPS s:$i wait:0.1"; i=$((i+1)); done
FPS=60 SCION=$K exec "$(dirname "$0")/../.venv/bin/python" "$(dirname "$0")/melon_state.py" states/m_battle2.ml1 "$OUT" $STEPS
