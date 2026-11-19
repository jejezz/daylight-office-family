"""Checks of the single-page start screen (assets/start) through the DevTools port. Called by tests\\start-screen.ps1.
usage: start-screen-check.py <shots-prefix>    (the app runs with --remote-debugging-port=9333 and has 3 recent files)"""
import sys, json, time, base64, os
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), 'lib'))
import cdp

s = cdp.connect(9333, match='onlyoffice://plugin')
v = lambda e: cdp.value(s, e)
fails = []

def check(name, ok, detail=''):
    print(('PASS  ' if ok else 'FAIL  ') + name + ('  ' + str(detail) if detail != '' else ''))
    if not ok:
        fails.append(name)

def call(method, params=None):
    cdp._id[0] += 1
    i = cdp._id[0]
    cdp.send(s, {'id': i, 'method': method, 'params': params or {}})
    while True:
        r = cdp.recv(s)
        if r.get('id') == i:
            return r

def shot(suffix):
    r = call('Page.captureScreenshot', {'format': 'png'})
    open(sys.argv[1] + suffix, 'wb').write(base64.b64decode(r['result']['data']))

def key(k, code, vk):
    for t in ('keyDown', 'keyUp'):
        call('Input.dispatchKeyEvent', {'type': t, 'key': k, 'code': code, 'windowsVirtualKeyCode': vk})

def names():
    return json.loads(v("JSON.stringify([...document.querySelectorAll('#dl-home .dl-row .dl-t')].map(e=>e.textContent))"))

def click(sel, txt=None):
    return v("(()=>{const l=[...document.querySelectorAll(%s)];const e=%s;if(!e)return false;e.click();return true})()"
             % (json.dumps(sel), ("l.find(x=>x.textContent.includes(%s))" % json.dumps(txt)) if txt else 'l[0]'))

call('Emulation.setDeviceMetricsOverride', {'width': 1100, 'height': 640, 'deviceScaleFactor': 1, 'mobile': False})
time.sleep(0.5)
check('home page is mounted', v("!!document.getElementById('dl-home')"))
check('left rail is hidden', v("getComputedStyle(document.querySelector('.col-sidebar')).display") == 'none')
bar = v("[...document.querySelectorAll('#dl-home .dl-bar button')].map(b=>b.textContent.trim()).length")
check('toolbar has 4 new + open + settings + about buttons', bar == 7, bar)
check('toolbar icons are 64px', v("[...document.querySelectorAll('#dl-home .dl-bar .dl-btn img')].every(i=>Math.round(i.getBoundingClientRect().width)===64)"))
orig = v("document.body.getAttribute('applang')")
bar_text = "document.querySelector('#dl-home .dl-bar').innerText"
v("document.body.setAttribute('applang','ko-KR')")
time.sleep(0.8)
check('language switch: Korean toolbar and header', '문서' in v(bar_text) and '이름' in v("document.querySelector('#dl-home .dl-head').innerText"))
v("document.body.setAttribute('applang','en-US')")
time.sleep(0.8)
check('language switch: English toolbar and header', 'Document' in v(bar_text) and 'Name' in v("document.querySelector('#dl-home .dl-head').innerText"))
# other languages: the bundle's own words (toolbar) and our translations (footer hint)
foot = "document.querySelector('#dl-home .dl-foot').innerText"
for code, bar_word, hint_word in [('ja-JP', 'ドキュメント', 'ドラッグ'), ('de-DE', 'Dokument', 'ziehen'), ('pt-BR', 'Documento', 'arrastar'), ('es-ES', 'Documento', 'arrastrar'), ('zh-CN', '打开', '拖到')]:
    v("document.body.setAttribute('applang',%s)" % json.dumps(code))
    time.sleep(0.6)
    check('language %s: toolbar and hint' % code, bar_word in v(bar_text) and hint_word in v(foot), ' '.join(v(bar_text).split())[:60])
