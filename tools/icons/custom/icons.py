"""Hand-made icons (those Phosphor has no counterpart for), generated from code so a whole family stays consistent.

ICONS maps a name to a list of layers (see dsl.py). apply.py reaches them through the mapping value "custom:<name>".
Add an icon: write a function below and register it; run tools/icons/custom/sheet.py to see all of them on one picture.
"""
import math

from dsl import (DIM, LIGHT, SW, THIN, L, arrow, box, capsule, chevron, circle, dashed, disc, frame, glyph, polygon, ring,
                 rrect, stroke, to_svg, transform)

ICONS = {}


def reg(name, layers):
    ICONS[name] = layers


# ---- border presets (3 x 3 grid) -----------------------------------------------------------------------------------
GX0, GY0, GS = 48, 48, 160


def _grid():
    x = [GX0 + GS * k / 3 for k in range(4)]
    y = [GY0 + GS * k / 3 for k in range(4)]
    return {'T': (x[0], y[0], x[3], y[0]), 'B': (x[0], y[3], x[3], y[3]), 'L': (x[0], y[0], x[0], y[3]), 'R': (x[3], y[0], x[3], y[3]),
            'H1': (x[0], y[1], x[3], y[1]), 'H2': (x[0], y[2], x[3], y[2]), 'V1': (x[1], y[0], x[1], y[3]), 'V2': (x[2], y[0], x[2], y[3])}


def border(emph, diag=None):
    light, strong = [], []
    for k, (a, b, c, d) in _grid().items():
        (strong if k in emph else light).append(capsule(a, b, c, d, SW if k in emph else THIN))
    layers = [L(light, 0.3), L(strong)]
    if diag == 'down':
        layers.append(L([capsule(GX0, GY0, GX0 + GS, GY0 + GS, SW)]))
    elif diag == 'up':
        layers.append(L([capsule(GX0, GY0 + GS, GX0 + GS, GY0, SW)]))
    return layers


ALL = ['T', 'B', 'L', 'R', 'H1', 'H2', 'V1', 'V2']
reg('border-all', border(ALL))
reg('border-out', border(['T', 'B', 'L', 'R']))
reg('border-inside', border(['H1', 'H2', 'V1', 'V2']))
reg('border-insidehor', border(['H1', 'H2']))
reg('border-insidevert', border(['V1', 'V2']))
reg('border-top', border(['T']))
reg('border-bottom', border(['B']))
reg('border-left', border(['L']))
reg('border-right', border(['R']))
reg('border-no', border([]))
reg('border-diagdown', border([], 'down'))
reg('border-diagup', border([], 'up'))
reg('border-style', [L([capsule(40, 72, 216, 72, SW)]),
                     L([c for x in (40, 104, 168) for c in [capsule(x, 128, x + 40, 128, SW)]]),
                     L([disc(x, 184, 9) for x in (48, 88, 128, 168, 208)])])
reg('freeze-panes', border(['V1', 'H1']))


# ---- paragraph borders (two stacked text blocks) -------------------------------------------------------------------
def para_border(emph):
    px0, py0, pw, ph = 48, 40, 160, 176
    edges = {'T': (px0, py0, px0 + pw, py0), 'B': (px0, py0 + ph, px0 + pw, py0 + ph), 'L': (px0, py0, px0, py0 + ph),
             'R': (px0 + pw, py0, px0 + pw, py0 + ph), 'D': (px0, py0 + ph / 2, px0 + pw, py0 + ph / 2)}
    light, strong = [], []
    for k, (a, b, c, d) in edges.items():
        (strong if k in emph else light).append(capsule(a, b, c, d, SW if k in emph else THIN))
    text = [capsule(76, y, x2, y, THIN) for y, x2 in ((76, 180), (100, 148), (156, 180), (180, 148))]
    return [L(light, 0.3), L(text, 0.7), L(strong)]


reg('paragraph-borders-all', para_border(['T', 'B', 'L', 'R', 'D']))
reg('paragraph-borders-outer', para_border(['T', 'B', 'L', 'R']))
reg('paragraph-borders-inner', para_border(['D']))
reg('paragraph-borders-none', para_border([]))
reg('paragraph-borders-top', para_border(['T']))
reg('paragraph-borders-bottom', para_border(['B']))
reg('paragraph-borders-left', para_border(['L']))
reg('paragraph-borders-right', para_border(['R']))


