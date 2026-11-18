"""Apply Korean term fixes (tools/ko/terms.json) to the ko locale of every editor.   python tools/ko/apply.py --app build/app.new"""
import argparse
import glob
import json
import os
import re
import sys
import zipfile

HERE = os.path.dirname(os.path.abspath(__file__))


def patch_new_docx(app, font):
    """New Korean documents open in the theme font (Arial in the upstream template). Point the theme's
    major/minor latin/ea/cs fonts at `font` so 'Normal' and headings use it; fontTable gets an entry too."""
    path = os.path.join(app, 'converter', 'empty', 'ko-KR', 'new.docx')
    if not os.path.isfile(path):
        raise SystemExit(f"new.docx template not found: {path}")
    zin = zipfile.ZipFile(path)
    items = [(i, zin.read(i.filename)) for i in zin.infolist()]
    zin.close()
    out = []
    n = 0
    for info, data in items:
        if info.filename == 'word/theme/theme1.xml':
            s = data.decode('utf-8')
            s, n = re.subn(r'(<a:(?:latin|ea|cs) typeface=")Arial(")', lambda m: m.group(1) + font + m.group(2), s)
            data = s.encode('utf-8')
        elif info.filename == 'word/fontTable.xml':
            s = data.decode('utf-8')
            s = s.replace('<w:font w:name="Arial">', '<w:font w:name="%s"><w:charset w:val="81"/></w:font><w:font w:name="Arial">' % font, 1)
            data = s.encode('utf-8')
        out.append((info, data))
    if n != 6:
        raise SystemExit(f"new.docx: expected 6 theme font entries to replace, got {n} (upstream template changed?)")
    with zipfile.ZipFile(path, 'w', zipfile.ZIP_DEFLATED) as zout:
        for info, data in out:
            zout.writestr(info, data)
    print(f"new.docx: theme fonts -> {font}")


def rewrite_zip(path, edits):
    """edits: {member name: function(str) -> str}. Rewrites the zip in place; every named member must exist."""
    zin = zipfile.ZipFile(path)
    items = [(i, zin.read(i.filename)) for i in zin.infolist()]
    zin.close()
    seen = set()
    with zipfile.ZipFile(path, 'w', zipfile.ZIP_DEFLATED) as zout:
        for info, data in items:
            fn = edits.get(info.filename)
            if fn:
                data = fn(data.decode('utf-8')).encode('utf-8')
                seen.add(info.filename)
            zout.writestr(info, data)
    missing = set(edits) - seen
    if missing:
        raise SystemExit(f"{path}: members not found {sorted(missing)}")


def sub_exact(pattern, repl, expect, what):
    def fn(s):
        s, n = re.subn(pattern, repl, s)
        if n != expect:
            raise SystemExit(f"{what}: expected {expect} replacement(s), got {n} (upstream template changed?)")
        return s
    return fn


def patch_new_xlsx(app, font):
    """New workbooks: default cell font and theme fonts (Calibri / Calibri Light) -> font."""
    path = os.path.join(app, 'converter', 'empty', 'ko-KR', 'new.xlsx')
    rewrite_zip(path, {
        'xl/styles.xml': sub_exact(r'<name val="Calibri"/>(<family val="2"/>)<charset val="204"/>',
                                   lambda m: '<name val="%s"/>%s<charset val="129"/>' % (font, m.group(1)), 1, 'new.xlsx styles'),
        'xl/theme/theme1.xml': sub_exact(r'(<a:(?:major|minor)Font><a:latin typeface=")Calibri(?: Light)?(" panose="[0-9A-F]+")?/>',
                                         lambda m: m.group(1) + font + '"/>', 2, 'new.xlsx theme'),
    })
    print(f"new.xlsx: default font -> {font}")


def patch_new_pptx(app, font):
    """New presentations: main theme's major/minor latin font (Arial) -> font. Bullet fonts stay Arial."""
    path = os.path.join(app, 'converter', 'empty', 'ko-KR', 'new.pptx')
    rewrite_zip(path, {
        'ppt/theme/theme1.xml': sub_exact(r'(<a:(?:major|minor)Font><a:latin typeface=")Arial(" panose="[0-9A-F]+")?/><a:ea typeface=""/>',
                                          lambda m: m.group(1) + font + '"/><a:ea typeface="' + font + '"/>', 2, 'new.pptx theme'),
    })
    print(f"new.pptx: theme fonts -> {font}")


def system_font(spec):
    """newDocFont is {windows, macos}: the OS system UI font for Korean. Only Windows builds exist for now."""
    return spec['macos'] if sys.platform == 'darwin' else spec['windows']


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--app', required=True)
    a = ap.parse_args()
    terms = json.load(open(os.path.join(HERE, 'terms.json'), encoding='utf-8'))
    files = glob.glob(os.path.join(a.app, 'editors', 'web-apps', 'apps', '*', 'main', 'locale', 'ko.json'))
    if len(files) < 4:
        raise SystemExit(f"ko locale: only {len(files)} file(s) found, upstream layout changed?")
    total = 0
    for f in files:
        text = open(f, encoding='utf-8', newline='').read()
        d = json.loads(text)
        n = 0
        for k, v in d.items():
            nv = v
            for old, new in terms['replace'].items():
                nv = nv.replace(old, new)
            for suffix, val in terms['keys'].items():
                if k.endswith(suffix):
                    nv = val
            if nv != v:
                d[k] = nv
                n += 1
        out = json.dumps(d, ensure_ascii=False, separators=(',', ':'))
        open(f, 'w', encoding='utf-8', newline='').write(out)
        total += n
    font = system_font(terms['newDocFont'])
    patch_new_docx(a.app, font)
    patch_new_xlsx(a.app, font)
    patch_new_pptx(a.app, font)
    print(f"ko: {total} strings adjusted in {len(files)} locale files")


if __name__ == '__main__':
    main()
