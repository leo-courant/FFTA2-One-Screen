/* FFTA2 single-screen mod: code injected into the ARM9 binary.
 *
 * hook_entry is branched to from the tail of the game's per-frame key update
 * (0x0201EA60).  It replays the replaced instruction, runs frame_hook(), then
 * returns the way the original function did.
 */
typedef unsigned char u8;
typedef unsigned short u16;
typedef unsigned int u32;

/* big functions that run at most once a frame are compiled as Thumb code: the blob's room
   is fixed (BLOB_RESERVE), and the linker adds the jumps between the two kinds.  Not for
   functions with 64-bit multiplication (Thumb needs a library routine for that). */
#define SMALL __attribute__((target("thumb")))

#define REG16(a) (*(volatile u16 *)(a))
#define REG32(a) (*(volatile u32 *)(a))

#define POWCNT1    0x04000304
#define DISPCNT_A  0x04000000
#define BG1CNT_A   0x0400000A
#define BG0CNT_B   0x04001008
#define BG1CNT_B   0x0400100A
#define MAIN_BGPAL ((u16 *)0x05000000)
#define SUB_BGPAL  ((u16 *)0x05000400)
#define SUB_BGVRAM 0x06200000

/* Our private corner of main-engine BG VRAM (unused by the game in battle). */
#define M_CHAR     ((u32 *)0x06008000)   /* char base 2 */
#define M_MAP      ((u16 *)0x0600F800)   /* screen base 31 */
#define M_BG1CNT   0x1F08                /* priority 0, char 2, screen 31 */

#define KEY_SELECT 0x0004
#define KEY_DPAD   0x00F0

/* SELECT is the mod's only button (ADR 0006): a tap shows the info screen when
   SELECT is let go, a hold this many frames (60 a second) switches the banner. */
#define HOLD_FRAMES 30

/* Banner geometry, in 8px cells on the gameplay screen. Columns 0-5 stay
   clear so the game's own tile-height tab remains visible. */
#define OBJ_COL0   5
#define COLS_END   32
/* Where the pieces sit on the original top screen's text layer. */
#define SRC_OBJ_ROW 0
#define SRC_OBJ_COL 3
#define SRC_LAW_ROW 3
#define SRC_LAW_COL 4
#define SRC_PRIV_ROW 6   /* the clan privilege chosen for this battle, if any */
#define SRC_PRIV_COL 4
#define BAR_INDEX  4     /* palette index unused by the text; becomes the bar */

/* Turn order: unit heads copied from the top screen's sprites into BG cells
   just under the banner.  Each slot is 3x3 cells (24x24px). */
#define DISPCNT_B  0x04001000
#define SUB_OAM    ((const u16 *)0x07000400)
#define SUB_OBJPAL ((const u16 *)0x05000600)
#define SUB_OBJVRAM 0x06600000
#define TURN_SLOTS 4
#define TURN_ROW0  2
#define TURN_COL0  18
#define TURN_PAL0  10    /* main BG palette rows 10..13 */

static u32 frame_no;
static SMALL void rects_new_frame(void);

static u8 banner_enabled = 1;
static u8 sel_frames;     /* frames SELECT has been down (up to HOLD_FRAMES), 0 = up */
static u8 sel_spoilt;     /* this press is no longer a tap or a hold */

/* The battle's outcome: 0 while it is fought (preparation included), 1 won, 2 lost.
   The game's own win check (0x02091C6C) sets it as the battle is decided, before the
   closing talk and "Complete!", and it stays until the next battle's opening script
   clears it (event opcode 0x11, in every one of them).  Ticket 40: the word tested
   before, 0x02124104, stays 2 through some endings.  0x0212418C (1 on the world map
   and in its top menus, 2 in everything entered from there) is no battle signal either. */
#define BATTLE_OVER  (*(volatile u8 *)0x0212EF07 != 0)
/* 0x02127D00 holds a pointer (into the battle's heap) from the battle's opening
   scene to the end of its results, and 0 on the world map and in everything
   entered from it: the one word that told the two apart across all 57 test
   screens of battles 1 and 2 and the menus (ticket 08, 2026-11-23).  The word at
   0x0212418C used before stays 2 on the world map after a battle. */
#define BATTLE_OBJ   (*(volatile u32 *)0x02127D00 != 0)
/* in a battle scene, its own sub-screens (unit sheet, View Abilities) and results included */
static u8 in_battle;

static int battle_hud_present(void)
{
    /* Gameplay screen in 3D mode, and the top screen showing the battle
       frame (its top-left cells are the "!" objective badge).  Once the law is
       broken and the judge has left, the game redraws the same frame cells in
       palette 10 instead of 14 (teal, no law or privilege; ticket 42). */
    if ((REG32(DISPCNT_A) & 0xF) != 0xD)
        return 0;
    const u16 *fmap = (const u16 *)(SUB_BGVRAM + ((REG16(BG0CNT_B) >> 8) & 31) * 0x800);
    u16 p = fmap[0] & 0xF000;
    return (p == 0xE000 || p == 0xA000) && fmap[0] == (p | 1) && fmap[1] == (p | 2) && fmap[4] == (p | 4);
}

/* ---- display preset ------------------------------------------------------
 * The view size and nudge come from the display preset chosen when patching
 * (ADR 0007): scripts/patch.py passes VIEW_W/VIEW_H (game pixels shown),
 * NUDGE_X/NUDGE_Y (sub-pixel nudge in projection units) and the margins.  The
 * defaults are the Steam Deck preset: a 366x228 view, 3.5 screen px per game px
 * at 1280x800 (ADR 0009).  A 256x192 view is the plain game. */
#ifndef VIEW_W
#define VIEW_W 366
#endif
#ifndef VIEW_H
#define VIEW_H 228
#endif
#ifndef NUDGE_X
#define NUDGE_X 3
#endif
#ifndef NUDGE_Y
#define NUDGE_Y (-3)
#endif
/* extra pixels kept beyond the old 256x192 view on each side (map cells,
   backdrop bands, layout pieces); 0 for the plain game */
#ifndef SIDE_MARGIN
#define SIDE_MARGIN 96
#endif
#ifndef V_MARGIN
#define V_MARGIN 24
#endif
/* The settings as the code reads them, in one block after a "VIEW" marker so the
   test rig can find and change them (PLAIN in scripts/play.py): screen size in
   game pixels, projection multipliers (20.12 fixed point), nudge. */
extern int view_cfg[7];
static int sdiv(int a, int b);
/* The view during a Scion's animation, in game pixels (ticket 26): the two screens as one
   tall picture, 256x384, plus the side areas.  Set by the display preset. */
#ifndef TALL_W
#define TALL_W 640
#endif
#ifndef TALL_H
#define TALL_H 400
#endif
#define screen_w (view_cfg[1])
#define screen_h (view_cfg[2])
#define wide_x   (view_cfg[3])
#define wide_y   (view_cfg[4])
#define nudge_x  (view_cfg[5])
#define nudge_y  (view_cfg[6])

/* ---- banner and turn order, drawn as 3D polygons -------------------------
 * Text and unit heads are still copied from the info screen (ADR 0002), but
 * into a private texture, and drawn as quads just before the game swaps
 * buffers.  Going through the 3D path makes them high-resolution and
 * correctly proportioned in widescreen.  Coordinates are screen pixels with
 * the origin at the true top-left corner; the screen is screen_w px wide
 * (256 in the plain game, 320 on the Deck). */
extern int hud_hidden;
extern int tile_cfg[4];

#define VRAMCNT_B  (*(volatile u8 *)0x04000241)
#define VRAMCNT_G  (*(volatile u8 *)0x04000246)
/* Texture memory: the top HUD_TEX_SIZE of texture bank B (slot 1), shared with
   the game (ADR 0008).  In battle the game hands out 0x2E000-0x3FFFF to unit
   sprites and effects from a heap, bottom-up, so the top is the last part it
   uses.  Each frame, right before touching it, the mod checks the heap's free
   list: the units' half (lower) and the banner text's half (top) are used only
   while the game has nothing there.
   Palette: a stretch of the texture palette that battle does not use.
   Checked with scripts/vram_guard.py over every battle test state (ticket 25):
   no clash in either range. */
#ifndef HUD_TEX_SIZE
#define HUD_TEX_SIZE 0x2000
#endif
#define TEX_ADDR   (0x40000 - HUD_TEX_SIZE)
#define TEX_LCDC   ((u32 *)(0x06800000 + TEX_ADDR))
#define PAL_ADDR   0x3A00
#define PAL_LCDC   ((u16 *)(0x06894000 + PAL_ADDR))
#define HEAD_TEX   TEX_ADDR              /* 128x64, 16 colours: four 32px columns, each a unit's body (rows 0-31) and feet (32-39) */
#define TEXT_TEX   (TEX_ADDR + 0x1000)   /* 512x32, 4 colours: two lines of 64 text cells */
/* the game's battle texture heap (vram_scene_setup, mode 2): *TEX_HEAP_PTR is
   { start, size, free list, used list }, list nodes { prev, next, start, size } */
#define TEX_HEAP_PTR (*(volatile u32 *)0x0212F048)
#define TEXT_CELLS 64

#define GX(port)   (*(volatile u32 *)(0x04000400 + (port) * 4))
#define G_MODE 0x10
#define G_PUSH 0x11
#define G_POP 0x12
#define G_IDENT 0x15
#define G_LOAD44 0x16
#define G_COLOR 0x20
#define G_TEXCOORD 0x22
#define G_VTX16 0x23
#define G_POLY_ATTR 0x29
#define G_TEXIMAGE 0x2A
#define G_PLTT_BASE 0x2B
#define G_BEGIN 0x40
#define G_END 0x41

#define BANNER_X   48      /* right of the height tab */
#define HEAD_PX    24
#define HEADS_RIGHT_GAP 28 /* leave the top-right corner for the game's B hint */
/* Turn order (ticket 07, the user's choice "stage"): no box; the units stand
   at the bottom centre between the unit panel and the Help bar, as whole
   sprites with their ground shadows, the acting one on an orange ring, and a
   row of pips along the bottom edge gives the side of each coming turn
   (blue ally, red enemy), the first being the acting unit's.  It steps aside
   while a game panel is there.  Where that gap is too narrow (4:3) the units
   go in a strip at the top right instead, under the banner. */
#define QUEUE_MAX  20      /* turns the info screen's pip strip shows */
#define TURN_SEEN  8       /* units the info screen's turn area shows at most */

static u32 hud_hash;
static u32 bar_frame;       /* last frame the action name bar was drawn edge to edge, and where it ended */
static int bar_bottom;
static int turn_left;      /* left edge of the turn order as last drawn, in screen pixels */
static int hud_bottom;     /* lowest row of the banner and turn order as last drawn */
static int banner_extra;   /* height of the banner's rows beyond the first, as last drawn */
/* Banner text: the info screen draws each box's text in three colours of one
   group of four in its palette (objective 5-7, law 9-11, privilege 13-15), so
   it is kept at 2 bits per pixel with the group remembered per cell. */
static u8 txt_grp[2][TEXT_CELLS];
/* each text's inked pixels, from the start of its run: the boxes hug these */
static short txt_l[3], txt_r[3];
#define BOX_PAD 5          /* pixels between a box's edge and its text */
/* turn order: where each unit's picture sits in its 32x32 sprite, and the side
   of each coming turn read from the info screen's pip strip (1 ally, 2 enemy) */
static short unit_box[TURN_SLOTS][4];
static u8 q_side[QUEUE_MAX];
static int q_n;
static int q_mark;                 /* the focused (acting or browsed) unit's turn, index into q_side */
static int shown_n;                /* units shown in the turn order */
static u8 slot_turn[TURN_SLOTS];   /* the turn (pip index) of each slot */
static int cursor_mark;            /* 1 + the slot the player browsed to with L/R; 0: none */
static u8 slot0_ok;                /* slot 0 of the unit texture holds the acting unit */
static u32 last_pos;               /* where the info screen's units were last frame */
static u32 last_src;               /* the texture sources as they were last frame */
static u32 stage_hit;              /* last frame a game panel covered the stage */
static short stage_box[4];         /* the stage as last laid out, screen pixels */
static u32 hud_hit;                /* last frame a game panel covered the banner (ticket 17) */
static short hud_box[8];           /* the banner, then the 4:3 turn-order strip, as last laid out
                                      (two boxes: the action name bar runs left of the strip, under the banner) */

/* filled shapes as rows of flat quads, on one depth layer */
static const u8 RING14[9] = { 6, 10, 13, 14, 14, 14, 13, 10, 6 };
static const u8 RING9[5] = { 5, 8, 9, 8, 5 };
static const u8 SHADOW10[5] = { 6, 9, 10, 9, 6 };
#define STAGE_PIPS 18                    /* as many turns as fit under the stage */
static u32 hud_drawn_frame;
static u32 speech_frame = 0xFFFFFFFF;
static int hud_layer;

static u8 quad_texel;       /* quads show one texel all over */
static int hold_layer;     /* non-zero: quads share one depth layer (pieces that never overlap) */
static void quad(int x0, int y0, int x1, int y1, int s0, int t0)
{
    int z = hold_layer ? -8 * (hud_layer - 1) : -8 * hud_layer++;
    int s1 = quad_texel ? s0 : s0 + (x1 - x0), t1 = quad_texel ? t0 : t0 + (y1 - y0);
    GX(G_BEGIN) = 1;
    GX(G_TEXCOORD) = (u32)((s0 << 4) & 0xFFFF) | ((u32)(t0 << 4) << 16);
    GX(G_VTX16) = (u32)((x0 << 4) & 0xFFFF) | ((u32)(y0 << 4) << 16); GX(G_VTX16) = (u32)(z & 0xFFFF);
    GX(G_TEXCOORD) = (u32)((s0 << 4) & 0xFFFF) | ((u32)(t1 << 4) << 16);
    GX(G_VTX16) = (u32)((x0 << 4) & 0xFFFF) | ((u32)(y1 << 4) << 16); GX(G_VTX16) = (u32)(z & 0xFFFF);
    GX(G_TEXCOORD) = (u32)((s1 << 4) & 0xFFFF) | ((u32)(t1 << 4) << 16);
    GX(G_VTX16) = (u32)((x1 << 4) & 0xFFFF) | ((u32)(y1 << 4) << 16); GX(G_VTX16) = (u32)(z & 0xFFFF);
    GX(G_TEXCOORD) = (u32)((s1 << 4) & 0xFFFF) | ((u32)(t0 << 4) << 16);
    GX(G_VTX16) = (u32)((x1 << 4) & 0xFFFF) | ((u32)(y0 << 4) << 16); GX(G_VTX16) = (u32)(z & 0xFFFF);
    GX(G_END) = 0;
}

static void flat(int x0, int y0, int x1, int y1, u16 colour, int alpha)
{
    GX(G_TEXIMAGE) = 0;
    GX(G_POLY_ATTR) = 0x000000C0 | ((u32)alpha << 16) | (alpha < 31 ? 0x3F000000 : 0);
    GX(G_COLOR) = colour;
    quad(x0, y0, x1, y1, 0, 0);
}

static void textured(int x0, int y0, int x1, int y1, int s0, int t0, u32 tex, int w_log, int h_log, u32 pal)
{
    /* 16-colour texture, colour 0 transparent */
    GX(G_TEXIMAGE) = (tex >> 3) | ((u32)w_log << 20) | ((u32)h_log << 23) | (3u << 26) | (1u << 29);
    GX(G_PLTT_BASE) = pal >> 4;
    GX(G_POLY_ATTR) = 0x001F00C0;
    GX(G_COLOR) = 0x7FFF;
    quad(x0, y0, x1, y1, s0, t0);
}

static void textured4(int x0, int y0, int x1, int y1, int s0, int t0, u32 tex, int w_log, int h_log, u32 pal)
{
    /* 4-colour texture, colour 0 transparent; palettes in 8-byte steps */
    GX(G_TEXIMAGE) = (tex >> 3) | ((u32)w_log << 20) | ((u32)h_log << 23) | (2u << 26) | (1u << 29);
    GX(G_PLTT_BASE) = pal >> 3;
    GX(G_POLY_ATTR) = 0x001F00C0;
    GX(G_COLOR) = 0x7FFF;
    quad(x0, y0, x1, y1, s0, t0);
}

/* a game panel at x0..x1, y0..y1 in old-screen pixels, as finally drawn: does it
   cover the stage, or the banner?  Either steps aside while it does (the rule
   "never one layer of panels over another"): on 4:3 the Help window, the
   privilege list's heading and the like reach the banner's corner. */
static SMALL void stage_check(int x0, int y0, int x1, int y1, int banner)
{
    extern int edge_px, edge_py;
    x0 += edge_px; x1 += edge_px; y0 += edge_py; y1 += edge_py;
    if (x0 >= x1)
        return;
    if (x0 < stage_box[2] - 2 && x1 > stage_box[0] + 2 && y0 < stage_box[3] && y1 > stage_box[1] + 2)
        stage_hit = frame_no;
    for (int i = 0; i < 8 && banner; i += 4)
        if (x0 < hud_box[i + 2] - 2 && x1 > hud_box[i] + 2 && y0 < hud_box[i + 3] - 2 && y1 > hud_box[i + 1])
            hud_hit = frame_no;
}

static SMALL void shape(int cx, int cy, const u8 *hw, int rows, u16 colour, int alpha)
{
    int y = cy - (rows >> 1);
    for (int r = 0; r < rows; r++) {
        flat(cx - hw[r], y + r, cx + hw[r], y + r + 1, colour, alpha);
        hold_layer = 1;
    }
    hold_layer = 0;
}

static SMALL void pip(int x, int y, u16 colour)       /* 4x3 lozenge, like the game's diamonds */
{
    flat(x + 1, y, x + 3, y + 1, colour, 31);
    hold_layer = 1;
    flat(x, y + 1, x + 4, y + 2, colour, 31);
    flat(x + 1, y + 2, x + 3, y + 3, colour, 31);
    hold_layer = 0;
}

/* one unit's picture, centred on cx, standing on base_y */
static SMALL void unit_pic(int k, int cx, int base_y)
{
    int x0 = unit_box[k][0], y0 = unit_box[k][1], x1 = unit_box[k][2], y1 = unit_box[k][3];
    if (x1 <= x0)
        return;
    int w = x1 - x0, h = y1 - y0, sx = cx - (w >> 1);
    textured(sx, base_y - h, sx + w, base_y, k * 32 + x0, y0, HEAD_TEX, 4, 3, PAL_ADDR + (k + 1) * 32);
}

#define SIDE_FILL(s)  SUB_OBJPAL[((s) == 2 ? 4 : 3) * 16 + 14]   /* the game's pip colours */
#define SIDE_RIM(s)   SUB_OBJPAL[((s) == 2 ? 4 : 3) * 16 + 13]
#define DISC_ORANGE   0x1EBF
#define DISC_LIGHT    0x37DF

/* ---- info screen overlay ------------------------------------------------
 * Outside battle, SELECT drops the whole info screen in front of the gameplay
 * screen as a translucent panel.  To be sharp in widescreen it has to be a
 * texture on a 3D quad, so the info screen (four 16-colour tile layers plus
 * sprites) is redrawn in software, a few tile rows per frame, into a
 * 256-colour texture.
 *   texture:  upper part of texture bank A (0x14000, 48 KB), which the menus
 *             leave unreferenced; its old contents are parked in the unused
 *             main-engine BG bank while the overlay is up and put back after.
 *             scripts/vram_guard.py (ticket 25) confirms this for the menus,
 *             but late-game pub menus, the title, and story and after-battle
 *             dialogue scenes do use these areas (ticket 31).
 *   palette:  256 entries at 0x3C00 of the texture palette, built by merging
 *             the palette rows the info screen actually uses.
 *   scratch:  word-sized tables also live in the main BG bank. */
#define VRAMCNT_A  (*(volatile u8 *)0x04000240)
#ifndef OV_TEX                            /* overridable only for the guard's clash test (ticket 25) */
#define OV_TEX      0x14000
#endif
#define OV_TEX_LCDC ((u32 *)(0x06800000 + OV_TEX))
#define OV_WORDS    (256 * 192 / 4)
#define OV_PAL      0x3C00
#define OV_PAL_LCDC ((u16 *)(0x06894000 + OV_PAL))
#define OV_BACKUP   ((u32 *)0x06001000)   /* 48 KB */
#define OV_SRC      ((u16 *)0x0600D200)   /* the source colours each row was mapped from */
#define OV_COL      ((u16 *)0x0600D600)   /* texture palette as built so far */
#define OV_STRIDE   384
/* byte-addressed tables must be in main RAM: byte writes to video memory are dropped */
static u8 OV_REMAP[32 * 16];              /* 32 palette rows x 16 -> texture colour */
static u8 OV_BUF[8 * OV_STRIDE] __attribute__((aligned(4)));   /* one band: 8 rows x (64 + 256 + 64) */
#define OV_BANDS_PER_FRAME 4
#define OV_ALPHA    25                    /* panel opacity, 1..31 */
#define OV_DIM      6                     /* darkening of the scene behind it, 0..31 */

