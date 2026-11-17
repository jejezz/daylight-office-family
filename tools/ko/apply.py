"""Apply Korean term fixes (tools/ko/terms.json) to the ko locale of every editor.   python tools/ko/apply.py --app build/app.new"""
import argparse
import glob
import json
import os

HERE = os.path.dirname(os.path.abspath(__file__))


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
    print(f"ko: {total} strings adjusted in {len(files)} locale files")


if __name__ == '__main__':
    main()
