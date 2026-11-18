"""Appearance step: write the Saturn palette over the built-in 'theme-night' / 'theme-white' themes.

  python tools/theme/apply.py --app build/app.new

Why not register new themes: the desktop app only lists user theme files from the per-user data folder, and the
built-in themes live inside the executable. So the color tokens of the two built-in themes are overridden by a
<style id="daylight-theme"> block added at the end of <head> in every editor page. It comes after the (late
loaded) app.css in document order, so it wins at equal specificity, and it also recolors the loading skeleton.
"""
import argparse
import shutil
import json
import os
import re
import struct
import zlib

HERE = os.path.dirname(os.path.abspath(__file__))
APPS_REL = os.path.join('editors', 'web-apps', 'apps')
MARK = 'id="daylight-theme"'
USER_CSS = 'daylight-user.css'   # personal settings file next to the exe; linked after our CSS, never overwritten by the installer


def hex_rgb(h):
    h = h.lstrip('#')
    return tuple(int(h[i:i + 2], 16) for i in (0, 2, 4))


def rgb_hex(c):
    return '#%02X%02X%02X' % tuple(max(0, min(255, round(v))) for v in c)


def mix(a, b, t):
    ca, cb = hex_rgb(a), hex_rgb(b)
    return rgb_hex(tuple(ca[i] + (cb[i] - ca[i]) * t for i in range(3)))


def rgba(spec, alpha=None):
    r, g, b, a = spec.split(',')
    return f"rgba({r}, {g}, {b}, {alpha if alpha is not None else a})"


def header_colors(p):
    """Title-row color per editor type (Word blue, Excel green, PowerPoint orange, PDF red, like the MS Office
    signature colors) and the text/icon color on top of it; without a 'header' block the title row uses the bar color."""
    if 'header' not in p:
        return {k: p['bar'] for k in ('document', 'spreadsheet', 'presentation', 'pdf', 'visio')}, p['text']
    return dict(p['header']), p.get('headerText', '#FFFFFF')


def tokens(p):
    H, HT = header_colors(p)
    HOV, PRS = ('rgba(255,255,255,0.14)', 'rgba(255,255,255,0.26)') if 'header' in p else (rgba(p['hover']), rgba(p['press']))
    checked = mix(p['surface'], p['accent'], p['checkedMix'])
    checked_hover = mix(p['surface'], p['accent'], min(1.0, p['checkedMix'] + 0.10))
    t = {
        # title strip inside the editor window (the native tab row keeps the native dark/light look)
        'toolbar-header-document': H['document'], 'toolbar-header-spreadsheet': H['spreadsheet'],
        'toolbar-header-presentation': H['presentation'], 'toolbar-header-pdf': H['pdf'], 'toolbar-header-visio': H['visio'],
        'text-toolbar-header-on-background-document': HT, 'text-toolbar-header-on-background-spreadsheet': HT,
        'text-toolbar-header-on-background-presentation': HT, 'text-toolbar-header-on-background-pdf': HT,
        'text-toolbar-header-on-background-visio': HT,
        'text-toolbar-header': HT, 'icon-toolbar-header': HT,
        # selected-tab underline in the title/menu rows: visible on every editor color
        'highlight-header-tab-underline-document': HT, 'highlight-header-tab-underline-spreadsheet': HT,
        'highlight-header-tab-underline-presentation': HT, 'highlight-header-tab-underline-pdf': HT,
        'highlight-header-tab-underline-visio': HT,
        # surfaces
        'background-normal': p['surface'], 'background-toolbar': p['surface'], 'background-toolbar-additional': p['bar'],
        'background-contrast-popover': p['bar'], 'background-notification-popover': p['bar'],
        'background-primary-dialog-button': p['accent'], 'background-accent-button': p['accent'],
        # states
        'highlight-button-hover': rgba(p['hover']), 'highlight-button-pressed': checked,
        'highlight-button-pressed-hover': checked_hover,
        'highlight-header-button-hover': HOV, 'highlight-header-button-pressed': PRS,
        'highlight-primary-dialog-button-hover': mix(p['accent'], p['text'], 0.18),
        # borders
        'border-toolbar': rgba(p['stroke']), 'border-toolbar-active-panel-top': rgba(p['stroke']),
        'border-divider': rgba(p['stroke']), 'border-color-shading': rgba(p['stroke']),
        'border-regular-control': rgba(p['strokeStrong']), 'border-contrast-popover': rgba(p['strokeStrong']),
        'border-preview-hover': rgba(p['strokeStrong']), 'border-preview-select': p['accent'],
        'border-control-focus': p['accent'],
        # text and icons
        'text-normal': p['text'], 'text-normal-pressed': p['text'], 'text-secondary': p['muted'],
        'text-tertiary': mix(p['muted'], p['surface'], 0.35),
        'text-link': p['link'], 'text-link-hover': p['link'], 'text-link-active': p['link'], 'text-link-visited': p['link'],
        'text-inverse': p['accentText'],
        'icon-normal': p['text'], 'icon-normal-pressed': p['text'], 'icon-success': p['success'],
        # canvas: the area around the pages, rulers, scroll bars (the page itself stays white)
        'canvas-background': p['canvas'], 'canvas-page-border': rgba(p['stroke'], 0.18),
        'canvas-ruler-background': p['bar'], 'canvas-ruler-margins-background': p['surface'],
        'canvas-ruler-border': rgba(p['stroke']), 'canvas-ruler-mark': p['muted'], 'canvas-ruler-handle-border': p['muted'],
        'canvas-scroll-thumb': p['bar'], 'canvas-scroll-thumb-hover': mix(p['bar'], p['muted'], 0.35),
        'canvas-scroll-thumb-pressed': mix(p['bar'], p['muted'], 0.55), 'canvas-scroll-thumb-border': rgba(p['stroke']),
        'canvas-scroll-thumb-border-hover': rgba(p['strokeStrong']), 'canvas-scroll-thumb-border-pressed': rgba(p['strokeStrong']),
        'canvas-scroll-arrow': p['muted'],
    }
    return t


