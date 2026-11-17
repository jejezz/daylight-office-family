"""Generate one .ico per file-type icon of DesktopEditors.exe plus a map file (group id -> ico path)
that tools/win/replace-exe-icon.ps1 reads (-MapFile).

  python tools/brand/make_type_icons.py --out build/brand/types

Override: assets/brand/types/<ext>.ico replaces the generated icon for that extension.
"""
import argparse
import json
import os

import art_types

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(HERE))

ap = argparse.ArgumentParser()
ap.add_argument('--out', required=True)
ap.add_argument('--assets', default=os.path.join(ROOT, 'assets', 'brand', 'types'))
a = ap.parse_args()
os.makedirs(a.out, exist_ok=True)
table = json.load(open(os.path.join(HERE, 'filetypes.json'), encoding='utf-8'))['icons']
cache, mapping = {}, {}
for e in table:
    key = (e['ext'], e['cat'])
    if key not in cache:
        path = os.path.join(a.out, f"{e['ext']}.ico")
        ovr = os.path.join(a.assets, f"{e['ext']}.ico")
        data = open(ovr, 'rb').read() if os.path.exists(ovr) else art_types.type_ico(e['ext'], e['cat'])
        open(path, 'wb').write(data)
        cache[key] = path
    mapping[str(e['group'])] = cache[key]
json.dump(mapping, open(os.path.join(a.out, 'map.json'), 'w', encoding='utf-8'), indent=1)
print(f"file-type icons: {len(cache)} generated for {len(mapping)} groups -> {a.out}")
