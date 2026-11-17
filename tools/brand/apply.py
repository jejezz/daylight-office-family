"""Apply the brand (name, logos, icon, notice) to an assembled app tree (build/app). Idempotent: run on a fresh copy.

  python tools/brand/apply.py --app build/app [--dry-run]

Every binary string rule must match exactly the expected number of NUL-delimited whole strings, otherwise the
script stops. That keeps an upstream upgrade from silently changing settings keys or paths.
Optional artwork overrides (same names as art.py): assets/brand/<name>.
"""
import argparse
import json
import os
import struct
import sys
import zlib

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(HERE))
sys.path.insert(0, HERE)
import art  # noqa: E402


def enc_of(kind, s):
    return s.encode('utf-16-le') if kind == 'u16' else s.encode('ascii')


def whole_matches(data, kind, s):
    k = enc_of(kind, s)
    z = 2 if kind == 'u16' else 1
    out, pos = [], 0
    while True:
        i = data.find(k, pos)
        if i < 0:
            return out
        pos = i + 1
        if kind == 'u16' and i % 2:
            continue
        before_ok = i == 0 or data[i - z:i] == b'\x00' * z
        after_ok = data[i + len(k):i + len(k) + z] == b'\x00' * z
        if before_ok and after_ok:
            out.append(i)


def patch_whole(buf, kind, old, new, lo, hi, log, dry, label=''):
    k_old, k_new = enc_of(kind, old), enc_of(kind, new)
    if len(k_new) > len(k_old):
        raise SystemExit(f"replacement longer than original: {old!r} -> {new!r}")
    offs = whole_matches(bytes(buf), kind, old)
    if not (lo <= len(offs) <= hi):
        raise SystemExit(f"rule {kind} {old!r}: expected {lo}..{hi} whole-string matches, found {len(offs)}")
    if not dry:
        for o in offs:
            buf[o:o + len(k_old)] = k_new + b'\x00' * (len(k_old) - len(k_new))
    log.append(f"  {label:18} {kind:5} x{len(offs)}  {old[:60]!r} -> {new[:40]!r}")


def binary_rules(cfg):
    n, p, d = cfg['name'], cfg['product'], cfg['dataDir']
    # (file, kind, old, new, min, max)
    return [
        # organization name: title-bar suffix AND settings key (HKCU\Software\<name>\DesktopEditors); also printed by --version
        ('editors.exe', 'ascii', 'ONLYOFFICE', n, 2, 2),
        # per-user data folder: %LOCALAPPDATA%/<dataDir>/DesktopEditors (keeps our data apart from an installed original)
        ('editors.exe', 'ascii', '/ONLYOFFICE/DesktopEditors', f'/{d}/DesktopEditors', 1, 1),
        ('editors.exe', 'ascii', 'ONLYOFFICE Desktop Editors', p, 1, 1),
        ('editors.exe', 'ascii', 'ONLYOFFICE Desktop Enterprise', p, 1, 1),
        ('editors.exe', 'ascii', 'ONLYOFFICE Update Service', f'{n} Update Service', 1, 1),
        ('editors.exe', 'u16', 'ONLYOFFICE', n, 2, 2),                      # update manager text, VERSIONINFO ProductName
        ('editors.exe', 'u16', 'ONLYOFFICE Desktop Editors', p, 1, 1),      # VERSIONINFO FileDescription
        ('editors.exe', 'u16', r'SOFTWARE\ONLYOFFICE\DesktopEditors\Capabilities\FileAssociations',
         rf'SOFTWARE\{n}\DesktopEditors\Capabilities\FileAssociations', 1, 1),
        ('DesktopEditors.exe', 'u16', 'ONLYOFFICE Editors', p, 2, 2),       # VERSIONINFO FileDescription, ProductName
        # online template gallery: the start page loads it at launch (an outbound connection to the vendor); open a blank page instead
        ('editors.exe', 'ascii', 'https://templates.onlyoffice.com/?desktop=true', 'about:blank', 1, 1),
        # online help (the editor loads it when a document opens): blank page instead of a request to the vendor
        ('editors.exe', 'ascii', 'https://download.onlyoffice.com/install/desktop/editors/help/v10.0.0/apps', 'about:blank', 1, 1),
        # update check: point both appcast URLs at a closed local port (the check then simply fails)
        ('editors.exe', 'u16', 'https://download.onlyoffice.com/install/desktop/editors/windows/onlyoffice/appcast.json',
         cfg['updateUrl'], 1, 1),
        ('editors.exe', 'u16', 'https://download.onlyoffice.com/install/desktop/editors/windows/onlyoffice/appcastdev.json',
         cfg['updateUrl'], 1, 1),
    ]


