"""Tiny drawing kit for hand-made icons in the Phosphor Duotone style (256 x 256 box, 16 unit outline, 20 % under-layer).

Everything is built from polygons so orientation is under control: additive shapes are clockwise (positive area),
holes counter-clockwise, and the renderer's nonzero fill then gives unions and cut-outs for free.

A layer is (polygons, opacity). An icon is a list of layers, drawn in order with 'over' compositing.
"""
import math
import os
import re
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import raster  # noqa: E402

SW = 16        # regular outline weight
THIN = 12      # secondary lines (text lines, grid lines)
LIGHT = 0.2    # the Duotone under-layer opacity
DIM = 0.45     # de-emphasized strokes


def area(p):
    s = 0.0
    for i in range(len(p)):
        x1, y1 = p[i]
        x2, y2 = p[(i + 1) % len(p)]
        s += x1 * y2 - x2 * y1
    return s / 2


def cw(p):
    return p if area(p) > 0 else p[::-1]


def ccw(p):
    return p if area(p) < 0 else p[::-1]


def _arc(cx, cy, r, a0, a1, n):
    return [(cx + r * math.cos(math.radians(a0 + (a1 - a0) * k / n)),
             cy + r * math.sin(math.radians(a0 + (a1 - a0) * k / n))) for k in range(n + 1)]


def rrect(x, y, w, h, r=0, n=8):
    r = min(r, w / 2, h / 2)
    if r <= 0.01:
        return cw([(x, y), (x + w, y), (x + w, y + h), (x, y + h)])
    pts = []
    for cx, cy, a0 in ((x + w - r, y + r, -90), (x + w - r, y + h - r, 0), (x + r, y + h - r, 90), (x + r, y + r, 180)):
        pts += _arc(cx, cy, r, a0, a0 + 90, n)
    return cw(pts)


def circle(cx, cy, r, n=48):
    return cw(_arc(cx, cy, r, 0, 360, n)[:-1])


def capsule(x1, y1, x2, y2, w, n=8):
    a = math.degrees(math.atan2(y2 - y1, x2 - x1))
    h = w / 2
    pts = _arc(x2, y2, h, a - 90, a + 90, n) + _arc(x1, y1, h, a + 90, a + 270, n)
    return cw(pts)


def stroke(points, w=SW, closed=False):
    """Polyline with round joins/caps as a list of polygons (union through nonzero fill)."""
    segs = list(zip(points[:-1], points[1:]))
    if closed:
        segs.append((points[-1], points[0]))
    return [capsule(a[0], a[1], b[0], b[1], w) for a, b in segs]


def dashed(x1, y1, x2, y2, w=THIN, dash=24, gap=20):
    length = math.hypot(x2 - x1, y2 - y1)
    ux, uy = (x2 - x1) / length, (y2 - y1) / length
    out, t = [], 0.0
    while t < length:
        e = min(t + dash, length)
        out.append(capsule(x1 + ux * t, y1 + uy * t, x1 + ux * e, y1 + uy * e, w))
        t = e + gap
    return out


def polygon(points):
    return [cw(points)]


def frame(x, y, w, h, r=14, sw=SW):
    return [rrect(x, y, w, h, r), ccw(rrect(x + sw, y + sw, w - 2 * sw, h - 2 * sw, max(r - sw, 0)))]


def box(x, y, w, h, r=14):
    return [rrect(x, y, w, h, r)]


def ring(cx, cy, ro, ri):
    return [circle(cx, cy, ro), ccw(circle(cx, cy, ri))]


def disc(cx, cy, r):
    return [circle(cx, cy, r)]


def chevron(cx, cy, size, direction, w=THIN):
    """Open arrow head ( > ) pointing up/down/left/right, centered at (cx, cy)."""
    s = size
    pts = {'up': [(cx - s, cy + s / 2), (cx, cy - s / 2), (cx + s, cy + s / 2)],
           'down': [(cx - s, cy - s / 2), (cx, cy + s / 2), (cx + s, cy - s / 2)],
           'left': [(cx + s / 2, cy - s), (cx - s / 2, cy), (cx + s / 2, cy + s)],
           'right': [(cx - s / 2, cy - s), (cx + s / 2, cy), (cx - s / 2, cy + s)]}[direction]
    return stroke(pts, w)


def arrow(x1, y1, x2, y2, head=26, w=THIN):
    a = math.atan2(y2 - y1, x2 - x1)
    out = stroke([(x1, y1), (x2, y2)], w)
    for d in (150, -150):
        ax = x2 + head * math.cos(a + math.radians(d))
        ay = y2 + head * math.sin(a + math.radians(d))
        out += stroke([(x2, y2), (ax, ay)], w)
    return out


# ---- reuse of Phosphor glyphs (flattened, then transformed) ---------------------------------------------------------
_PHOSPHOR = os.path.normpath(os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', '..', '..', 'assets', 'phosphor-duotone'))


def glyph(name, x=0, y=0, size=256, flip=False, rot=0):
    """Layers of a Phosphor icon placed with its 256 box at (x, y) scaled to `size` px (optionally mirrored/rotated)."""
    text = open(os.path.join(_PHOSPHOR, name + '.svg'), encoding='utf-8').read()
    k = size / 256.0
    layers = []
    for m in re.finditer(r'<path\b([^>]*)/?>', text):
        a = ' ' + m.group(1)
        d = re.search(r'\sd="([^"]+)"', a).group(1)
        op = re.search(r'\sopacity="([^"]+)"', a)
        polys = []
        for poly in raster.parse_path(d):
            out = []
            for px, py in poly:
                if flip:
                    px = 256 - px
                if rot:
                    r = math.radians(rot)
                    dx, dy = px - 128, py - 128
                    px, py = 128 + dx * math.cos(r) - dy * math.sin(r), 128 + dx * math.sin(r) + dy * math.cos(r)
                out.append((x + px * k, y + py * k))
            polys.append(out)
        layers.append((polys, float(op.group(1)) if op else 1.0))
    return layers


def transform(polys, sx=1.0, sy=1.0, tx=0.0, ty=0.0, rot=0.0, cx=128, cy=128):
    out = []
    r = math.radians(rot)
    for p in polys:
        q = []
        for x, y in p:
            dx, dy = (x - cx) * sx, (y - cy) * sy
            q.append((cx + tx + dx * math.cos(r) - dy * math.sin(r), cy + ty + dx * math.sin(r) + dy * math.cos(r)))
        out.append(q if (sx * sy) > 0 else q[::-1])
    return out


# ---- icon assembly -------------------------------------------------------------------------------------------------
def L(polys, opacity=1.0):
    return (polys, opacity)


def to_svg(layers):
    paths = []
    for polys, op in layers:
        d = ''.join('M' + 'L'.join(f'{x:.1f},{y:.1f}' for x, y in p) + 'Z' for p in polys if len(p) >= 3)
        if d:
            paths.append(f'<path d="{d}"' + (f' opacity="{op:g}"' if op != 1.0 else '') + '/>')
    return '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 256 256" fill="currentColor">' + ''.join(paths) + '</svg>'