v("document.body.setAttribute('applang',%s)" % json.dumps(orig or 'en-US'))
time.sleep(0.8)
check('clear-all looks like a button (border and fill)', v("(()=>{const b=document.querySelector('#dl-home .dl-clear');const c=getComputedStyle(b);return parseFloat(c.borderTopWidth)>=1&&c.backgroundColor!=='rgba(0, 0, 0, 0)'&&b.getBoundingClientRect().height>=28})()"))
check('content uses the full width', v("document.getElementById('dl-home').getBoundingClientRect().width") > 900)
rows = names()
check('recent files are listed', len(rows) >= 3, rows)
shot('-home.png')

# settings: modal above the home page
click('#dl-home .dl-btn', 'Settings')
click('#dl-home .dl-btn', '설정')
time.sleep(1.5)
check('settings opens as a modal', v("document.body.classList.contains('dl-modal')"), v('location.hash'))
check('home page stays visible behind it', v("getComputedStyle(document.querySelector('.home-panel')).display") == 'block')
check('home page is inert while the dialog is open', v("document.getElementById('dl-home').inert") is True)
shot('-settings.png')
# a dropdown inside the dialog must show its list on top of the dialog (it is drawn in a separate layer under <body>)
v("(()=>{const c=document.querySelector('.col-center > :not(.home-panel):not(#dl-scrim):not(#dl-close) button[aria-haspopup]');const b=c.getBoundingClientRect();for(const t of ['pointerdown','mousedown','pointerup','mouseup','click'])c.dispatchEvent(new (t.startsWith('pointer')?PointerEvent:MouseEvent)(t,{bubbles:true,cancelable:true,clientX:b.x+5,clientY:b.y+5,button:0,pointerType:'mouse'}))})()")
time.sleep(0.8)
shot('-dropdown.png')
check('dropdown list is visible above the dialog', v("(()=>{const lb=document.querySelector('[role=listbox]');if(!lb)return false;const r=lb.getBoundingClientRect();const t=document.elementFromPoint(r.x+20,r.y+20);return !!t&&lb.contains(t)})()"))
key('Escape', 'Escape', 27)
time.sleep(0.5)
out = []
for i in range(14):
    key('Tab', 'Tab', 9)
    time.sleep(0.12)
    out.append(v("(()=>{const a=document.activeElement;const d=document.querySelector('.col-center > :not(.home-panel):not(#dl-scrim):not(#dl-close)');return !!a&&((d&&d.contains(a))||a.id==='dl-close')})()"))
check('Tab never leaves the dialog', all(out), out)
key('Escape', 'Escape', 27)
time.sleep(1)
check('Escape closes the dialog', v('location.hash') in ('#/', '') and not v("document.body.classList.contains('dl-modal')"))

# one removal removes exactly one row
before = names()
target = before[1]
v("(()=>{const r=[...document.querySelectorAll('#dl-home .dl-row')].find(x=>x.querySelector('.dl-t').textContent==%s);r.querySelector('.dl-more').click()})()" % json.dumps(target))
time.sleep(0.4)
labels = v("[...document.querySelectorAll('#dl-menu button')].map(b=>b.textContent)")
check('row menu: folder, pin, remove only', len(labels) == 3, labels)
shot('-menu.png')
click('#dl-menu button', 'Remove')
click('#dl-menu button', '제거')
time.sleep(1.2)
after = names()
check('removing one file removes only that file', after == [n for n in before if n != target], after)

# clear all: one button, asks first, cancel keeps the list
check('exactly one clear-all control exists', v("document.querySelectorAll('#dl-home .dl-clear').length") == 1)
click('#dl-home .dl-clear')
time.sleep(0.3)
check('clear all asks for confirmation', v("!!document.querySelector('#dl-home .dl-confirm')"))
shot('-confirm.png')
click('#dl-home .dl-no')
time.sleep(0.3)
check('cancel keeps the list', names() == after)
click('#dl-home .dl-clear')
time.sleep(0.2)
click('#dl-home .dl-yes')
time.sleep(1.2)
check('confirmed clear empties the list', names() == [] and v("!!document.querySelector('#dl-home .dl-empty')"))
shot('-empty.png')

print('\n%d failed' % len(fails))
sys.exit(1 if fails else 0)