def parse_theme_block(css_text, selector):
    """All custom properties the app's own CSS defines for one built-in theme class (merged over its blocks)."""
    out = {}
    for m in re.finditer(re.escape(selector) + r'\{([^}]*)\}', css_text):
        for decl in m.group(1).split(';'):
            if ':' in decl:
                k, v = decl.split(':', 1)
                out[k.strip().lstrip('-')] = v.strip()
    return out


# Old neutral grays of the built-in themes -> palette roles. Only used for background/canvas tokens that the explicit
# mapping above does not cover (left/right panes, status bar, inactive tabs, sheet headers ...).
OLD_GRAYS = {
    'theme-night': {'#222222': 'surface', '#222': 'surface', '#404040': 'surface', '#333333': 'surface', '#333': 'surface',
                    '#2a2a2a': 'bar', '#555555': 'bar', '#555': 'bar', '#505050': 'bar', '#3a3a3a': 'bar'},
    'theme-white': {'#ffffff': 'surface', '#fff': 'surface', '#f7f7f7': 'bar', '#f1f1f1': 'bar', '#efefef': 'bar',
                    '#eeeeee': 'bar', '#eee': 'bar', '#e0e0e0': 'bar', '#f3f3f3': 'bar'},
}


def extra_tokens(p, app_css_text, explicit):
    old = parse_theme_block(app_css_text, ':root .' + p['theme'])
    extra = {}
    for k, v in old.items():
        if k in explicit or not (k.startswith('background') or k.startswith('canvas-')):
            continue
        role = OLD_GRAYS[p['theme']].get(v.lower())
        if role:
            extra[k] = p[role]
    return extra


def skeleton(p):
    """Colors of the loading skeleton (shown while a document opens), same palette."""
    H, _ = header_colors(p)
    return {
        'sk-background-toolbar': p['surface'], 'sk-background-toolbar-controls': p['surface'],
        'sk-background-toolbar-header-word': H['document'], 'sk-background-toolbar-header-pdf': H['pdf'],
        'sk-background-toolbar-header-slide': H['presentation'], 'sk-background-toolbar-header-cell': H['spreadsheet'],
        'sk-background-toolbar-header-visio': H['visio'],
        'sk-background-toolbar-tab': rgba(p['strokeStrong']), 'sk-background-toolbar-button': p['bar'],
        'sk-canvas-background': p['canvas'], 'sk-canvas-page-border': rgba(p['stroke']),
        'sk-shadow-toolbar': 'inset 0 -1px ' + rgba(p['stroke']),
    }


