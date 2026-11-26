/* The map of Ivalice's extended edges (ticket 36, ADR 0018).  Included by hook.c
 * when patch.py finds the art (work/map_art/map_art.lz, made by map_art_pack.py
 * from an AI extension of the game's picture; it is not in the repository).
 *
 * The game's map picture is 408x300 texels (a 408x256 piece plus a row of four
 * strips) and fades into sea at its left and right ends; beyond it the game
 * stretches an 8x8 patch of sea.  The wide view reaches up to 40 texels left
 * of the picture, 20 right of it and 2 below it, never above it, over all 22
 * areas on the Deck and 16:9 presets (scripts/map_reach.py).  The pieces below cover those bands
 * with some room, and each side band also covers the picture's own faded
 * edge (8 texels on the left, 16 on the right) so the extension joins clean
 * picture.  They are packed into
 * one 256x128 16-colour texture in the map's own palette, stored compressed in
 * the blob (LZ, the DS BIOS's format) and unpacked once into the variables.
 * While the map is on screen the texture is copied to texture memory
 * 0x26000-0x29FFF, the unused lower part of a texture the map screen does not
 * draw from (checked empty for all 22 areas).  After the game draws the map's
 * main piece (texture coordinates 0,0..408,256), each piece is drawn as a quad
 * in the same coordinates, so it pans and zooms with the map. */

/* picture x0, y0, x1, y1, then where it sits in the texture: x, y.
   map_art_pack.py reads this table: keep one piece a line. */
#define MAP_ART_PIECES 12
static const short map_art_piece[MAP_ART_PIECES][6] = {
    /* PIECES BEGIN */
    { -48, 0, 8, 128, 0, 0 },           /* left */
    { -48, 128, 8, 256, 56, 0 },
    { -48, 256, 8, 304, 192, 0 },
    { 392, 0, 432, 128, 112, 0 },       /* right (its fade starts about 13 texels from the end) */
    { 392, 128, 432, 256, 152, 0 },
    { 392, 256, 432, 304, 192, 48 },
    { 8, 300, 72, 304, 192, 96 },       /* below */
    { 72, 300, 136, 304, 192, 100 },
    { 136, 300, 200, 304, 192, 104 },
    { 200, 300, 264, 304, 192, 108 },
    { 264, 300, 328, 304, 192, 112 },
    { 328, 300, 392, 304, 192, 116 },
    /* PIECES END */
};

__asm__(".section .rodata\n.balign 4\nmap_art_lz:\n"
        ".incbin \"map_art.lz\"\n.text\n");   /* from the build folder: patch.py compiles there */
extern const u8 map_art_lz[];

#define MAP_ART_ADDR    0x26000
#define MAP_ART_LCDC    ((u32 *)(0x06800000 + MAP_ART_ADDR))   /* bank B is texture 0x20000-0x3FFFF */
#define MAP_ART_IMAGE   (((MAP_ART_ADDR) >> 3) | (5 << 20) | (4 << 23) | (3u << 26))   /* 256x128, 16 colours, opaque */
#define MAP_IMAGE       0x2EE00000u
#ifndef MAP_ART_Z
#define MAP_ART_Z       16              /* depth offset (vertex z, 4.12) */
#endif     /* the game's map texture: 512x256, 16 colours, @0 */

static u32 map_art_tex[4096];           /* unpacked, 16 KB (a variable: outside the blob) */
static u32 map_art_seen, map_art_up;    /* seen: frame_no + 1 when the map was last drawn, 0 = never */
static u8 map_art_ready;

/* LZ as the DS BIOS has it (header: size << 8 | 0x10; then a flag byte before
   every 8 items, high bit first: 0 = one byte, 1 = two bytes, 4 bits length - 3
   and 12 bits distance - 1).  Into main RAM only: VRAM drops byte writes. */