/* The game's own Item Info panel (L/R in shops and equipment lists) is on the
   gameplay screen.  Judged from the game's resource slots (table 0x0212E4E8,
   0x20 bytes each, +0xC non-zero while loaded): the info screen's sheet pictures
   live there, and Item Info loads the item sheet (file 0x1F, slot 26) by itself.
   Set Abilities loads the ability sheet (file 0x1E, slot 25) with the item sheet
   as its second picture, so the item sheet alone is not enough (ticket 32). */
#define RES_LOADED(slot) (*(volatile u32 *)(0x0212E4E8 + (slot) * 0x20 + 0xC))
#define ITEM_PANEL  (RES_LOADED(26) && !RES_LOADED(25))

/* Change Jobs: what a job changes is only on the info screen.  While the Jobs
   list is open the info screen's stat column, with the +/- changes of the
   highlighted job, is shown top left by itself, and the list slides right by
   JOBS_SHIFT to clear it (layout_obj_begin).
   JOBS_LIST: 3 while Change Jobs is open (2 and 1 in Change Equipment, else 0).
   (View Abilities needs nothing like it: A on a category opens the game's own
   ability list on the gameplay screen.) */
#define JOBS_LIST   (*(volatile u32 *)0x021326D4 == 3)
static u8 jobs_panel;

/* Bazaar (ticket 33): the loot kinds a recipe takes, the loot sent for each, the
   grades that allows and the item it makes are only on the info screen, in its
   loot rows (one per kind, 32 px apart from y 22) and the recipe header (y 150).
   While they are up they are shown at 1:1 under the list, which moves up to the
   tab bar; the game's description box is put away (layout_obj_begin).  Deck view
   only: the others have no room under the list.
   BAZAAR: the word is 5 from the recipe list until the bazaar is left (0 in every
   other menu seen); after a trade the info screen shows the new item's sheet
   instead, with no row labels, so nothing is drawn then. */
#define BAZAAR      (*(volatile u32 *)0x0212EA88 == 5)
#define BZ_PITCH    24                    /* a row and its kind icon; the current kind's glow is cut by 3 px */
#ifndef BZ_DEBUG
#define BZ_DEBUG    0                     /* 1: test builds draw the rows off screen (to see what lies under them) */
#endif
#define BZ_Y        124                   /* just under the moved list's frame */
static u8 bazaar_rows, bazaar_head, bazaar_open;
static void *bz_desc;                     /* the description box, put away */
static u32 bz_list;                       /* frame the bazaar's list was last drawn */
#define JOBS_SRC_X0 10
#define JOBS_SRC_Y0 78
#define JOBS_SRC_X1 126
#define JOBS_SRC_Y1 186
#define JOBS_SHIFT  28

static u8 ov_on;        /* overlay memory is borrowed and being filled */
/* Where the overlay texture lives while it is up (ticket 31, ADR 0013): the top
   48 KB of the game's texture heap in bank B where the scene has a heap and that
   memory is free (nothing to park: the game has nothing there), else the upper
   part of bank A with its contents parked in the main BG bank (ADR 0005). */
#define OV_HEAP_TEX 0x34000
static u32 ov_tex;
static u8 ov_parked;
static SMALL int tex_free(u32 lo, u32 hi);
static int heap_present(void);
static u8 ov_manual;    /* SELECT: whole info screen */
static u8 auction;      /* bids are being placed, and this display has room for the layout (ticket 28) */
#define AUC_ROOM (VIEW_W >= 366 && VIEW_H >= 216)
static void auction_project(int on);
static u8 ov_ready, ov_band, ov_pal_dirty;
static u32 ov_sum[24];  /* what each band of the texture holds */
static u16 ov_ncol;
static u32 ov_rows_ok;

/* The 3D engine picks up texture memory when it starts drawing a frame
   (scanline 215 in melonDS; around the frame wrap in DeSmuME).  A bank that is
   mapped to the CPU at that instant is missing from the whole frame, so never
   start a write just before those moments. */
#define VCOUNT (REG16(0x04000006))
static void ov_safe(int lines)
{
    for (;;) {
        int v = VCOUNT;
        /* 192: the game's vblank interrupt uploads its own textures, and leaves the banks mapped
           back to the 3D engine: what we write after that is dropped (ticket 41) */
        if (!((v >= 192 - lines && v <= 192) || (v >= 215 - lines && v <= 216) || v >= 262 - lines || v <= 1))
            return;
    }
}

static const u8 *ov_row(int r)
{
    u8 *map = OV_REMAP + r * 16;
    if (ov_rows_ok & (1u << r))
        return map;
    ov_rows_ok |= 1u << r;
    const u16 *src = SUB_BGPAL + r * 16;      /* rows 16..31 are the sprite palette */
    u16 *seen = OV_SRC + r * 16;
    for (int i = 1; i < 16; i++) {
        u16 c = src[i] | 0x8000;
        if (seen[i] == c)
            continue;
        seen[i] = c;
        int j = 1;
        while (j < ov_ncol && OV_COL[j] != c)
            j++;
        if (j == ov_ncol) {
            if (ov_ncol < 256) {
                OV_COL[ov_ncol++] = c;
                ov_pal_dirty = 1;
            } else
                j = 1;
        }
        map[i] = (u8)j;
    }
    return map;
}

static void ov_px8(u8 *d, u32 w, int flip, const u8 *map)
{
    for (int i = 0; i < 8; i++) {
        u32 v = (w >> (4 * (flip ? 7 - i : i))) & 15;
        if (v)
            d[i] = map[v];
    }
}

#ifdef GUARD
/* ---- in-play clash marker (patch.py --guard, never in published patches) ----
 * Ticket 25.  While the overlay is up, the mod checks what it can cheaply:
 *   1  the game wrote into the overlay texture (a band changed since the mod
 *      wrote it; checked just before each band is rewritten)
 *   2  the game wrote into the parked copy of bank A (one 2 KB slice checked
 *      per frame, all of it before it is put back)
 *   4  a main-engine BG layer shows the parked copy
 * A hit lights a small red dot in the top-left corner for 10 s and is kept in
 * guard_info (after a "GURD" marker): hits, kinds seen, first and last frame,
 * so a savestate made there tells what happened.  The game drawing 3D from the
 * borrowed texture is not seen here: scripts/vram_guard.py finds that. */
const char guard_build[] = "GUARD BUILD (ticket 25): not for publishing";
u32 guard_info[5];
static u32 guard_until;
static u32 ov_hash[24], bk_hash[24];
static u32 ov_hash_ok;

static void guard_hit(int kind)
{
    guard_info[0] = 0x44525547;             /* "GURD" */
    if (!guard_info[1])
        guard_info[3] = frame_no;
    guard_info[1]++;
    guard_info[2] |= (u32)kind;
    guard_info[4] = frame_no;
    guard_until = frame_no + 600;
}

static u32 guard_sum(const volatile u32 *p, int n)
{
    u32 h = 0x811C9DC5;
    for (int i = 0; i < n; i++)
        h = ((h << 5) | (h >> 27)) ^ p[i];
    return h;
}

static void guard_backup_sums(void)
{
    for (int b = 0; b < 24; b++)
        bk_hash[b] = guard_sum(OV_BACKUP + b * 512, 512);
}

static void guard_backup_check(int b)
{
    if (guard_sum(OV_BACKUP + b * 512, 512) != bk_hash[b])
        guard_hit(2);
}

/* does an enabled main BG layer show any of the parked copy? */
static void guard_bg_check(void)
{
    u32 disp = REG32(0x04000000);
    int mode = disp & 7;
    u16 bld = REG16(0x04000050), alpha = REG16(0x04000052);
    const u32 lo = ov_parked ? (u32)OV_BACKUP : (u32)OV_SRC, hi = (u32)(OV_COL + 256);
    for (int n = 0; n < 4; n++) {
        if (!(disp & (0x100u << n)) || (n == 0 && (disp & 8)))
            continue;
        if (((bld >> 6) & 3) == 1 && ((bld >> n) & 1) && !(alpha & 31))
            continue;                       /* blended at weight 0: shows nothing */
        u16 cnt = REG16(0x04000008 + 2 * n);
        int size = cnt >> 14;
        int affine = (n == 3 && mode >= 1 && mode <= 5) || (n == 2 && (mode == 2 || mode == 4 || mode == 5));
        int ext = (n == 3 && mode >= 3 && mode <= 5) || (n == 2 && mode == 5);
        u32 a0, a1;
        if (ext && (cnt & 0x80)) {          /* bitmap */
            static const u16 bw[4] = { 128, 256, 512, 512 }, bh[4] = { 128, 256, 256, 512 };
            a0 = 0x06000000 + ((cnt >> 8) & 31) * 0x4000;
            a1 = a0 + (u32)bw[size] * bh[size] * ((cnt & 4) ? 2 : 1);
            if (a0 < hi && a1 > lo)
                guard_hit(4);
            continue;
        }
        u32 cbase = 0x06000000 + ((disp >> 24) & 7) * 0x10000 + ((cnt >> 2) & 15) * 0x4000;
        u32 mbase = 0x06000000 + ((disp >> 27) & 7) * 0x10000 + ((cnt >> 8) & 31) * 0x800;
        int entries, tb = 32, wide = 1;
        if (affine && !ext) {
            int side = (128 << size) >> 3;
            entries = side * side;
            wide = 0;
            tb = 64;
        } else if (ext) {
            int side = (128 << size) >> 3;
            entries = side * side;
            tb = 64;
        } else {
            static const u16 tl[4] = { 1024, 2048, 2048, 4096 };
            entries = tl[size];
            if (cnt & 0x80)
                tb = 64;
        }
        a0 = mbase;
        a1 = mbase + (u32)entries * (wide ? 2 : 1);
        if (a0 < hi && a1 > lo) {
            guard_hit(4);
            continue;
        }
        int tmax = 0;
        for (int i = 0; i < entries; i++) {
            int t = wide ? (((const volatile u16 *)mbase)[i] & 0x3FF) : ((const volatile u8 *)mbase)[i];
            if (t > tmax)
                tmax = t;
        }
        if (cbase < hi && cbase + (u32)(tmax + 1) * tb > lo)
            guard_hit(4);
    }
}

static void hud_begin(int z_offset);
static void hud_end(void);
static void guard_draw(void)
{
#ifndef GUARD_DOT_TEST                      /* test builds only: the dot always lit, to judge its look */
    if (guard_until <= frame_no)
        return;
#endif
    hud_begin(-4090);                       /* in front of everything, overlay included */
    flat(0, 2, 5, 7, 0x001F, 31);           /* 5x5 red dot in the very corner (clear of the height tab's figures) */
    hud_end();
}
#endif

static void ov_band_draw(int ty)
{
    static const u8 wide[4][2] = { {16, 8}, {32, 8}, {32, 16}, {64, 32} };
    u32 disp = REG32(DISPCNT_B);
    int oshift = 5 + ((disp >> 20) & 3);
    u32 *b32 = (u32 *)OV_BUF;
    for (int i = 0; i < 8 * OV_STRIDE / 4; i++)
        b32[i] = 0;
    for (int p = 3; p >= 0; p--) {
        for (int b = 3; b >= 0; b--) {
            u16 cnt = REG16(BG0CNT_B + 2 * b);
            if (!(disp & (0x100u << b)) || (cnt & 3) != p)
                continue;
            if (!b && bazaar_rows && ty < 18)   /* the bazaar's rows without the teal behind them */
                continue;
            const u32 *chr = (const u32 *)(SUB_BGVRAM + ((cnt >> 2) & 15) * 0x4000);
            const u16 *map = (const u16 *)(SUB_BGVRAM + ((cnt >> 8) & 31) * 0x800) + ty * 32;
            for (int tx = 0; tx < 32; tx++) {
                u16 e = map[tx];
                const u32 *t = chr + (e & 0x3FF) * 8;
                const u8 *rm = 0;
                for (int k = 0; k < 8; k++) {
                    u32 w = t[e & 0x800 ? 7 - k : k];
                    if (!w)
                        continue;
                    if (!rm)
                        rm = ov_row(e >> 12);
                    ov_px8(OV_BUF + k * OV_STRIDE + 64 + tx * 8, w, e & 0x400, rm);
                }
            }
        }
        if (!(disp & 0x1000) || auction)    /* the token list's only sprites are the help's frames */
            continue;
        for (int i = 127; i >= 0; i--) {
            u16 a0 = SUB_OAM[i * 4], a1 = SUB_OAM[i * 4 + 1], a2 = SUB_OAM[i * 4 + 2];
            if ((a0 & 0x0300) == 0x0200 || (a0 & 0x2C00) >= 0x0800 || ((a2 >> 10) & 3) != p)
                continue;                   /* hidden, window, 256-colour, or another priority */
            if (bazaar_rows && !(((a2 & 0x3FF) - 226u) & ~32u))   /* tiles 226, 258 */
                continue;                   /* the ring around the bazaar's current row, which
                                               the cut rows would clip (the tab bar shows the kind) */
            int sh = a0 >> 14, sz = a1 >> 14, w, h;
            if (sh == 0) w = h = 8 << sz;
            else if (sh == 1) { w = wide[sz][0]; h = wide[sz][1]; }
            else { w = wide[sz][1]; h = wide[sz][0]; }
            int y0 = a0 & 0xFF, x0 = a1 & 0x1FF;
            if (y0 >= 192) y0 -= 256;
            if (x0 >= 256) x0 -= 512;
            if (x0 <= -64)
                continue;
            const u8 *rm = ov_row(16 + (a2 >> 12));
            const u32 *base = (const u32 *)(SUB_OBJVRAM + ((a2 & 0x3FF) << oshift));
            for (int k = 0; k < 8; k++) {
                int sy = ty * 8 + k - y0;
                if (sy < 0 || sy >= h)
                    continue;
                if (a1 & 0x2000) sy = h - 1 - sy;
                for (int cx = 0; cx < w / 8; cx++) {
                    int tc = a1 & 0x1000 ? w / 8 - 1 - cx : cx;
                    u32 wd = base[((sy >> 3) * (w >> 3) + tc) * 8 + (sy & 7)];
                    if (wd)
                        ov_px8(OV_BUF + k * OV_STRIDE + 64 + x0 + cx * 8, wd, a1 & 0x1000, rm);
                }
            }
        }
    }
    /* unchanged bands are not written again: melonDS's 3D renderer reads the texture bank
       anew after every write, and runs at half speed if that is every frame (ticket 28) */
    u32 sum = 1;
    for (int k = 0; k < 8; k++) {
        const u32 *s = (const u32 *)(OV_BUF + k * OV_STRIDE + 64);
        for (int i = 0; i < 64; i++)
            sum = ((sum << 5) | (sum >> 27)) + s[i];
    }
    if (sum == ov_sum[ty])
        return;
    ov_sum[ty] = sum;
#ifdef GUARD
    ov_safe(8);                             /* the check reads the band first: more room */
#else
    ov_safe(4);
#endif
    volatile u8 *bank = ov_tex < 0x20000 ? &VRAMCNT_A : &VRAMCNT_B;   /* A = texture slot 0, B = slot 1 */
    u8 old = *bank;
    *bank = 0x80;                           /* map to CPU while we write */
    u32 *dst = (u32 *)(0x06800000 + ov_tex) + ty * 8 * 64;
#ifdef GUARD
    if ((ov_hash_ok & (1u << ty)) && guard_sum(dst, 512) != ov_hash[ty])
        guard_hit(1);
    u32 *band = dst;
#endif
    for (int k = 0; k < 8; k++) {
        const u32 *s = (const u32 *)(OV_BUF + k * OV_STRIDE + 64);
        for (int i = 0; i < 64; i++)
            *dst++ = s[i];
    }
#ifdef GUARD
    ov_hash[ty] = guard_sum(band, 512);
    ov_hash_ok |= 1u << ty;
#endif
    *bank = old;
}

static void ov_copy(int restore)
{
    while (VCOUNT != 217)                   /* 48 KB takes a while: start right after a pick-up */
        ;
    u8 old = VRAMCNT_A;
    VRAMCNT_A = 0x80;
    u32 *a = restore ? OV_TEX_LCDC : OV_BACKUP, *b = restore ? OV_BACKUP : OV_TEX_LCDC;
    for (int i = 0; i < OV_WORDS; i++)
        a[i] = b[i];
    VRAMCNT_A = old;
}

static SMALL void ov_set(int on)
{
    if (on == ov_on)
        return;
    ov_on = (u8)on;
#ifdef GUARD
    ov_hash_ok = 0;
    if (!on && ov_parked)
        for (int b = 0; b < 24; b++)
            guard_backup_check(b);
#endif
    if (!on) {
        if (ov_parked)
            ov_copy(1);
        ov_manual = 0;
        return;
    }
    /* the heap's free top if this scene has a heap, it is free, and bank B is texture slot 1 */
    if (heap_present() && VRAMCNT_B == 0x8B && tex_free(OV_HEAP_TEX, OV_HEAP_TEX + OV_WORDS * 4)) {
        ov_tex = OV_HEAP_TEX;
        ov_parked = 0;
    } else {
        ov_tex = OV_TEX;
        ov_parked = 1;
        ov_copy(0);
#ifdef GUARD
        guard_backup_sums();
#endif
    }
    for (int i = 0; i < 32 * 16; i++)
        OV_SRC[i] = 0;
    for (int i = 0; i < 24; i++)
        ov_sum[i] = 0;
    ov_ncol = 1;
    ov_band = 0;
    ov_ready = 0;
}

static void ov_step(void)
{
    ov_rows_ok = 0;
    /* an auction keeps the list up for minutes and changes it seldom: half the pace */
    for (int n = auction ? OV_BANDS_PER_FRAME / 2 : 0; n < OV_BANDS_PER_FRAME; n++) {
        ov_band_draw(ov_band);
        if (++ov_band == 24) {
            ov_band = 0;
            ov_ready = 1;
        }
    }
    if (ov_pal_dirty) {
        ov_pal_dirty = 0;
        ov_safe(4);
        u8 oldg = VRAMCNT_G;
        VRAMCNT_G = 0x80;
        for (int i = 1; i < ov_ncol; i++)
            PAL_LCDC[(OV_PAL - PAL_ADDR) / 2 + i] = OV_COL[i] & 0x7FFF;
        VRAMCNT_G = oldg;
    }
}

/* our own projection: pixels*16 in, true screen corners out */
static __attribute__((noinline)) void proj_begin(int kx, int ky, int tx, int ty, int z)
{
    GX(G_MODE) = 0;
    GX(G_PUSH) = 0;
    volatile u32 *l = &GX(G_LOAD44);
    *l = (u32)(2 * kx); *l = 0; *l = 0; *l = 0;
    *l = 0; *l = (u32)-((10923 * ky) >> 12); *l = 0; *l = 0;
    *l = 0; *l = 0; *l = 4096; *l = 0;
    *l = (u32)tx; *l = (u32)ty; *l = (u32)z; *l = 4096;
    GX(G_MODE) = 2;
    GX(G_PUSH) = 0;
    GX(G_IDENT) = 0;
    hud_layer = 0;
}

static void hud_begin(int z_offset)
{
    if (tile_cfg[1])                    /* test captures: one unsqueezed piece of the wide view */
        proj_begin(4096, 4096, -4096 * screen_w / 256 + tile_cfg[2], 4096 * VIEW_H / 192 + tile_cfg[3], z_offset);
    else
        proj_begin(wide_x, wide_y, -4096 + nudge_x, 4096 + nudge_y, z_offset);
}

static void hud_end(void)
{
    GX(G_POP) = 1;
    GX(G_MODE) = 0;
    GX(G_POP) = 1;
    GX(G_MODE) = 2;
}

static void ov_texture(void)
{
    GX(G_TEXIMAGE) = (ov_tex >> 3) | (5u << 20) | (5u << 23) | (4u << 26) | (1u << 29);
    GX(G_PLTT_BASE) = OV_PAL >> 4;
    GX(G_POLY_ATTR) = 0x3E0000C0 | ((u32)(auction || bazaar_rows ? 31 : OV_ALPHA) << 16);
    GX(G_COLOR) = 0x7FFF;
}

static void ov_quad(int x, int y, int s0, int t0, int s1, int t1)
{
    ov_texture();
    quad(x, y, x + s1 - s0, y + t1 - t0, s0, t0);
}

/* The bidding layout: the field, at its own size, fills the left of the wide
   picture (auction_project); the rest is cut from the token list, redrawn like
   the overlay.  The list's rows are in the order of the field's lanes, so each
   clan's name and counts stand beside its lane. */
