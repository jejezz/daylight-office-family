r"""Checks of the margin boundary marks (engine patch 0001 + View tab checkbox). Run by tests\margin-marks.ps1 against the
running app (--remote-debugging-port=9333). Prints PASS/FAIL lines; exit 1 if any failed."""
import os, sys, time
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), 'lib'))
import cdp

s = cdp.connect(9333)
fails = 0
def check(name, ok, detail=''):
    global fails
    print(('PASS' if ok else 'FAIL'), name, detail)
    if not ok: fails += 1
def js(expr):
    return cdp.value(s, "(function(){var w=document.querySelector('iframe').contentWindow;var a=w.Asc.editor;" + expr + "})()")

# overlay helpers: number of non-transparent pixels, and whether a 3x3 area around (x,y) has any
HELP = """
var wc=a.WordControl, c=wc.m_oOverlay.HtmlElement, ctx=c.getContext('2d');
function count(){var d=ctx.getImageData(0,0,c.width,c.height).data,n=0;for(var i=3;i<d.length;i+=4)if(d[i])n++;return n;}
function hit(x,y){var d=ctx.getImageData(Math.round(x)-2,Math.round(y)-2,5,5).data;for(var i=3;i<d.length;i+=4)if(d[i])return true;return false;}
function corners(){var dd=wc.m_oDrawingDocument,p=dd.m_arrPages[0],dp=p.drawingPage,kx=(dp.right-dp.left)/p.width_mm,ky=(dp.bottom-dp.top)/p.height_mm;
 return {x1:dp.left+p.margin_left*kx,y1:dp.top+p.margin_top*ky,x2:dp.left+p.margin_right*kx,y2:dp.top+p.margin_bottom*ky,W:c.width,H:c.height};}
"""
# 1. UI: the checkbox exists in the View tab, with its label
ui = js("var d=w.document;var e=d.getElementById('slot-chk-marginmarks');return e?e.textContent.trim():null")
check('View tab has the "Text boundaries" checkbox', ui == 'Text boundaries', repr(ui))
check('API function exported', js("return typeof a.put_ShowMarginBoundaries+'/'+typeof a.get_ShowMarginBoundaries") == 'function/function')

# 2. off -> no marks
js("a.put_ShowMarginBoundaries(false);return 1")
time.sleep(0.5)
n_off = js(HELP + "wc.OnUpdateOverlay();return count()")
check('off: overlay has no pixels', n_off == 0, f'pixels={n_off}')

# 3. on -> marks at the four text-area corners (zoom 100, then 50 and 200 after the page moves)
for zoom in (100, 50, 200):
    js(f"a.zoom({zoom});return 1")
    time.sleep(1.5)
    js("a.put_ShowMarginBoundaries(true);return 1")
    time.sleep(0.5)
    r = js(HELP + "wc.OnUpdateOverlay();var k=corners();return {n:count(),k:k,tl:hit(k.x1,k.y1),tr:hit(k.x2,k.y1),bl:hit(k.x1,k.y2),br:hit(k.x2,k.y2),vis:wc.m_oOverlay.HtmlElement.style.display}")
    k = r['k']
    # a corner that is scrolled out of the visible canvas cannot be tested
    vis = lambda x, y: 0 <= x < k['W'] and 0 <= y < k['H']
    cs = {'tl': (k['x1'], k['y1']), 'tr': (k['x2'], k['y1']), 'bl': (k['x1'], k['y2']), 'br': (k['x2'], k['y2'])}
    tested = [n for n, (x, y) in cs.items() if vis(x, y)]
    check(f'zoom {zoom}: marks drawn', r['n'] > 20 and r['vis'] == 'block', f"pixels={r['n']}")
    check(f'zoom {zoom}: visible corners have a mark', len(tested) > 0 and all(r[n] for n in tested), f"tested={tested} " + str({n: r[n] for n in tested}))

# 4. off again -> cleared; the saved setting is restored to off so the developer's state is not changed
js("a.put_ShowMarginBoundaries(false);return 1")
time.sleep(0.5)
n_off2 = js(HELP + "wc.OnUpdateOverlay();return count()")
check('off again: overlay cleared', n_off2 == 0, f'pixels={n_off2}')
js("a.zoom(100);w.Common.localStorage.setBool('de-show-margin-marks', false);return 1")
print(f'\n{"all passed" if not fails else str(fails) + " failed"}')
sys.exit(1 if fails else 0)
