#!/usr/bin/env python3
"""How long the banner's upload keeps texture bank B mapped to the CPU (ticket 41).

usage: hud_upload.py STATE ROM FRAMES      (STATE under states/; one line on stderr)
Counts the mod's uploads, the longest in scanlines (and the lines it ran over), and "cuts":
writes the game made to VRAMCNT_B meanwhile, after which the rest of the upload is lost.
The longest must stay within ov_safe()'s argument in hud3d_draw and off lines 192 and 215."""
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from emu import boot
state,rom,n=sys.argv[1],sys.argv[2],int(sys.argv[3])
emu=boot(state,rom,frames=0); m=emu.memory
st={'s':None,'o':[],'cut':0}; cur=[0]; L=lambda: m.unsigned.read_short(0x04000006)
def cb(addr,size):
    pc=m.register_arm9.pc
    v=m.unsigned.read_byte(0x04000241)
    if 0x02143E20<=pc<0x0214BE20:
        if v==0x80: st['s']=(cur[0],L())
        elif st['s'] and v==0x8B:
            f,l=st['s']; st['o'].append(((L()-l)%263, l, L())); st['s']=None
    elif st['s']: st['cut']+=1
m.register_write(0x04000241,cb,1)
for i in range(n): cur[0]=i; emu.cycle(False)
if st['o'] or st['cut']:
    b=max(st['o'],default=None); sys.stderr.write("SPAN %-28s n=%d worst=%s lines %s-%s cuts=%d\n"%(state.split('states/')[1],len(st['o']),b[0],b[1],b[2],st['cut']))