#define AUC_SPLIT  (VIEW_H >= 228 ? 112 : 176)   /* where the round's box ends */
#define AUC_X      (256 + (VIEW_W - 256 - 110) / 2)
static const struct { short x; u8 y, s0, t0, s1, t1; } AUC_CUT[] = {
    { AUC_X + 10, 0, 139, 66, 236, 79 },                        /* the four tokens */
#if VIEW_H >= 228
    { 0, 195, 4, 8, 112, 22 }, { 0, 211, 4, 26, 112, 39 },      /* round, and what is up for bids */
    { 176, 204, 135, 178, 212, 191 },                           /* Retire */
    { AUC_X, 170, 127, 2, 237, 59 },                            /* the buttons, as the game draws them */
#else                                       /* 16:9: lower, so the cross is flattened */
    { 0, 197, 4, 8, 92, 22 }, { 88, 198, 4, 26, 92, 39 },
    { 178, 197, 135, 178, 212, 191 },
    { AUC_X + 24, 171, 152, 3, 190, 26 }, { AUC_X, 195, 129, 27, 157, 44 },
    { AUC_X + 29, 195, 152, 43, 181, 60 }, { AUC_X + 59, 195, 177, 27, 206, 44 },
    { AUC_X + 94, 178, 212, 18, 237, 45 },
#endif
};

static SMALL void auc_fill(int x0, int y0, int x1, int y1, int s, int t)
{
    quad_texel = 1;
    ov_texture();
    quad(x0, y0, x1, y1, s, t);
    quad_texel = 0;
}

static SMALL void auction_draw(void)
{
    /* the fills are texels of the list too: melonDS shows a plain colour a shade lighter
       than the same colour in a texture */
    auc_fill(256, 0, VIEW_W + 1, 6, 90, 56);
    hold_layer = 1;
    auc_fill(256, 6, VIEW_W + 1, 169, 150, 185);
    auc_fill(256, 169, VIEW_W + 1, VIEW_H + 1, 90, 56);
    auc_fill(0, 192, AUC_SPLIT, VIEW_H + 1, 50, 40);
    auc_fill(AUC_SPLIT, 192, 256, VIEW_H + 1, 150, 185);
    hold_layer = 0;
    for (u32 i = 0; i < sizeof AUC_CUT / sizeof *AUC_CUT; i++, hold_layer = 1)
        ov_quad(AUC_CUT[i].x, AUC_CUT[i].y, AUC_CUT[i].s0, AUC_CUT[i].t0, AUC_CUT[i].s1, AUC_CUT[i].t1);
    for (int i = 0; i < 6; i++) {
        int y = 13 + 26 * i, t = 81 + 16 * i;
        ov_quad(AUC_X + 4, y, 124, t + 1, 130, t + 13);         /* the lane's colour, */
        ov_quad(AUC_X + 10, y, 14, t + 1, 110, t + 13);         /* the clan's name, */
        ov_quad(AUC_X + 4, y + 12, 133, t, 235, t + 14);        /* its tokens */
    }
    hold_layer = 0;
    /* the first auction's help frames the token counts, then the buttons, with the
       list's only sprites: a frame around the same thing here */
    if (SUB_OAM[0] && (SUB_OAM[0] >> 14) != 3) {    /* a parked sprite has shape 3 */
        int y0 = (SUB_OAM[0] & 0xFF) > 64 ? 0 : 168, y1 = y0 ? VIEW_H : 170;
        u16 c = SUB_OBJPAL[(SUB_OAM[2] >> 12) * 16 + 7];   /* the two rows take turns: it blinks */
        flat(256, y0, VIEW_W, y0 + 2, c, 31);
        hold_layer = 1;
        flat(256, y1 - 2, VIEW_W, y1, c, 31);
        flat(256, y0 + 2, 258, y1 - 2, c, 31);
        flat(VIEW_W - 2, y0 + 2, VIEW_W, y1 - 2, c, 31);
        hold_layer = 0;
    }
}

/* A loot row's kind icon sits in a round bubble that the game draws from the screen's
   left edge (a 64x32 sprite at x 0), so its left part was never drawn: it is drawn here,
   left of the row at (x, y) = the sprite's top left, in the sprite's own colours (outline,
   three shades inward, fill: entries 1, 3, 4, 5, 6).  The caps above and below the icon
   make a circle of radius 13 about x 6.5; bands of rows of the same width, mirrored about
   its middle (rows 6..25 of the sprite). */
static const u8 BZ_ARC[6] = { 6, 7, 8, 10, 12, 16 };     /* first row of each band; widths 2..6 */
static const u8 BZ_ARC_COL[5] = { 1, 3, 4, 5, 6 };

static SMALL void bz_arc(int x, int y, int k)
{
    const u16 *o = SUB_OAM;
    for (int i = 0; i < 128; i++, o += 4)
        if ((o[0] & 0xC3FF) == 0x4000 + 16 + 32 * k && (o[1] & 0xC1FF) == 0xC000)
            break;                          /* the row's bar: shape 64x32, at x 0 */
    if (o == SUB_OAM + 128 * 4)
        return;
    const u16 *pl = SUB_OBJPAL + (o[2] >> 12) * 16;
    for (int b = 0; b < 5; b++) {
        int w = b + 2, r0 = BZ_ARC[b], r1 = BZ_ARC[b + 1];
        for (int h = 0; h < 2; h++) {
            int y0 = h ? y + 32 - r1 : y + r0;
            for (int i = 0; i < 5 && i < w; i++)
                flat(x - w + i, y0, i == 4 ? x : x - w + i + 1, y0 + r1 - r0, pl[BZ_ARC_COL[i]], 31);
        }
    }
}

static SMALL void ov_draw(void)
{
    hud_begin(-4080);                       /* in front of the game's own panels */
    if (auction) {
        auction_draw();
    } else if (ov_manual) {
        if (OV_DIM)
            flat(0, 0, screen_w, screen_h, 0, OV_DIM);
        ov_quad((screen_w - 256) / 2, (screen_h - 192) / 2, 0, 0, 256, 192);
    } else if (jobs_panel) {
        ov_quad(0, 0, JOBS_SRC_X0, JOBS_SRC_Y0, JOBS_SRC_X1, JOBS_SRC_Y1);
    } else if (bazaar_rows) {
        int x = (screen_w - 256) / 2 + BZ_DEBUG * 300, y = BZ_Y;
        for (int k = 0; k < bazaar_rows; k++, y += BZ_PITCH) {
            ov_quad(x, y, 0, 20 + 32 * k, 256, 20 + 32 * k + BZ_PITCH);
            hold_layer = 1;                 /* side by side: one layer */
            bz_arc(x, y - 4, k);
        }
        if (bazaar_head)
            ov_quad(x + 8, y, 8, 153, 256, 185);       /* down to the view's bottom edge */
        hold_layer = 0;
    } else {
        /* beside the game's Item Info panel, which fills the right half: only
           the stats part of the info screen.  With a unit sheet up (equipment)
           that is its left column, otherwise (shop) the item's stat block. */
        const u16 *name = (const u16 *)(SUB_BGVRAM + ((REG16(BG1CNT_B) >> 8) & 31) * 0x800) + 32 + 8;
        if (name[0] | name[1] | name[2])
            ov_quad(8, (screen_h - 192) / 2, 0, 0, 128, 192);
        else
            ov_quad(20, 40, 144, 64, 256, 192);
    }
    hud_end();
}

/* is texture memory lo..hi free in the game's battle heap?  (no heap: free) */
/* does the current scene have the game's texture heap? (battle and the heap menus) */
static int heap_present(void)
{
    u32 heap = TEX_HEAP_PTR;
    return heap >= 0x02000000 && heap < 0x02400000;
}

static SMALL int tex_free(u32 lo, u32 hi)
{
    u32 heap = TEX_HEAP_PTR, have = 0;
    if (heap < 0x02000000 || heap >= 0x02400000)
        return 1;
    u32 node = *(volatile u32 *)(heap + 8);
    for (int i = 0; i < 64 && node >= 0x02000000 && node < 0x02400000; i++) {
        u32 a = *(volatile u32 *)(node + 8), b = a + *(volatile u32 *)(node + 12);
        if (a < lo) a = lo;
        if (b > hi) b = hi;
        if (b > a)
            have += b - a;
        node = *(volatile u32 *)(node + 4);
    }
    return have >= hi - lo;
}

/* ---- turn order drawing (stage at the bottom, or the strip on 4:3) ---- */
#define TURN_PITCH 22
#define TURN_GAP0  3       /* extra room after slot 0, the acting unit */
#define CURSOR_COL 0x7F8C  /* light blue: the unit browsed to with L/R */

static int turn_width(int n)
{
    return n * TURN_PITCH + (n > 1 ? TURN_GAP0 : 0);
}

static const u8 TRI_OUT[5] = { 4, 4, 3, 2, 1 };
static const u8 TRI_IN[3] = { 3, 2, 1 };

static SMALL void turn_units(int n, int gx, int base)
{
    for (int k = 0; k < n; k++) {
        int cx = gx + k * TURN_PITCH + (k ? TURN_GAP0 : 0) + (TURN_PITCH >> 1);
        int t = slot_turn[k], side = t < q_n ? q_side[t] : 0;
        if (k == 0) {
            shape(cx, base - 3, RING14, 9, DISC_ORANGE, 31);
            shape(cx, base - 3, RING9, 5, DISC_LIGHT, 31);
        } else if (side)
            shape(cx, base - 3, SHADOW10, 5, SIDE_FILL(side), 20);   /* a rim in the side's colour around the game's shadow */
        unit_pic(k, cx, base);
        if (k + 1 == cursor_mark) {         /* a bobbing arrow over the browsed unit */
            int y = base - (unit_box[k][3] - unit_box[k][1]) - 6 + ((frame_no >> 4) & 1);
            int ys = y - 1;
            for (int r = 0; r < 5; r++) {
                flat(cx - TRI_OUT[r], ys + r, cx + TRI_OUT[r], ys + r + 1, 0x0842, 31);
                hold_layer = 1;
            }
            hold_layer = 0;
            for (int r = 0; r < 3; r++) {
                flat(cx - TRI_IN[r], y + r, cx + TRI_IN[r], y + r + 1, CURSOR_COL, 31);
                hold_layer = 1;
            }
            hold_layer = 0;
        }
    }
    if (n > 1 && slot_turn[1] > 1) {        /* turns skipped between the acting unit and the rest */
        int x = gx + TURN_PITCH + 1;
        for (int d = 0; d < 3; d++)
            flat(x, base - 16 + d * 4, x + 1, base - 15 + d * 4, 0x5294, 31);
    }
}

/* every coming turn, the first being the acting unit's; the browsed one outlined */
static SMALL void turn_pips(int np, int x0, int y)
{
    int b = cursor_mark ? slot_turn[cursor_mark - 1] : -1, j0 = b >= np ? b - np + 1 : 0;
    if (b >= 0)
        flat(x0 + (b - j0) * 5 - 1, y - 1, x0 + (b - j0) * 5 + 5, y + 4, CURSOR_COL, 31);
    for (int j = 0; j < np; j++)
        pip(x0 + j * 5, y, SIDE_FILL(q_side[j0 + j]));
}

/* width in cells of a two-row text run on the info screen (0 if empty) */
static int run_width(const u16 *smap, int row, int col)
{
    int last = -1;
    for (int c = col; c < 32; c++)
        if ((smap[row * 32 + c] & 0x3FF) || (smap[(row + 1) * 32 + c] & 0x3FF))
            last = c;
    return last < 0 ? 0 : last - col + 2;   /* one pad cell each side */
}

static SMALL void glow_draw(void);
static void proj_begin(int kx, int ky, int tx, int ty, int z);

