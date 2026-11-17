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


# Interface font (user setting): kept in localStorage 'daylight-ui-font', applied as the CSS variable --dl-font on <html>.
# The shell and the editor pages (file: URLs share one localStorage) read it; the CSS written by tools/theme uses var(--dl-font, <default stack>).
DL_FONT_JS = r'''var dlStack='"SeoulNamsan","Segoe UI","Malgun Gothic",system-ui,sans-serif';function dlClean(v){return(v||"").replace(/["\;{}<>]/g,"").trim()}function dlRead(){try{return dlClean(localStorage.getItem("daylight-ui-font"))}catch(e){return""}}function dlApply(v){const r=document.documentElement.style;v?r.setProperty("--dl-font",'"'+v+'",'+dlStack):r.removeProperty("--dl-font")}var[dlFont,dlFontSet]=F(dlRead());function dlGetFont(){return dlFont()}function dlSetFont(v){dlFontSet((v||"").replace(/["\;{}<>]/g,""));v=dlClean(v);try{v?localStorage.setItem("daylight-ui-font",v):localStorage.removeItem("daylight-ui-font")}catch(e){}dlApply(v)}dlApply(dlRead());var[dlList,dlListSet]=F([]);var dlLoaded=!1;const dlCands=["Malgun Gothic","Segoe UI","Segoe UI Variable","Segoe UI Symbol","Segoe Print","Segoe Script","Arial","Arial Black","Arial Narrow","Arial Rounded MT Bold","Bahnschrift","Baskerville Old Face","Bell MT","Bodoni MT","Book Antiqua","Bookman Old Style","Calibri","Calibri Light","Cambria","Candara","Century","Century Gothic","Century Schoolbook","Comic Sans MS","Consolas","Constantia","Copperplate Gothic Light","Corbel","Courier New","Dubai","Ebrima","Franklin Gothic Medium","Gabriola","Gadugi","Garamond","Georgia","Gill Sans MT","Impact","Ink Free","Javanese Text","Leelawadee UI","Lucida Console","Lucida Sans Unicode","Microsoft JhengHei","Microsoft Sans Serif","Microsoft YaHei","MingLiU","MS Gothic","MS PGothic","MS Mincho","MV Boli","Myanmar Text","Nirmala UI","Palatino Linotype","Rockwell","Sitka Text","Sylfaen","Tahoma","Times New Roman","Trebuchet MS","Verdana","Yu Gothic","Yu Mincho","SimSun","SimHei","NSimSun","Gulim","GulimChe","Dotum","DotumChe","Batang","BatangChe","Gungsuh","GungsuhChe","Nanum Gothic","NanumGothic","Nanum Myeongjo","NanumMyeongjo","Nanum Barun Gothic","NanumBarunGothic","Nanum Square","NanumSquare","Nanum Pen Script","Nanum Gothic Coding","NanumGothicCoding","Noto Sans KR","Noto Serif KR","Noto Sans","Noto Serif","Noto Sans Mono","Pretendard","Pretendard Variable","D2Coding","Spoqa Han Sans Neo","KoPubWorld Dotum","KoPubWorld Batang","IBM Plex Sans KR","Gmarket Sans","SUIT","SUIT Variable","Paperlogy","SeoulNamsan","SeoulHangang","Source Han Sans K","Source Han Serif K","Apple SD Gothic Neo","HCR Batang","HCR Dotum","Roboto","Open Sans","Lato","Inter","Fira Sans","Fira Code","JetBrains Mono","Cascadia Code","Cascadia Mono","Hack","Ubuntu","Montserrat","Nunito","Poppins","Source Sans Pro","Source Sans 3","Source Code Pro","Helvetica","Helvetica Neue","Cooper Black","Papyrus","Tw Cen MT","Verdana Pro","Aptos","Aptos Display","Bierstadt","Grandview","Skeena","Seaford","Sagona","Tenorite","맑은 고딕","굴림","굴림체","돋움","돋움체","바탕","바탕체","궁서","궁서체","나눔고딕","나눔명조","나눔스퀘어","나눔바른고딕","나눔바른펜","나눔손글씨 펜","함초롬바탕","함초롬돋움","한컴 고딕","한컴 바탕","HY헤드라인M","HY견고딕","HY중고딕","HY신명조","HY견명조","HY울릉도M","HY강M","HY그래픽M","HY목판L","HY수평선M","HY엽서M","HY센스L","휴먼명조","휴먼고딕","휴먼둥근헤드라인","휴먼매직체","한양신명조","한양중고딕","배달의민족 주아","배달의민족 한나","배달의민족 도현","배달의민족 연성","배달의민족 기랑해랑","배달의민족 을지로체","야놀자 야체","에스코어 드림","S-Core Dream","이서윤체","서울한강체","서울남산체","제주고딕","제주명조","고운돋움","고운바탕","마루 부리","Maru Buri","KoPub돋움체","KoPub바탕체","윤고딕","윤명조","산돌고딕","Sandoll Gothic Neo","Cafe24 Ssurround","Cafe24 Ohsquare","빙그레체","Black Han Sans","Do Hyeon","Jua","Gothic A1","Gowun Dodum","Gowun Batang","Hahmlet","Nanum Brush Script","Single Day","Stylish","Sunflower","Yeon Sung","East Sea Dokdo"];function dlProbe(){const c=document.createElement("canvas").getContext("2d"),t="mmmmmmmmmmlli한글가나다 WWW",m=f=>{c.font="40px "+f;return c.measureText(t).width},a=m("monospace"),b=m("serif");return dlCands.filter(n=>{const q='"'+n+'",';return m(q+"monospace")!==a||m(q+"serif")!==b})}function dlLoad(){if(dlLoaded)return;dlLoaded=!0;dlListSet(dlProbe());if(!window.queryLocalFonts)return;const g=()=>{try{Promise.race([window.queryLocalFonts(),new Promise((r,j)=>setTimeout(j,4000))]).then(l=>{const s=[...new Set(l.map(x=>x.family))].sort((x,y)=>x.localeCompare(y));s.length>0&&dlListSet(s)}).catch(()=>{})}catch(e){}};document.addEventListener("pointerdown",g,{once:!0,capture:!0})}function dlOpts(){const l=dlList(),c=dlFont(),o=[{value:"__d",label:D("settUiFontDefault")}];c&&!l.includes(c)&&o.push({value:c,label:c});return o.concat(l.map(n=>({value:n,label:n})))}'''


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
        ('dropZoneOpenAction:"Open file",', 'dropZoneOpenAction:"Open file",dropHintList:"Tip: drag a file onto this window to open it",settUiFont:"Interface font",settUiFontDefault:"Default (SeoulNamsan)",'),
        ('dropZoneOpenAction:"파일 열기",', 'dropZoneOpenAction:"파일 열기",dropHintList:"팁: 파일을 이 창에 끌어다 놓으면 바로 열어 줍니다",settUiFont:"인터페이스 글꼴",settUiFontDefault:"기본 (서울남산체)",'),
    ]
    for old, new in hint:
        if h.count(old) < 1:
            raise SystemExit(f"index.html: drop-hint dictionary anchor {old!r} not found")
        h = h.replace(old, new)
    for old, new in [
        ('onAddToChat:N}),null),L})()}const by=',
         'onAddToChat:N}),null),O(L,m(j,{get when(){return ce(()=>!!i())()&&c()},get children(){var Y=dlDropHint();return O(Y,()=>D("dropHintList")),Y}})),L})()}var dlDropHint=P("<p class=drop-hint>");'+DL_FONT_JS+'const by='),
    ]:
        if h.count(old) != 1:
            raise SystemExit(f"index.html: drop-hint code anchor found {h.count(old)} times (expected 1)")
        h = h.replace(old, new)
    # settings: an 'Interface font' text field in place of the (disabled) country row
    country = ('get when(){return 0},get children(){var A=Ai(),R=A.firstChild,V=R.nextSibling;return O(R,()=>D("settingsCountry")),O(V,m(he,{get options(){return e()},get value(){return B.country},onChange:z=>de("country",z),disallowEmptySelection:!0,get children(){return[m(he.Trigger,{get class(){return Q.fullWidth}}),m(he.Content,{})]}}))',
               'get when(){return!0},get children(){var A=Ai(),R=A.firstChild,V=R.nextSibling;dlLoad();return O(R,()=>D("settUiFont","Interface font")),O(V,m(he,{get options(){return dlOpts()},get value(){return dlGetFont()||"__d"},onChange:z=>dlSetFont(z==="__d"?"":z),disallowEmptySelection:!0,get children(){return[m(he.Trigger,{get class(){return Q.fullWidth}}),m(he.Content,{})]}}))')
    if h.count(country[0]) != 1:
        raise SystemExit(f"index.html: country row anchor found {h.count(country[0])} times (expected 1)")
    h = h.replace(*country)
    # settings: drop the 'Enable AI features' row (the AI functions are not available here)
    ai = ('O(c,m(j,{get when(){return B.showai===!0},', 'O(c,m(j,{get when(){return!1},')
    if h.count(ai[0]) != 1:
        raise SystemExit(f"index.html: AI settings row anchor found {h.count(ai[0])} times (expected 1)")
    h = h.replace(*ai)
    # recent files: no 'AI chat' entry in the row menu or as a row button (the AI functions are not available here)
    ai = ('get when(){return ce(()=>!!e.model.islocal)()&&yo()}', 'get when(){return!1}')
    if h.count(ai[0]) != 2:
        raise SystemExit(f"index.html: recent-file AI chat anchor found {h.count(ai[0])} times (expected 2)")
    h = h.replace(*ai)
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