def decls(d):
    # !important: the page also writes cached colors of the current theme as inline/late styles; ours must win
    return ';'.join(f"--{k}:{v} !important" for k, v in d.items())


def all_tokens(p, app_css_text):
    t = tokens(p)
    ex = extra_tokens(p, app_css_text, t)
    # status bar and inactive tabs read slightly lighter than the panes
    for k in ('background-statusbar', 'background-toolbar-tab'):
        if k in ex:
            ex[k] = p['bar']
    t.update(ex)
    return t, len(ex)


def make_css(pal, app_css_text):
    dark, light = pal['dark'], pal['light']
    td, nd = all_tokens(dark, app_css_text)
    tl, nl = all_tokens(light, app_css_text)
    common = {k: v for k, v in pal.get('common', {}).items() if not k.startswith('_')}
    parts = [
        f":root{{{decls(common)}}}",
        # light defaults for the skeleton, then the dark override (same specificity pattern as the page's own CSS)
        f".loadmask{{{decls(skeleton(light))}}}",
        f".{dark['theme']} .loadmask,.theme-type-dark .loadmask{{{decls(skeleton(dark))}}}",
        f":root .{light['theme']}{{{decls(tl)}}}",
        f":root .{dark['theme']}{{{decls(td)}}}",
    ]
    sizes = {k: v for k, v in pal.get('sizes', {}).items() if not k.startswith('_')}
    parts.append(f":root .{light['theme']},:root .{dark['theme']}{{{decls(sizes)}}}")
    # Icon sheets are rebuilt larger by tools/icons (style.json scaleUp); the icon elements are zoomed by the same
    # ratio so sheet pixels map 1:1 to screen pixels (no stretching). Vector (svg) icons just scale.
    st = json.load(open(os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'icons', 'style.json'), encoding='utf-8'))
    zs, zb, zh = (st['scaleUp'][n] / st['cell'][n] for n in ('small', 'big', 'huge'))
    parts.append(f".toolbar__icon:not(.toolbar__icon-big),.menu__icon,.btn-toolbar:not(.x-huge) .icon:not(.toolbar__icon){{zoom:{zs:.5f}}}")
    parts.append(f".toolbar__icon.toolbar__icon-big,.x-huge .toolbar__icon,.btn-group.icon-top.x-huge .icon:not(svg),.btn.icon-top.x-huge .icon:not(svg),.btn-group.icon-top.x-huge svg.icon,.btn.icon-top.x-huge svg.icon{{zoom:{zb:.5f}}}")
    parts.append(f".options__icon-huge{{zoom:{zh:.5f}}}")
    if 'header' in light:
        # the colored title row needs the light glyph column of the header icon sheets (the light theme uses the dark one)
        parts.append(f":root .{light['theme']}{{--button-header-normal-icon-offset-x:-24px !important;--button-header-active-icon-offset-x:-24px !important}}")
    th = int(pal['layout']['document-title-height'])
    parts.append(f".top-title .cousers-menu{{top:calc({th}px + 28px - 8px) !important}}")
    hid = json.load(open(os.path.join(os.path.dirname(os.path.abspath(__file__)), 'hidden.json'), encoding='utf-8'))
    for g in hid['groups']:
        parts.append(f".separator:has(+ .group {g}),.group:has({g}){{display:none!important}}")
    parts.append(','.join(hid['elements']) + '{display:none!important}')
    fam = common.get('font-family-base-custom', '"Segoe UI"')
    parts.append(f":root{{--font-family-base-custom:var(--dl-font,{fam}) !important}}")
    parts.insert(0, font_face_css('../../common/main/resources/fonts/'))
    return '\n'.join(parts), nd, nl


