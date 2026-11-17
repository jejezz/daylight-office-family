"""Tiny SVG path rasterizer for Phosphor icons (paths only): parse -> flatten -> nonzero fill with supersampling.

  alpha = render_svg(svg_text, box_px, ss=4)   # numpy float32 array (box_px, box_px), values 0..1

Phosphor Duotone icons are two filled <path>s on a 256x256 viewBox: the first with opacity 0.2, the second opaque.
"""
import math
import re

import numpy as np

VERSION = 'r1'   # bump when the rendering changes (invalidates the on-disk cache of rendered glyphs)

_TOKEN = re.compile(r'([MmLlHhVvCcSsQqTtAaZz])|(-?(?:\d+\.?\d*|\.\d+)(?:[eE][-+]?\d+)?)')


def _numbers(tokens, i, n):
    vals = []
    while len(vals) < n and i < len(tokens) and tokens[i][1] is not None:
        vals.append(float(tokens[i][1]))
        i += 1
    if len(vals) < n:
        raise ValueError('path data ended early')
    return vals, i


def _arc_points(x0, y0, rx, ry, phi_deg, fa, fs, x1, y1):
    if rx == 0 or ry == 0 or (x0 == x1 and y0 == y1):
        return [(x1, y1)]
    rx, ry = abs(rx), abs(ry)
    phi = math.radians(phi_deg)
    cp, sp = math.cos(phi), math.sin(phi)
    dx, dy = (x0 - x1) / 2, (y0 - y1) / 2
    x1p, y1p = cp * dx + sp * dy, -sp * dx + cp * dy
    lam = (x1p ** 2) / (rx ** 2) + (y1p ** 2) / (ry ** 2)
    if lam > 1:
        s = math.sqrt(lam)
        rx, ry = rx * s, ry * s
    num = rx ** 2 * ry ** 2 - rx ** 2 * y1p ** 2 - ry ** 2 * x1p ** 2
    den = rx ** 2 * y1p ** 2 + ry ** 2 * x1p ** 2
    co = math.sqrt(max(0.0, num / den)) if den else 0.0
    if fa == fs:
        co = -co
    cxp, cyp = co * rx * y1p / ry, -co * ry * x1p / rx
    cx, cy = cp * cxp - sp * cyp + (x0 + x1) / 2, sp * cxp + cp * cyp + (y0 + y1) / 2

    def ang(ux, uy, vx, vy):
        a = math.atan2(ux * vy - uy * vx, ux * vx + uy * vy)
        return a

    t1 = ang(1, 0, (x1p - cxp) / rx, (y1p - cyp) / ry)
    dt = ang((x1p - cxp) / rx, (y1p - cyp) / ry, (-x1p - cxp) / rx, (-y1p - cyp) / ry)
    if not fs and dt > 0:
        dt -= 2 * math.pi
    elif fs and dt < 0:
        dt += 2 * math.pi
    steps = max(4, int(abs(dt) / math.radians(4)) + 1)
    pts = []
    for k in range(1, steps + 1):
        t = t1 + dt * k / steps
        px = cx + rx * math.cos(t) * cp - ry * math.sin(t) * sp
        py = cy + rx * math.cos(t) * sp + ry * math.sin(t) * cp
        pts.append((px, py))
    pts[-1] = (x1, y1)
    return pts


def _bezier(p0, p1, p2, p3, n=18):
    out = []
    for k in range(1, n + 1):
        t = k / n
        u = 1 - t
        out.append((u ** 3 * p0[0] + 3 * u * u * t * p1[0] + 3 * u * t * t * p2[0] + t ** 3 * p3[0],
                    u ** 3 * p0[1] + 3 * u * u * t * p1[1] + 3 * u * t * t * p2[1] + t ** 3 * p3[1]))
    return out


