#!/usr/bin/env python3
"""The auction on one screen (ticket 28): preview/auction.html.

usage: preview_auction.py      (copies solo.py and melonDS captures from shots/t28)"""
import json, os, shutil, time
OUT = "preview/t28"
os.makedirs(OUT, exist_ok=True)
MOMENTS = [("think", "final/rank.png", "Rivals thinking"), ("bid", "final/bid.png", "Your bid up"),
           ("land", "final/think.png", "Bids land"), ("rank", "final/land.png", "Ranking"),
           ("bonus", "final/bonus.png", "Bonus round"), ("retire", "final/retire.png", "Retire question"),
           ("tut1", "final/tut1.png", "Help: tokens"), ("tut2", "final/tut2.png", "Help: buttons"),
           ("melon", "melon/final4.png", "melonDS capture")]
for k, f, _ in MOMENTS:
    shutil.copy("shots/t28/" + f, "%s/built_%s.png" % (OUT, k))
open("preview/auction.html", "w").write("""<!doctype html><meta charset=utf-8>
<meta name=viewport content="width=device-width,initial-scale=1"><title>Auction, built</title>
<style>body{background:#16161a;color:#ddd;font:15px/1.5 system-ui;margin:0;padding:16px}h1{font-size:19px;margin:0}
p{margin:4px 0 10px;max-width:900px}button{font:inherit;background:#2a2a32;color:#ddd;border:1px solid #444;border-radius:6px;padding:6px 12px;margin:0 6px 8px 0;cursor:pointer}
button.on{background:#3b5bdb;border-color:#7c95ff;color:#fff}img{display:block;image-rendering:pixelated}.wrap{overflow:auto}</style>
<h1>The auction on one screen, built (layout B)</h1>
<p>Left and right change the moment. Captures of the finished build at the Deck's 1280x800, pixel for pixel; the last one is melonDS.</p>
<div id=m></div><div class=wrap><img id=i alt="auction"></div>
<script>const M=%s,T=%d;let m=0;const $=s=>document.getElementById(s);
function show(){$('i').src='t28/built_'+M[m][0]+'.png?t='+T;$('i').style.width=1280/devicePixelRatio+'px';[...$('m').children].forEach((b,k)=>b.className=k==m?'on':'')}
M.forEach((x,k)=>{const b=document.createElement('button');b.textContent=x[1];b.onclick=()=>{m=k;show()};$('m').append(b);new Image().src='t28/built_'+x[0]+'.png?t='+T});
onkeydown=e=>{if(e.key=='ArrowRight')m=(m+1)%%M.length;else if(e.key=='ArrowLeft')m=(m+M.length-1)%%M.length;else return;e.preventDefault();show()};show()</script>
""" % (json.dumps([(a, c) for a, _, c in MOMENTS]), int(time.time())))
print("preview/auction.html written")