def patch_pngs(buf, offsets, assets, log, dry):
    for e in offsets['editors.exe']['logos']:
        o, w, h, ln = e['off'], e['w'], e['h'], e['len']
        blob = bytes(buf[o:o + ln])
        if blob[:8] != b'\x89PNG\r\n\x1a\n' or struct.unpack('>II', blob[16:24]) != (w, h):
            raise SystemExit(f"logo at {o}: not the expected {w}x{h} PNG (upstream changed? re-derive offsets.json)")
        name = f"logo_{e['theme']}_{w}x{h}.png"
        ovr = os.path.join(assets, name)
        new = open(ovr, 'rb').read() if os.path.exists(ovr) else art.logo_png(w, h, e['theme'])
        if len(new) > ln:
            raise SystemExit(f"{name}: {len(new)} bytes does not fit the original slot of {ln} bytes")
        if not dry:
            buf[o:o + ln] = new + b'\x00' * (ln - len(new))
        log.append(f"  logo {name} {len(new)}/{ln} bytes")


def patch_qt_ico(buf, ico, log, dry):
    """The window/taskbar icon is a zlib-compressed Qt resource (':/app.ico'): [be32 size-of-rest][be32 raw size][zlib]."""
    data = bytes(buf)
    hits = []
    pos = 0
    while True:
        i = data.find(b'\x78\x9c', pos)
        if i < 0:
            break
        pos = i + 1
        try:
            d = zlib.decompressobj()
            out = d.decompress(data[i:i + 400000])
        except Exception:
            continue
        if out[:4] == b'\x00\x00\x01\x00' and len(out) > 100000:
            used = len(data[i:i + 400000]) - len(d.unused_data)
            hits.append((i, len(out), used))
    if len(hits) != 1:
        raise SystemExit(f"Qt :/app.ico: expected 1 compressed icon, found {len(hits)}")
    i, raw_len, used = hits[0]
    z = zlib.compress(ico, 9)
    if len(z) > used:
        raise SystemExit(f"new icon ({len(z)} B compressed) does not fit the slot ({used} B)")
    if not dry:
        buf[i - 4:i] = struct.pack('>I', len(ico))
        buf[i:i + used] = z + b'\x00' * (used - len(z))
    log.append(f"  Qt :/app.ico {len(z)}/{used} bytes compressed")


