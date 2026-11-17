"""App icon: the shared cat big in the centre, our sun behind it at the upper right, transparent background, as large as
the canvas allows. (A deliberate departure from conventions/icons.md "prop + cat badge on a tile": the owner wants this
app to stand apart from the many family apps that share that look.)

  python tools/brand/make_cat_icon.py <path to icons8-grinning-cat-1024.png>

Writes assets/brand/app.ico (BMP frames up to 128 px, PNG for 256 px, as the PE icon resource needs), app_qt.ico (frames up
to 48 px: the Qt resource slot inside editors.exe is only ~16 KB compressed) and app_icon_1024.png. The cat is a paid
Icons8 asset that is NOT kept in this repository; only the generated icon is. Re-run only when the artwork changes.
"""
import math
import os
import shutil
import struct
import subprocess
import sys
import tempfile
import zlib

from PIL import Image, ImageChops, ImageDraw, ImageFilter

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(HERE))
GEN = os.path.normpath(os.path.join(ROOT, '..', 'application-release-templates', 'common', 'tool', 'icon', 'generate_icons.py'))
SIZES = [256, 128, 64, 48, 40, 32, 24, 20, 16]


def sun_glyph(n=1024):
    """Yellow sun (disc + 8 rays) on transparent, no outline."""
    ss = 2
    big = n * ss
    im = Image.new('L', (big, big), 0)
    d = ImageDraw.Draw(im)
    c = big / 2
    r = big * 0.17
    d.ellipse((c - r, c - r, c + r, c + r), fill=255)
    for k in range(8):
        a = math.radians(45 * k)
        x0, y0 = c + math.cos(a) * big * 0.26, c + math.sin(a) * big * 0.26
        x1, y1 = c + math.cos(a) * big * 0.40, c + math.sin(a) * big * 0.40
        d.line((x0, y0, x1, y1), fill=255, width=int(big * 0.07))
        for x, y in ((x0, y0), (x1, y1)):
            rr = big * 0.035
            d.ellipse((x - rr, y - rr, x + rr, y + rr), fill=255)
    mask = im.resize((n, n), Image.LANCZOS)
    out = Image.new('RGBA', (n, n), (0, 0, 0, 0))
    out.paste(Image.new('RGBA', (n, n), (245, 184, 46, 255)), (0, 0), mask)   # no sticker outline (user preference)
    return out


def pack_ico(frames):
    """Frames (PIL RGBA, square) -> ICO bytes: DIB for <=128 px, PNG for 256 px."""
    imgs = []
    for im in frames:
        n = im.width
        if n == 256:
            import io
            b = io.BytesIO()
            im.save(b, 'PNG')
            imgs.append(b.getvalue())
        else:
            px = im.load()
            hdr = struct.pack('<IiiHHIIiiII', 40, n, 2 * n, 1, 32, 0, 0, 0, 0, 0, 0)
            body = b''.join(bytes((px[x, y][2], px[x, y][1], px[x, y][0], px[x, y][3])) for y in range(n - 1, -1, -1) for x in range(n))
            mask = (b'\x00' * (((n + 31) // 32) * 4)) * n
            imgs.append(hdr + body + mask)
    head = struct.pack('<HHH', 0, 1, len(frames))
    off = 6 + 16 * len(frames)
    ent = data = b''
    for im, blob in zip(frames, imgs):
        n = im.width
        ent += struct.pack('<BBBBHHII', 0 if n == 256 else n, 0 if n == 256 else n, 0, 0, 1, 32, len(blob), off + len(data))
        data += blob
    return head + ent + data


def tight(im):
    return im.crop(im.getbbox())


def compose(cat_path, n=1024):
    cat = tight(Image.open(cat_path).convert('RGBA'))
    sun = tight(sun_glyph(1024))
    margin = round(n * 0.01)
    cs = round(n * 0.80)                       # cat: big, centred (a little low/left to leave room for the sun)
    cat = cat.resize((cs, round(cs * cat.height / cat.width)), Image.LANCZOS)
    ss = round(n * 0.64)                       # sun: upper right, behind the cat
    sun = sun.resize((ss, ss), Image.LANCZOS)
    canvas = Image.new('RGBA', (n, n), (0, 0, 0, 0))
    canvas.alpha_composite(sun, (n - ss - margin, margin))
    cx, cy = round(n * 0.07), n - cat.height - margin
    # the cat shades the sun a little so the two warm colours stay apart
    shadow = Image.new('RGBA', cat.size, (60, 30, 0, 255))
    sh_mask = cat.getchannel('A').filter(ImageFilter.GaussianBlur(round(n * 0.012))).point(lambda v: int(v * 0.45))
    layer = Image.new('RGBA', (n, n), (0, 0, 0, 0))
    layer.paste(shadow, (cx + round(n * 0.008), cy + round(n * 0.012)), sh_mask)
    # shadow only where the sun is
    sun_a = Image.new('L', (n, n), 0)
    sun_a.paste(sun.getchannel('A'), (n - ss - margin, margin))
    layer.putalpha(ImageChops.multiply(layer.getchannel('A'), sun_a))
    canvas.alpha_composite(layer)
    canvas.alpha_composite(cat, (cx, cy))
    return canvas


def main():
    if len(sys.argv) != 2 or not os.path.exists(sys.argv[1]):
        raise SystemExit(__doc__)
    master = compose(os.path.abspath(sys.argv[1]))
    frames = []
    for n in SIZES:
        f = master.resize((n, n), Image.LANCZOS)
        if n <= 48:
            f = f.filter(ImageFilter.UnsharpMask(radius=0.8, percent=60, threshold=2))
        frames.append(f)
    out = os.path.join(ROOT, 'assets', 'brand')
    os.makedirs(out, exist_ok=True)
    open(os.path.join(out, 'app.ico'), 'wb').write(pack_ico(frames))
    qt = pack_ico([f for f in frames if f.width <= 48])
    if len(zlib.compress(qt, 9)) > 16000:
        raise SystemExit('slim icon does not fit the Qt slot; drop a frame size')
    open(os.path.join(out, 'app_qt.ico'), 'wb').write(qt)
    master.save(os.path.join(out, 'app_icon_1024.png'))
    print('wrote assets/brand/app.ico, app_qt.ico, app_icon_1024.png')


if __name__ == '__main__':
    main()