# ---- picture wrapping ----------------------------------------------------------------------------------------------
def star(cx, cy, r, n=5):
    pts = []
    for k in range(n * 2):
        a = math.radians(-90 + k * 180 / n)
        rr = r if k % 2 == 0 else r * 0.45
        pts.append((cx + rr * math.cos(a), cy + rr * math.sin(a)))
    return pts


def wrap(kind):
    ys = [48, 80, 112, 144, 176, 208]
    segs = []                  # text segments (y, x1, x2)
    shape, shape_op = [], []
    if kind == 'inline':
        for y in ys:
            if y == 112:
                segs += [(y, 32, 76), (y, 152, 224)]
            else:
                segs.append((y, 32, 224))
        return [L([capsule(x1, y, x2, y, THIN) for y, x1, x2 in segs]), L([rrect(88, 94, 56, 36, 8)], LIGHT),
                L([capsule(88, 130, 144, 130, THIN), capsule(88, 94, 144, 94, THIN)], 0.6)]
    if kind == 'square':
        for y in ys:
            segs += [(y, 32, 76), (y, 180, 224)] if y in (112, 144) else [(y, 32, 224)]
        return [L([capsule(x1, y, x2, y, THIN) for y, x1, x2 in segs]), L(frame(88, 92, 80, 80, 10, 12)), L([rrect(88, 92, 80, 80, 10)], LIGHT)]
    if kind == 'tight':
        for y in ys:
            segs += [(y, 32, 84), (y, 172, 224)] if y in (112, 144) else [(y, 32, 224)]
        return [L([capsule(x1, y, x2, y, THIN) for y, x1, x2 in segs]), L(ring(128, 128, 44, 32)), L([circle(128, 128, 44)], LIGHT)]
    if kind == 'through':
        for y in ys:
            segs += [(y, 32, 70), (y, 186, 224)] if y in (112, 144) else [(y, 32, 224)]
        return [L([capsule(x1, y, x2, y, THIN) for y, x1, x2 in segs]), L(stroke(star(128, 130, 62) , 12, closed=True)), L(polygon(star(128, 130, 62)), LIGHT)]
    if kind == 'topandbottom':
        for y in ys:
            if y in (48, 80, 176, 208):
                segs.append((y, 32, 224))
        return [L([capsule(x1, y, x2, y, THIN) for y, x1, x2 in segs]), L(frame(84, 104, 88, 48, 10, 12)), L([rrect(84, 104, 88, 48, 10)], LIGHT)]
    if kind == 'behind':
        return [L([rrect(84, 88, 88, 88, 10)], LIGHT), L(frame(84, 88, 88, 88, 10, 12), 0.35),
                L([capsule(32, y, 224, y, THIN) for y in ys])]
    if kind == 'infront':
        return [L([capsule(32, y, 224, y, THIN) for y in ys], 0.6), L([rrect(84, 88, 88, 88, 10)])]


for _k in ('inline', 'square', 'tight', 'through', 'topandbottom', 'behind', 'infront'):
    reg('wrap-' + _k, wrap(_k))
reg('wrap-topbottom', wrap('topandbottom'))
for _k in ('inline', 'square', 'tight', 'through', 'topandbottom', 'behind', 'infront'):
    reg('small-wrap-' + _k, wrap(_k))


# ---- page columns --------------------------------------------------------------------------------------------------
def columns(widths):
    page = [L(frame(40, 32, 176, 192, 16)), L([rrect(40, 32, 176, 192, 16)], LIGHT)]
    inner_x0, inner_x1, gap = 62, 194, 14
    total = sum(widths)
    avail = inner_x1 - inner_x0 - gap * (len(widths) - 1)
    x, lines = inner_x0, []
    for w in widths:
        cw_ = avail * w / total
        for y, shorten in ((72, 0), (100, 0), (128, 0), (156, 0), (184, 30)):
            lines.append(capsule(x, y, x + cw_ - shorten * min(1, cw_ / 60), y, THIN))
        x += cw_ + gap
    return page + [L(lines, 0.85)]