__attribute__((used)) SMALL void hud3d_draw(void)
{
    glow_draw();
    /* retire the old 2D banner if a saved state still has it on screen */
    if (REG16(BG1CNT_A) == M_BG1CNT) {
        for (int i = 0; i < 6 * 32; i++)
            M_MAP[i] = 0;
        REG16(BG1CNT_A) = 0x0003;
    }
    if (ov_on && ov_ready)
        ov_draw();
#ifdef GUARD
    guard_draw();
#endif
    if (!battle_hud_present()) {
        hud_hash = 0;                   /* other scenes may reuse the memory: upload again next time */
        return;
    }
    if (!banner_enabled)
        return;
    if (*(volatile int *)0x02131BD0)
        return;                         /* a Scion's animation (dual_state +0x18, ticket 26) */
    if (BATTLE_OVER)
        return;                         /* decided: results and law bonus need no objective, law or turn order */
    if (speech_frame == frame_no)
        return;                         /* a dialogue box is up: stay out of its way */

    u16 scnt = REG16(BG1CNT_B);
    const u32 *schar = (const u32 *)(SUB_BGVRAM + ((scnt >> 2) & 15) * 0x4000);
    const u16 *smap = (const u16 *)(SUB_BGVRAM + ((scnt >> 8) & 31) * 0x800);
    /* the banner's boxes: objective, law, privilege.  In the text texture the
       objective has line 0 and the law and privilege share line 1; the info
       screen holds at most 29 cells per line, so nothing has to give way. */
    static const u8 run_src[3][2] = {
        { SRC_OBJ_ROW, SRC_OBJ_COL }, { SRC_LAW_ROW, SRC_LAW_COL }, { SRC_PRIV_ROW, SRC_PRIV_COL } };
    int rw[3];
    for (int b = 0; b < 3; b++)
        rw[b] = run_width(smap, run_src[b][0], run_src[b][1]);
    if (rw[0] > TEXT_CELLS) rw[0] = TEXT_CELLS;
    if (rw[1] > TEXT_CELLS) rw[1] = TEXT_CELLS;
    if (rw[1] + rw[2] > TEXT_CELLS) rw[2] = TEXT_CELLS - rw[1];
    const int tline[3] = { 0, 1, 1 }, tcol[3] = { 0, 0, rw[1] };

    /* turn order: 32x32 16-colour sprites in the info screen's turn area, in
       turn order from the left; the enlarged one is the focused unit: the acting
       unit, or the one the player browses to with L/R (up to three earlier
       units then stand to its left) */
    int xs[TURN_SEEN], ys[TURN_SEEN];
    u16 a2s[TURN_SEEN], feet[TURN_SLOTS];
    u8 focus[TURN_SEEN];
    int n = 0;
    for (int i = 0; i < 128; i++) {
        u16 a0 = SUB_OAM[i * 4], a1 = SUB_OAM[i * 4 + 1];
        if ((a0 & 0x0300) == 0x0200 || (a0 & 0xE000) || (a1 >> 14) != 2)
            continue;
        int y = a0 & 0xFF;
        if (y < 96 || y > 152)
            continue;
        int x = a1 & 0x1FF;
        if (x >= 256)
            continue;
        {   /* ignore placeholder sprites with no picture in them */
            const u32 *px = (const u32 *)(SUB_OBJVRAM + ((SUB_OAM[i * 4 + 2] & 0x3FF) << (5 + ((REG32(DISPCNT_B) >> 20) & 3))));
            u32 any = 0;
            for (int w = 0; w < 96; w += 3)
                any |= px[w];
            if (!any)
                continue;
        }
        int j = n < TURN_SEEN ? n : TURN_SEEN - 1;
        if (n >= TURN_SEEN && x >= xs[j])
            continue;
        while (j > 0 && xs[j - 1] > x) {
            xs[j] = xs[j - 1];
            ys[j] = ys[j - 1];
            a2s[j] = a2s[j - 1];
            focus[j] = focus[j - 1];
            j--;
        }
        xs[j] = x;
        ys[j] = y;
        a2s[j] = SUB_OAM[i * 4 + 2];
        focus[j] = y < 128;
        if (n < TURN_SEEN)
            n++;
    }
    int oshift = 5 + ((REG32(DISPCNT_B) >> 20) & 3);
    int f = 0;
    while (f < n && !focus[f])
        f++;
    int focus_found = f < n;
    if (!focus_found)
        f = 0;
    int mark_found = 0;

    /* the pip strip along the bottom of the info screen: one 8x8 sprite per
       coming turn, left to right, squares for the turns shown as heads and
       diamonds after; palette 3 = an ally's turn, 4 = an enemy's */
    {
        short qx[QUEUE_MAX];
        q_n = 0;
        for (int i = 0; i < 128; i++) {
            u16 a0 = SUB_OAM[i * 4], a1 = SUB_OAM[i * 4 + 1], a2 = SUB_OAM[i * 4 + 2];
            int y = a0 & 0xFF, pal = a2 >> 12;
            if ((a0 & 0x0300) == 0x0200 || (a0 & 0xC000) || (a1 & 0xC000) || y < 178 || y > 190 || (pal != 3 && pal != 4))
                continue;
            int x = a1 & 0x1FF, j = q_n < QUEUE_MAX ? q_n : QUEUE_MAX - 1;
            if (x >= 384)
                x -= 512;                   /* off the left edge */
            if (q_n >= QUEUE_MAX && x >= qx[j])
                continue;
            while (j > 0 && qx[j - 1] > x) {
                qx[j] = qx[j - 1];
                q_side[j] = q_side[j - 1];
                j--;
            }
            qx[j] = (short)x;
            q_side[j] = (u8)(pal - 2);
            if (q_n < QUEUE_MAX)
                q_n++;
        }
        /* the focused unit's turn: the pip under the enlarged sprite's middle
           (it is drawn at double size, 64 px wide) */
        int mid = n ? xs[f] + 32 : 128;
        q_mark = 0;
        for (int j = 0; j < q_n; j++)
            if (qx[j] <= mid && mid < qx[j] + 8) {
                q_mark = j;
                mark_found = 1;
            }
    }

    /* Which units go in the four slots.  Slot 0 is always the acting unit
       (whose turn it is, on the orange ring).  The info screen is either
         settled on the acting unit (enlarged, leftmost, over the first pip):
           slots = turns 1-4;
         settled on a unit the player browses to with L/R (or a forecast's
           target): slot 0 keeps the acting unit's picture from before, the
           other three show turns 2-4, or from turn 5 on the unit before the
           browsed one, the browsed one and the one after; the browsed one gets
           the cursor;
         between the two (the units slide after an L/R press, or are not yet at
           rest): nothing changes. */
    u32 pos = (u32)n;                       /* the units must be at rest: same places as last frame */
    for (int k = 0; k < n; k++)
        pos = pos * 509 + (u32)xs[k] * 263 + (u32)ys[k];
    int at_rest = pos == last_pos;
    last_pos = pos;
    int mode = !(focus_found && mark_found && at_rest) ? 2 : (f == 0 && q_mark == 0) ? 0 : 1;
    int up_from = mode == 1 ? 1 : 0;
    if (mode == 2) {
        n = shown_n;
    } else {
        int t0 = q_mark - f;                /* the turn of the leftmost unit seen */
        int want[TURN_SLOTS], m = 0;
        if (mode == 0)
            for (; m < TURN_SLOTS; m++)
                want[m] = m;
        else {
            int b = q_mark, first = b <= 3 ? 1 : b - 1;
            if (first + 2 > t0 + n - 1)
                first = t0 + n - 3;         /* the end of what the info screen shows */
            if (first < 1)
                first = 1;
            want[m++] = 0;
            for (int t = first; m < TURN_SLOTS; t++)
                want[m++] = t;
            cursor_mark = b - first + 2;
        }
        if (mode == 0)
            cursor_mark = 0;
        int k = 0, tx[TURN_SLOTS], ty_[TURN_SLOTS];
        u16 ta[TURN_SLOTS];
        for (; k < m; k++) {
            int i = want[k] - t0;
            if (k < up_from)
                continue;
            if (i < 0 || i >= n)
                break;
            tx[k] = xs[i]; ty_[k] = ys[i]; ta[k] = a2s[i];
        }
        for (int j = up_from; j < k; j++) {
            xs[j] = tx[j]; ys[j] = ty_[j]; a2s[j] = ta[j];
        }
        n = k;
        for (k = 0; k < TURN_SLOTS; k++)
            slot_turn[k] = (u8)(k < n ? want[k] : 0);
        if (mode == 1 && !slot0_ok)
            n = 0;                          /* the acting unit's picture is gone (memory was taken) */
        shown_n = n;
    }

    /* each unit is two sprites on the info screen: the 32x32 body and, under
       it, a 32x8 strip with the feet and the ground shadow (same x, same palette) */
    for (int k = up_from; k < n && mode != 2; k++) {
        feet[k] = 0xFFFF;
        for (int i = 0; i < 128; i++) {
            u16 a0 = SUB_OAM[i * 4], a1 = SUB_OAM[i * 4 + 1], a2 = SUB_OAM[i * 4 + 2];
            int y = a0 & 0xFF;
            if ((a0 & 0x0300) == 0x0200 || (a0 >> 14) != 1 || (a1 >> 14) != 1 ||
                (a1 & 0x1FF) != xs[k] || (a2 >> 12) != (a2s[k] >> 12) || y < ys[k] + 16 || y > ys[k] + 72)
                continue;
            feet[k] = a2;
            break;
        }
    }

    /* the shared texture memory: without the top half no banner, without the
       lower half no units; upload again when it comes back */
    if (!tex_free(TEXT_TEX, TEXT_TEX + 0x1000)) {
        hud_hash = 0;
        slot0_ok = 0;
        return;
    }
    int units_ok = tex_free(HEAD_TEX, HEAD_TEX + 0x1000);
    if (!units_ok) {
        n = 0;
        slot0_ok = 0;
    }

    /* upload texture and palettes only when the source changed */
    u32 h = (u32)n * 2 + (u32)units_ok;
    if (mode == 2 && hud_hash)
        goto uploaded;                      /* mid-slide: the texture still holds what is shown */
    h = h * 7 + (u32)mode;
    for (int b = 0; b < 3; b++) {
        h = h * 131 + (u32)rw[b];
        for (int r = 0; r < 2; r++)
            for (int c = 0; c < rw[b]; c++)
                h = h * 33 + smap[(run_src[b][0] + r) * 32 + run_src[b][1] + c];
    }
    for (int k = up_from; k < n; k++) {
        const u32 *src = (const u32 *)(SUB_OBJVRAM + ((a2s[k] & 0x3FF) << oshift));
        h = h * 33 + a2s[k];
        h = h * 33 + feet[k];
        for (int i = 0; i < 96; i += 5)
            h = h * 33 + src[i];
    }
    h = h * 33 + SUB_BGPAL[5] + SUB_BGPAL[9];
    /* the game may still be changing a sprite's graphics the frame after it
       moved it: upload only what has stayed the same for two frames */
    int steady = h == last_src;
    last_src = h;
    if (h != hud_hash && !steady && hud_hash)
        goto uploaded;
    if (h != hud_hash) {
        hud_hash = h;
        ov_safe(34);                        /* up to 30 lines, then the palettes; bank B also holds the map and units: not while the 3D engine picks it up */
        u8 oldb = VRAMCNT_B, oldg = VRAMCNT_G;
        VRAMCNT_B = 0x80;                   /* map to CPU while we write */
        u32 *tt = TEX_LCDC + 0x1000 / 4;    /* 512x32 at 2 bits: 32 words per pixel row */
        for (int i = 0; i < 32 * 32; i++)
            tt[i] = 0;
        u16 *t16 = (u16 *)tt;               /* one 8-pixel cell row is one halfword */
        for (int b = 0; b < 3; b++) {
            txt_l[b] = 0x7FFF;
            txt_r[b] = -1;
            for (int c = 0; c < rw[b]; c++) {
                int g = 0xFF;
                u32 any = 0;
                for (int r = 0; r < 2; r++) {
                    u16 cell = smap[(run_src[b][0] + r) * 32 + run_src[b][1] + c];
                    const u32 *sp = schar + (cell & 0x3FF) * 8;
                    for (int k = 0; k < 8; k++) {
                        u32 w = sp[k];
                        any |= w;
                        if (w && g == 0xFF) {
                            u32 v = w;
                            while (!(v & 15))
                                v >>= 4;
                            g = (v & 15) >> 2;
                        }
                        w &= 0x33333333;        /* 4 bits a pixel to 2 */
                        w = (w | w >> 2) & 0x0F0F0F0F;
                        w = (w | w >> 4) & 0x00FF00FF;
                        w |= w >> 8;
                        t16[(tline[b] * 16 + r * 8 + k) * 64 + tcol[b] + c] = (u16)w;
                    }
                }
                txt_grp[tline[b]][tcol[b] + c] = (u8)g;
                for (int i = 0; i < 8; i++, any >>= 4)
                    if (any & 15) {
                        if (c * 8 + i < txt_l[b]) txt_l[b] = (short)(c * 8 + i);
                        if (c * 8 + i > txt_r[b]) txt_r[b] = (short)(c * 8 + i);
                    }
            }
        }
        u32 *ht = TEX_LCDC;                 /* 128x64: 16 words per pixel row */
        for (int i = 0; units_ok && i < 64 * 16; i++)
            if ((i & 15) >= up_from * 4)    /* slot 0 keeps the acting unit while browsing */
                ht[i] = 0;
        for (int k = up_from; k < n; k++) {
            const u32 *src = (const u32 *)(SUB_OBJVRAM + ((a2s[k] & 0x3FF) << oshift));
            int bx0 = 32, by0 = 32, bx1 = 0, by1 = 0;
            u32 any[4] = { 0, 0, 0, 0 };
            const u32 *fsrc = feet[k] == 0xFFFF ? 0 : (const u32 *)(SUB_OBJVRAM + ((feet[k] & 0x3FF) << oshift));
            for (int row = 0; row < 40; row++)
                for (int tx = 0; tx < 4; tx++) {
                    u32 w = row < 32 ? src[((row >> 3) * 4 + tx) * 8 + (row & 7)] : fsrc ? fsrc[tx * 8 + row - 32] : 0;
                    ht[row * 16 + k * 4 + tx] = w;
                    if (!w)
                        continue;
                    if (row < by0) by0 = row;
                    by1 = row + 1;
                    any[tx] |= w;
                }
            for (int x = 0; x < 32; x++)
                if ((any[x >> 3] >> (4 * (x & 7))) & 15) {
                    if (x < bx0) bx0 = x;
                    bx1 = x + 1;
                }
            unit_box[k][0] = (short)bx0; unit_box[k][1] = (short)by0;
            unit_box[k][2] = (short)bx1; unit_box[k][3] = (short)by1;
        }
        int whole = VRAMCNT_B == 0x80;
        if (!whole) {                       /* the game took the bank while we wrote: do it again */
            hud_hash = 1;                   /* not 0: that would upload even while the units slide */
            slot0_ok = 0;
        }
        VRAMCNT_B = oldb;
        VRAMCNT_G = 0x80;
        for (int i = 0; i < 16; i++)
            PAL_LCDC[i] = SUB_BGPAL[i];
        for (int k = up_from; k < n; k++)
            for (int i = 0; i < 16; i++)
                PAL_LCDC[(k + 1) * 16 + i] = SUB_OBJPAL[(a2s[k] >> 12) * 16 + i];
        if (mode == 0 && n && whole)
            slot0_ok = 1;
        VRAMCNT_G = oldg;
    }
uploaded:
    hud_drawn_frame = frame_no;         /* also while hidden below: the B hint stays dropped */
    if (hud_hit && hud_hit + 2 > frame_no)
        return;                         /* a game panel lies on the banner's corner */

    hud_begin(-3686);

    /* the boxes sit against the right edge: objective on red, law and
       privilege on parchment with a rule between them.  What does not fit
       beside the height tab flows onto further rows, each against the right
       edge; the turn order goes under the last row. */
    int row[3], row_w[3] = { 0, 0, 0 }, rows = 1, bw[3];
    for (int b = 0; b < 3; b++)             /* each box: its text's inked width and a pad each side */
        bw[b] = rw[b] && txt_r[b] >= txt_l[b] ? txt_r[b] - txt_l[b] + 1 + 2 * BOX_PAD : 0;
    for (int b = 0; b < 3; b++) {
        int w = bw[b], pair = b == 1 && bw[2] ? w + bw[2] : 0;
        row[b] = 2;
        if (!w)
            continue;
        /* the first row with room for the box (the law: for the law and the
           privilege together), except that the law goes alone into a row that
           would otherwise stay empty above them (4:3 with a long objective) */
        int solo = 3, both = 3;
        for (int r = 2; r >= 0; r--) {
            int room = screen_w - (r ? 0 : BANNER_X) - row_w[r];
            if (w <= room) solo = r;
            if (pair && pair <= room) both = r;
        }
        if (b == 2 && bw[1] && row_w[row[1]] + w <= screen_w - (row[1] ? 0 : BANNER_X))
            row[b] = row[1];
        else if (pair && both < 3 && !(solo < both && !row_w[solo]))
            row[b] = both;
        else if (solo < 3)
            row[b] = solo;
        row_w[row[b]] += w;
        if (row[b] + 1 > rows)
            rows = row[b] + 1;
    }
    int row_x[3], hud_left = screen_w;
    for (int r = 0; r < 3; r++) {
        row_x[r] = screen_w - row_w[r] < 0 ? 0 : screen_w - row_w[r];
        if (row_w[r] && row_x[r] < hud_left)
            hud_left = row_x[r];
    }
    for (int b = 0; b < 3; b++) {
        int w = bw[b], r = row[b], y = r * 16, x = row_x[r];
        if (!w)
            continue;
        row_x[r] += w;
        flat(x, y, x + w, y + 16, SUB_BGPAL[b ? 13 * 16 + 14 : 14 * 16 + 7], 31);
        if (b == 2 && bw[1] && row[1] == r)
            flat(x, y + 2, x + 1, y + 14, SUB_BGPAL[13 * 16 + 4], 31);
        /* one quad per stretch of cells in the same colour group */
        const u8 *grp = txt_grp[tline[b]] + tcol[b];
        for (int c0 = 0, c = 0, g = 0xFF; c <= rw[b]; c++) {
            if (c < rw[b] && (grp[c] == 0xFF || g == 0xFF || grp[c] == g)) {
                if (grp[c] != 0xFF)
                    g = grp[c];
                continue;
            }
            /* the run's cells, shifted so the ink starts BOX_PAD in; the empty
               ends of the first and last cells are cut at the box's edges */
            int a = x + BOX_PAD - txt_l[b] + c0 * 8, e = x + BOX_PAD - txt_l[b] + c * 8, s0 = (tcol[b] + c0) * 8;
            if (a < x) { s0 += x - a; a = x; }
            if (e > x + w) e = x + w;
            if (g != 0xFF && e > a)
                textured4(a, y, e, y + 16, s0, tline[b] * 16, TEXT_TEX, 6, 2, PAL_ADDR + 8 * g);
            c0 = c;
            g = c < rw[b] ? grp[c] : 0xFF;
        }
    }
    int ty = rows * 16 + 1;                 /* top of the turn order */
    banner_extra = (rows - 1) * 16;
    hud_bottom = rows * 16;
    turn_left = screen_w;
    if (n) {
        /* stage: between the unit panel (ends at x 124 in every preset) and
           the Help bar (starts 94 px from the right edge), on the bottom rows */
        int gl = 128, gr = screen_w - 98, gw = turn_width(n);
        if (gr - gl >= turn_width(TURN_SLOTS)) {
            /* the shadows' bottom row; the screen's last row or two can fall off the
               edge in melonDS (the vertical sub-pixel nudge), so keep clear of them */
            int gx = gl + ((gr - gl - gw) >> 1), base = screen_h - 4;
            stage_box[0] = (short)(gx - 1); stage_box[1] = (short)(base - 46);
            stage_box[2] = (short)(gx + gw + 1); stage_box[3] = (short)screen_h;
            if (stage_hit + 2 <= frame_no) {
                flat(gx - 1, base - 5, gx + gw + 1, screen_h, 0x0842, 14);         /* a low ledge for the feet and pips */
                turn_units(n, gx, base);
                int np = q_n < STAGE_PIPS ? q_n : STAGE_PIPS;
                turn_pips(np, gx + ((gw - np * 5) >> 1) + 1, screen_h - 6);
            }
        } else {
            /* too narrow down there (4:3): the same units, ring and pips in a dark
               strip at the top right, under the banner */
            int sw = turn_width(n) + 4, hx = screen_w - sw, base = ty + 41;
            turn_left = hx;
            flat(hx, ty, screen_w, ty + 46, 0x1463, 18);                            /* dark backing */
            hud_bottom = ty + 46;
            turn_units(n, hx + 2, base);
            int np = q_n;
            while (np * 5 > sw - 4)
                np--;
            turn_pips(np, hx + 3, ty + 42);
        }
    }
    hud_box[0] = (short)hud_left;
    hud_box[1] = 0;
    hud_box[2] = (short)screen_w;
    hud_box[3] = (short)(rows * 16);
    hud_box[4] = (short)turn_left;          /* empty when the units are on the stage */
    hud_box[5] = (short)(rows * 16);
    hud_box[6] = (short)screen_w;
    hud_box[7] = (short)hud_bottom;

    hud_end();
}

__attribute__((naked, used)) void swap_stub(void)   /* call at 0x0201E274 */
{
    __asm__("push {r0, r1, r2, r3, r12, lr}\n"
            "bl hud3d_draw\n"
            "pop {r0, r1, r2, r3, r12, lr}\n"
            "ldr r12, =0x01FFB51C\n"   /* the game's swap-buffers routine */
            "bx r12\n"
            ".ltorg\n");
}

#ifdef MAP_ART
static SMALL void map_art_frame(void);
#endif

/* Is the info screen a menu's?  Menus build it from 16-colour tile layers only,
   the one kind the overlay can redraw.  Story scenes, after-battle dialogue and
   the title show a 256-colour picture layer there instead; the overlay is not
   offered then (ticket 31: its panel would be noise, and those scenes show the
   memory where the overlay parks bank A's contents). */
static int info_screen_is_menu(void)
{
#ifdef OV_ANYWHERE                          /* guard test builds only (ticket 25) */
    return 1;
#endif
    u32 disp = REG32(DISPCNT_B);
    if (disp & 7)
        return 0;
    for (int b = 0; b < 4; b++)
        if ((disp & (0x100u << b)) && (REG16(BG0CNT_B + 2 * b) & 0x80))
            return 0;
    return 1;
}

/* ---- auctions (ticket 28, ADR 0015) ------------------------------------------
 * The auction house (overlay 4) puts the 3D engine, which draws the bidding
 * field, on the info screen while bids are placed, and takes it back with one
 * bit of POWCNT1, from four places.  Each reads the register's address from a
 * literal word in the overlay.  Pointed at AUC_POW instead, the field stays on
 * the gameplay screen and bit 15 of AUC_POW says that bidding is on.  AUC_POW
 * is the two spare bytes after the overlay's last string: there a savestate
 * keeps it whatever build of the mod runs next.
 * The third place is the Retire question, which only takes the bit for as long
 * as it is up: it gets a word of its own, so the layout stays.
 * The words also tell overlay 4 from whatever else is loaded there. */
#define AUC_POW 0x0213E0B6
static u32 auction_ask;

static SMALL int auction_check(void)
{
    static const u32 lit[4] = { 0x02139158, 0x0213978C, 0x0213DC54, 0x0213CB60 };
    u32 is = *(volatile u32 *)lit[0];
    if (is != POWCNT1 && is != AUC_POW)
        return 0;
    for (int i = 1; i < 3; i++)
        if (*(volatile u32 *)lit[i] != is)
            return 0;
    if (is == POWCNT1) {                            /* freshly loaded */
        REG16(AUC_POW) = REG16(POWCNT1);
        REG16(POWCNT1) &= 0x7FFF;                   /* a state saved by a build without this */
        for (int i = 0; i < 3; i++)
            *(volatile u32 *)lit[i] = AUC_POW;
    }
    *(volatile u32 *)lit[3] = (u32)&auction_ask;
    return AUC_ROOM && wide_x != 4096 && (REG16(AUC_POW) & 0x8000);
}

SMALL void frame_hook(u16 *keys)
{
#ifdef MAP_ART
    map_art_frame();
#endif
    u16 held = keys[0], pressed = keys[1];
    auction = (u8)auction_check();
    auction_project(auction);

    frame_no++;
    rects_new_frame();

    int menu = !battle_hud_present() && (REG32(DISPCNT_A) & 8);
    in_battle = !menu || BATTLE_OBJ;
    int ov_ok = menu && info_screen_is_menu();
    /* SELECT: tap = info screen, hold = banner on/off.  Any other button with it
       (the game's L+R+START+SELECT soft reset, or a slip) cancels both. */
    if (held & KEY_SELECT) {
        if (!sel_frames)                    /* SELECT just went down */
            sel_spoilt = 0;
        if ((held & ~(KEY_SELECT | KEY_DPAD) & 0x0FFF) || (pressed & KEY_DPAD))
            sel_spoilt = 1;
        if (sel_frames < HOLD_FRAMES)
            sel_frames++;
        if (sel_frames == HOLD_FRAMES && !sel_spoilt) {
            banner_enabled ^= 1;
            sel_spoilt = 1;                 /* the hold is used up; letting go does nothing */
        }
    } else if (sel_frames) {
        if (!sel_spoilt) {
            if (menu) {
                if (ov_ok)
                    ov_manual ^= 1;         /* outside battle, in menus: info screen overlay */
            } else
                REG16(POWCNT1) ^= 0x8000;   /* in battle: swap the two screens */
        }
        sel_frames = 0;
    }
    /* the manual overlay is a peek: browsing with the D-pad keeps it, any
       confirm/cancel/menu button puts it away (it also costs loading speed) */
    if (!ov_ok || (pressed & (0x0001 | 0x0002 | 0x0008 | 0x0400 | 0x0800)))
        ov_manual = 0;
    /* the stats beside Item Info are for the shop and equipment menus; in battle the
       same signal is up for View Abilities, where they would cover the unit's portrait */
    /* the panels beside the Jobs list and beside Item Info need the side areas' room:
       widescreen only (on the plain 4:3 view they would cover the game's own panels) */
    jobs_panel = menu && wide_x != 4096 && JOBS_LIST;
    if (!bazaar_rows)
        bz_desc = 0;
    bazaar_rows = 0;
#if VIEW_H >= 228
    /* only while the game's list is up: after a trade the info screen keeps its rows
       a while as the panels go and the shop room fills the screen */
    bazaar_open = menu && wide_x != 4096 && BAZAAR;
    if (bazaar_open && bz_list + 3 > frame_no) {
        const u16 *m1 = (const u16 *)(SUB_BGVRAM + ((REG16(BG1CNT_B) >> 8) & 31) * 0x800);
        const u16 *m3 = (const u16 *)(SUB_BGVRAM + ((REG16(BG1CNT_B + 4) >> 8) & 31) * 0x800);
        while (bazaar_rows < 3 && (m1[(3 + 4 * bazaar_rows) * 32 + 6] & 0x3FF))   /* "Metal:" etc. */
            bazaar_rows++;
        bazaar_head = (m3[20 * 32 + 5] & 0x3FF) != 0;      /* the recipe's name */
    }
#endif
    if (ov_on && !ov_parked && !tex_free(ov_tex, ov_tex + OV_WORDS * 4))
        ov_set(0);                          /* the game has claimed the heap window: let go at once */
    ov_set(auction || (ov_ok && (ov_manual || jobs_panel || (bazaar_rows && BZ_DEBUG < 2) || (ITEM_PANEL && !in_battle && wide_x != 4096))));
    if (auction)
        ov_manual = 0;
    hud_hidden = ov_manual && ov_ready;
    if (ov_on)
        ov_step();
#ifdef GUARD
    if (ov_on) {
        if (ov_parked)
            guard_backup_check(frame_no % 24);
        guard_bg_check();
    }
#endif
}

/* ---- widescreen -------------------------------------------------------
 * Every orthographic projection the game builds goes through G3_OrthoW
 * (0x0200523C).  Scaling the matrix there squeezes (and optionally zooms)
 * the whole 3D picture; the emulator then stretches the screen back out to
 * the display's aspect ratio, which shows more of the scene at the sides.
 * Values are 20.12 fixed point multipliers.
 * VIEW_W, VIEW_H, NUDGE_X, NUDGE_Y: see the display preset near the top. */
int view_cfg[7] = {
    0x57454956,     /* "VIEW" */
    VIEW_W, VIEW_H,
    (256 * 4096 + VIEW_W / 2) / VIEW_W, (192 * 4096 + VIEW_H / 2) / VIEW_H,
    NUDGE_X, NUDGE_Y,
};

/* The same for Scion animations, after a "TALL" marker. */
int tall_cfg[5] = {
    0x4C4C4154,     /* "TALL" */
    TALL_W, TALL_H,
    (256 * 4096 + TALL_W / 2) / TALL_W, (192 * 4096 + TALL_H / 2) / TALL_H,
};
#define tall_w (tall_cfg[1])
#define tall_h (tall_cfg[2])
#define tall_x (tall_cfg[3])
#define tall_y (tall_cfg[4])

/* Set while the whole-screen overlay is showing: the game's own panels, text
   and portraits (everything it draws with its top-left-origin HUD projection)
   are pushed off screen, so there is never more than one layer of panels. */
int hud_hidden;

/* Test captures (scripts/solo.py).  An emulator that renders at DS resolution
   cannot show the squeezed widescreen picture cleanly, so the test rig draws
   the wide view unsqueezed in four overlapping 256x192 pieces, one per run, and
   stitches them.  tile_cfg: marker, on/off, x and y shift of this piece in
   projection units.  Everything else (side areas, panels at the edges) behaves
   exactly as in widescreen. */
int tile_cfg[4] = { 0x454C4954, 0, 0, 0 };

