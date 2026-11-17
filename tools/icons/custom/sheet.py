"""Contact sheet of all hand-made icons: python tools/icons/custom/sheet.py [out.png] [--px 96] [--small]
--small also shows each icon at 24 px (the real toolbar size) under the big one."""
import os
import sys

import numpy as np
from PIL import Image, ImageDraw

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import icons  # noqa: E402
import raster  # noqa: E402


def main():
    args = [a for a in sys.argv[1:] if not a.startswith('--')]
    out = args[0] if args else 'build/custom-icons.png'
    px = 96
    small = '--small' in sys.argv
    names = icons.names()
    cols = 10
    cw_, ch_ = px + 24, px + 36 + (28 if small else 0)
    rows = (len(names) + cols - 1) // cols
    sheet = Image.new('RGB', (cols * cw_, rows * ch_), (255, 255, 255))
    dr = ImageDraw.Draw(sheet)
    for i, n in enumerate(names):
        x, y = (i % cols) * cw_, (i // cols) * ch_
        a = raster.render_svg(icons.svg(n), px)
        img = Image.fromarray((255 - a * 235).astype(np.uint8)).convert('RGB')
        sheet.paste(img, (x + 12, y + 4))
        if small:
            a2 = raster.render_svg(icons.svg(n), 24)
            sheet.paste(Image.fromarray((255 - a2 * 235).astype(np.uint8)).convert('RGB'), (x + 12, y + px + 6))
        dr.text((x + 4, y + ch_ - 16), n[:20], fill=(90, 90, 90))
    os.makedirs(os.path.dirname(os.path.abspath(out)), exist_ok=True)
    sheet.save(out)
    print(len(names), 'icons ->', out)


if __name__ == '__main__':
    main()