reg('columns-one', columns([1]))
reg('columns-two', columns([1, 1]))
reg('columns-three', columns([1, 1, 1]))
reg('columns-left', columns([1, 2]))
reg('columns-right', columns([2, 1]))


# ---- page placement (huge sheet) -----------------------------------------------------------------------------------
def page_frame():
    return [L(frame(56, 24, 144, 208, 14)), L([rrect(56, 24, 144, 208, 14)], LIGHT)]


def faint_lines(ys, x1=80, x2=176):
    return L([capsule(x1, y, x2, y, THIN) for y in ys], 0.35)


for _pos, _x in (('left', 76), ('center', 106), ('right', 136)):
    reg('page-number-top-' + _pos, page_frame() + [faint_lines((100, 132, 164)), L([rrect(_x, 46, 44, 18, 6)])])
    reg('page-number-bottom-' + _pos, page_frame() + [faint_lines((84, 116, 148)), L([rrect(_x, 192, 44, 18, 6)])])
for _pos, _x in (('left', 76), ('center', 98), ('right', 120)):
    reg('horizontal-line-' + _pos, page_frame() + [faint_lines((72, 104, 168, 200)), L([capsule(_x, 136, _x + 60, 136, SW)])])
for _pos, _x in (('left', 76), ('center', 92), ('right', 108)):
    reg('table-align-' + _pos, page_frame() + [faint_lines((60, 192)), L(frame(_x, 96, 72, 64, 6, 12)),
                                                  L([capsule(_x + 36, 96, _x + 36, 160, 10), capsule(_x, 128, _x + 72, 128, 10)])])
reg('page-portrait', [L(frame(72, 32, 112, 192, 14)), L([rrect(72, 32, 112, 192, 14)], LIGHT), faint_lines((96, 128, 160), 100, 156)])
reg('page-landscape', [L(frame(32, 72, 192, 112, 14)), L([rrect(32, 72, 192, 112, 14)], LIGHT), faint_lines((108, 136), 60, 196)])
reg('pageorient', [L(frame(36, 40, 96, 136, 12)), L([rrect(36, 40, 96, 136, 12)], LIGHT),
                   L(frame(104, 112, 120, 92, 12), 0.7), L([rrect(104, 112, 120, 92, 12)], 0.1)])
reg('pagesize', page_frame()[:1] + [L([rrect(56, 24, 144, 208, 14)], LIGHT), L(arrow(224, 56, 224, 200, 22, 12)), L(arrow(224, 200, 224, 56, 22, 12))])
reg('pagemargins', page_frame() + [L(dashed(84, 52, 172, 52, 10, 14, 12) + dashed(84, 204, 172, 204, 10, 14, 12) +
                                    dashed(84, 52, 84, 204, 10, 14, 12) + dashed(172, 52, 172, 204, 10, 14, 12), 0.55),
                                   faint_lines((96, 128, 160), 100, 156)])
reg('pagebreak', [L(stroke([(64, 120), (64, 40), (192, 40), (192, 120)], SW)), L(stroke([(64, 136), (64, 216), (192, 216), (192, 136)], SW)),
                  L(dashed(32, 128, 224, 128, 12, 22, 16), 0.6), L([rrect(64, 40, 128, 80, 6)], LIGHT)])
reg('line-numbering', [L([capsule(52, y, 52, y + 14, 12) for y in (52, 108, 164)] + [capsule(84, y, 216, y, THIN) for y in (60, 92, 116, 148, 172, 204)]),
                       L([capsule(84, y, 216, y, THIN) for y in ()])])
reg('line-numbering-rtl', [L([capsule(204, y, 204, y + 14, 12) for y in (52, 108, 164)] + [capsule(40, y, 172, y, THIN) for y in (60, 92, 116, 148, 172, 204)])])
reg('hyphenation', [L([capsule(40, 60, 216, 60, THIN), capsule(40, 100, 188, 100, THIN), capsule(40, 156, 150, 156, THIN), capsule(40, 196, 216, 196, THIN)]),
                    L([capsule(196, 100, 220, 100, SW)], 0.9)])
