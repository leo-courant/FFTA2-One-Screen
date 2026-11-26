# 28: Auctions on one screen

**What to build:** During an auction the bidding happens on the info screen: a bar that fills in real time while the clans' avatars show whether they are about to bid. The gameplay screen only has the token list and the buttons, so with the mod a player bids blind. Put all the auction's information on one widescreen picture, laid out for the wide screen rather than stretched, in a layout the user picks.

**Approach (user, 2026-11-24):** first find out whether a decent solution exists at all, then show the user an HTML page of options to choose from visually (melonDS-accurate pictures at the Deck's real size, flipped in place). The direction to explore:
- Combine both screens' information on the one screen (an overlay, or a new arrangement), using the extra width the wide screen gives.
- Don't distort to fill: the key elements (the clans' character sprites, tokens, the bar's markers) keep their own pixel proportions.
- Backgrounds may stretch; where a background no longer fits the frame, extend it (from the ROM for the public build; AI-extended only as the private add-on, as for the map of Ivalice).
- Align the unstretched elements with the stretched background, then see what space is really left and place the remaining information there.
- Brainstorm how to get there and decide honestly whether it can be done well; say so if not.

**Blocked by:** None (found in ticket 24). Second batch. A bigger piece of work: its own session.

**Status:** done, approved by the user (2026-11-25). Layout B; the design is in ADR 0015

**Found (ticket 24, 2026-11-24):** reach it from the late save: `states/late/l_auction_round.dst` (round 1 of the Camoa auction, both screens up) and `l_auction_bid.dst` (bidding started); the walk is in `scripts/to_late.sh`. Pictures of both original screens: `shots/t24/late/_auction_round.png`, `_auction_bid.png`; preview http://localhost:8765/late.html. The bottom screen here is a 2D screen, which `scripts/solo.py` draws repeated: check the mod's look in melonDS. Auctions open in the month held in event variable 0xC3 (`docs/symbols.tsv`); bids are timed, so a SELECT tap to the info screen is not a real answer.

**Found (2026-11-24, user review):** the bidding screen itself is distorted too. The live bar with the avatars, the tokens and the "Place bids in real time" message is drawn by the 3D engine on the info screen, and the mod's widescreen squeeze still applies to it, although the info screen is shown at 4:3: text is compressed, the yellow token is uneven and stretched vertically, the sprites are squeezed (compare `shots/t24/late/_auction_bid.png` top half with a `PLAIN=1` capture of `states/late/l_auction_bid.dst`). The gameplay screen during bidding (token list, buttons) is a 2D screen that the emulator stretches about 43% wider. So both halves need work: the 3D bar needs the squeeze handled for wherever it ends up, the 2D list needs either the 2D-into-3D treatment the banner got (ticket 07) or a new layout.

**Questions to settle first:**
- What exactly draws each element (`scripts/gxtrace.py` + `gx_report.py` for the 3D bar; `scripts/vidregs.py` for the 2D layers of both screens), and which ones can be moved one by one (layout objects, as in ticket 18) versus copied as a picture (the SELECT overlay's compositor, ticket 14).
- Whether the 3D engine can draw the bar on the gameplay screen while the 2D engine keeps the list (the game's dual-screen 3D mode, `dual3d_state`, ticket 26, may be related).
- Timing: bids are real time, so whatever is shown must update every frame without lag.
- Melon captures: an auction state for `scripts/melon_state.py` does not exist yet (only `m_battle1`, `m_story`); `scripts/melon_save.sh` with `saves/late.sav` reaches the map, the walk to the auction is in `scripts/to_late.sh`.

## Feasibility (2026-11-25): yes, and without scaling anything

**How the game does it.** Overlay 4 sets POWCNT1 bit 15 while bids are placed, which puts the 3D engine (the bidding field) on the info screen and the 2D token list on the gameplay screen; it takes the bit back between rounds, for the Retire question, and at the end. Four places, each reading the register's address from its own literal word (0x02139158, 0x0213978C, 0x0213CB60, 0x0213DC54; overlay 4 loads at 0x02132FC0). Pointed at a variable of the mod's at run time, the 3D engine stays on the gameplay screen and bit 15 of the variable says that bidding is on. The four words also identify overlay 4. No game code is stored or changed on disk.

**What draws what.** Field: layout objects (board, lane tabs, time bar; `0x020B0A18`), queued sprites (coins, gem numbers, markers, bubbles, bar fill; `0x020A449C`) and animated sprites (the clans; `0x01FF8628`). All follow the one ortho projection, so moving the field is one shift in `ortho_fix`. Nothing needs moving one by one. The board is a screen-sized layout object, so the frame rule of `layout_piece` stretches it: that was the distortion in the late review. Off during bidding.

**The list.** The SELECT overlay's compositor redraws the 2D screen into a texture; quads cut from it can sit anywhere. Rows are in the same clan order as the lanes, so counts line up with them.

**Checked on a prototype** (since replaced by the build below): field at the top left, live counts beside the lanes; tutorial, "bids land", ranking captured in DeSmuME (`shots/t28/proto`). Timing unchanged: the bar is within 1 px of the current build after 600 frames. `vram_guard.py` silent over 600 frames of bidding.

**Room.** View 366x228, field 256x192, count rows 102 wide, lane pitch 26: the column fits at 1:1, with 36 rows over for a strip below. Code: about 31.9 of 32 KB used with the prototype, so the rest must be Thumb (`SMALL`) or the blob reserve must grow (that moves the heap: old states go stale).

**Options on the page:** A names and counts right, buttons in a row below; B the same with the buttons in the game's own cross; C board, stripes and time bar carried on to the right edge, no names. The pictures are composed from 1:1 pixels (`scripts/auction_mock.py`), not captures of a finished build.

**To watch when building:** the first-time help draws coloured boxes as sprites on the token list, which show up in the cuts (leave sprites out of the compositor there, or move the box); the Retire question and the scroll and title bands are drawn over the field; 6-clan auctions and coin counts past the old right edge not seen yet; the 4:3 and 16:9 presets need their own arrangement (4:3 has no room beside the field); SELECT has nothing left to do in an auction; melonDS not run yet. Savestates: `late/l_auction_mid.dst` (bids running, from `l_auction_live.dst`); both were walked from `l_auction_bid.dst`.

## Built (2026-11-25): layout B, ADR 0015

`auction_check`, `auction_project`, `auction_draw` in `src/hook.c`; `queue_widen`, `layout_piece` and `ov_band_draw` know about it. Preview `scripts/preview_auction.py`. Blob 32424 of 32768 bytes: about 340 left, so the next feature needs `SMALL` functions or a bigger reserve.

**Checked.** DeSmuME, frame-exact pictures: fade into bidding and out of it, help frames around the counts and the buttons, bids landing, ranking, bonus rounds 2 and 3, skipping a round (the waiting screen), the Retire question answered with Continue, end of the auction with records and prizes. 16:9 and 4:3 too. Clock the same as the old build (0 px apart after 600 frames). melonDS 1280x800: from the map through the help into bidding, no hairlines. Memory guard silent on every state and menu walk, and again on four auction states with the final build. 96 menu captures against the build from the last commit: 8 differ, all animation phase (bobbing cursor, sliding hint, scrolling banner text; the hint checked at rest: identical). Patcher tests pass.

**Not checked.** Answering Retire with Retire: greyed out in round 1 and not reached later. Auctions with five or six clans, and coin rows past the field's edge (they go behind the panel). The Deck itself: melonDS does about 17% more work during bidding (138-160 frames a second on this PC uncapped, against 160-198).

**Slips worth knowing.** A `build/ffta2-1screen.nds` copied as "before" was already the new build, so the first menu comparison proved nothing: build "before" from a worktree of HEAD. Two apparent freezes in melonDS were stale window grabs; the CPU's program counter and the frame counter in a saved state settled it.