/* ---- Scion animations: both screens as one tall picture (ticket 26, ADR 0014) ----
 * A Scion (effect ids 0x152-0x15E) is the only thing in the game drawn on both screens at
 * once.  The game draws the scene twice, in turns: even frames with the top screen's camera,
 * odd frames with the bottom screen's, each captured so the other screen can show it.  The
 * two cameras are one continuous picture (the top one is exactly one screen higher).
 * Here every frame is drawn once, with the even camera (which also has its own stored
 * projection for sprites, used by nothing else) widened to take in both screens and the
 * side areas, and shown on the gameplay screen.
 * dual_state (0x02131BB8): +0x18 the mode is on, +4 the two-screen picture has begun (the
 * lead-in, where the battle zooms out and fades, comes first), +0x14 frame parity. */
#define DUAL_STATE ((volatile int *)0x02131BB8)
#define DUAL_ON    (DUAL_STATE[6])
#define DUAL_VIEW  (DUAL_STATE[6] && DUAL_STATE[1])
#define DUAL_SPRITE_PROJ ((volatile int *)0x027E10B4)   /* even frames' stored projection */

static void dual_projection(int *m)
{
    /* m is off by one whole screen (-2 in clip units); the tall view's middle is the
       join between the screens, one unit up */
    if (tile_cfg[1]) {
        m[12] += tile_cfg[2];
        m[13] += 4096 + tile_cfg[3];
        return;
    }
    m[0] = (int)(((long long)m[0] * tall_x) >> 12);
    m[5] = (int)(((long long)m[5] * tall_y) >> 12);
    m[12] = (int)(((long long)m[12] * tall_x) >> 12) + nudge_x;
    m[13] = (int)(((long long)(m[13] + 4096) * tall_y) >> 12) + nudge_y;
}

/* Before the two-screen picture begins the game fades to black and photographs the
   battlefield (a display capture), to show it small at the Scion's feet.  While the screen
   is black the squeeze is off, so the photograph is the game's own, at its own size. */
#define DUAL_PHOTO (DUAL_ON && !DUAL_STATE[1] && (REG16(0x04000054) & 31) == 16)
#define SPRITE_PROJ ((volatile int *)0x027E1274)        /* the stored projection sprites use */
static int photo_saved[4];
static u8 photo_on;

static void dual_photo(int on)
{
    static const u8 word[4] = { 0, 5, 12, 13 };
    if (on == photo_on)
        return;
    photo_on = (u8)on;
    for (int i = 0; i < 4; i++) {
        if (on)
            photo_saved[i] = SPRITE_PROJ[word[i]];
        SPRITE_PROJ[word[i]] = !on ? photo_saved[i] : i == 0 ? 2 * 4096 : i == 1 ? 10922 : 0;
    }
}

/* The game shows every frame of the scene through a capture: new capture = 12/16 of what
   the 3D engine draws + 8/16 of the old capture (the weights are at dual_blend +0x48/+0x49).
   That gives the trails and the glow.  A capture is 256x192 however sharply the emulator
   draws 3D, so here the live 3D is shown itself, and the last capture is laid over it as a
   2D picture with the same weights: the same sum, with the new part sharp.  The captures
   are of that finished picture, taken in turns into banks C and D, 30 a second as in the
   game, so the trails are as long. */
#define DUAL_BLEND ((volatile u8 *)0x02131BEC)
#define BG2CNT_A   0x0400000C
#define TRAIL_BG   0x4884           /* BG2: 256x256 direct-colour bitmap at 0x06020000, on top */
static u8 trail_on, trail_flip, trail_tick, trail_seen, trail_held;
static u16 trail_saved, trail_bld;
static u8 dual_was;

static SMALL void trail_frame(int playing)
{
    if (!playing) {
        if (trail_on) {
            REG16(BG2CNT_A) = trail_saved;
            REG16(0x04000050) = trail_bld;      /* the closing fade to white uses it */
            trail_on = 0;
        }
        return;
    }
    if (!trail_on) {
        trail_saved = REG16(BG2CNT_A);
        trail_bld = REG16(0x04000050);
        trail_on = 1;
        trail_tick = trail_seen = trail_held = 0;
    }
    u32 d = REG32(DISPCNT_A) & ~0x31F00u;
    REG32(0x04000064) = 0;              /* not the game's own capture */
    /* the effect is over a frame or two before the white-out: its last capture stands in */
    int weight = DUAL_BLEND[0x49], hold = !weight && trail_seen > 1 && trail_held < 6;
    trail_held = hold ? trail_held + 1 : 0;
    if (hold)
        weight = 16;
    else if (!weight)
        trail_seen = 0;
    if (!hold && !(trail_tick++ & 1)) {
        trail_flip ^= 1;                /* show the bank captured last, capture into the other */
        *(volatile u8 *)0x04000242 = trail_flip ? 0x89 : 0x80;      /* C */
        *(volatile u8 *)0x04000243 = trail_flip ? 0x80 : 0x89;      /* D */
        REG32(0x04000064) = 0x80300000u | (trail_flip ? 3u << 16 : 2u << 16);
        if (trail_seen < 2)
            trail_seen++;
    } else {
        *(volatile u8 *)0x04000242 = trail_flip ? 0x89 : 0x80;
        *(volatile u8 *)0x04000243 = trail_flip ? 0x80 : 0x89;
    }
    REG16(BG2CNT_A) = TRAIL_BG;
    REG16(0x04000020) = 0x100;
    REG16(0x04000022) = 0;
    REG16(0x04000024) = 0;
    REG16(0x04000026) = 0x100;
    REG32(0x04000028) = 0;
    REG32(0x0400002C) = 0;
    REG16(0x04000050) = 0x2000 | 0x0100 | 0x0040 | 0x0004;  /* BG2 over the 3D, weighted sum */
    REG16(0x04000052) = (u16)(weight | (hold ? 0 : DUAL_BLEND[0x48] << 8));
    REG32(DISPCNT_A) = d | 0x10100 | (trail_seen > 1 && weight ? 0x400 : 0);
}

/* Six of the Scions also have a glow: a round 128x128 picture on the 2D layer BG3, scaled and
   added to the 3D.  A 2D layer is not part of the tall view (and the trails need the one
   weighted sum the 2D hardware can do), so it is drawn in 3D as translucent rings instead,
   in the picture's own colours along its radius.  glow_affine stands in for the call that
   sets the layer up (0x020E847C; effect object in r9: +0x20C its weight, 0..16), and
   glow_blend for the one that sets its blending (0x020E81FC), which would undo the trails'. */
static int glow_x, glow_y, glow_sx, glow_sy, glow_w;
static u32 glow_frame;
void *glow_obj;

__attribute__((used)) void glow_affine(int pa, int pb, int pc, int pd, int cx, int cy, int x1, int y1)
{
    if (!DUAL_VIEW) {
        ((void (*)(int, int, int, int, int, int, int, int))0x02083834)(pa, pb, pc, pd, cx, cy, x1, y1);
        return;
    }
    /* (it is never turned: pb and pc are 0 in all six, and the picture is round) */
    glow_x = cx - x1 - 128;             /* its middle, from the middle of the tall picture */
    glow_y = cy - y1 - 192;
    glow_sx = sdiv(16 << 12, pa | !pa);         /* 1/16 game pixels per texel */
    glow_sy = sdiv(16 << 12, pd | !pd);
    glow_w = *(int *)((char *)glow_obj + 0x20C);
    glow_frame = frame_no;
}

__attribute__((naked, used)) void glow_stub(void)
{
    __asm__("ldr r12, =glow_obj\n"
            "str r9, [r12]\n"
            "b glow_affine\n"
            ".ltorg\n");
}

/* A starting glow also switches the 2D layers (str r1, [r2], DISPCNT, at 0x020E7FD8), in
   the middle of a frame: not during the two-screen picture. */
__attribute__((naked, used)) void glow_layers_stub(void)
{
    __asm__("ldr r12, =0x02131BB8\n"
            "ldr r3, [r12, #0x18]\n"
            "ldr r12, [r12, #4]\n"
            "cmp r3, #0\n"
            "cmpne r12, #0\n"
            "streq r1, [r2]\n"
            "bx lr\n"
            ".ltorg\n");
}

__attribute__((naked, used)) void glow_blend_stub(void)
{
    __asm__("push {r0, r1}\n"
            "ldr r12, =0x02131BB8\n"
            "ldr r0, [r12, #0x18]\n"
            "ldr r1, [r12, #4]\n"
            "cmp r0, #0\n"
            "cmpne r1, #0\n"
            "pop {r0, r1}\n"
            "bxne lr\n"
            "ldr r12, =0x02004B68\n"
            "bx r12\n"
            ".ltorg\n");
}

/* Rings are kept few and cheap: the scenes run close to a full frame's work as it is. */
#define GLOW_SEG 24
#define GLOW_STEP 2                     /* texels from one ring to the next */
#define G_VTX_XY 0x25

static SMALL __attribute__((noinline)) void glow_draw(void)
{
#ifndef GLOW_OFF
#define GLOW_OFF 0
#endif
    if (GLOW_OFF || !DUAL_VIEW || frame_no - glow_frame > 1 || glow_w <= 0)
        return;
    if (tile_cfg[1])
        proj_begin(4096, 4096, tile_cfg[2], tile_cfg[3], -4080);
    else
        proj_begin(tall_x, tall_y, nudge_x, nudge_y, -4080);
    static const u8 sine[GLOW_SEG / 4 + 1] = { 0, 66, 128, 181, 222, 247, 255 };    /* x 255 */
    int ux[GLOW_SEG + 1], uy[GLOW_SEG + 1];     /* one texel's step, 1/4096 game pixels */
    for (int q = 0; q <= GLOW_SEG / 4; q++) {
        int x = sine[GLOW_SEG / 4 - q] * glow_sx, y = sine[q] * glow_sy;
        ux[q] = x;                  uy[q] = y;
        ux[GLOW_SEG / 2 - q] = -x;  uy[GLOW_SEG / 2 - q] = y;
        ux[GLOW_SEG / 2 + q] = -x;  uy[GLOW_SEG / 2 + q] = -y;
        ux[GLOW_SEG - q] = x;       uy[GLOW_SEG - q] = -y;
    }
    GX(G_TEXIMAGE) = 0;
    const u8 *row = (const u8 *)(0x06000000 + (REG16(0x0400000E) >> 8 & 31) * 0x4000 + 64 * 128 + 64);
    int small = glow_sx < glow_sy ? glow_sx : glow_sy;
    for (int r = 0; r < 62 && r * small < 900 * 16; r += GLOW_STEP) {
        u32 p = MAIN_BGPAL[row[r + 1]];
        int cr = p & 31, cg = p >> 5 & 31, cb = p >> 10 & 31, top = cr > cg ? cr : cg;
        if (cb > top) top = cb;
        int a = row[r + 1] ? (top * glow_w + 8) >> 4 : 0;
        if (!a)
            continue;
        if (a > 30) a = 30;
        /* its hue at full strength; the strength is the alpha */
        int k = sdiv(31 << 8, top);
        /* polygon ID 0x20: the game's own go round 0x21..0x3F, and equal ones don't blend */
        GX(G_POLY_ATTR) = 0x200000C0 | (u32)a << 16;
        GX(G_COLOR) = (u32)(cr * k >> 8) | (u32)(cg * k >> 8) << 5 | (u32)(cb * k >> 8) << 10;
        GX(G_BEGIN) = 3;
        for (int i = 0; i <= GLOW_SEG; i++) {
            for (int e = 0; e < 2; e++) {
                int rr = e ? r + GLOW_STEP : r;
                int x = glow_x * 16 + (ux[i] * rr >> 8), y = glow_y * 16 + (uy[i] * rr >> 8);
                if (x > 32767) x = 32767;
                if (x < -32767) x = -32767;
                if (y > 32767) y = 32767;
                if (y < -32767) y = -32767;
                if (!i && !e) {         /* the first one sets the depth, which VTX_XY keeps */
                    GX(G_VTX16) = ((u32)x & 0xFFFF) | (u32)y << 16;
                    GX(G_VTX16) = 0;
                } else
                    GX(G_VTX_XY) = ((u32)x & 0xFFFF) | (u32)y << 16;
            }
        }
        GX(G_END) = 0;
    }
    hud_end();
}

/* Wraps the game's per-frame routine for the mode (call at 0x0201D6F8). */
SMALL void dual_frame(void)
{
    dual_photo(DUAL_PHOTO ? 1 : 0);
    if (DUAL_VIEW)
        DUAL_STATE[5] = 1;          /* take its odd path: 3D on the bottom screen */
    ((void (*)(void))0x020F94F8)();
    if (!DUAL_VIEW) {
        trail_frame(0);
        if (dual_was)
            REG32(DISPCNT_A) |= 0x1F00;         /* hand the 2D layers back */
        dual_was = 0;
        return;
    }
    dual_was = 1;
    if (DUAL_STATE[5] != 1)         /* a new frame is up (else the game left early) */
        trail_frame((REG32(DISPCNT_A) >> 16 & 3) == 2 && !(REG16(0x04000054) & 31));
    if (!trail_on)
        REG32(DISPCNT_A) = (REG32(DISPCNT_A) & ~0x31F00u) | 0x10100;   /* the 3D alone (the glow is in it) */
    DUAL_STATE[5] = 0;              /* but the even camera for everything drawn */
    REG32(DISPCNT_B) &= ~0x1F00u;   /* the other screen would show a stale capture */
    {
        int m[16];
        m[0] = 2 * 4096; m[5] = 10922; m[12] = 0; m[13] = -2 * 4096;
        dual_projection(m);
        DUAL_SPRITE_PROJ[0] = m[0];
        DUAL_SPRITE_PROJ[5] = m[5];
        DUAL_SPRITE_PROJ[12] = m[12];
        DUAL_SPRITE_PROJ[13] = m[13];
    }
}

/* the field goes to the top left of the wide picture */
#define AUC_DX (-(VIEW_W - 256) / 2)
#define AUC_DY ((VIEW_H - 192) / 2)
static int auc_sx, auc_sy;
static void auction_project(int on)
{
    /* the corner of the 4:3 picture goes exactly to the corner of the wide one: an odd
       unit would eat into the nudge and show as hairlines between pieces */
    auc_sx = !on ? 0 : tile_cfg[1] ? AUC_DX * 32 : wide_x - 4096;
    auc_sy = !on ? 0 : tile_cfg[1] ? sdiv(AUC_DY * 128, 3) : 4096 - wide_y;
}

void ortho_fix(int *m)
{
    if (hud_hidden && m[12] < 0 && m[13] > 0) {
        m[12] += 16 * 4096;
        return;
    }
    if (DUAL_ON && m[13] >= -2 * 4096 - 2 && m[13] <= -2 * 4096 + 2) {
        dual_projection(m);     /* the top screen's camera in a two-screen animation */
        return;
    }
    if (DUAL_PHOTO)
        return;
    if (tile_cfg[1]) {
        m[12] += tile_cfg[2] + auc_sx;
        m[13] += tile_cfg[3] + auc_sy;
        return;
    }
    m[0] = (int)(((long long)m[0] * wide_x) >> 12);
    m[5] = (int)(((long long)m[5] * wide_y) >> 12);
    /* keep off-centre projections (the HUD's origin is the top-left corner)
       squeezed about the screen centre, not about their own origin */
    m[12] = (int)(((long long)m[12] * wide_x) >> 12);
    m[13] = (int)(((long long)m[13] * wide_y) >> 12);
    /* sub-pixel nudge so game-pixel edges do not sit on the emulator's
       rounding boundary (see ticket 08) */
    m[12] += nudge_x + auc_sx;
    m[13] += nudge_y + auc_sy;
}

/* ---- side areas -------------------------------------------------------
 * In widescreen the view is wider than the 256px the game culls and fills
 * to.  side_margin is how many extra pixels are kept on each side. */
int side_margin = SIDE_MARGIN;

/* Replaces the game's map-cell visibility test (0x0208B0BC).
   view: x, y, originX, originY ; cell: left, top, right, bottom. */
int map_cell_visible(const short *view, const short *cell)
{
    int left = view[0] - view[2] - side_margin;
    int top = view[1] - view[3] - V_MARGIN;
    return cell[2] > left && cell[3] > top &&
           cell[0] < left + 256 + 2 * side_margin && cell[1] < top + 192 + 2 * V_MARGIN;
}

/* Wraps the camera query used by the backdrop bands (call at 0x020D54AC) so
   the bands start side_margin further left and V_MARGIN higher; patch.py
   sets their width constant to 256 + 2*SIDE_MARGIN and their height constant
   to 192 + 2*V_MARGIN.  While the camera is zoomed out (a Scion's lead-in) the
   bands are drawn larger by the same factor; w and h are their size as drawn
   (the caller's r7 and [sp, #12]), so the margins grow with them. */
#define BACK_W (256 + 2 * SIDE_MARGIN)
#define BACK_H (192 + 2 * V_MARGIN)
__attribute__((used)) void backdrop_margins(short *x, short *y, int w, int h)
{
    ((void (*)(short *, short *))0x0208FAC0)(x, y);
    *x -= ((SIDE_MARGIN * 4096 + BACK_W - 1) / BACK_W * w) >> 12;
    *y -= ((V_MARGIN * 4096 + BACK_H - 1) / BACK_H * h) >> 12;
}

__attribute__((naked, used)) void backdrop_camera(void)
{
    __asm__("mov r2, r7\n"
            "ldr r3, [sp, #12]\n"
            "b backdrop_margins\n");
}

/* ---- patterned floor in the menus (party list, equipment, Fitting Room) ----
 * FUN_020d4be0 draws the scene's picture layers: clouds and the like in
 * battle, and in these menus a diamond floor made of four 128px quads that
 * fill the 4:3 view exactly.  When a layer is such a fixed sheet, exactly one
 * old screen wide, it is drawn twice more, one screen to either side; the
 * pattern repeats every 128px, so the copies join up.  Called in place of the
 * routine (0x020D60C0). */
extern int edge_px, edge_py;

void layer_draw(char *obj)
{
    void (*draw)(char *) = (void (*)(char *))0x020D4BE0;
    draw(obj);
    int n = *(u8 *)(obj + 0x3A);
    const short *q = *(const short **)(obj + 0x74);     /* 0x2C bytes per quad */
    if (wide_x == 4096 || !n || !*(u32 *)(obj + 0x80) || !*(u32 *)(obj + 0x70))
        return;
    int lo = 32767, hi = -32768;
    for (int i = 0; i < n; i++, q += 0x16) {
        if (q[0x14] | q[0x15] || q[0x12] != 4096)       /* animated or scaled: scenery, not a sheet */
            return;
        for (int k = 0; k < 4; k++) {
            int x = q[2] + q[4 + 2 * k];
            if (x < lo) lo = x;
            if (x > hi) hi = x;
        }
    }
    if (hi - lo != 256)
        return;
    /* the routine sets its own position matrix; the layer's scroll offset at
       +0xC is what places it */
    short *off = (short *)(obj + 0xC), keep = *off;
    *off = (short)(keep - 256);
    draw(obj);
    *off = (short)(keep + 256);
    draw(obj);
    *off = keep;
}

/* ---- full-screen map pictures narrower than the wide view ------------------
 * A "map" can also be one fixed picture built for the old screen
 * (the clan menu's parchment: 272x192, six cells).  Where it ends inside the
 * wide picture, its outermost row or column of pixels is drawn on out to the
 * screen edge, so the dark table the parchment lies on carries on instead of
 * stopping at a black area.  Runs at the end of the map routine (0x0208CE08),
 * with texture, palette and colour still set for the map's cells.
 * map: view x, y, originX, originY shorts; cell list at +0xD0, 0x3C bytes per
 * cell from +0xC: four corners (x, y, -, s, t, -), z at +0x3A. */