reg('watermark', page_frame() + [L(stroke([(96, 184), (128, 84), (160, 184)], 18) + [capsule(108, 152, 148, 152, 16)], 0.45)])
reg('dropcap', [L([rrect(40, 44, 72, 72, 10)]), L([capsule(132, y, 220, y, THIN) for y in (56, 88)]),
                L([capsule(40, y, 220, y, THIN) for y in (140, 172, 204)], 0.8)])
reg('editheader', page_frame() + [L([rrect(56, 24, 144, 52, 14)], 0.35), L([capsule(56, 76, 200, 76, 12)]), faint_lines((112, 144, 176))])
reg('caption', [L(frame(40, 40, 176, 112, 12)), L([rrect(40, 40, 176, 112, 12)], LIGHT), L(disc(84, 82, 12), 0.9),
                L(stroke([(52, 132), (100, 96), (132, 124), (160, 100), (204, 132)], 12)),
                L([capsule(64, 184, 192, 184, THIN), capsule(88, 214, 168, 214, THIN)])])
reg('cross-reference', [L(frame(32, 48, 80, 64, 10)), L(frame(144, 144, 80, 64, 10)), L([rrect(32, 48, 80, 64, 10), rrect(144, 144, 80, 64, 10)], LIGHT),
                        L(stroke([(112, 80), (176, 80), (176, 144)], 12)), L(chevron(176, 128, 14, 'down', 12))])
omega = [(128 + 60 * math.cos(math.radians(t)), 104 + 60 * math.sin(math.radians(t))) for t in range(125, 420, 12)]
reg('symbol', [L(stroke(omega, SW) + stroke([(48, 184), (100, 184), (96, 156)], SW) + stroke([(208, 184), (156, 184), (160, 156)], SW))])


# ---- stacking order, grouping --------------------------------------------------------------------------------------
def arrange(emph_front, step):
    a, b = (40, 40, 112, 112), (104, 104, 112, 112)       # back square, front square
    back_lines = [capsule(a[0], a[1], a[0] + a[2], a[1], SW if not emph_front else THIN), capsule(a[0], a[1], a[0], a[1] + a[3], SW if not emph_front else THIN),
                  capsule(a[0] + a[2], a[1], a[0] + a[2], b[1], SW if not emph_front else THIN), capsule(a[0], a[1] + a[3], b[0], a[1] + a[3], SW if not emph_front else THIN)]
    front = frame(*b, 12) if emph_front else frame(*b, 12, 12)
    layers = [L([rrect(*b, 12)], LIGHT if emph_front else 0.1), L(front, 1.0 if emph_front else 0.4)]
    layers.insert(0, L(back_lines, 0.45 if emph_front else 1.0))
    if step == 'all':
        layers.append(L(chevron(228, 52, 14, 'up' if emph_front else 'down', 12) + chevron(228, 76, 14, 'up' if emph_front else 'down', 12)))
    else:
        layers.append(L(chevron(228, 64, 14, 'up' if emph_front else 'down', 12)))
    return layers


reg('arrange-front', arrange(True, 'all'))
reg('arrange-forward', arrange(True, 'one'))
reg('arrange-back', arrange(False, 'all'))
reg('arrange-backward', arrange(False, 'one'))
reg('shape-group', [L(dashed(32, 40, 224, 40, 12) + dashed(32, 216, 224, 216, 12) + dashed(32, 40, 32, 216, 12) + dashed(224, 40, 224, 216, 12), 0.55),
                    L(frame(60, 68, 60, 60, 8)), L(frame(136, 128, 60, 60, 8)), L([rrect(60, 68, 60, 60, 8), rrect(136, 128, 60, 60, 8)], LIGHT)])
reg('shape-ungroup', [L(frame(32, 40, 76, 76, 8)), L(frame(148, 140, 76, 76, 8)), L([rrect(32, 40, 76, 76, 8), rrect(148, 140, 76, 76, 8)], LIGHT),
                      L(arrow(120, 116, 144, 140, 22, 12), 0.7)])


# ---- text direction and orientation --------------------------------------------------------------------------------
def tlines(angle, n=3, length=150, gap=44, cx=128, cy=128):
    out = []
    for i in range(n):
        off = (i - (n - 1) / 2) * gap
        a = math.radians(angle)
        dx, dy = math.cos(a) * length / 2, math.sin(a) * length / 2
        ox, oy = -math.sin(a) * off, math.cos(a) * off
        out.append(capsule(cx + ox - dx, cy + oy - dy, cx + ox + dx, cy + oy + dy, THIN + 2))
    return out


