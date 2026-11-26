#!/bin/sh
# Ticket 25: scripts/vram_guard.py over every DeSmuME state in states/ and states/late/,
# then over the menu walks of scripts/solo_menus.sh.  Silent (apart from the headings)
# means clean.  ROM picks the build.  usage: scripts/vram_guard_all.sh   (a few minutes)
# Each state plays 20 s: still, SELECT tapped (overlay or screen swap) and tapped again,
# SELECT held (banner off) and held again.
P=.venv/bin/python
STEPS="w120,SELECT4,w240,SELECT4,w120,SELECT40,w120,SELECT40,w240"
echo "== states"
ls states/*.dst states/late/*.dst | xargs -P 8 -I{} sh -c \
    "$P scripts/vram_guard.py {} '$STEPS' 2>&1 | grep -E '^(frame|  +[A-Z]|Traceback|[A-Za-z]*Error)' | sed 's|^|{}: |'"
echo "== menu walks"
GUARD=1 sh scripts/solo_menus.sh