static SMALL void lz_unpack(const u8 *s, u8 *d)
{
    u8 *end = d + ((s[1] | s[2] << 8 | s[3] << 16));
    s += 4;
    while (d < end) {
        u32 flags = *s++;
        for (int k = 0; k < 8 && d < end; k++, flags <<= 1) {
            if (flags & 0x80) {
                u32 a = *s++, b = *s++;
                const u8 *from = d - ((a & 15) << 8 | b) - 1;
                for (int n = (a >> 4) + 3; n > 0 && d < end; n--)
                    *d++ = *from++;
            } else {
                *d++ = *s++;
            }
        }
    }
}

static SMALL void map_art_frame(void)
{
    /* never seen, or off the map for half a second: upload again next time.  (0 = never:
       frame_no is near 0 after a boot or a state load, and the art must not be written
       into texture memory another screen is using) */
    if (!map_art_seen || map_art_seen + 29 < frame_no) {
        map_art_up = 0;
        return;
    }
    if (map_art_up || map_art_seen + 1 < frame_no)
        return;
    if (!map_art_ready) {                   /* the first time the map is shown: unpack (once) */
        lz_unpack(map_art_lz, (u8 *)map_art_tex);
        map_art_ready = 1;
        return;
    }
    ov_safe(24);
    u8 old = VRAMCNT_B;
    VRAMCNT_B = 0x80;                       /* map to the CPU while we write */
    u32 *d = (u32 *)(0x06820000 + (MAP_ART_ADDR - 0x20000));
    for (int i = 0; i < 4096; i++)
        d[i] = map_art_tex[i];
    VRAMCNT_B = old;
    map_art_up = 1;
}

static SMALL int map_art_quad(int *q)
{
    if (wide_x == 4096 || !tree_big)
        return 0;
    if (q[0] || q[1] || q[6] != 408 << 12 || q[7] != 256 << 12)
        return 0;
    map_art_seen = frame_no + 1;
    if (!map_art_up)
        return 1;
    const short *h = (const short *)q;
    int x0 = h[4], y0 = h[5];
    int xr = h[3 * 6 + 4] - x0, yr = h[3 * 6 + 5] - y0;   /* along s: 408 texels */
    int xd = h[1 * 6 + 4] - x0, yd = h[1 * 6 + 5] - y0;   /* along t: 256 texels */
    /* per texel, in 1/4096 units (sdiv: Thumb has no divide by a constant without a library) */
    int sx = sdiv(xr << 12, 408), sy = sdiv(yr << 12, 408), tx = xd << 4, ty = yd << 4;
    GX(G_TEXIMAGE) = MAP_ART_IMAGE;
    for (int i = 0; i < MAP_ART_PIECES; i++) {
        const short *p = map_art_piece[i];
        int px[2] = { p[0], p[2] }, py[2] = { p[1], p[3] };
        int ax0 = p[4], ay0 = p[5], aw = p[2] - p[0], ah = p[3] - p[1];
        /* corners top left, bottom left, bottom right, top right */
        static const u8 cu[4] = { 0, 0, 1, 1 }, cv[4] = { 0, 1, 1, 0 };
        for (int k = 0; k < 4; k++) {
            int u = px[cu[k]], v = py[cv[k]];
            int x = x0 + ((u * sx + v * tx) >> 12);
            int y = y0 + ((u * sy + v * ty) >> 12);
            /* as still_vertex, but a hair nearer than the map: where a piece lies over
               the picture's faded end it must win the depth test (equal depth loses) */
            GX(G_TEXCOORD) = (u32)((((ay0 + cv[k] * ah) << 4) << 16) | (((ax0 + cu[k] * aw) << 4) & 0xFFFF));
            GX(G_VTX16) = (u32)(((y & 0xFFFF) << 16) | (x & 0xFFFF));
            GX(G_VTX16) = MAP_ART_Z & 0xFFFF;
        }
    }
    GX(G_TEXIMAGE) = MAP_IMAGE;
    return 1;
}