reg('text-orient-hor', [L(tlines(0, 3, 168), 0.9), L(arrow(40, 220, 216, 220, 24, 12))])
reg('text-orient-vertical', [L([capsule(76, y, 140, y, THIN + 2) for y in (52, 96, 140, 184)], 0.9), L(arrow(200, 44, 200, 212, 24, 12))])
reg('text-orient-rup', [L(tlines(-90, 3, 160, 44, 140, 128), 0.9), L(arrow(36, 216, 36, 40, 24, 12))])
reg('text-orient-rdown', [L(tlines(90, 3, 160, 44, 140, 128), 0.9), L(arrow(36, 40, 36, 216, 24, 12))])
reg('text-orient-ccw', [L(tlines(-45, 3, 150, 46), 0.9), L(arrow(60, 212, 196, 76, 24, 12), 0.7)])
reg('text-orient-cw', [L(tlines(45, 3, 150, 46), 0.9), L(arrow(60, 44, 196, 180, 24, 12), 0.7)])
reg('text-vertical', ICONS['text-orient-vertical'])
reg('big-text-vertical', ICONS['text-orient-vertical'])


def mirror(name, flip=True):
    return glyph(name, 0, 0, 256, flip=flip)


reg('numbering-rtl', mirror('list-numbers'))
reg('setmarkers-rtl', mirror('list-bullets'))
reg('multilevels-rtl', mirror('list-dashes'))
reg('ltr', glyph('paragraph', 40, 16, 176) + [L(arrow(64, 232, 192, 232, 22, 12))])
reg('rtl', glyph('paragraph', 40, 16, 176, flip=True) + [L(arrow(192, 232, 64, 232, 22, 12))])


# ---- font ----------------------------------------------------------------------------------------------------------
def letter_a(x, y, h, w=SW):
    """Capital A with apex at (x, y), height h."""
    half = h * 0.36
    return stroke([(x - half, y + h), (x, y), (x + half, y + h)], w) + [capsule(x - half * 0.6, y + h * 0.66, x + half * 0.6, y + h * 0.66, w)]


reg('incfont', [L(letter_a(96, 56, 148)), L(arrow(200, 168, 200, 72, 24, 14))])
reg('decfont', [L(letter_a(96, 56, 148)), L(arrow(200, 72, 200, 168, 24, 14))])
_x_lines = lambda x, y, s: [capsule(x, y, x + s, y + s, SW), capsule(x + s, y, x, y + s, SW)]
_two = stroke([(168, 66), (180, 48), (206, 48), (218, 66), (170, 112), (222, 112)], 12)
reg('superscript', [L(_x_lines(40, 104, 100)), L(_two)])
reg('subscript', [L(_x_lines(40, 52, 100)), L([transform_p for transform_p in transform(_two, 1, 1, -4, 112)])])
reg('shadow', [L([transform_p for transform_p in letter_a(120, 76, 140, SW)], 0.3), L(letter_a(96, 52, 140))])
reg('styles', [L(frame(40, 36, 176, 52, 10)), L(frame(40, 102, 176, 52, 10), 0.7), L(frame(40, 168, 176, 52, 10), 0.4), L([rrect(40, 36, 176, 52, 10)], LIGHT)])
reg('zoom-100', glyph('magnifying-glass') + [L([capsule(116, 92, 116, 140, 14), capsule(116, 92, 100, 106, 12)])])


# ---- chart kinds ---------------------------------------------------------------------------------------------------
reg('chartcategory-area-normal', [L(polygon([(36, 200), (36, 132), (84, 92), (132, 148), (180, 68), (220, 116), (220, 200)]), LIGHT),
                                  L(stroke([(36, 132), (84, 92), (132, 148), (180, 68), (220, 116)], SW)), L(stroke([(36, 40), (36, 208), (224, 208)], 12), 0.6)])
