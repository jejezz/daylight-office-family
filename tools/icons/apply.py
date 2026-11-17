"""Replace toolbar icons with Phosphor Duotone in the modern (v2) icon sheets of every editor.

  python tools/icons/apply.py --app build/app.new [--dry-run]

For each editor: read the sprite row of every icon class from that editor's compiled app.css, paint the mapped Phosphor
glyph into the PNG sheets (100/125/150/175/200 %) and into the 2.5x SVG sheet. Icons that are not in mapping.json are
left untouched. Glyph colors are the palette text colors (left column = light theme, right column = dark theme).
"""
import argparse
import hashlib
import json
import os
import re
import sys

import numpy as np
from PIL import Image

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(HERE))
sys.path.insert(0, HERE)
import raster  # noqa: E402

CACHE_DIR = os.path.join(ROOT, 'build', 'cache', 'icons')
SCALES = [(1.0, ''), (1.25, '@1.25x'), (1.5, '@1.5x'), (1.75, '@1.75x'), (2.0, '@2x')]
APPS_REL = os.path.join('editors', 'web-apps', 'apps')


def hex_rgb(h):
    h = h.lstrip('#')
    return tuple(int(h[i:i + 2], 16) for i in (0, 2, 4))


def css_rows(css):
    """name -> row offset (px at 100%, positive) per sheet, read from the compiled CSS."""
    rows = {'small': {}, 'big': {}, 'huge': {}}
    pos_small = re.compile(r'background-position:\s*var\(--button-small-normal-icon-offset-x,\s*0\)\s*(-?\d+)px')
    pos_big = re.compile(r'background-position:\s*var\(--button-xhuge-normal-icon-offset-x,\s*0\)\s*(-?\d+)px')
    pos_huge = re.compile(r'background-position:0 (-?\d+)px')
    name_re = re.compile(r'\.(btn-[A-Za-z0-9_\-]+)')
    # one linear pass over the rules ("selector{body}"); the earlier all-in-one regexes were very slow on a 600 KB file
    for chunk in css.split('}'):
        sel, brace, body = chunk.partition('{')
        if not brace:
            continue
        if '.theme-icons-cls-mod2' in sel:
            pm = pos_small.search(body)
            if pm:
                for nm in name_re.findall(sel.split('.theme-icons-cls-mod2')[-1]):
                    rows['small'][nm] = -int(pm.group(1))
        elif '.toolbar__icon-big.btn-' in sel:
            pm = pos_big.search(body)
            if pm:
                for nm in re.findall(r'\.toolbar__icon-big\.(btn-[A-Za-z0-9_\-]+)', sel):
                    rows['big'][nm] = -int(pm.group(1))
        elif '.options__icon-huge.btn-' in sel:
            pm = pos_huge.search(body)
            if pm:
                for nm in re.findall(r'\.options__icon-huge\.(btn-[A-Za-z0-9_\-]+)', sel):
                    rows['huge'][nm] = -int(pm.group(1))
    return rows


class Glyphs:
    def __init__(self, directory):
        self.dir = directory
        self.svg = {}
        self.cache = {}

    def text(self, name):
        if name not in self.svg and name.startswith('custom:'):
            sys.path.insert(0, os.path.join(HERE, 'custom'))
            import icons as custom_icons  # hand-made icons, see tools/icons/custom/icons.py
            if name[7:] not in custom_icons.ICONS:
                raise SystemExit(f"custom icon not found: {name}")
            self.svg[name] = custom_icons.svg(name[7:])
        if name not in self.svg:
            path = os.path.join(self.dir, name + '.svg')
            if not os.path.exists(path):
                raise SystemExit(f"Phosphor icon not found: {path}")
            self.svg[name] = open(path, encoding='utf-8').read()
        return self.svg[name]

    def alpha(self, name, px):
        """Rendering costs ~40 ms per icon and size, so results are cached on disk (build/cache/icons, keyed by the
        SVG's hash and the renderer's version); the second build onwards skips rendering."""
        key = (name, px)
        if key in self.cache:
            return self.cache[key]
        digest = hashlib.sha1((raster.VERSION + self.text(name)).encode('utf-8')).hexdigest()[:12]
        path = os.path.join(CACHE_DIR, f'{name}-{px}-{digest}.npy')
        if os.path.exists(path):
            arr = np.load(path)
        else:
            arr = raster.render_svg(self.text(name), px)
            os.makedirs(CACHE_DIR, exist_ok=True)
            np.save(path, arr)
        self.cache[key] = arr
        return arr

    def paths(self, name):
        """The <path> elements of the icon as (d, opacity) pairs."""
        out = []
        for m in re.finditer(r'<path\b([^>]*)/?>', self.text(name)):
            a = ' ' + m.group(1)
            d = re.search(r'\sd="([^"]+)"', a).group(1)
            op = re.search(r'\sopacity="([^"]+)"', a)
            out.append((d, op.group(1) if op else None))
        return out