def parse_path(d):
    """Returns a list of closed polygons (lists of (x, y))."""
    tokens = []
    # arc flags can be glued to the next number ("0 01-40"): handled when the command is 'a'/'A'
    for m in _TOKEN.finditer(d):
        tokens.append((m.group(1), m.group(2)))
    polys, cur = [], []
    x = y = sx = sy = 0.0
    lcx = lcy = None   # last cubic control for S
    lqx = lqy = None   # last quad control for T
    cmd = None
    i = 0
    while i < len(tokens):
        c, num = tokens[i]
        if c:
            cmd = c
            i += 1
            if cmd in 'Zz':
                if cur:
                    polys.append(cur)
                cur = []
                x, y = sx, sy
                lcx = lcy = lqx = lqy = None
                continue
        elif cmd is None:
            raise ValueError('number before command')
        rel = cmd.islower()
        C = cmd.upper()
        if C == 'M':
            (a, b), i = _numbers(tokens, i, 2)
            x, y = (x + a, y + b) if rel else (a, b)
            if cur:
                polys.append(cur)
            cur = [(x, y)]
            sx, sy = x, y
            cmd = 'l' if rel else 'L'
            lcx = lcy = lqx = lqy = None
        elif C == 'L':
            (a, b), i = _numbers(tokens, i, 2)
            x, y = (x + a, y + b) if rel else (a, b)
            cur.append((x, y)); lcx = lcy = lqx = lqy = None
        elif C == 'H':
            (a,), i = _numbers(tokens, i, 1)
            x = x + a if rel else a
            cur.append((x, y)); lcx = lcy = lqx = lqy = None
        elif C == 'V':
            (a,), i = _numbers(tokens, i, 1)
            y = y + a if rel else a
            cur.append((x, y)); lcx = lcy = lqx = lqy = None
        elif C == 'C':
            v, i = _numbers(tokens, i, 6)
            if rel:
                v = [v[0] + x, v[1] + y, v[2] + x, v[3] + y, v[4] + x, v[5] + y]
            cur.extend(_bezier((x, y), (v[0], v[1]), (v[2], v[3]), (v[4], v[5])))
            lcx, lcy = v[2], v[3]; lqx = lqy = None
            x, y = v[4], v[5]
        elif C == 'S':
            v, i = _numbers(tokens, i, 4)
            if rel:
                v = [v[0] + x, v[1] + y, v[2] + x, v[3] + y]
            c1 = (2 * x - lcx, 2 * y - lcy) if lcx is not None else (x, y)
            cur.extend(_bezier((x, y), c1, (v[0], v[1]), (v[2], v[3])))
            lcx, lcy = v[0], v[1]; lqx = lqy = None
            x, y = v[2], v[3]
        elif C == 'Q':
            v, i = _numbers(tokens, i, 4)
            if rel:
                v = [v[0] + x, v[1] + y, v[2] + x, v[3] + y]
            q0, q1, q2 = (x, y), (v[0], v[1]), (v[2], v[3])
            c1 = (q0[0] + 2 / 3 * (q1[0] - q0[0]), q0[1] + 2 / 3 * (q1[1] - q0[1]))
            c2 = (q2[0] + 2 / 3 * (q1[0] - q2[0]), q2[1] + 2 / 3 * (q1[1] - q2[1]))
            cur.extend(_bezier(q0, c1, c2, q2))
            lqx, lqy = v[0], v[1]; lcx = lcy = None
            x, y = v[2], v[3]
        elif C == 'T':
            (a, b), i = _numbers(tokens, i, 2)
            ex, ey = (x + a, y + b) if rel else (a, b)
            q1 = (2 * x - lqx, 2 * y - lqy) if lqx is not None else (x, y)
            q0, q2 = (x, y), (ex, ey)
            c1 = (q0[0] + 2 / 3 * (q1[0] - q0[0]), q0[1] + 2 / 3 * (q1[1] - q0[1]))
            c2 = (q2[0] + 2 / 3 * (q1[0] - q2[0]), q2[1] + 2 / 3 * (q1[1] - q2[1]))
            cur.extend(_bezier(q0, c1, c2, q2))
            lqx, lqy = q1; lcx = lcy = None
            x, y = ex, ey
        elif C == 'A':
            (rx, ry, rot), i = _numbers(tokens, i, 3)
            # flags: single digits, possibly glued to the following number
            flags = []
            while len(flags) < 2:
                cc, nn = tokens[i]
                if nn is None:
                    raise ValueError('arc flag expected')
                if nn[0] in '01' and (len(nn) == 1 or nn[1] in '.-0123456789' ):
                    flags.append(int(nn[0]))
                    rest = nn[1:]
                    if rest:
                        tokens[i] = (None, rest)
                    else:
                        i += 1
                else:
                    raise ValueError('bad arc flag ' + nn)
            (a, b), i = _numbers(tokens, i, 2)
            ex, ey = (x + a, y + b) if rel else (a, b)
            cur.extend(_arc_points(x, y, rx, ry, rot, flags[0], flags[1], ex, ey))
            x, y = ex, ey
            lcx = lcy = lqx = lqy = None
        else:
            raise ValueError('unsupported command ' + cmd)
    if cur:
        polys.append(cur)
    return polys


def fill_nonzero(polys, size, ss=4):
    """Coverage mask (size x size, float32) of the polygons (already in pixel coordinates), nonzero winding."""
    n = size * ss
    xs = (np.arange(n, dtype=np.float32) + 0.5) / ss
    gx, gy = np.meshgrid(xs, xs)
    gx, gy = gx.ravel(), gy.ravel()
    wn = np.zeros(gx.shape, dtype=np.int16)
    edges = []
    for poly in polys:
        pts = poly + [poly[0]]
        for a, b in zip(pts[:-1], pts[1:]):
            if a[1] != b[1]:
                edges.append((a[0], a[1], b[0], b[1]))
    e = np.array(edges, dtype=np.float32)
    for s in range(0, len(e), 48):
        ch = e[s:s + 48]
        x0, y0, x1, y1 = (ch[:, k][None, :] for k in range(4))
        Y, X = gy[:, None], gx[:, None]
        up = (y0 <= Y) & (y1 > Y)
        down = (y0 > Y) & (y1 <= Y)
        cross = (x1 - x0) * (Y - y0) - (X - x0) * (y1 - y0)
        wn += (up & (cross > 0)).sum(axis=1, dtype=np.int16) - (down & (cross < 0)).sum(axis=1, dtype=np.int16)
    inside = (wn != 0).reshape(n, n).astype(np.float32)
    return inside.reshape(size, ss, size, ss).mean(axis=(1, 3))


def render_svg(svg_text, box_px, ss=4):
    """Alpha (box_px x box_px) of a Phosphor SVG; paths composited 'over' with their own opacity."""
    if re.search(r'<(polygon|polyline|rect|circle|ellipse|line)\b', svg_text):
        raise ValueError('this renderer only draws <path> elements; the icon uses another shape element')
    vb = re.search(r'viewBox="([^"]+)"', svg_text).group(1).split()
    vbw = float(vb[2])
    scale = box_px / vbw
    out = np.zeros((box_px, box_px), dtype=np.float32)
    for m in re.finditer(r'<path\b([^>]*)/?>', svg_text):
        attrs = m.group(1)
        d = re.search(r'\sd="([^"]+)"', ' ' + attrs).group(1)
        op = re.search(r'\sopacity="([^"]+)"', ' ' + attrs)
        opacity = float(op.group(1)) if op else 1.0
        polys = [[(px * scale, py * scale) for px, py in poly] for poly in parse_path(d)]
        mask = fill_nonzero(polys, box_px, ss) * opacity
        out = out + mask * (1 - out)
    return out
