"""Placeholder brand art (sun mark + pixel-font wordmark) generated without external libraries.

Real artwork can replace any of it: put files with the same names into assets/brand/ (see apply.py).
  logo_<theme>_<W>x<H>.png   tab-bar wordmark, theme = dark (white text) | light (dark text)
  app.ico                    application icon (BMP images up to 128 px, PNG for 256 px)
"""
import math
import struct
import zlib

FONT = {
    'A': ["0110", "1001", "1001", "1111", "1001", "1001", "1001"],
    'D': ["1110", "1001", "1001", "1001", "1001", "1001", "1110"],
    'G': ["0111", "1000", "1000", "1011", "1001", "1001", "0111"],
    'H': ["1001", "1001", "1001", "1111", "1001", "1001", "1001"],
    'I': ["111", "010", "010", "010", "010", "010", "111"],
    'L': ["1000", "1000", "1000", "1000", "1000", "1000", "1111"],
    'T': ["11111", "00100", "00100", "00100", "00100", "00100", "00100"],
    'Y': ["1001", "1001", "0110", "0110", "0100", "0100", "0100"],
}


def _chunk(t, d):
    c = struct.pack('>I', len(d)) + t + d
    return c + struct.pack('>I', zlib.crc32(t + d) & 0xffffffff)


def logo_png(w, h, theme, text='DAYLIGHT'):
    """Palette PNG (tiny, so it fits the original Qt resource slot). Logical canvas 85x20, point-sampled."""
    fg = (255, 255, 255) if theme == 'dark' else (68, 68, 68)
    f = w / 85.0
    canvas = [[0] * 85 for _ in range(20)]
    for y in range(20):
        for x in range(85):
            d = math.hypot(x + 0.5 - 10, y + 0.5 - 10)
            if d <= 4.2:
                canvas[y][x] = 1
            elif 6 <= d <= 8:
                ang = math.degrees(math.atan2(y + 0.5 - 10, x + 0.5 - 10)) % 360
                if any(abs(((ang - a + 180) % 360) - 180) < 9 for a in range(0, 360, 45)):
                    canvas[y][x] = 1
    x0 = 22
    for ch in text.upper():
        g = FONT[ch]
        for r, row in enumerate(g):
            for c, v in enumerate(row):
                if v == '1':
                    canvas[6 + r][x0 + c] = 2
        x0 += len(g[0]) + 2
    pix = [canvas[min(19, int((y + 0.5) / f))][min(84, int((x + 0.5) / f))] for y in range(h) for x in range(w)]
    pal = [(0, 0, 0, 0), (245, 184, 46, 255), fg + (255,)]
    raw = b''.join(b'\x00' + bytes(pix[y * w:(y + 1) * w]) for y in range(h))
    return (b'\x89PNG\r\n\x1a\n' + _chunk(b'IHDR', struct.pack('>IIBBBBB', w, h, 8, 3, 0, 0, 0))
            + _chunk(b'PLTE', b''.join(bytes(c[:3]) for c in pal)) + _chunk(b'tRNS', bytes(c[3] for c in pal))
            + _chunk(b'IDAT', zlib.compress(raw, 9)) + _chunk(b'IEND', b''))


def _raster_icon(n):
    ss = 4
    teal, sun = (31, 111, 92), (245, 184, 46)
    cx = cy = n / 2.0
    rows = []
    for py in range(n):
        row = []
        for px in range(n):
            r = g = b = cnt = 0
            for sy in range(ss):
                for sx in range(ss):
                    x = px + (sx + .5) / ss
                    y = py + (sy + .5) / ss
                    rr = n * 0.22
                    dx = max(abs(x - cx) - (n / 2 - rr), 0)
                    dy = max(abs(y - cy) - (n / 2 - rr), 0)
                    if dx * dx + dy * dy > rr * rr:
                        continue
                    col = teal
                    d = math.hypot(x - cx, y - cy) / n
                    ang = math.degrees(math.atan2(y - cy, x - cx)) % 360
                    if d <= 0.19:
                        col = sun
                    elif 0.27 <= d <= 0.38 and min(abs((ang - a + 180) % 360 - 180) for a in range(0, 360, 45)) < 7:
                        col = sun
                    r += col[0]; g += col[1]; b += col[2]; cnt += 1
            row.append((r // cnt, g // cnt, b // cnt, cnt * 255 // (ss * ss)) if cnt else (0, 0, 0, 0))
        rows.append(row)
    return rows


def app_ico():
    """ICO with BMP (DIB) images for <=128 px and PNG for 256 px (small PNG entries are not accepted in PE resources)."""
    sizes = [16, 24, 32, 48, 64, 128, 256]
    imgs = []
    for n in sizes:
        px = _raster_icon(n)
        if n == 256:
            raw = b''.join(b'\x00' + b''.join(bytes(p) for p in row) for row in px)
            imgs.append(b'\x89PNG\r\n\x1a\n' + _chunk(b'IHDR', struct.pack('>IIBBBBB', n, n, 8, 6, 0, 0, 0))
                        + _chunk(b'IDAT', zlib.compress(raw, 9)) + _chunk(b'IEND', b''))
        else:
            hdr = struct.pack('<IiiHHIIiiII', 40, n, 2 * n, 1, 32, 0, 0, 0, 0, 0, 0)
            body = b''.join(b''.join(bytes((p[2], p[1], p[0], p[3])) for p in row) for row in reversed(px))
            mask = (b'\x00' * (((n + 31) // 32) * 4)) * n
            imgs.append(hdr + body + mask)
    head = struct.pack('<HHH', 0, 1, len(sizes))
    off = 6 + 16 * len(sizes)
    ent = data = b''
    for n, im in zip(sizes, imgs):
        ent += struct.pack('<BBBBHHII', 0 if n == 256 else n, 0 if n == 256 else n, 0, 0, 1, 32, len(im), off + len(data))
        data += im
    return head + ent + data


def about_symbol():
    """SVG <symbol> that replaces the shell About logo (id idx-logo, viewBox 52x45)."""
    return ('<symbol id="idx-logo" width="52" height="45" viewBox="0 0 52 45" fill="none">'
            '<circle cx="26" cy="22.5" r="11" fill="#f5b82e"/>'
            '<g stroke="#f5b82e" stroke-width="3" stroke-linecap="round">'
            '<path d="M26 4v5M26 36v5M7 22.5h5M40 22.5h5M12.5 9l3.5 3.5M36 32.5l3.5 3.5M39.5 9L36 12.5M16 32.5L12.5 36"/></g></symbol>')