SMALL void map_extend(const short *map)
{
    if (wide_x == 4096 || *(u8 *)((char *)map + 0x18) != 1 ||
        *(int *)((char *)map + 0x10) != 4096 || map[10])
        return;
    int n = *(u16 *)((char *)map + 0x1A);
    const short *cells = (const short *)(*(char **)((char *)map + 0xD0) + 0xC);
    /* b: the picture's box; v: what the wide view needs (left, top, right, bottom) */
    int b[4] = { 32767, 32767, -32768, -32768 }, v[4], plain[2][2] = { { 0, 0 }, { 0, 0 } };
    const short *c = cells;
    v[0] = map[0] - map[2];
    v[1] = map[1] - map[3];
    for (int i = 0; i < n; i++, c += 0x1E) {
        /* a picture made for the old screen is exactly its height: a battle map's cells
           leave at the first one outside (the whole loop takes 15 lines a frame there) */
        if (c[1] < v[1] || c[13] > v[1] + 192)
            return;
        for (int k = 0; k < 2; k++) {
            if (c[k] < b[k]) b[k] = c[k];
            if (c[12 + k] > b[2 + k]) b[2 + k] = c[12 + k];
        }
    }
    /* the picture's top-left and bottom-left texels (the cells share one texture
       atlas, so both coordinates come from the corner cell itself) */
    c = cells;
    for (int i = 0; i < n; i++, c += 0x1E)
        if (c[0] == b[0]) {
            int s = c[3] * 16 + (c[15] > c[3] ? 8 : -8), in = c[16] > c[4] ? 8 : -8;
            if (c[1] == b[1]) { plain[0][0] = s; plain[0][1] = c[4] * 16 + in; }
            if (c[13] == b[3]) { plain[1][0] = s; plain[1][1] = c[16] * 16 - in; }
        }
    /* a picture made for the old screen: exactly its height, covering it, and too
       narrow for the wide view.  Battle maps are far bigger and have a backdrop. */
    if (b[3] - b[1] != 192 || b[1] != v[1] || b[0] > v[0] || b[2] < v[0] + 256 || b[2] - b[0] >= 256 + 2 * edge_px)
        return;
    v[2] = v[0] + 256 + edge_px + 8;
    v[3] = v[1] + 192 + edge_py + 8;
    v[0] -= edge_px + 8;
    v[1] -= edge_py + 8;
    GX(G_BEGIN) = 1;
    c = cells;
    for (int i = 0; i < n; i++, c += 0x1E) {
        /* corners: 0 top-left, 1 bottom-left, 2 bottom-right, 3 top-right, six
           shorts each (x, y, -, s, t, -).  The cell is the middle of a 3x3 grid;
           an outer part is drawn when the cell lies on that edge of the picture
           and the picture stops short of the view there.  Its texture coordinate
           across the gap is fixed half a texel inside the cell (1/16 texels). */
        for (int g = 0; g < 16; g++) {
            int p[2][2], t[2][2], ok = g != 5 && (g & 3) < 3 && g < 12;   /* [axis][near, far] */
            for (int a = 0; a < 2; a++) {
                int part = a ? g >> 2 : g & 3;
                int lo = c[a], hi = c[12 + a], t0 = c[3 + a] * 16, t1 = c[15 + a] * 16;
                int in = t1 > t0 ? 8 : -8;
                p[a][0] = lo; p[a][1] = hi; t[a][0] = t0; t[a][1] = t1;
                if (part == 0) {
                    ok &= lo == b[a] && lo > v[a];
                    p[a][0] = v[a]; p[a][1] = lo; t[a][0] = t[a][1] = t0 + in;
                } else if (part == 2) {
                    ok &= hi == b[2 + a] && hi < v[2 + a];
                    p[a][0] = hi; p[a][1] = v[2 + a]; t[a][0] = t[a][1] = t1 - in;
                }
            }
            /* above and below, the picture's top and bottom rows are patterned and
               would streak: fill with its corner texel (the background beside the
               sheet) instead, so the picture reads as a sheet lying on it (the clan parchment) */
            if ((g >> 2) != 1) {
                const int *pl = plain[(g >> 2) == 2];
                t[0][0] = t[0][1] = pl[0];
                t[1][0] = t[1][1] = pl[1];
            }
            for (int k = 0; ok && k < 4; k++) {
                int kx = k >> 1, ky = (k == 1) | (k == 2);
                GX(G_TEXCOORD) = (u32)(t[0][kx] & 0xFFFF) | ((u32)t[1][ky] << 16);
                GX(G_VTX16) = (u32)(p[0][kx] & 0xFFFF) | ((u32)p[1][ky] << 16);
                GX(G_VTX16) = (u16)c[0x1D];
            }
        }
    }
    GX(G_END) = 0;
}

__attribute__((naked, used)) void map_stub(void)   /* at 0x0208CE08 */
{
    __asm__("push {r0, r2, r3, r12, lr}\n"
            "mov r0, r10\n"
            "bl map_extend\n"
            "pop {r0, r2, r3, r12, lr}\n"
            "mov r1, #1\n"           /* replaced instruction */
            "bx lr\n");
}

/* ---- game panels at the screen edges -----------------------------------
 * Widescreen squeezes the HUD toward the centre along with everything else.
 * Panels that belong at a screen edge are slid back out, each as one unit:
 *   - layout objects (status panel + portrait, height tab, Config/Help bars)
 *   - windows (the COMMANDS box) and the text lines that sit inside them
 * Anything that straddles the centre is left alone so it cannot tear. */
static u32 frame_no;

int edge_px = (VIEW_W - 256) / 2;
int edge_py = (VIEW_H - 192) / 2;

static int edge_shift(void)
{
    /* distance, in HUD pixels, from the squeezed edge back to the real edge */
    return wide_x == 4096 || auction ? 0 : edge_px;
}

#define RECT_SLOTS 12
struct rect { short x0, y0, x1, y1, shift, dy; };

/* ---- sprites that sit on a moved corner ornament ---------------------------
 * Animated sprites (units, map markers, the world map's weather icon) are
 * queued by FUN_02034164: each gets a 0xA0-byte entry whose 4x4 matrix at
 * +0x14 is the finished clip matrix, read back from the 3D hardware, so the
 * position is already in screen terms.  Called right after an entry is queued
 * (0x02034C5C).  A sprite whose anchor lies on a small panel at the top of the
 * screen that the mod moved last frame is moved the same way: the weather icon
 * belongs inside the world map's corner globe.  Only on the world map and its
 * top menus: in a battle a unit can stand under the height tab. */
static struct rect prev_rects[], moved_rects[];
static int moved_count;
static int prev_count;
extern int tile_cfg[4];
static int *sprite_last;

/* there is no division routine in here to link against */
static int sdiv(int a, int b)
{
    int neg = (a < 0) != (b < 0);
    u32 n = (u32)(a < 0 ? -a : a), d = (u32)(b < 0 ? -b : b), q = 0;
    for (int i = 31; i >= 0; i--)
        if ((n >> i) >= d) {
            n -= d << i;
            q |= 1u << i;
        }
    return neg ? -(int)q : (int)q;
}

void sprite_fix(void)
{
    int **queue = *(int ***)(*(u32 *)0x01FFCF3C);   /* the routine's own pointer to the queue */
    int *e = (int *)((char *)queue[2] - 0xA0);      /* the entry just added */
    if (e == sprite_last || wide_x == 4096 || BATTLE_OBJ)
        return;
    sprite_last = e;
    int *m = e + 5;
    if (m[15] != 4096)
        return;
    int wx = tile_cfg[1] ? 4096 : wide_x, wy = tile_cfg[1] ? 4096 : wide_y;
    int ox = tile_cfg[1] ? tile_cfg[2] : nudge_x, oy = tile_cfg[1] ? tile_cfg[3] : nudge_y;
    int x = 128 + sdiv((m[12] - ox) * 128, wx);     /* where it is on the 4:3 screen */
    int y = 96 - sdiv((m[13] - oy) * 96, wy);
    /* this frame's panels first, then last frame's (one drawing pass can span both);
       near the top only, but anywhere in the bazaar (the cursor of its Yes/Cancel box) */
    for (int i = 0; i < moved_count + prev_count; i++) {
        const struct rect *r = i < moved_count ? &moved_rects[i] : &prev_rects[i - moved_count];
        if ((r->shift || r->dy) && (r->y1 <= 48 || bazaar_rows) && x >= r->x0 && x < r->x1 && y >= r->y0 && y < r->y1) {
            m[12] += (r->shift * wx) >> 7;
            m[13] -= sdiv(r->dy * wy, 96);
            return;
        }
    }
}

__attribute__((naked, used)) void sprite_stub(void)   /* at 0x02034C5C */
{
    __asm__("push {r1, r2, r3, r12, lr}\n"
            "bl sprite_fix\n"
            "pop {r1, r2, r3, r12, lr}\n"
            "ldr r0, [sp, #0x28]\n"   /* replaced instruction */
            "bx lr\n");
}

/* ---- full-screen sprite pictures (story scenes, ticket 29) ------------------
 * Some story scenes draw their background as a sprite: one quad in the sprite
 * queue, exactly as wide as the 4:3 picture (the book pulling the hero in: a
 * 256x256 texture that wraps and scrolls, plus a tall strip of light shafts).
 * The queue is drawn by one call (0x0208F97C, into ITCM 0x01FFB390); just
 * before it, each such quad is widened to the real screen edges and its
 * texture coordinates are carried on by the same amount.  A wrapping texture
 * then simply continues: the game's own art, made to tile.  A texture that
 * does not wrap and is shown exactly once is mirrored at its edges instead
 * (wrap + flip, as the title's still picture, ADR 0010).  An untextured quad
 * (a fade to a colour) is simply widened.
 *
 * Entry layout (0xA0 bytes, 40 words, a ready GX command list): [0] packed
 * commands 29 2A 2B, [1] polygon attr, [2] TEXIMAGE_PARAM, [3] palette,
 * [4] packed 11 18 40, [5..20] the clip matrix, [21] BEGIN quads,
 * [22] 20 22 23 22, [23] colour, [24] texcoord, [25..26] vertex, [27] texcoord,
 * [28] 23 22 23 22, [29..30] vertex, [31] texcoord, [32..33] vertex,
 * [34] texcoord, [35] 23, [36..37] vertex, [38..39] END + pop. */
#ifndef BAR_MIN
#define BAR_MIN 160     /* px a strip must be stretched to, to count as an announcement bar */
#endif
/* Scion animations (ticket 26): the same for the tall view.  Every full-screen layer in all
   13 (mist, flames, lightning, rain, flashes) is a quad with a texture made to tile, or none
   at all, that covers the old two-screen picture; its quad is enlarged about its middle and
   its texture carried on.  A rotated one is enlarged both ways alike.  The battlefield's
   photograph (a direct-colour texture) and single sprites (not tiling, or mirrored) stay. */
static int tall_grow(int lo, int hi, int old, int full, int mid)
{
    /* how much to enlarge (20.12) so lo..hi, about its own middle, covers mid +- full */
    if (lo > mid - old + (old >> 6) || hi < mid + old - (old >> 6))
        return 0;                       /* does not cover the old picture that way */
    int half = (hi - lo) >> 1, c = (lo + hi) >> 1;
    int need = full + (c > mid ? c - mid : mid - c);
    return need <= half ? 4096 : sdiv(need << 11, half) << 1;
}

static int scale12(int v, int c, int k)
{
    return c + (int)(((long long)(v - c) * k) >> 12);
}

/* A plain quad entry (40 words).  Some effects (the portal of event 137) put longer entries
   into the queue, with the same first word: after one, the walks below look for the next
   first word one by one (ticket 30). */
#define QUEUE_OP 0x002B2A29
#define PLAIN_QUAD(e) ((e)[4] == 0x00401811 && (e)[21] == 1 && (e)[22] == 0x22232220 && \
                       (e)[28] == 0x22232223 && (e)[35] == 0x23)

/* tall: the Scions' view.  Otherwise the normal wide view (ticket 30): the mist over the
   battlefields of quests 18, 23 and 24 is drawn as tiling quads somewhat larger than the
   old picture, straight (texture turned) or rotated; those exactly as wide as the old
   picture are left to queue_widen. */
static __attribute__((noinline)) void quad_grow(int *e, int tall)
{
    int tile = tile_cfg[1];
    int oldx = tile ? 4096 : tall ? tall_x : wide_x, oldy = tile ? 4096 : tall ? tall_y : wide_y;
    int fullx = tile ? 16 * (tall ? tall_w : VIEW_W) : 4096;
    int fully = tile ? sdiv(4096 * (tall ? tall_h : VIEW_H), 192) : 4096;
    if (tall)
        oldy *= 2;
    int midx = tile ? tile_cfg[2] : nudge_x, midy = tile ? tile_cfg[3] : nudge_y;
    fullx += fullx >> 7;                /* a little past the edge, so the nudge can't leave a gap */
    fully += fully >> 7;
    do {
        int *m = e + 5;
        u32 tex = (u32)e[2], fmt = (tex >> 26) & 7;
        if (fmt == 7 || (fmt && (tex & 0xF0000) != 0x30000) || m[15] != 4096)
            continue;
        if (!tall && !m[1] && !m[4] && m[0] - 2 * oldx <= 4 && m[0] - 2 * oldx >= -4)
            continue;
        static const u8 vw[4] = { 25, 29, 32, 36 }, tw[4] = { 24, 27, 31, 34 };
        int x0 = 1 << 30, x1 = -(1 << 30), y0 = 1 << 30, y1 = -(1 << 30), straight = !m[1] && !m[4];
        int vx[4], vy[4];
        for (int i = 0; i < 4; i++) {
            vx[i] = (short)e[vw[i]];
            vy[i] = e[vw[i]] >> 16;
            int x = ((vx[i] * m[0] + vy[i] * m[4]) >> 12) + m[12];
            int y = ((vx[i] * m[1] + vy[i] * m[5]) >> 12) + m[13];
            if (x < x0) x0 = x;
            if (x > x1) x1 = x;
            if (y < y0) y0 = y;
            if (y > y1) y1 = y;
        }
        if (!(vx[0] == vx[1] && vx[2] == vx[3] && vy[1] == vy[2] && vy[0] == vy[3]))
            straight = 0;
        int kx = tall_grow(x0, x1, oldx, fullx, midx), ky = tall_grow(y0, y1, oldy, fully, midy);
        if (!tall) {
            /* (a rotated quad's box says nothing about its corners; one already enlarged,
               in a queue drawn twice, is left) */
            if (!ky || vx[0] > 2048 || vx[0] < -2048 || (straight && kx == 4096 && ky == 4096))
                continue;
            straight = 0;               /* its texture may be turned: enlarge both ways alike */
        }
        if (!kx || (!straight && !ky))
            continue;
        if (!straight)
            kx = ky = 2 * 4096;
        else if (!ky)
            ky = 4096;                  /* a band across the picture: only its length */
        if (kx == 4096 && ky == 4096)
            continue;
        int cx = (vx[0] + vx[2]) >> 1, cy = (vy[0] + vy[2]) >> 1;
        int s[4], t[4], cs, ct, ok = 1;
        for (int i = 0; i < 4; i++)
            s[i] = (short)e[tw[i]], t[i] = e[tw[i]] >> 16;
        cs = (s[0] + s[2]) >> 1;
        ct = (t[0] + t[2]) >> 1;
        /* texture coordinates along s follow the quad's x (as the game lays its straight
           quads out); for a rotated quad both are enlarged alike */
        int ds = cs & ~((128 << ((tex >> 20) & 7)) - 1), dt = ct & ~((128 << ((tex >> 23) & 7)) - 1);
        for (int i = 0; i < 4; i++) {
            vx[i] = scale12(vx[i], cx, kx);
            vy[i] = scale12(vy[i], cy, ky);
            s[i] = scale12(s[i], cs, kx) - ds;      /* back by whole tiles: they hold 16 bits */
            t[i] = scale12(t[i], ct, ky) - dt;
            if ((short)vx[i] != vx[i] || (short)vy[i] != vy[i] || (fmt && ((short)s[i] != s[i] || (short)t[i] != t[i])))
                ok = 0;
        }
        if (!ok)
            continue;
        for (int i = 0; i < 4; i++) {
            e[vw[i]] = (int)(((u32)vy[i] << 16) | ((u32)vx[i] & 0xFFFF));
            if (fmt)
                e[tw[i]] = (int)(((u32)t[i] << 16) | ((u32)s[i] & 0xFFFF));
        }
    } while (0);
}

static void tall_widen(int *q)
{
    for (int *e = (int *)q[0]; e + 40 <= (int *)q[2];) {
        if (e[0] != QUEUE_OP) {
            e++;
            continue;
        }
        if (PLAIN_QUAD(e))
            quad_grow(e, 1);
        e += 40;
    }
}

SMALL void queue_widen(void)
{
    int *q = *(int **)(*(u32 *)0x01FFCF3C);
#ifndef WIDEN_OFF
#define WIDEN_OFF 0
#endif
    if (DUAL_VIEW) {
        if (!WIDEN_OFF)
            tall_widen(q);
        return;
    }
    if (auction) {
        /* titles and bands lie at the very front and run past the field: just behind
           the panel beside it (auction_draw), still in front of the field */
        int edge = (tile_cfg[1] ? tile_cfg[2] : nudge_x) + (((512 - VIEW_W) * (tile_cfg[1] ? 4096 : wide_x)) >> 8) + 8;
        for (int *e = (int *)q[0]; e < (int *)q[2]; e += 40)
            if (e[0] == 0x002B2A29 && e[19] < -4080 &&
                (e[17] + ((e[5] * (short)e[25]) >> 12) > edge || e[17] + ((e[5] * (short)e[32]) >> 12) > edge))
                e[19] += 24;
        return;
    }
    int ex = edge_shift();
    if (!ex)
        return;
    ex += 1;    /* a pixel past the edge, so the nudge can't leave a gap */
    int wx = tile_cfg[1] ? 4096 : wide_x, ox = tile_cfg[1] ? tile_cfg[2] : nudge_x;
    for (int *p = (int *)q[0], *end = (int *)q[2]; p + 40 <= end;) {
        if (p[0] != QUEUE_OP) {
            p++;
            continue;
        }
        int *e = p, *m = e + 5;
        p += 40;
        /* ordinary sprites, most of the queue, leave here (this runs every frame, and
           without it battles drop frames) */
        int lo = (short)e[25], hi = (short)e[32], big = lo == -2048 || lo == 2048;
        if (!big && lo != -128 && hi != 128 && e[25])
            continue;
        if (!PLAIN_QUAD(e))
            continue;
        /* the bar of the law and objective announcements: an 8x64 strip stretched
           far, which the game runs off the right edge of the 4:3 picture.  Its
           left end stays, its right end goes on to the real edge (ticket 39) */
        if (e[25] == 0 && e[29] == (64 << 16) && e[32] == ((64 << 16) | 8) && e[36] == 8 &&
            !(((u32)e[2] >> 20) & 7) && !m[1] && !m[4] && m[15] == 4096) {
            int x1 = m[12] + ((m[0] * 8) >> 12);
            int edge = ox + (((128 + ex) * wx) >> 7);
            if (sdiv((x1 - m[12]) * 128, wx) >= BAR_MIN && x1 - ox >= wx && x1 < edge)
                m[0] = (edge - m[12]) << 9;
            continue;
        }
        int d = m[0] - 2 * wx, c = m[12] - ox;
        /* mist cut into pieces around a speech bubble (ticket 30): whole-pixel corners, and
           the sheet's own borders at +-128; those borders are carried on past the real edge,
           each row's texture (it may be turned) at the rate it has across the piece */
        if (((u32)e[2] & 0xF0000) == 0x30000 && !m[1] && !m[4] && c >= -8 && c <= 8 && (m[0] >> 5) >= wx &&
            (lo == -128 || hi == 128) && hi > lo && (short)e[29] == lo && (short)e[36] == hi) {
            static const u8 row[2][4] = { { 24, 25, 34, 36 }, { 27, 29, 31, 32 } };
            for (int i = 0; i < 2; i++) {
                int *ta = e + row[i][0], *tb = e + row[i][2];
                int ds = sdiv(((short)*tb - (short)*ta) * 64, hi - lo), dt = sdiv(((*tb >> 16) - (*ta >> 16)) * 64, hi - lo);
                if (lo == -128) {
                    *ta = (int)(((u32)((*ta >> 16) - dt) << 16) | (((u32)*ta - (u32)ds) & 0xFFFF));
                    e[row[i][1]] = (e[row[i][1]] & ~0xFFFF) | (-192 & 0xFFFF);
                }
                if (hi == 128) {
                    *tb = (int)(((u32)((*tb >> 16) + dt) << 16) | (((u32)*tb + (u32)ds) & 0xFFFF));
                    e[row[i][3]] = (e[row[i][3]] & ~0xFFFF) | 192;
                }
            }
            continue;
        }
        if (m[1] || m[4] || m[15] != 4096 || d < -4 || d > 4 || c < -8 || c > 8) {
            /* not exactly the old picture: it may still cover it */
            if (big && (m[0] < 0 ? -m[0] : m[0]) + (m[4] < 0 ? -m[4] : m[4]) >= 2 * wx - (wx >> 4))
                quad_grow(e, 0);
            continue;
        }
        int *tc[4] = { e + 24, e + 27, e + 31, e + 34 };
        int vx[4] = { (short)e[25], (short)e[29], (short)e[32], (short)e[36] };
        int sl = 0, sr = 0, nl = 0, nr = 0;
        for (int i = 0; i < 4; i++) {
            int s = (short)*tc[i];
            if (vx[i] == -2048)
                sl = s, nl++;
            else if (vx[i] == 2048)
                sr = s, nr++;
        }
        if (nl != 2 || nr != 2)
            continue;
        for (int i = 0; i < 4; i++)
            if ((short)*tc[i] != (vx[i] < 0 ? sl : sr))
                nl = 0;
        if (!nl)
            continue;
        u32 tex = (u32)e[2];
        int span = sr - sl;                 /* 1/16 texels across the 256 pixels */
        if (!((tex >> 26) & 7)) {
            /* untextured: a colour over the whole picture (the white flash
               that ends the scene) */
            m[0] = sdiv(m[0] * (256 + 2 * ex), 256);
            continue;
        }
        if (!(tex & (1 << 16))) {
            /* not wrapping: only a picture shown once, unflipped, is mirrored */
            if (sl != 0 || span != (8 << ((tex >> 20) & 7)) << 4)
                continue;
            tex |= (1 << 16) | (1 << 18);
        }
        int grow = sdiv(span * ex, 256);
        if (sl - grow < -32768 || sl - grow > 32767 || sr + grow < -32768 || sr + grow > 32767)
            continue;
        e[2] = (int)tex;
        m[0] = sdiv(m[0] * (256 + 2 * ex), 256);
        for (int i = 0; i < 4; i++) {
            int s = (vx[i] < 0 ? sl - grow : sr + grow);
            *tc[i] = (int)(((u32)*tc[i] & 0xFFFF0000u) | ((u32)s & 0xFFFF));
        }
    }
}