def cell_image(alpha, cell_px, box_px, color0, color1):
    """RGBA array (cell_px, 2*cell_px, 4): left = color0 glyph, right = color1 glyph, both centered."""
    off = (cell_px - box_px) // 2
    out = np.zeros((cell_px, cell_px * 2, 4), dtype=np.uint8)
    a = np.clip(alpha * 255 + 0.5, 0, 255).astype(np.uint8)
    for col, rgb in enumerate((color0, color1)):
        x0 = col * cell_px + off
        out[off:off + box_px, x0:x0 + box_px, 0] = rgb[0]
        out[off:off + box_px, x0:x0 + box_px, 1] = rgb[1]
        out[off:off + box_px, x0:x0 + box_px, 2] = rgb[2]
        out[off:off + box_px, x0:x0 + box_px, 3] = a
    return out


def patch_svg_sheet(path, names_box, glyphs, cell):
    """Replace <symbol> contents in the 2.5x SVG sheet (viewBox = cell px at 100%)."""
    text = open(path, encoding='utf-8').read()
    n = 0
    for name, (phosphor, box) in names_box.items():
        m = re.search(r'(<symbol\b[^>]*\bid="' + re.escape(name) + r'"[^>]*>)(.*?)(</symbol>)', text, re.S)
        if not m:
            continue
        off = (cell - box) / 2
        k = box / 256.0
        body = ''.join(f'<path d="{d}" class="icon-fill-gray-primary"' + (f' opacity="{op}"' if op else '') + '/>'
                       for d, op in glyphs.paths(phosphor))
        new = f'{m.group(1)}<g transform="translate({off:g} {off:g}) scale({k:.6g})">{body}</g>{m.group(3)}'
        text = text[:m.start()] + new + text[m.end():]
        n += 1
    open(path, 'w', encoding='utf-8', newline='').write(text)
    return n


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--app', required=True)
    ap.add_argument('--dry-run', action='store_true')
    a = ap.parse_args()
    style = json.load(open(os.path.join(HERE, 'style.json'), encoding='utf-8'))
    mapping = json.load(open(os.path.join(HERE, 'mapping.json'), encoding='utf-8'))
    pal = json.load(open(os.path.join(ROOT, 'tools', 'theme', 'palette.json'), encoding='utf-8'))
    color0, color1 = hex_rgb(pal['light']['text']), hex_rgb(pal['dark']['text'])
    glyphs = Glyphs(os.path.normpath(os.path.join(ROOT, style['phosphorDir'])))
    total = {'small': 0, 'big': 0, 'huge': 0}
    missing = []
    for ed in style['editors']:
        base = os.path.join(a.app, APPS_REL, ed, 'main', 'resources')
        css = open(os.path.join(base, 'css', 'app.css'), encoding='utf-8', errors='ignore').read()
        rows = css_rows(css)
        for sheet in ('small', 'big', 'huge'):
            cell, box = style['cell'][sheet], style['box'][sheet]
            todo = {}
            for name, ph in mapping.get(sheet, {}).items():
                cls = 'btn-' + name
                if cls in rows[sheet]:
                    todo[cls] = (ph, box, rows[sheet][cls])
                else:
                    missing.append(f"{ed}/{sheet}/{cls}")
            if not todo:
                continue
            sheet_dir = os.path.join(base, 'img', 'v2')
            for scale, suffix in SCALES:
                p = os.path.join(sheet_dir, f'icons{sheet}{suffix}.png')
                img = Image.open(p).convert('RGBA')
                cpx = round(cell * scale)
                if img.width != cpx * 2:
                    raise SystemExit(f"{p}: width {img.width}, expected {cpx * 2}")
                bpx = round(box * scale)
                for cls, (ph, _box, row) in todo.items():
                    cell_arr = cell_image(glyphs.alpha(ph, bpx), cpx, bpx, color0, color1)
                    y0 = round(row * scale)
                    if y0 + cpx > img.height:
                        raise SystemExit(f"{p}: row {row} is outside the sheet")
                    img.paste(Image.fromarray(cell_arr, 'RGBA'), (0, y0))
                if not a.dry_run:
                    img.save(p, optimize=True)
            svg = os.path.join(sheet_dir, f'icons{sheet}@2.5x.svg')
            if not a.dry_run:
                patch_svg_sheet(svg, {c: (v[0], v[1]) for c, v in todo.items()}, glyphs, cell)
            total[sheet] += len(todo)
            print(f"  {ed:18} {sheet:5} {len(todo):3} icons replaced")
    print(f"icons: Phosphor Duotone in the modern sheets - small {total['small']}, big {total['big']}, huge {total['huge']} (per editor counts above)")
    if missing:
        print(f"note: {len(missing)} mapped icon(s) not present in some editors' sheets (normal: sets differ per editor), e.g. {missing[:3]}")


if __name__ == '__main__':
    main()