def patch_index_html(path, cfg, version, log, dry):
    h = open(path, 'rb').read().decode('utf-8')
    import re
    counts = []
    for old, new in cfg['htmlReplacements']:
        counts.append((old, h.count(old)))
        h = h.replace(old, new.format(product=cfg['product'], name=cfg['name']))
    # left rail of the start screen: hide AI Chat / AI Tools / Clouds (minified-code anchors, pinned to the base version)
    rail = {
        'aichat': ('get when(){return yo()},get children(){return[m(ut,{href:"/aichat"',
                   'get when(){return!1},get children(){return[m(ut,{href:"/aichat"'),
        'aitools': ('get when(){return yo()},get children(){return m(ut,{href:"/aitools"',
                    'get when(){return!1},get children(){return m(ut,{href:"/aitools"'),
        'clouds': ('m(ut,{action:"clouds",href:"/clouds",icon:"#cloud",',
                   'm(ut,{hidden:!0,action:"clouds",href:"/clouds",icon:"#cloud",'),
        'templates': ('m(ut,{action:"templates",href:"/templates",icon:"#templates",',
                      'm(ut,{hidden:!0,action:"templates",href:"/templates",icon:"#templates",'),
    }
    for key in cfg['hideRail']:
        old, new = rail[key]
        if h.count(old) != 1:
            raise SystemExit(f"index.html: rail anchor for {key!r} found {h.count(old)} times (expected 1)")
        h = h.replace(old, new)
    # hint under the recent-files list: dropping a file anywhere on the window opens it (the empty-state box already says so)
    hint = [
        ('dropZoneOpenAction:"Open file",', 'dropZoneOpenAction:"Open file",dropHintList:"Tip: drag a file onto this window to open it",dlFontLabel:"Interface font",dlFontDescr:"Change it from the Start menu: Daylight Office font settings. Applies after the app restarts.",'),
        ('dropZoneOpenAction:"파일 열기",', 'dropZoneOpenAction:"파일 열기",dropHintList:"팁: 파일을 이 창에 끌어다 놓으면 바로 열어 줍니다",dlFontLabel:"인터페이스 글꼴",dlFontDescr:"시작 메뉴의 “Daylight Office 글꼴 설정”에서 바꿉니다. 앱을 다시 시작하면 적용됩니다.",'),
    ]
    for old, new in hint:
        if h.count(old) < 1:
            raise SystemExit(f"index.html: drop-hint dictionary anchor {old!r} not found")
        h = h.replace(old, new)
    for old, new in [
        ('onAddToChat:N}),null),L})()}const by=',
         'onAddToChat:N}),null),O(L,m(j,{get when(){return ce(()=>!!i())()&&c()},get children(){var Y=dlDropHint();return O(Y,()=>D("dropHintList")),Y}})),L})()}var dlDropHint=P("<p class=drop-hint>");const by='),
    ]:
        if h.count(old) != 1:
            raise SystemExit(f"index.html: drop-hint code anchor found {h.count(old)} times (expected 1)")
        h = h.replace(old, new)
    # settings: the dead 'Enable AI features' row becomes an 'Interface font' info row pointing to the Start menu
    # shortcut (set-ui-font.ps1). A daylight-font: link was tried: the app never hands custom schemes to Windows.
    ai = ('O(c,m(j,{get when(){return B.showai===!0},get children(){var A=bC(),R=A.firstChild,V=R.firstChild;return O(R,()=>D("settingsEnableAI"),V),O(R,()=>Ue.available&&" *",V),O(V,()=>D("settingsEnableAIDescr")),O(A,m(Bi,{id:"chb-use-ai",get checked(){return B.useai!==!1},onChange:z=>de("useai",z)}),null),',
          'O(c,m(j,{get when(){return!0},get children(){var A=bC(),R=A.firstChild,V=R.firstChild;return O(R,()=>D("dlFontLabel"),V),O(V,()=>D("dlFontDescr")),')
    if h.count(ai[0]) != 1:
        raise SystemExit(f"index.html: AI settings row anchor found {h.count(ai[0])} times (expected 1)")
    h = h.replace(*ai)
    # recent files: no 'AI chat' entry in the row menu or as a row button (the AI functions are not available here)
    ai = ('get when(){return ce(()=>!!e.model.islocal)()&&yo()}', 'get when(){return!1}')
    if h.count(ai[0]) != 2:
        raise SystemExit(f"index.html: recent-file AI chat anchor found {h.count(ai[0])} times (expected 2)")
    h = h.replace(*ai)
    # recent-file dates: format with the UI language (UC() holds the dictionary locale), not the browser default
    # (which is English here, so Korean UI showed "5 seconds ago")
    dt = ('const Qn=new Intl.RelativeTimeFormat(void 0,{numeric:"auto"}),Za=new Intl.DateTimeFormat(void 0,{year:"numeric",month:"short",day:"numeric"}),Cm=new Intl.DateTimeFormat(void 0,{hour:"2-digit",minute:"2-digit"}),',
          'const dlLoc=()=>String(UC()).replaceAll("_","-"),Qn={format:(a,b)=>new Intl.RelativeTimeFormat(dlLoc(),{numeric:"auto"}).format(a,b)},Za={format:a=>new Intl.DateTimeFormat(dlLoc(),{year:"numeric",month:"short",day:"numeric"}).format(a)},Cm={format:a=>new Intl.DateTimeFormat(dlLoc(),{hour:"2-digit",minute:"2-digit"}).format(a)},')
    if h.count(dt[0]) != 1:
        raise SystemExit(f"index.html: date formatter anchor found {h.count(dt[0])} times (expected 1)")
    h = h.replace(*dt)
    m = re.search(r'<symbol id="idx-logo"[^>]*>.*?</symbol>', h, re.S)
    if not m:
        raise SystemExit("index.html: idx-logo symbol not found")
    h = h[:m.start()] + art.about_symbol() + h[m.end():]
    anchor = '<p class=about-version><span class=about-edition-label></span> </p></div></section>'
    if h.count(anchor) != 1:
        raise SystemExit("index.html: About template anchor not found exactly once")
    notice = cfg['notice'].format(version=version, modified=cfg['modified'])
    h = h.replace(anchor, anchor.replace('</div></section>', f'<p class=about-version>{notice}</p></div></section>'))
    # extra CSS (e.g. hide the About update row: the update check is disabled)
    if cfg.get('css'):
        if h.count('</head>') != 1:
            raise SystemExit("index.html: expected exactly one </head>")
        h = h.replace('</head>', '<style>' + cfg['css'] + '</style></head>')
        log.append(f"  index.html: css injected: {cfg['css']}")
    if not dry:
        open(path, 'wb').write(h.encode('utf-8'))
    log.append("  index.html: " + '; '.join(f"{o!r} x{c}" for o, c in counts) + f" -> {cfg['product']!r}")
    log.append(f"  index.html: idx-logo replaced; About notice added; rail hidden: {', '.join(cfg['hideRail'])}")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--app', required=True)
    ap.add_argument('--config', default=os.path.join(HERE, 'brand.json'))
    ap.add_argument('--assets', default=os.path.join(ROOT, 'assets', 'brand'))
    ap.add_argument('--out', default=os.path.join(ROOT, 'build', 'brand'))
    ap.add_argument('--dry-run', action='store_true')
    a = ap.parse_args()
    cfg = json.load(open(a.config, encoding='utf-8'))
    ver = cfg['baseVersion']
    offsets = json.load(open(os.path.join(HERE, 'offsets.json'), encoding='utf-8'))[ver]
    os.makedirs(a.out, exist_ok=True)
    log = [f"brand: {cfg['name']} / {cfg['product']}  (base {ver})"]

    ico_path = os.path.join(a.assets, 'app.ico')
    ico = open(ico_path, 'rb').read() if os.path.exists(ico_path) else art.app_ico()
    open(os.path.join(a.out, 'app.ico'), 'wb').write(ico)

    bufs = {}
    for f in ('editors.exe', 'DesktopEditors.exe'):
        bufs[f] = bytearray(open(os.path.join(a.app, f), 'rb').read())
    for (f, kind, old, new, lo, hi) in binary_rules(cfg):
        patch_whole(bufs[f], kind, old, new, lo, hi, log, a.dry_run, label=f)
    patch_pngs(bufs['editors.exe'], offsets, a.assets, log, a.dry_run)
    qt_path = os.path.join(a.assets, 'app_qt.ico')   # slim variant when the full icon does not fit the Qt resource slot
    patch_qt_ico(bufs['editors.exe'], open(qt_path, 'rb').read() if os.path.exists(qt_path) else ico, log, a.dry_run)
    if not a.dry_run:
        for f, b in bufs.items():
            open(os.path.join(a.app, f), 'wb').write(bytes(b))
    log.append("[remove]")
    import shutil
    for rel in cfg['removePaths']:
        t = os.path.join(a.app, rel.replace('/', os.sep))
        if not os.path.exists(t):
            raise SystemExit(f"removePaths: not found: {rel}")
        if not a.dry_run:
            shutil.rmtree(t) if os.path.isdir(t) else os.remove(t)
        log.append(f"  removed {rel}")
    log.append("[index.html]")
    patch_index_html(os.path.join(a.app, 'index.html'), cfg, ver, log, a.dry_run)
    print('\n'.join(log))
    print('app icon for the PE resource step:', os.path.join(a.out, 'app.ico'))


if __name__ == '__main__':
    main()