__attribute__((naked, used)) void queue_stub(void)   /* at 0x0208F97C, was bl 0x01FFB390 */
{
    __asm__("push {r0, r1, r2, r3, r12, lr}\n"
            "bl queue_widen\n"
            "pop {r0, r1, r2, r3, r12, lr}\n"
            "ldr r12, =0x01FFB390\n"
            "bx r12\n"
            ".ltorg\n");
}

/* layout objects: classify by where their pieces were last frame */
#define LAYOUT_SLOTS 48     /* the Quest Report alone draws more than twenty objects */
static struct layout_slot {
    void *obj;
    u32 frame;
    short min, max;         /* piece x range seen last time it was drawn */
    short acc_min, acc_max; /* range being collected this frame */
    short base, base_y;     /* where the object's origin is on the 4:3 screen, before any shift */
    short moved;            /* non-zero when the object, or a parent, was slid sideways this frame */
    short box[4], acc_box[4];   /* full extent incl. piece sizes: x0, y0, x1, y1 */
} layout_slots[LAYOUT_SLOTS];
static struct layout_slot *layout_cur;
int layout_dy;
int text_dy;

/* windows and moved panels drawn this frame and last: the rectangle as the game
   placed it, and how far the mod moved it (0 for a full-width window, which
   stays put).  Things that sit on one of these go where it went. */
static struct rect moved_rects[RECT_SLOTS], prev_rects[RECT_SLOTS];
static int moved_count;

/* A ground is a root object that covers the 4:3 screen and is bigger than it:
   a board the game scrolls under everything else (the Quest Report grid, the
   world map's table).  Kept apart from the list above because it contains
   every other object: only things that touch no screen edge, and so are marks
   on the ground and not panels of the screen, go where it went. */
static struct rect ground, prev_ground;
static u8 ground_set, prev_ground_set;

static SMALL void rects_new_frame(void)
{
    /* the world map draws at 30 Hz: a frame that drew nothing keeps last frame's list */
    if (!moved_count && !ground_set)
        return;
    /* word by word: there is no memcpy in here for a struct assignment to call */
    volatile short *d = (volatile short *)prev_rects;
    const short *f = (const short *)moved_rects;
    for (int i = 0; i < moved_count * 6; i++)
        d[i] = f[i];
    prev_count = moved_count;
    moved_count = 0;
    d = (volatile short *)&prev_ground;
    f = (const short *)&ground;
    for (int i = 0; i < 6; i++)
        d[i] = f[i];
    prev_ground_set = ground_set;
    ground_set = 0;
}

/* Objects are drawn as trees: FUN_020b2ff0 draws a root with an identity
   parent matrix, then each child with its parent's finished matrix, from an
   array of 0x44-byte matrix slots, one per depth.  A child therefore inherits
   whatever the mod did to its parent and is never moved on its own: list rows
   (cursor, icon, name) are children of their panel, map markers of their map. */
static const int *root_parent;
static short inherit_dx[5], inherit_dy[5];

/* ---- the ability list of View Abilities, made more compact ---------------
 * The game lays the list out for the old 256-pixel screen: two columns 118
 * pixels apart and the scroll bar at the far right.  The widest ability name
 * in the game is 87 pixels (ticket 22), so each column can give up ABIL_TIGHT
 * pixels.  The list is a grid widget that places its cells itself (cell
 * width at +0x94, columns at +0x9E, its own width, which carries the scroll
 * bar, at +0x20): list_fix narrows those while the list's panel is on screen.
 * The highlight bar is shortened to match, and the panel, which is anchored
 * to the right screen edge, slides right by the total.  abil_tree is set
 * while the panel's tree of objects is being drawn, abil_frame when it last was. */
#define ABIL_TIGHT 14
#define ABIL_CELL  118      /* the game's column pitch in this list */
static u32 abil_frame;
static void *abil_obj;     /* the list's panel, once recognised: it loses pieces while slid out */
static u8 abil_tree, cur_depth, cur_highlight, bz_holder;
/* set while drawing the tree of a root object that reaches past the 4:3 picture
   on all four sides (last frame's box): a board the game scrolls, such as the map
   of Ivalice.  Its pieces beyond the picture are real picture, not parked. */
static u8 tree_big;

/* The bazaar (ticket 33): its rows go under the list (ov_draw), so the list and what
   pops up over it move up to the tab bar and the description box goes away, below
   the view.  Its panels hang from holders without pieces at the screen's
   middle (bz_holder), whose origin lies in the list: those stay where they are, and
   the panels under them are placed by their own boxes like the others. */
static SMALL __attribute__((noinline)) int bz_place(void *obj, const short *box, int bare, int depth)
{
    if (!depth && !bare && box[1] < 40 && box[3] > 96 && box[2] - box[0] >= 240)
        bz_list = frame_no;                 /* the recipe or loot list */
    if (!bazaar_rows)
        return 0;
    if (depth && (depth > 1 || !bz_holder))
        return 0;
    /* once away the game no longer draws its pieces, so there is no box to tell
       it by: remembered (as the View Abilities list, abil_obj) */
    if (obj == bz_desc || (!bare && box[1] >= 104 && box[2] - box[0] >= 240)) {
        bz_desc = obj;
        return 120;                         /* away below the view */
    }
    return bare || box[1] >= 104 ? 0 : -edge_py;
}

int layout_obj_begin(void *obj, int x, const int *parent, int y)
{
    struct layout_slot *e = 0, *oldest = &layout_slots[0];
    for (int i = 0; i < LAYOUT_SLOTS; i++) {
        struct layout_slot *c = &layout_slots[i];
        if (c->obj == obj) { e = c; break; }
        if (c->frame < oldest->frame) oldest = c;
    }
    if (!e) {
        e = oldest;
        e->obj = obj;
        e->frame = 0;
        e->min = e->acc_min = 32767;
        e->max = e->acc_max = -32768;
        e->box[0] = e->box[1] = e->acc_box[0] = e->acc_box[1] = 32767;
        e->box[2] = e->box[3] = e->acc_box[2] = e->acc_box[3] = -32768;
    }
    if (e->frame != frame_no) {
        e->min = e->acc_min;
        e->max = e->acc_max;
        e->acc_min = 32767;
        e->acc_max = -32768;
        for (int i = 0; i < 4; i++) {
            e->box[i] = e->acc_box[i];
            e->acc_box[i] = i < 2 ? 32767 : -32768;
        }
        e->frame = frame_no;
    }

    u32 depth = (u32)((const char *)parent - (const char *)root_parent);
    if (!root_parent || depth > 3 * 0x44 || depth % 0x44) {
        root_parent = parent;
        depth = 0;
    }
    depth /= 0x44;
    if (!depth)
        inherit_dx[0] = inherit_dy[0] = 0;
    int in_dx = inherit_dx[depth], in_dy = inherit_dy[depth];
    if (!depth) {
        bz_holder = bazaar_rows && x == 128 && y == 96;    /* see bz_place */
        abil_tree = 0;
        tree_big = e->box[0] < 0 && e->box[1] < 0 && e->box[2] > 256 && e->box[3] > 192;
    }
    cur_depth = (u8)depth;
    cur_highlight = 0;

    /* x and y include the object's scaling pivot (+0x6C, +0x6E), which the game
       subtracts again after scaling; the parent matrix holds its position in
       words 9 and 10.  Pieces are positioned relative to this origin. */
    e->base = (short)(x - *(short *)((char *)obj + 0x6C) + parent[9] - in_dx);
    e->base_y = (short)(y - *(short *)((char *)obj + 0x6E) + parent[10] - in_dy);
    layout_cur = e;

    int shift = 0, dy = 0;
    int bare = e->min > e->max;         /* no pieces of its own: a text label, or not seen yet */
    if (depth && abil_tree)             /* the list's cell is the one object about a column wide */
        cur_highlight = !bare && e->box[2] - e->box[0] >= 96 && e->box[2] - e->box[0] <= 128;
    const struct rect *w = 0;
    /* the Jobs list reaches from left of centre to the right edge */
    int jobs_list = jobs_panel && !depth && !bare && e->box[0] >= 32 && e->box[0] < 128 && e->box[2] >= 250;
    /* a panel as wide as the 4:3 picture whose right end lies well outside it:
       the ability list of View Abilities */
    int abil_list = !depth && !bare && edge_shift() && e->box[0] >= -16 && e->box[0] <= 2 &&
                    (e->box[2] >= 272 || (obj == abil_obj && abil_frame + 4 > frame_no));
    if (abil_list) {
        abil_obj = obj;
        abil_frame = frame_no;
        abil_tree = 1;
    }
    if (!depth && !jobs_list && !abil_list && !bz_holder) {
        /* an object that sat inside a window or a moved panel last frame goes
           where that went; one without pieces is judged by its origin */
        for (int i = 0; i < prev_count && !w; i++) {
            const struct rect *r = &prev_rects[i];
            if (bare ? e->base >= r->x0 && e->base < r->x1 && e->base_y >= r->y0 && e->base_y < r->y1
                     : e->box[0] >= r->x0 && e->box[2] <= r->x1 && e->box[1] >= r->y0 && e->box[3] <= r->y1)
                w = r;
        }
    }
    int is_ground = !depth && !bare && e->box[0] <= 2 && e->box[1] <= 2 && e->box[2] >= 254 && e->box[3] >= 190 &&
                    (e->box[2] - e->box[0] > 264 || e->box[3] - e->box[1] > 200);
    if (!w && !depth && !is_ground && prev_ground_set) {
        const struct rect *r = &prev_ground;
        /* an object without pieces is a holder for children (the report's quest nodes) */
        if (bare ? e->base >= r->x0 && e->base < r->x1 && e->base_y >= r->y0 && e->base_y < r->y1
                 : e->box[0] > 2 && e->box[2] < 254 && e->box[1] > 2 && e->box[3] < 190 &&
                   e->box[0] >= r->x0 && e->box[2] <= r->x1 && e->box[1] >= r->y0 && e->box[3] <= r->y1)
            w = r;
    }
    if (w) {
        shift = w->shift;
        dy = w->dy;
    } else if (is_ground) {
        /* where the ground's own edge shows inside the wide picture, slide it
           out to the real screen edge, as far as it still covers the other side */
        int ex = edge_shift(), ey = wide_y != 4096 && !auction ? edge_py : 0;
        if (e->box[0] > -ex && e->box[2] - ex - e->box[0] >= 256 + ex)
            shift = -ex - e->box[0];
        else if (e->box[2] < 256 + ex && e->box[0] + 256 + ex - e->box[2] <= -ex)
            shift = 256 + ex - e->box[2];
        if (e->box[1] > -ey && e->box[3] - ey - e->box[1] >= 192 + ey)
            dy = -ey - e->box[1];
        else if (e->box[3] < 192 + ey && e->box[1] + 192 + ey - e->box[3] <= -ey)
            dy = 192 + ey - e->box[3];
        ground.x0 = e->box[0]; ground.y0 = e->box[1]; ground.x1 = e->box[2]; ground.y1 = e->box[3];
        ground.shift = (short)shift;
        ground.dy = (short)dy;
        ground_set = 1;
    } else if (!depth && !bare) {
        /* as wide as the 4:3 picture (a still picture, the title's copyright
           line), or well clear of both sides and centred on it (the title
           menu 60..210, the difficulty menu 70..221): stays centred across, still pushed to the top or
           bottom.  Panels reaching near a side (the item description box,
           3..253) still slide with their side. */
        int full = (e->box[0] <= 2 && e->box[2] >= 254) ||
                   (e->box[0] >= 32 && e->box[0] < 96 && e->box[2] > 160 && e->box[2] <= 224 &&
                    e->box[0] + e->box[2] - 256 <= 40 && 256 - e->box[0] - e->box[2] <= 40);
        if (wide_y != 4096 && !auction) {
            if (e->box[3] <= 96)
                dy = -edge_py;
            else if (e->box[1] >= 96)
                dy = edge_py;
        }
        /* a small top-right panel (the B hint of unit placement and targeting)
           would sit on the banner: drop it below the banner and turn-order strip
           instead, on 4:3 too (it stays up all through placement, so the banner
           can't step aside for it as it does for bigger panels) */
        if (e->box[3] <= 32 && e->box[0] >= 192 && hud_drawn_frame + 2 > frame_no) {
            dy = hud_bottom + 2;
            /* and below the action name bar, which runs to the edge (ticket 37) */
            if (bar_frame + 2 > frame_no && dy < bar_bottom)
                dy = bar_bottom;
        }
        if (jobs_list)
            shift = JOBS_SHIFT;
        else if (abil_list)
            /* its pieces stop at different places past the old edge (the last
               33 px out): right until they are all off the wide picture, and
               by what list_fix takes out of the list */
            shift = edge_shift() - 1 + 2 * ABIL_TIGHT;
        else if (full)
            ;
        /* a panel that starts inside the picture and runs past its right edge (the
           list of ability sets in Set Abilities, 29..264, its set icons beyond 256)
           keeps running off the right edge, even when its own pieces all lie on the
           left: sliding it left cut it short and showed the icons (ticket 32) */
        else if (e->box[2] > 258 && e->box[0] > 2 && e->box[0] < 128)
            shift = edge_shift();
        else if (e->max < 128)
            shift = -edge_shift();
        else if (e->min >= 128)
            shift = edge_shift();
        /* a panel that starts mid-screen and runs off one side of the 4:3 picture
           (the Item Info box) stays attached to that side */
        else if (e->box[2] >= 254 && e->box[0] >= 64)
            shift = edge_shift();
        else if (e->box[0] <= 2 && e->box[2] <= 192)
            shift = -edge_shift();
    }
    /* the bazaar's rows go under the list (ov_draw): its panels, and those under
       its holders, placed by bz_place */
    if (bazaar_open) {
        int d = bz_place(obj, e->box, bare, depth);
        if (d)
            dy = d;
    }
    /* record it, also when it only followed its own rectangle from last frame (the
       world map's globe): otherwise it is listed every other frame, and what sits on it
       (the place name, the weather icon) would flicker between two places */
    int self = w && w->x0 == e->box[0] && w->y0 == e->box[1] && w->x1 == e->box[2] && w->y1 == e->box[3];
    if ((!w || self) && !bare && !is_ground && (shift || dy) && moved_count < RECT_SLOTS) {
        struct rect *r = &moved_rects[moved_count++];
        r->x0 = e->box[0]; r->y0 = e->box[1]; r->x1 = e->box[2]; r->y1 = e->box[3];
        r->shift = (short)shift;
        r->dy = (short)dy;
    }
    if (!bare)
        stage_check(e->box[0] + shift, e->box[1] + dy, e->box[2] + shift, e->box[3] + dy, 1);
    e->moved = (short)(in_dx + shift);
    inherit_dx[depth + 1] = (short)(in_dx + shift);
    inherit_dy[depth + 1] = (short)(in_dy + dy);
    layout_dy = dy;
    return x + shift;
}

void layout_piece_seen(int x, int y)
{
    struct layout_slot *e = layout_cur;
    if (!e) return;
    (void)y;
    x += e->base;
    if (x < e->acc_min) e->acc_min = (short)x;
    if (x > e->acc_max) e->acc_max = (short)x;
}

/* A layout object that is exactly one screen big is a frame around the whole
   picture (the world map's border).  Its pieces go out to the real screen
   edges: left/top pieces slide out, right/bottom ones the other way, and the
   bars in between are lengthened.  piece: x, y, w, h shorts at +0xC;
   scratch: the quad being built, w at +0x20/+0x2C and h at +0x16/+0x22. */
int piece_y;
static short *still_quad;
static short *bar_quad;

/* ---- "Complete!" reaches both edges (ticket 40) ---------------------------
 * The game's bar is one 256x32 piece running across the whole 4:3 picture: flat
 * stripes, the lettering in the middle, a slanted right end.  layout_piece cuts
 * the game's quad off at BAR_CUT, between lettering and slant; then the first
 * and the cut's texel columns carry the stripes on to the left edge and as far to
 * the right, and the slanted end goes to the real edge.  The lettering stays. */
#define BAR_CUT  216
#define BATTLE_PHASE  (*(volatile u8 *)0x0212EE26)   /* 7 = "Complete!" (event opcode 0x23) */

/* ---- still pictures fill the wide screen (ticket 12) ----------------------
 * A full-screen still (the title background) has no more picture beyond its
 * 256x192.  The side areas and the bands above and below show it mirrored at
 * its edges: eight more quads around the game's own one, sampling the same
 * texture with the texture coordinates running backwards.  Everything comes
 * from the player's ROM while the game runs.  Called at 0x020B0B4C, between
 * the game's last vertex and END_VTXS, so the quads share its texture,
 * palette, colour and matrix.  scratch: the quad being built, per vertex a
 * 20.12 texcoord pair at words 0/1, 3/4, 6/7, 9/10 (v0 top left, v1 bottom
 * left, v2 bottom right, v3 top right), positions as shorts at +8/+0x14/... */
static SMALL void still_vertex(int s, int t, int x, int y)
{
    GX(G_TEXCOORD) = (u32)(((t >> 8) << 16) | ((s >> 8) & 0xFFFF));
    GX(G_VTX16) = (u32)(((y & 0xFFFF) << 16) | (x & 0xFFFF));
    GX(G_VTX16) = 0;
}

static SMALL void bar_part(const int *scratch, int sa, int sb, int x0, int x1)
{
    int t0 = scratch[1], t1 = scratch[7];
    still_vertex(sa, t0, x0, 0);
    still_vertex(sa, t1, x0, 32);
    still_vertex(sb, t1, x1, 32);
    still_vertex(sb, t0, x1, 0);
}

#ifdef MAP_ART
/* the map of Ivalice's extended edges (ticket 36) */
#include "map_art.c"
#endif

SMALL void still_edges(int *scratch)
{
#ifdef MAP_ART
    if (map_art_quad(scratch))
        return;
#endif
    if ((short *)scratch == bar_quad) {
        bar_quad = 0;
        int ex = edge_shift() + 1, s0 = scratch[0], cut = s0 + (BAR_CUT << 12);     /* +1: as in queue_widen */
        bar_part(scratch, s0 + 0x800, s0 + 0x800, -ex, 0);
        bar_part(scratch, cut + 0x800, cut + 0x800, BAR_CUT, BAR_CUT + ex);
        bar_part(scratch, cut, s0 + (256 << 12), BAR_CUT + ex, 256 + ex);
        return;
    }
    if ((short *)scratch != still_quad)
        return;
    still_quad = 0;
    int s0 = scratch[0], t0 = scratch[1], s1 = scratch[6], t1 = scratch[7];
    /* only a picture drawn one texel per pixel, unflipped */
    if (s1 - s0 != 256 << 12 || t1 - t0 != 192 << 12)
        return;
    int ex = edge_shift(), ey = wide_y != 4096 ? edge_py : 0;
    /* per axis, three spans: the mirrored band before, the picture, the band after;
       position from..to and texture coordinate from..to */
    int xs[3][4] = { { -ex, 0, s0 + (ex << 12), s0 }, { 0, 256, s0, s1 }, { 256, 256 + ex, s1, s1 - (ex << 12) } };
    int ys[3][4] = { { -ey, 0, t0 + (ey << 12), t0 }, { 0, 192, t0, t1 }, { 192, 192 + ey, t1, t1 - (ey << 12) } };
    for (int j = 0; j < 3; j++)
        for (int i = 0; i < 3; i++) {
            const int *a = xs[i], *b = ys[j];
            if ((i == 1 && j == 1) || a[0] == a[1] || b[0] == b[1])
                continue;
            still_vertex(a[2], b[2], a[0], b[0]);
            still_vertex(a[2], b[3], a[0], b[1]);
            still_vertex(a[3], b[3], a[1], b[1]);
            still_vertex(a[3], b[2], a[1], b[0]);
        }
}