def inject(app, css):
    apps = os.path.join(app, APPS_REL)
    block = f"<style {MARK}>\n{css}\n</style>"
    changed = 0
    for root, _dirs, files in os.walk(apps):
        for f in files:
            if not (f.startswith('index') and f.endswith('.html')):
                continue
            path = os.path.join(root, f)
            t = open(path, encoding='utf-8', errors='ignore', newline='').read()
            if 'resources/css/app.css' not in t or MARK in t:
                continue
            if t.count('</head>') != 1:
                raise SystemExit(f"{path}: expected exactly one </head>")
            rel = os.path.relpath(os.path.join(app, USER_CSS), root).replace(os.sep, '/')
            link = f'<link rel="stylesheet" href="{rel}">'
            open(path, 'w', encoding='utf-8', newline='').write(t.replace('</head>', block + link + '</head>'))
            changed += 1
    if changed < 6:
        raise SystemExit(f"theme css: only {changed} editor page(s) changed (expected 6 or more); upstream changed?")
    return changed


def solid(p, key, over='surface'):
    """A translucent stroke ('r,g,b,a') flattened onto a surface color, for places that need an opaque color."""
    r, g, b, a = p[key].split(',')
    base = hex_rgb(p[over])
    return rgb_hex(tuple(base[i] * (1 - float(a)) + float(c) * float(a) for i, c in enumerate((r, g, b))))


# ---- start screen (the shell's index.html uses its own, smaller token set) --------------------------------------------
def shell_tokens(p, common):
    t = p['text']
    return {
        'background-normal': p['canvas'], 'background-normal-element': p['bar'], 'background-normal-element-light': p['bar'],
        'background-tabbar': p['surface'], 'background-action-panel': p['surface'],
        'background-primary-button': p['accent'], 'background-scroll-thumb': mix(p['bar'], p['muted'], 0.25),
        'background-icon-normal': t,
        'highlight-button-hover': rgba(p['hover']), 'highlight-button-pressed': rgba(p['press']),
        'highlight-primary-button-hover': mix(p['accent'], t, 0.18), 'highlight-primary-button-pressed': mix(p['accent'], p['canvas'], 0.25),
        'highlight-text-select': mix(p['accent'], p['canvas'], 0.35),
        'highlight-scroll-thumb-hover': mix(p['bar'], p['muted'], 0.45), 'highlight-sidebar-item-pressed': p['bar'],
        'border-tabbar': solid(p, 'stroke'), 'border-divider': rgba(p['stroke']), 'border-regular-control': rgba(p['strokeStrong']),
        'border-control-focus': p['accent'],
        'text-normal': t, 'text-normal-pressed': t, 'text-secondary': p['muted'], 'text-tertiary': mix(p['muted'], p['surface'], 0.35),
        'text-link': p['link'], 'text-inverse': p['accentText'], 'icon-normal': t,
        'font-family-base': common.get('font-family-base-custom', '"Segoe UI"'),
    }


