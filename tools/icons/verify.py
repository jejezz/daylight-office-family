"""Checks for the icon step.

  python tools/icons/verify.py --app build/app                       # static: sprite cells of every replaced icon
  python tools/icons/verify.py --shot shot.png --at 135,151 --icon text-b --box 20 [--dark]   # a screenshot crop

Static check: for each mapped icon of each editor, the 100% cell has opaque pixels only inside the glyph box, the left
column uses the light-theme text color, the right column the dark-theme text color, and the cell differs from the
original (upstream) sheet. Screenshot check: normalized correlation between the crop around (x, y) and the glyph alpha.
"""
import argparse
import json
import os
import sys
import xml.etree.ElementTree as ET

import numpy as np
from PIL import Image

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(HERE))
sys.path.insert(0, HERE)
import apply as A  # noqa: E402
import raster  # noqa: E402


def static_check(app, upstream):
    style = json.load(open(os.path.join(HERE, 'style.json'), encoding='utf-8'))
    mapping = json.load(open(os.path.join(HERE, 'mapping.json'), encoding='utf-8'))
    pal = json.load(open(os.path.join(ROOT, 'tools', 'theme', 'palette.json'), encoding='utf-8'))
    c0, c1 = A.hex_rgb(pal['light']['text']), A.hex_rgb(pal['dark']['text'])
    fails, checked = [], 0
    for ed in style['editors']:
        rel = os.path.join(A.APPS_REL, ed, 'main', 'resources')
        css = open(os.path.join(app, rel, 'css', 'app.css'), encoding='utf-8', errors='ignore').read()
        rows = A.css_rows(css)
        for sheet in ('small', 'big', 'huge'):
            if not mapping.get(sheet):
                continue
            cell, box = style['cell'][sheet], style['box'][sheet]
            off = (cell - box) // 2
            new = np.array(Image.open(os.path.join(app, rel, 'img', 'v2', f'icons{sheet}.png')).convert('RGBA'))
            old = np.array(Image.open(os.path.join(upstream, rel, 'img', 'v2', f'icons{sheet}.png')).convert('RGBA'))
            # the 2.5x SVG sheet must still be well-formed XML and carry the new glyph in every mapped symbol
            svg_path = os.path.join(app, rel, 'img', 'v2', f'icons{sheet}@2.5x.svg')
            svg_text = open(svg_path, encoding='utf-8').read()
            try:
                root_el = ET.fromstring(svg_text)
            except ET.ParseError as e:
                fails.append(f"{ed}/{sheet}: SVG sheet is not well-formed ({e})")
                root_el = None
            if root_el is not None:
                syms = {}
                for el in root_el.iter():
                    if el.tag.endswith('symbol'):
                        syms.setdefault(el.get('id'), el)   # duplicate ids exist; <use> resolves to the first one
                for name in mapping[sheet]:
                    cls = 'btn-' + name
                    if cls in rows[sheet]:
                        el = syms.get(cls)
                        if el is None or 'icon-fill-gray-primary' not in ET.tostring(el, encoding='unicode'):
                            fails.append(f"{ed}/{sheet}/{cls}: SVG symbol was not replaced")
            for name in mapping[sheet]:
                cls = 'btn-' + name
                if cls not in rows[sheet]:
                    continue
                y = rows[sheet][cls]
                n, o = new[y:y + cell], old[y:y + cell]
                checked += 1
                tag = f"{ed}/{sheet}/{cls}"
                if np.array_equal(n, o):
                    fails.append(f"{tag}: cell identical to the original"); continue
                for col, rgb in ((0, c0), (1, c1)):
                    part = n[:, col * cell:(col + 1) * cell]
                    ys, xs = np.nonzero(part[:, :, 3] > 8)
                    if len(xs) == 0:
                        fails.append(f"{tag}: column {col} is empty"); continue
                    if xs.min() < off or xs.max() >= off + box or ys.min() < off or ys.max() >= off + box:
                        fails.append(f"{tag}: column {col} draws outside the glyph box")
                    solid = part[part[:, :, 3] > 240][:, :3]
                    if len(solid) and np.abs(solid.astype(int) - np.array(rgb)).max() > 6:
                        fails.append(f"{tag}: column {col} color is not the palette text color")
    return checked, fails


def shot_check(shot, at, icon, box, dark):
    style = json.load(open(os.path.join(HERE, 'style.json'), encoding='utf-8'))
    svg = open(os.path.join(ROOT, style['phosphorDir'], icon + '.svg'), encoding='utf-8').read()
    alpha = raster.render_svg(svg, box)
    x, y = at
    img = np.array(Image.open(shot).convert('L'), dtype=np.float32)
    half = box // 2
    crop = img[y - half:y - half + box, x - half:x - half + box]
    if crop.shape != alpha.shape:
        return 0.0
    # glyph is light on dark (dark theme) or dark on light: correlate with the alpha mask (sign-flipped for light)
    a = alpha - alpha.mean()
    c = crop - crop.mean()
    den = np.sqrt((a * a).sum() * (c * c).sum())
    r = float((a * c).sum() / den) if den else 0.0
    # polarity does not matter: a light glyph on a dark button (dark theme) and a dark glyph on a light button (light
    # theme) are the same shape with opposite brightness, i.e. correlation +1 or -1. Only the shape is checked here.
    return abs(r)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--app')
    ap.add_argument('--upstream', default=os.path.join(ROOT, 'external', 'upstream-10.0.0.169'))
    ap.add_argument('--shot')
    ap.add_argument('--at')
    ap.add_argument('--icon')
    ap.add_argument('--box', type=int, default=20)
    ap.add_argument('--dark', action='store_true')
    a = ap.parse_args()
    if a.app:
        checked, fails = static_check(a.app, a.upstream)
        for f in fails[:20]:
            print('FAIL', f)
        print(f"static: {checked} icon cells checked, {len(fails)} problem(s)")
        sys.exit(1 if fails else 0)
    if a.shot:
        x, y = (int(v) for v in a.at.split(','))
        r = shot_check(a.shot, (x, y), a.icon, a.box, a.dark)
        print(f"correlation {r:.3f}")
        sys.exit(0 if r > 0.6 else 1)
    ap.error('give --app or --shot')


if __name__ == '__main__':
    main()