int layout_piece(short *piece, short *scratch, int obj_y)
{
    int x = piece[6], y = piece[7], w = piece[8], h = piece[9];
    struct layout_slot *e = layout_cur;
    piece_y = y;
    layout_piece_seen(x, y);
    if (!e)
        return x;
    int ax = x + e->base, ay = y + obj_y + e->base_y;
    if (ax < e->acc_box[0]) e->acc_box[0] = (short)ax;
    if (ay < e->acc_box[1]) e->acc_box[1] = (short)ay;
    if (ax + w > e->acc_box[2]) e->acc_box[2] = (short)(ax + w);
    if (ay + h > e->acc_box[3]) e->acc_box[3] = (short)(ay + h);
    /* The game parks some pieces just outside the 4:3 picture (the list cursor
       of a full-width list).  On an object that was slid outward they leave the
       wide picture too; on one that stayed put they would show in the side
       area, so send them further away.  Not on a board bigger than the screen
       (tree_big, the map of Ivalice): there the pieces outside are the rest of
       the picture (ticket 24). */
    if (wide_x != 4096 && !auction && !e->moved && !tree_big && (ax + w <= 0 || ax >= 256))
        return x + (ax < 128 ? -512 : 512);
    if (wide_x != 4096 && BATTLE_PHASE == 7 && x == 0 && w == 256 && h == 32) {
        scratch[16] = scratch[22] = BAR_CUT;
        ((int *)scratch)[6] = ((int *)scratch)[9] = ((int *)scratch)[0] + (BAR_CUT << 12);
        bar_quad = scratch;
        return x;
    }
    if (abil_tree && cur_highlight) {
        /* a cell of the ability list: the highlight bar is three pieces a row,
           6 + 95 + 6 wide; the marker and the mastery mark stay as they are */
        if (w >= 90)
            scratch[16] = scratch[22] = (short)(w - ABIL_TIGHT);
        else if (w <= 8 && x >= 100)
            x -= ABIL_TIGHT;
        return x;
    }
    /* screen-sized: the 4:3 width, and the 4:3 height or more (the auction's
       backdrop has tabs parked above and below the picture, ticket 24) */
    int *tcs = (int *)scratch;
    if (auction && tcs[0] > tcs[6] && (tcs[0] & 0xFFF) == 0x800) {
        /* mirrored and half a texel off (the time bar's left end): sharper than the DS,
           the last half pixel shows the next image in the texture */
        tcs[0] = tcs[3] += 0x800;
        tcs[6] = tcs[9] += 0x800;
    }
    if (wide_x == 4096 || auction ||
        e->box[0] < -2 || e->box[0] > 2 || e->box[2] < 254 || e->box[2] > 259 ||
        e->box[1] > 2 || e->box[3] < 190 ||
        ((e->box[1] < -2 || e->box[3] > 194) && cur_depth))
        return x;
    /* one piece that is the whole picture (the title screen's background): a
       still picture, not a frame.  It stays as it is; still_edges adds its
       mirror image around it when the quad is finished. */
    if (ax == 0 && ay == 0 && w == 256 && h == 192) {
        still_quad = scratch;
        return x;
    }
    if (ax + w <= 128)
        x -= edge_px;
    else if (ax >= 128)
        x += edge_px;
    else {
        x -= edge_px;
        scratch[16] = scratch[22] = (short)(w + 2 * edge_px);
        /* a piece sampled from half a texel to half a texel (the auction map's
           border tiles) shows a sliver of the next image in the texture at each
           end; stretched, that sliver becomes a visible line: sample whole texels */
        int *tc = (int *)scratch, half = 1 << 11;
        int s0 = tc[0], s1 = tc[6];
        if ((s0 & 0xFFF) == half || (s1 & 0xFFF) == half) {
            if (s0 < s1) { s0 += half; s1 -= half; } else { s0 -= half; s1 += half; }
            tc[0] = tc[3] = s0;
            tc[6] = tc[9] = s1;
        }
    }
    if (wide_y != 4096) {
        if (ay + h <= 96)
            piece_y = y - edge_py;
        else if (ay >= 96)
            piece_y = y + edge_py;
        else {
            piece_y = y - edge_py;
            scratch[11] = scratch[17] = (short)(h + 2 * edge_py);
        }
    }
    return x;
}

/* windows: x, y, w, h are shorts at +0x10 in the window object */

SMALL static void window_draw_with(short *win, void (*draw)(short *))
{
    int x = win[8], y = win[9], w = win[10], h = win[11];
    int shift = 0;
    int at_left = x <= 2, at_right = x + w >= 254;
    if (at_left && at_right)
        shift = 0;                      /* full width: leave alone */
    else if (at_right || x >= 128)
        shift = edge_shift();           /* touches the right edge, or sits wholly right */
    else if (at_left || x + w <= 128)
        shift = -edge_shift();
    int dy = 0;
    if (wide_y != 4096) {
        int at_top = y <= 2, at_bottom = y + h >= 190;
        if (at_top && !at_bottom)
            dy = -edge_py;
        else if (at_bottom && !at_top)
            dy = edge_py;
        if (bazaar_rows && y < 104)         /* up with the list, clear of the bazaar's rows */
            dy = -edge_py;
    }
    /* The bar with the action's name ("Attack"), 0,12 256x24: edge to edge, as in the
       original (the only window that touches both sides this high up, ticket 37).  In a
       view too narrow for the stage the turn order is a strip on the bar's rows: then the
       bar ends where the strip starts, its text centred in what is left; the rectangle
       recorded below is the bar as the game placed it, so the text line moves as much. */
    int nx = x + shift, nw = w, bar = at_left && at_right && y > 2 && y + h <= 48;
    if (bar && edge_shift()) {
        nx = -edge_shift();
        nw = screen_w;
        if (hud_drawn_frame + 2 > frame_no && turn_left < screen_w) {
            nw = turn_left - 2;
            dy += banner_extra;             /* and under the banner when it has more rows */
        }
        shift = nx + nw / 2 - (x + w / 2);
        bar_frame = frame_no;
        bar_bottom = y + dy + h + 1;
        /* its frame is 3x3 pieces (0x28 each from +0x18; x, y at +1 and w, h at +5, all
           bytes, so a 354 px middle doesn't fit); every column looks the same, so each
           takes about a third.  The game lays them out anew when it opens a window. */
        u8 *pc = (u8 *)win + 0x18;
        int third = sdiv(nw, 3);
        if (third > 127)
            third = 127;                    /* the last column's x is a byte too */
        for (int r = 0; r < 3; r++)
            for (int c = 0; c < 3; c++, pc += 0x28) {
                pc[1] = (u8)(c * third);
                pc[5] = (u8)(c < 2 ? third : nw - 2 * third);
            }
    }
    if (moved_count < RECT_SLOTS) {
        moved_rects[moved_count].x0 = (short)x;
        moved_rects[moved_count].y0 = (short)y;
        moved_rects[moved_count].x1 = (short)(x + w);
        moved_rects[moved_count].y1 = (short)(y + h);
        moved_rects[moved_count].shift = (short)shift;
        moved_rects[moved_count].dy = (short)dy;
        moved_count++;
    }
    /* the action name bar lies under the banner's rows by design (on 4:3 it keeps
       its full width under the turn-order strip): it doesn't push the banner away */
    stage_check(nx, y + dy, nx + nw, y + dy + h, !bar);
    win[8] = (short)nx;
    win[9] = (short)(y + dy);
    win[10] = (short)nw;
    /* a Yes/Cancel box places its marks and cursor at its text lines' stored
       positions (0x0204EBE0, the only reader of their y, 0x0204CD80), while the
       lines themselves move only when drawn, later: for this draw the lines inside
       the window are moved with it.  List nodes: next +4, id +8, x +10, y +12. */
    short *moved_lines[8];
    int nl = 0;
    if (bazaar_rows && dy)
        for (char *n = **(char ***)0x0204CDB0; n && nl < 8; n = *(char **)(n + 4)) {
            short *p = (short *)(n + 10);
            if (p[0] >= x && p[0] < x + w && p[1] >= y && p[1] < y + h) {
                p[1] += dy;
                moved_lines[nl++] = p;
            }
        }
    draw(win);
    while (nl)
        moved_lines[--nl][1] -= dy;
    win[8] = (short)x;
    win[9] = (short)y;
    win[10] = (short)w;
}

/* the game's three window kinds, each called from the window list walker */
void window_draw(short *win)  { window_draw_with(win, (void (*)(short *))0x020525E8); }
void window_draw_speech(short *win)
{
    speech_frame = frame_no;
    window_draw_with(win, (void (*)(short *))0x0204F944);
}
void window_draw_other(short *win)  { window_draw_with(win, (void (*)(short *))0x0204FFFC); }

int text_line_x(int x, int y)
{
    text_dy = 0;
    /* y is the top of the line; judge by its middle (the world map's place name starts
       a pixel above the tab it sits on) */
    y += 6;
    for (int i = 0; i < moved_count; i++)
        if (x >= moved_rects[i].x0 && x < moved_rects[i].x1 &&
            y >= moved_rects[i].y0 && y < moved_rects[i].y1) {
            text_dy = moved_rects[i].dy;
            return x + moved_rects[i].shift;
        }
    /* on every other frame some lines are placed before their panel is drawn (the
       world map's place name): then last frame's panels decide, or the line would
       jump between two places */
    for (int i = 0; i < prev_count; i++)
        if (x >= prev_rects[i].x0 && x < prev_rects[i].x1 &&
            y >= prev_rects[i].y0 && y < prev_rects[i].y1) {
            text_dy = prev_rects[i].dy;
            return x + prev_rects[i].shift;
        }
    return x;
}

/* On the mist maps the game cuts the mist around the windows on screen (up to three
   rectangles, 0x021299F4, count 0x021299E8, so it doesn't lie over their text) and works on a
   copy at 0x02129A0C.  Called for the list by the effect renderer (bl at 0x02031EE0): hands
   over the copy, each rectangle moved as the mod moved its window (ticket 30). */
SMALL short *mist_holes(u8 *n)
{
    const short *s = (const short *)0x021299F4;
    short *d = (short *)0x02129A0C;
    *n = *(u8 *)0x021299E8;
    for (int i = 0; i < 3; i++, s += 4, d += 4) {
        int x = (s[0] + s[2]) >> 1, dx = text_line_x(x, ((s[1] + s[3]) >> 1) - 6) - x;
        d[0] = (short)(s[0] + dx);
        d[2] = (short)(s[2] + dx);
        d[1] = (short)(s[1] + text_dy);
        d[3] = (short)(s[3] + text_dy);
    }
    return (short *)0x02129A0C;
}

__attribute__((naked, used)) void layout_obj_stub(void)   /* at 0x020B2E98 */
{
    /* r0 = the parent's matrix, r3 = x, r8 = y, r5 = the object */
    __asm__("push {r0, r1, r2, r12, lr}\n"
            "mov r2, r0\n"
            "mov r1, r3\n"
            "mov r3, r8\n"
            "mov r0, r5\n"
            "bl layout_obj_begin\n"
            "mov r3, r0\n"
            "ldr r0, =layout_dy\n"
            "ldr r0, [r0]\n"
            "add r8, r8, r0\n"         /* r8 is the y the caller stores next */
            "pop {r0, r1, r2, r12, lr}\n"
            "str r3, [r1, #0x30]\n"    /* replaced instruction */
            "mov r3, lr\n"
            "mov lr, #0x1000\n"        /* the caller keeps this constant in lr */
            "bx r3\n");
}

__attribute__((naked, used)) void layout_piece_stub(void) /* at 0x020B095C */
{
    /* replaces "ldrsh r2, [r6, #0xc]"; r3 already holds the piece's y, r5 the
       object's y, r8 the quad being built.  Returns x in r2 and y in r3. */
    __asm__("push {r0, r1, r12, lr}\n"
            "mov r0, r6\n"
            "mov r1, r8\n"
            "mov r2, r5\n"
            "bl layout_piece\n"
            "mov r2, r0\n"
            "ldr r3, =piece_y\n"
            "ldr r3, [r3]\n"
            "pop {r0, r1, r12, pc}\n");
}

__attribute__((naked, used)) void still_stub(void)   /* at 0x020B0B4C */
{
    /* replaces "str r1, [ip, #4]" (END_VTXS, r1 = 0); r8 is the quad, lr holds 1
       for the MTX_POP that follows */
    __asm__("push {r0, r1, r2, r3, r12, lr}\n"
            "mov r0, r8\n"
            "bl still_edges\n"
            "pop {r0, r1, r2, r3, r12, lr}\n"
            "str r1, [r12, #4]\n"      /* replaced instruction */
            "mov r3, lr\n"
            "mov lr, #1\n"
            "bx r3\n");
}

/* ---- button-hint labels without their second copy (ticket 34) --------------
 * The game draws labels with the shadow flag twice, the second copy a pixel down
 * and right behind the first.  The text of a hint bar already has its outline and
 * fills the bar: the copy's bottom row pokes out under the frame, and its light
 * pixels show through the first copy wherever an emulator rounds the two
 * differently.  Only the world map's place name, high on the screen and bare on
 * the art, keeps it.  Widescreen presets only (patch.py). */
static SMALL __attribute__((used)) int label_shadow(int flag)
{
    return flag && layout_cur && layout_cur->base_y < 64;
}

__attribute__((naked, used)) void label_stub(void)        /* at 0x0204CF84 and 0x0204D19C */
{
    /* replaces "cmp r0, #1"; r0 = the label's shadow flag */
    __asm__("push {r1, r2, r3, r12, lr}\n"
            "bl label_shadow\n"
            "cmp r0, #1\n"                /* replaced instruction */
            "pop {r1, r2, r3, r12, pc}\n");
}

__attribute__((naked, used)) void text_line_stub(void)    /* at 0x0204B514 */
{
    __asm__("ldrsh r2, [r11, #0xa]\n"  /* replaced instruction */
            "push {r0, r1, r3, r12, lr}\n"
            "mov r0, r2\n"
            "mov r1, r3\n"
            "bl text_line_x\n"
            "mov r2, r0\n"
            "pop {r0, r1, r3, r12, lr}\n"
            "push {r0}\n"
            "ldr r0, =text_dy\n"
            "ldr r0, [r0]\n"
            "add r3, r3, r0\n"         /* r3 is the line's y, stored right after x */
            "pop {r0}\n"
            "bx lr\n");
}

/* a grid list about to draw its cells (0x020B34C0) */
void list_fix(short *list)
{
    if (abil_frame + 3 > frame_no && abil_frame && list[0x9E / 2] == 2 && list[0x94 / 2] == ABIL_CELL) {
        list[0x94 / 2] = ABIL_CELL - ABIL_TIGHT;
        list[0x20 / 2] -= 2 * ABIL_TIGHT;
    }
}

__attribute__((naked, used)) void list_stub(void)
{
    __asm__("push {r0, r1, r2, r3, r12, lr}\n"
            "mov r0, r1\n"
            "bl list_fix\n"
            "pop {r0, r1, r2, r3, r12, lr}\n"
            "ldr r12, =0x020B3208\n"
            "bx r12\n"
            ".ltorg\n");
}

__attribute__((naked, used)) void ortho_hook(void)
{
    __asm__("push {r4, lr}\n"
            "mov r0, r4\n"
            "bl ortho_whole\n"
            "pop {r4, lr}\n"
            "ldr r0, [sp, #0x64]\n"   /* instruction replaced by the hook */
            "bx lr\n");
}

/* Fixed entry table at the very start of the blob: patch.py branches to
   BLOB_ADDR + 4*n, so these slots must keep their order. */
__attribute__((naked, section(".entry"), used)) void entry_table(void)
{
    __asm__("b hook_entry\n"      /* +0: per-frame hook */
            "b ortho_hook\n"      /* +4: G3_OrthoW hook */
            "b backdrop_camera\n" /* +8: backdrop camera wrapper */
            "b map_cell_visible\n" /* +12: map cell visibility test */
            "b layout_obj_stub\n"  /* +16 */
            "b layout_piece_stub\n" /* +20 */
            "b window_draw\n"      /* +24 */
            "b text_line_stub\n"   /* +28 */
            "b window_draw_speech\n" /* +32 */
            "b window_draw_other\n" /* +36 */
            "b swap_stub\n"       /* +40 */
            "b sprite_stub\n"     /* +44 */
            "b layer_draw\n"      /* +48 */
            "b map_stub\n"       /* +52 */
            "b list_stub\n"      /* +56 */
            "b still_stub\n"     /* +60 */
            "b queue_stub\n"    /* +64 */
            "b dual_frame\n"    /* +68 */
            "b glow_stub\n"     /* +72 */
            "b glow_blend_stub\n"   /* +76 */
            "b glow_layers_stub\n"  /* +80 */
            "b label_stub\n"       /* +84 */
            "b mist_holes\n");     /* +88 */
}

__attribute__((naked, used)) void hook_entry(void)
{
    __asm__("strh r1, [r0, #8]\n"   /* instruction replaced by the hook */
            "bl frame_hook\n"
            "pop {r3, pc}\n");      /* original function epilogue */
}

/* ---- video memory the mod borrows (ticket 25) ----------------------------
 * Every range of video memory the mod writes, as the addresses it writes them
 * through: 0x068xxxxx is a bank seen through its LCDC window (A 0x06800000,
 * B 0x06820000, E 0x06880000, G 0x06894000, ...), 0x060xxxxx is main-engine BG
 * space (whichever bank the game has mapped there).  scripts/vram_guard.py
 * reads this table from the built blob, after its "BORR" marker, and reports a
 * clash when the game draws from or writes over the mod's data in these
 * ranges, or the mod draws from data the game changed.  Entries: four-letter
 * tag, start, end (exclusive); a zero tag ends the table. */
#define BORROW_TAG(s) ((u32)(s)[0] | (u32)(s)[1] << 8 | (u32)(s)[2] << 16 | (u32)(s)[3] << 24)
__attribute__((used)) const u32 borrowed_vram[] = {
    0x52524F42,                                                     /* "BORR" */
    BORROW_TAG("HUDT"), (u32)TEX_LCDC, 0x06840000,                  /* banner + turn-order texture, bank B top */
    BORROW_TAG("HUDP"), (u32)PAL_LCDC, (u32)(PAL_LCDC + (1 + TURN_SEEN) * 16),   /* their palettes */
    BORROW_TAG("OVTX"), (u32)OV_TEX_LCDC, (u32)(OV_TEX_LCDC + OV_WORDS),         /* overlay texture, bank A */
    BORROW_TAG("OVTH"), 0x06800000 + OV_HEAP_TEX, 0x06800000 + OV_HEAP_TEX + OV_WORDS * 4,   /* or the heap's free top, bank B */
    BORROW_TAG("OVPL"), (u32)OV_PAL_LCDC, (u32)(OV_PAL_LCDC + 256),              /* overlay palette */
    BORROW_TAG("OVBK"), (u32)OV_BACKUP, (u32)(OV_BACKUP + OV_WORDS),             /* bank A's parked contents */
    BORROW_TAG("OVSR"), (u32)OV_SRC, (u32)(OV_SRC + 32 * 16),                    /* overlay scratch tables */
    BORROW_TAG("OVCL"), (u32)OV_COL, (u32)(OV_COL + 256),
#ifdef MAP_ART
    BORROW_TAG("MAPA"), (u32)MAP_ART_LCDC, (u32)(MAP_ART_LCDC + 4096),           /* map of Ivalice's edges (ticket 36) */
#endif
    0,
};

/* The 2D projection (windows, speech bubbles, panels: 1 unit = 1 game pixel, 32 clip
   units across, origin top left; ui_draw_pass) draws piece by piece: move to the piece's
   corner, then a quad of its width.  The hardware rounds the move and the width apart,
   so once the squeeze makes a pixel 22.38 clip units (Deck), a piece's right edge and the
   next one's left edge can land a fraction of a pixel apart, and melonDS's high
   resolution shows the map through the crack (ticket 43).  Scaled by 128, x, y, z and w
   alike, the picture and the depth order are the same, but a pixel is wide_x clip units,
   a whole number, so the edges meet exactly; down, the rounding is 128 times finer.
   The plain game's pixel is 32 units already.  Not the sprites' centred projection (the
   same scale, x mirrored): the sprite queue multiplies it into each entry's matrix, which
   queue_widen reads expecting w = 1.0.
   Called by ortho_hook in place of ortho_fix, and kept last in the file so that no code
   before it moves: melonDS test states parked inside the mod's code stay usable. */
SMALL __attribute__((section(".text.zlast"))) void ortho_whole(int *m)
{
    int px = m[0] == 32 * 4096 && m[12] == -4096 && m[13] == 4096 && m[15] == 4096 && wide_x != 4096;
    ortho_fix(m);
    if (px)
#pragma clang loop unroll(disable)
        for (int i = 0; i < 16; i++)
            m[i] <<= 7;
}