FONT_FILES = [('seoul_namsan_regular.ttf', 400), ('seoul_namsan_bold.ttf', 700), ('seoul_namsan_extra_bold.ttf', 800)]
FONT_SRC = os.path.normpath(os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', '..', 'assets', 'fonts', 'seoul-namsan'))
FONT_UI_REL = os.path.join('editors', 'web-apps', 'apps', 'common', 'main', 'resources', 'fonts')


def font_face_css(prefix):
    return '\n'.join(f"@font-face{{font-family:SeoulNamsan;font-weight:{w};font-style:normal;font-display:swap;src:url('{prefix}{f}') format('truetype')}}" for f, w in FONT_FILES)


def install_fonts(app):
    """SeoulNamsan: into the UI font folder (@font-face) and into the app's fonts folder (the document engine lists it)."""
    for dest in (os.path.join(app, FONT_UI_REL), os.path.join(app, 'fonts')):
        os.makedirs(dest, exist_ok=True)
        for f, _w in FONT_FILES:
            shutil.copy2(os.path.join(FONT_SRC, f), os.path.join(dest, f))
    shutil.copy2(os.path.join(FONT_SRC, 'LICENSE.txt'), os.path.join(app, 'fonts', 'SeoulNamsan-LICENSE.txt'))


def shell_css(pal):
    common = {k: v for k, v in pal.get('common', {}).items() if not k.startswith('_')}
    rules = []
    for key in ('light', 'dark'):
        p = pal[key]
        rules.append(f".{p['theme']}{{{decls(shell_tokens(p, common))}}}")
    # the UI font is fixed: every built-in theme (classic, dark, gray, ...) sets its own --font-family-base, so pin it on all elements
    fam = common.get('font-family-base-custom', '"Segoe UI"')
    # --dl-font is set on <html> by the user's "Interface font" setting (see tools/brand/apply.py); empty -> the default stack
    uf = f"var(--dl-font,{fam})"
    rules.append(f":root,:root *{{--font-family-base:{uf} !important;--font-family-base-custom:{uf} !important}}")
    rules.insert(0, font_face_css(FONT_UI_REL.replace(os.sep, '/') + '/'))
    return '\n'.join(rules)


def inject_shell(app, css):
    path = os.path.join(app, 'index.html')
    t = open(path, encoding='utf-8', errors='ignore', newline='').read()
    if MARK in t:
        return False
    if t.count('</head>') != 1:
        raise SystemExit("shell index.html: expected exactly one </head>")
    link = f'<link rel="stylesheet" href="{USER_CSS}">'
    open(path, 'w', encoding='utf-8', newline='').write(t.replace('</head>', f"<style {MARK}>\n{css}\n</style>{link}</head>"))
    return True


# ---- native window (tab strip, window buttons, menus): JSON resources compiled into editors.exe ------------------------
def native_values(p):
    s, b, c, t, m, a = p['surface'], p['bar'], p['canvas'], p['text'], p['muted'], p['accent']
    stroke, strong = solid(p, 'stroke', 'bar'), solid(p, 'strokeStrong', 'bar')
    hover = mix(b, t, 0.08)
    v = {
        'brand-word': c, 'brand-slide': c, 'brand-cell': c, 'brand-pdf': c, 'brand-draw': c,
        'window-background': s, 'window-border': solid(p, 'stroke'),
        'border-control-focus': a,
        'text-normal': t, 'text-pretty': t, 'text-inverse': p['accentText'],
        'tool-button-background': c, 'tool-button-hover-background': b, 'tool-button-pressed-background': mix(b, t, 0.12),
        'tool-button-active-background': s,
        'download-widget-background': b, 'download-widget-border': strong, 'download-item-hover-background': hover,
        'download-ghost-button-text': p['link'], 'download-label-text': t, 'download-label-text-info': m,
        'download-progressbar-chunk': a, 'download-scrollbar-handle': m,
        'menu-background': b, 'menu-border': strong, 'menu-item-hover-background': hover,
        'menu-text': t, 'menu-text-item-hover': t, 'menu-text-item-disabled': mix(m, b, 0.45), 'menu-separator': stroke,
        'tooltip-text': t, 'tooltip-border': strong, 'tooltip-background': b,
        'tab-active-background': b, 'tab-simple-active-background': b, 'tab-simple-active-text': t,
        'tab-default-active-background': b, 'tab-default-active-text': t, 'tab-divider': stroke,
    }
    return v


def patch_native_themes(app, pal):
    """Rewrite the two built-in themes' JSON resources inside editors.exe (zlib-compressed Qt resources:
    [be32 size-of-rest][be32 raw size][zlib stream]); the new stream must fit the old slot."""
    path = os.path.join(app, 'editors.exe')
    data = bytearray(open(path, 'rb').read())
    wanted = {pal['dark']['theme']: pal['dark'], pal['light']['theme']: pal['light']}
    done = []
    pos = 0
    raw = bytes(data)
    while True:
        i = raw.find(b'\x78\x9c', pos)
        if i < 0:
            break
        pos = i + 1
        try:
            d = zlib.decompressobj()
            out = d.decompress(raw[i:i + 8000])
        except Exception:
            continue
        if not out.startswith(b'{') or b'"values"' not in out[:400]:
            continue
        try:
            obj = json.loads(out.decode('utf-8'))
        except Exception:
            continue
        if obj.get('id') not in wanted:
            continue
        used = len(raw[i:i + 8000]) - len(d.unused_data)
        obj['values'].update({k: v for k, v in native_values(wanted[obj['id']]).items() if k in obj['values']})
        new_raw = json.dumps(obj, separators=(',', ':')).encode('utf-8')
        z = zlib.compress(new_raw, 9)
        if len(z) > used:
            raise SystemExit(f"native theme {obj['id']}: {len(z)} B does not fit the {used} B slot")
        data[i - 4:i] = struct.pack('>I', len(new_raw))
        data[i:i + used] = z + b'\x00' * (used - len(z))
        done.append(obj['id'])
    if sorted(done) != sorted(wanted):
        raise SystemExit(f"native themes found {done}, expected {sorted(wanted)}")
    open(path, 'wb').write(bytes(data))
    return done


def scale_font_sizes(app, factor):
    """Raise every hard-coded `font-size: Npx` in the editors' app.css by `factor` (menus, dialogs, panels, combo
    boxes, status bar...). Sizes that come from --font-size-base are already raised by palette.json 'sizes'."""
    changed = 0
    pat = re.compile(r'(font-size:\s*)(\d+)px')
    for ed in ('documenteditor', 'spreadsheeteditor', 'presentationeditor', 'pdfeditor', 'visioeditor'):
        path = os.path.join(app, APPS_REL, ed, 'main', 'resources', 'css', 'app.css')
        if not os.path.isfile(path):
            continue
        t = open(path, encoding='utf-8', errors='ignore', newline='').read()
        t, n = pat.subn(lambda m: m.group(1) + str(int(int(m.group(2)) * factor + 0.5)) + 'px', t)
        open(path, 'w', encoding='utf-8', newline='').write(t)
        changed += n
    return changed


def patch_layout_js(app, layout):
    """Set the title-row height the editors hard-code in JavaScript (exactly one match, or the build fails)."""
    path = os.path.join(app, APPS_REL, 'common', 'main', 'lib', 'util', 'utils.js')
    t = open(path, encoding='utf-8', errors='ignore', newline='').read()
    old = "Common.Utils.InternalSettings.set('document-title-height', 28);"
    if t.count(old) != 1:
        raise SystemExit(f"utils.js: expected one document-title-height line, found {t.count(old)} (upstream changed?)")
    t = t.replace(old, f"Common.Utils.InternalSettings.set('document-title-height', {int(layout['document-title-height'])});")
    open(path, 'w', encoding='utf-8', newline='').write(t)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--app', required=True)
    ap.add_argument('--palette', default=os.path.join(HERE, 'palette.json'))
    ap.add_argument('--print-css', action='store_true')
    a = ap.parse_args()
    pal = json.load(open(a.palette, encoding='utf-8'))
    app_css = os.path.join(a.app, APPS_REL, 'documenteditor', 'main', 'resources', 'css', 'app.css')
    app_css_text = open(app_css, encoding='utf-8', errors='ignore').read()
    css, nd, nl = make_css(pal, app_css_text)
    if a.print_css:
        print(css)
        print(shell_css(pal))
        return
    nf = scale_font_sizes(a.app, float(pal['sizes']['font-size-base'].rstrip('px')) / 12.0)
    print(f"theme: {nf} hard-coded font sizes in app.css scaled x{float(pal['sizes']['font-size-base'].rstrip('px')) / 12.0:.3f}")
    patch_layout_js(a.app, pal['layout'])
    install_fonts(a.app)
    for name in (USER_CSS, 'set-ui-font.ps1'):
        shutil.copy2(os.path.join(HERE, '..', '..', 'assets', 'user', name), os.path.join(a.app, name))
    n = inject(a.app, css)
    print(f"theme: Saturn palette over {pal['dark']['theme']} / {pal['light']['theme']} "
          f"(+{nd} / +{nl} background tokens recolored from the old grays), injected into {n} editor page(s), {len(css)} bytes of CSS")
    scss = shell_css(pal)
    print(f"theme: start screen (index.html) {'injected' if inject_shell(a.app, scss) else 'already present'}, {len(scss)} bytes of CSS")
    print(f"theme: native window themes rewritten in editors.exe: {', '.join(patch_native_themes(a.app, pal))}")


if __name__ == '__main__':
    main()