reg('chartcategory-combo-bar-line', [L([rrect(40, 136, 40, 72, 6), rrect(108, 104, 40, 104, 6), rrect(176, 152, 40, 56, 6)], 0.35),
                                     L(stroke([(60, 92), (128, 60), (196, 100)], SW) + [circle(x, y, 14) for x, y in ((60, 92), (128, 60), (196, 100))])])
reg('chartcategory-stock-normal', [L(stroke([(60, 52), (60, 204)], 12) + stroke([(128, 84), (128, 220)], 12) + stroke([(196, 44), (196, 172)], 12), 0.9),
                                   L([rrect(40, 92, 40, 72, 6), rrect(176, 76, 40, 64, 6)]), L([rrect(108, 112, 40, 70, 6)], 0.35)])
reg('chartcategory-surface-normal', [L(stroke([(128, 36), (216, 84), (216, 172), (128, 220), (40, 172), (40, 84)], SW, closed=True)),
                                     L(stroke([(40, 84), (128, 132), (216, 84)], 12) + stroke([(128, 132), (128, 220)], 12) + stroke([(84, 108), (84, 196)], 10), 0.6),
                                     L(polygon([(128, 36), (216, 84), (128, 132), (40, 84)]), LIGHT)])
reg('chartcategory-spark-line', [L(frame(24, 84, 208, 88, 12)), L(stroke([(52, 144), (84, 112), (112, 136), (148, 104), (176, 130), (204, 108)], 12))])
reg('chartcategory-recommended', glyph('chart-bar', 8, 56, 190) + glyph('sparkle', 150, 16, 96))
reg('recommended-chart', ICONS['chartcategory-recommended'])


# ---- placeholders (slide layouts): dashed frame + the content symbol ------------------------------------------------
def placeholder(name, rot=0):
    d = (dashed(40, 40, 216, 40, 12, 22, 16) + dashed(40, 216, 216, 216, 12, 22, 16) + dashed(40, 40, 40, 216, 12, 22, 16) + dashed(216, 40, 216, 216, 12, 22, 16))
    return [L(d, 0.6)] + [L(p, o) for p, o in glyph(name, 76, 76, 104, rot=rot)]


reg('ins-chart-placeholder', placeholder('chart-bar'))
reg('ins-content-placeholder', placeholder('squares-four'))
reg('ins-picture-placeholder', placeholder('image'))
reg('ins-smartart-placeholder', placeholder('circles-three-plus'))
reg('ins-table-placeholder', placeholder('table'))
reg('ins-text-placeholder', placeholder('text-aa'))
reg('ins-vertical-content-placeholder', placeholder('columns'))
reg('ins-vertical-text-placeholder', placeholder('text-aa', 90))


# ---- spreadsheet ---------------------------------------------------------------------------------------------------
reg('incdecimal', [L(disc(52, 188, 12)), L(ring(124, 156, 40, 24)), L(arrow(84, 52, 212, 52, 26, 14))])
reg('decdecimal', [L(disc(52, 188, 12)), L(ring(124, 156, 40, 24)), L(arrow(212, 52, 84, 52, 26, 14))])
reg('comma', [L([disc(46, 176, 14), capsule(46, 176, 36, 210, 14)]), L(ring(120, 150, 34, 18) + ring(196, 150, 34, 18))])
reg('merge-and-center', [L(frame(24, 72, 208, 112, 12)), L([rrect(24, 72, 208, 112, 12)], LIGHT), L(arrow(52, 128, 100, 128, 22, 12) + arrow(204, 128, 156, 128, 22, 12))])
reg('merge-across', [L(frame(24, 52, 208, 70, 10)), L(frame(24, 134, 208, 70, 10)), L(arrow(52, 87, 100, 87, 20, 12) + arrow(204, 87, 156, 87, 20, 12) + arrow(52, 169, 100, 169, 20, 12) + arrow(204, 169, 156, 169, 20, 12), 0.8)])
_cells = []
for _r in range(3):
    for _c in range(3):
        _cells.append(L([rrect(44 + _c * 56, 44 + _r * 56, 44, 44, 8)], 1.0 if (_r + _c) % 2 == 0 and _r == _c else (0.55 if _r > _c else 0.2)))
reg('cond-format', _cells)


def svg(name):
    return to_svg(ICONS[name])


def names():
    return sorted(ICONS)
