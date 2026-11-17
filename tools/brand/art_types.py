"""Placeholder file-type icons (Explorer icons of associated documents): page with a folded corner,
a small sun, and a colored band carrying the extension in a 5x7 pixel font. No external libraries.
Real artwork can replace any icon: assets/brand/types/<ext>.ico (see make_type_icons.py)."""
import math
import struct

_FONT_SRC = {
    'A': "01110 10001 10001 11111 10001 10001 10001", 'B': "11110 10001 10001 11110 10001 10001 11110",
    'C': "01110 10001 10000 10000 10000 10001 01110", 'D': "11110 10001 10001 10001 10001 10001 11110",
    'E': "11111 10000 10000 11110 10000 10000 11111", 'F': "11111 10000 10000 11110 10000 10000 10000",
    'G': "01110 10001 10000 10111 10001 10001 01111", 'H': "10001 10001 10001 11111 10001 10001 10001",
    'I': "01110 00100 00100 00100 00100 00100 01110", 'J': "00111 00010 00010 00010 00010 10010 01100",
    'K': "10001 10010 10100 11000 10100 10010 10001", 'L': "10000 10000 10000 10000 10000 10000 11111",
    'M': "10001 11011 10101 10101 10001 10001 10001", 'N': "10001 11001 10101 10011 10001 10001 10001",
    'O': "01110 10001 10001 10001 10001 10001 01110", 'P': "11110 10001 10001 11110 10000 10000 10000",
    'Q': "01110 10001 10001 10001 10101 10010 01101", 'R': "11110 10001 10001 11110 10100 10010 10001",
    'S': "01111 10000 10000 01110 00001 00001 11110", 'T': "11111 00100 00100 00100 00100 00100 00100",
    'U': "10001 10001 10001 10001 10001 10001 01110", 'V': "10001 10001 10001 10001 10001 01010 00100",
    'W': "10001 10001 10001 10101 10101 11011 10001", 'X': "10001 10001 01010 00100 01010 10001 10001",
    'Y': "10001 10001 01010 00100 00100 00100 00100", 'Z': "11111 00001 00010 00100 01000 10000 11111",
    '0': "01110 10001 10011 10101 11001 10001 01110", '1': "00100 01100 00100 00100 00100 00100 01110",
    '2': "01110 10001 00001 00010 00100 01000 11111", '3': "11110 00001 00001 01110 00001 00001 11110",
    '4': "00010 00110 01010 10010 11111 00010 00010", '5': "11111 10000 11110 00001 00001 10001 01110",
    '6': "00110 01000 10000 11110 10001 10001 01110", '7': "11111 00001 00010 00100 01000 01000 01000",
    '8': "01110 10001 10001 01110 10001 10001 01110", '9': "01110 10001 10001 01111 00001 00010 01100",
}
FONT5 = {k: v.split() for k, v in _FONT_SRC.items()}

CAT_COLORS = {  # own palette: app colors from UX-DESIGN (blue / green / orange) plus red for PDF-like formats
    'word': (59, 125, 221), 'cell': (46, 158, 91), 'slide': (232, 134, 58),
    'pdf': (217, 83, 79), 'draw': (111, 99, 190), 'other': (110, 118, 132),
}


def _raster(n, ext, cat):
    ss = 3 if n <= 64 else 2
    col = CAT_COLORS.get(cat, CAT_COLORS['other'])
    dark = tuple(int(c * 0.72) for c in col)
    text = ext.upper()[:5]
    show_text = n >= 48
    x0, x1, y0, y1 = 0.18 * n, 0.82 * n, 0.07 * n, 0.93 * n
    rr, fold = 0.07 * n, 0.22 * n
    by0, by1 = 0.50 * n, 0.80 * n
    glyph_w = len(text) * 6 - 1
    cell = (0.60 * n) / max(glyph_w, 12)
    tx0 = (n - glyph_w * cell) / 2
    ty0 = by0 + (by1 - by0 - 7 * cell) / 2
    sun_c = (0.36 * n, 0.30 * n)
    rows = []
    for py in range(n):
        row = []
        for px in range(n):
            r = g = b = a = 0
            for sy in range(ss):
                for sx in range(ss):
                    x = px + (sx + .5) / ss
                    y = py + (sy + .5) / ss
                    dx = max(abs(x - (x0 + x1) / 2) - ((x1 - x0) / 2 - rr), 0)
                    dy = max(abs(y - (y0 + y1) / 2) - ((y1 - y0) / 2 - rr), 0)
                    if dx * dx + dy * dy > rr * rr:
                        continue
                    in_corner = x > x1 - fold and y < y0 + fold
                    u = (x - (x1 - fold)) + (y - y0)          # diagonal of the folded corner
                    if in_corner and u < 0:
                        continue                              # cut-away triangle
                    c = dark if (in_corner and u >= 0 and u < fold) else (247, 249, 252)
                    d = math.hypot(x - sun_c[0], y - sun_c[1])
                    ang = math.degrees(math.atan2(y - sun_c[1], x - sun_c[0])) % 360
                    if d <= 0.085 * n or (0.12 * n <= d <= 0.15 * n and (ang % 45) < 11):
                        c = (245, 184, 46)
                    if by0 <= y <= by1:
                        c = col
                        if show_text:
                            gx, gy = int((x - tx0) / cell), int((y - ty0) / cell)
                            if 0 <= gy < 7 and 0 <= gx < glyph_w and gx % 6 != 5:
                                glyph = FONT5.get(text[gx // 6])
                                if glyph and glyph[gy][gx % 6] == '1':
                                    c = (255, 255, 255)
                    r += c[0]; g += c[1]; b += c[2]; a += 255
            k = ss * ss
            row.append((r * 255 // a, g * 255 // a, b * 255 // a, a // k) if a else (0, 0, 0, 0))
        rows.append(row)
    return rows


def type_ico(ext, cat):
    """ICO for one file type; BMP images only (16..128 px), cheap to generate."""
    sizes = [16, 24, 32, 48, 64, 128]
    imgs = []
    for n in sizes:
        px = _raster(n, ext, cat)
        hdr = struct.pack('<IiiHHIIiiII', 40, n, 2 * n, 1, 32, 0, 0, 0, 0, 0, 0)
        body = b''.join(b''.join(bytes((p[2], p[1], p[0], p[3])) for p in row) for row in reversed(px))
        imgs.append(hdr + body + (b'\x00' * (((n + 31) // 32) * 4)) * n)
    head = struct.pack('<HHH', 0, 1, len(sizes))
    off = 6 + 16 * len(sizes)
    ent = data = b''
    for n, im in zip(sizes, imgs):
        ent += struct.pack('<BBBBHHII', n, n, 0, 0, 1, 32, len(im), off + len(data))
        data += im
    return head + ent + data
