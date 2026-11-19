/* Daylight start screen. Injected into index.html by tools/brand/apply.py (after the bundle).
   Talks to the native shell through window.AscDesktopEditor, the same calls the original start page uses:
     execCommand('create:new', 'word'|'cell'|'slide'|'form')   execCommand('open:folder', '')   (file dialog)
     execCommand('open:recent', json)   execCommand('files:explore', json)   execCommand('recent:pinned', json)
     LocalFileRecents() -> event 'onupdaterecents'   LocalFileRemoveRecent(id)   LocalFileRemoveAllRecents()
   The ids the shell hands out are POSITIONS in the list, renumbered after every removal: never keep one across a
   reload; every change reloads the list before the next click is possible. */
(function () {
  'use strict';
  var A = window.AscDesktopEditor;
  if (!A) return;

  // Texts. Three layers, later ones win:  OWN.en  <  the bundle's own translation of the same words (BUNDLE, all ~48
  // languages, extracted from the bundle's dictionaries by tools/brand/apply.py)  <  OWN[language].
  // OWN.ko is complete (it overrides the bundle); the other OWN entries only hold the words the bundle has no text for.
  var BUNDLE = /*DL_BUNDLE*/{}/*END*/;
  var OWN = {
    en: {
      create: 'New', word: 'Document', cell: 'Spreadsheet', slide: 'Presentation', form: 'PDF',
      open: 'Open', settings: 'Settings', about: 'About', name: 'Name', place: 'Location', last: 'Last opened',
      clearAll: 'Clear all', clearAsk: 'Clear the whole list?', yes: 'Clear', no: 'Cancel',
      empty: 'No recent files. Drag a file here or press Open.',
      hint: 'You can also drag a file onto this window to open it', folder: 'Show in folder', pin: 'Pin', unpin: 'Unpin',
      remove: 'Remove from list', close: 'Close', recovered: 'Recovered', now: 'just now', more: 'More', pinned: 'Pinned'
    },
    ko: {
      create: '신규 생성', word: '문서', cell: '스프레드시트', slide: '프레젠테이션', form: 'PDF',
      open: '열기', settings: '설정', about: '정보', name: '이름', place: '위치', last: '마지막으로 연 날짜',
      clearAll: '모두 지우기', clearAsk: '목록을 모두 지울까요?', yes: '지우기', no: '취소',
      empty: '최근 문서가 없습니다. 파일을 끌어다 놓거나 열기를 누르세요.',
      hint: '파일을 이 창에 끌어다 놓아도 열립니다', folder: '폴더에서 보기', pin: '고정', unpin: '고정 해제',
      remove: '목록에서 제거', close: '닫기', recovered: '복구', now: '방금', more: '더 보기', pinned: '고정됨'
    },
    ja: { about: 'バージョン情報',   // the bundle says 沿革 (history) here
      clearAll: 'すべて消去', clearAsk: 'リストをすべて消去しますか？', yes: '消去', no: 'キャンセル',
      empty: '最近使ったファイルはありません。ファイルをドラッグするか、「開く」を押してください。',
      hint: 'ファイルをこのウィンドウにドラッグしても開けます', close: '閉じる', now: 'たった今', more: 'その他', pinned: '固定済み', recovered: '復元' },
    'zh-cn': { clearAll: '全部清除', clearAsk: '清除整个列表吗？', yes: '清除', no: '取消',
      empty: '没有最近的文件。将文件拖到此处，或点击“打开”。',
      hint: '也可以把文件拖到此窗口来打开', close: '关闭', now: '刚刚', more: '更多', pinned: '已固定', recovered: '已恢复' },
    'zh-tw': { clearAll: '全部清除', clearAsk: '要清除整個清單嗎？', yes: '清除', no: '取消',
      empty: '沒有最近的檔案。請將檔案拖曳到此處，或按「開啟」。',
      hint: '也可以將檔案拖曳到此視窗來開啟', close: '關閉', now: '剛剛', more: '更多', pinned: '已釘選', recovered: '已復原' },
    de: { clearAll: 'Alle löschen', clearAsk: 'Gesamte Liste leeren?', yes: 'Leeren', no: 'Abbrechen',
      empty: 'Keine zuletzt verwendeten Dateien. Ziehen Sie eine Datei hierher oder klicken Sie auf „Öffnen“.',
      hint: 'Sie können Dateien auch auf dieses Fenster ziehen, um sie zu öffnen', close: 'Schließen', now: 'gerade eben', more: 'Mehr', pinned: 'Angeheftet', recovered: 'Wiederhergestellt' },
    fr: { clearAll: 'Tout effacer', clearAsk: 'Effacer toute la liste ?', yes: 'Effacer', no: 'Annuler',
      empty: 'Aucun fichier récent. Glissez un fichier ici ou cliquez sur « Ouvrir ».',
      hint: 'Vous pouvez aussi glisser un fichier sur cette fenêtre pour l’ouvrir', close: 'Fermer', now: 'à l’instant', more: 'Plus', pinned: 'Épinglé', recovered: 'Récupéré' },
    es: { clearAll: 'Borrar todo', clearAsk: '¿Borrar toda la lista?', yes: 'Borrar', no: 'Cancelar',
      empty: 'No hay archivos recientes. Arrastre un archivo aquí o pulse «Abrir».',
      hint: 'También puede arrastrar un archivo a esta ventana para abrirlo', close: 'Cerrar', now: 'ahora mismo', more: 'Más', pinned: 'Anclado', recovered: 'Recuperado' },
    ru: { clearAll: 'Очистить всё', clearAsk: 'Очистить весь список?', yes: 'Очистить', no: 'Отмена',
      empty: 'Нет недавних файлов. Перетащите файл сюда или нажмите «Открыть».',
      hint: 'Файл также можно открыть, перетащив его в это окно', close: 'Закрыть', now: 'только что', more: 'Ещё', pinned: 'Закреплён', recovered: 'Восстановлен' },
    pt: { clearAll: 'Limpar tudo', clearAsk: 'Limpar a lista inteira?', yes: 'Limpar', no: 'Cancelar',
      empty: 'Nenhum arquivo recente. Arraste um arquivo para cá ou clique em “Abrir”.',
      hint: 'Você também pode arrastar um arquivo para esta janela para abri-lo', close: 'Fechar', now: 'agora mesmo', more: 'Mais', pinned: 'Fixado', recovered: 'Recuperado' },
    it: { clearAll: 'Cancella tutto', clearAsk: 'Cancellare l’intero elenco?', yes: 'Cancella', no: 'Annulla',
      empty: 'Nessun file recente. Trascina un file qui oppure premi «Apri».',
      hint: 'Puoi anche trascinare un file su questa finestra per aprirlo', close: 'Chiudi', now: 'adesso', more: 'Altro', pinned: 'Fissato', recovered: 'Recuperato' }
  };
  // The UI language comes from the shell's settings message (the bundle copies it to body[applang] and changes it
  // at once when the user picks another language), so read it every time instead of only at start.
  function curLang() {
    return (document.body.getAttribute('applang') || new URLSearchParams(location.search).get('lang') || 'en').replace(/_/g, '-');
  }
  function ownKey(code) {
    var c = code.toLowerCase();
    if (OWN[c]) return c;
    var p = c.split('-')[0];
    if (p === 'zh') return /tw|hk|mo|hant/.test(c) ? 'zh-tw' : 'zh-cn';
    return OWN[p] ? p : null;
  }
  function bundleFor(code) {
    var c = code.toLowerCase(), k, p = c.split('-')[0], exact = null, prim = null;
    for (k in BUNDLE) {
      if (k.toLowerCase() === c) exact = BUNDLE[k];
      else if (k.toLowerCase() === p && !prim) prim = BUNDLE[k];
    }
    return exact || prim || null;
  }
  function textsFor(code) {
    var t = {}, k, src = [OWN.en, bundleFor(code), OWN[ownKey(code) || '']];
    src.forEach(function (s) { if (s) for (k in s) if (s[k]) t[k] = s[k]; });
    return t;
  }
  var langKey = null, T = OWN.en, loc = 'en';
  function setLang() {
    var code = curLang();
    if (code === langKey) return false;
    langKey = code; loc = code; T = textsFor(code);   // add a language = add an OWN entry (and its tag handling in ownKey)
    return true;
  }
  setLang();

  var items = [];
  var root = null, listEl = null, headEl = null, menuEl = null, scrimEl = null, closeEl = null;
  var asking = false;

  function cmd(name, value) {
    try { A.execCommand(name, typeof value === 'string' ? value : JSON.stringify(value)); } catch (e) { /* shell not ready */ }
  }
  function el(tag, cls, text) {
    var e = document.createElement(tag);
    if (cls) e.className = cls;
    if (text != null) e.textContent = text;
    return e;
  }
  // Icons8 PNGs (assets/start/icons): tools/brand/apply.py replaces the next line with {name: 'data:image/png;base64,...'}
  var ICONS = /*DL_ICONS*/{}/*END*/;
  // file extension -> toolbar icon name; anything else falls back to the bundle's own file-type symbol
  var EXT_ICON = { doc: 'doc', docx: 'doc', xls: 'xls', xlsx: 'xls', ppt: 'ppt', pptx: 'ppt', pdf: 'pdf' };
  function pic(name) {
    var im = document.createElement('img');
    im.src = ICONS[name];
    im.alt = '';
    im.draggable = false;
    return im;
  }
  function icon(id) {
    var ns = 'http://www.w3.org/2000/svg';
    var s = document.createElementNS(ns, 'svg');
    var u = document.createElementNS(ns, 'use');
    var ok = document.getElementById(id);
    u.setAttribute('href', '#' + (ok ? id : 'neutral'));
    s.appendChild(u);
    return s;
  }
  function splitName(path) {
    var base = path.replace(/^.*[\\/]/, '');
    var i = base.lastIndexOf('.');
    return { base: base, stem: i > 0 ? base.slice(0, i) : base, ext: i > 0 ? base.slice(i) : '' };
  }
  function parentOf(path) {
    var m = /^(.*)[\\/][^\\/]*$/.exec(path);
    return m ? m[1] : '';
  }

  // "19.11.2026 09:41" (day first) -> Date, or null
  function parseDate(s) {
    var m = /^(\d{1,2})\.(\d{1,2})\.(\d{4})\s+(\d{1,2}):(\d{2})/.exec(s || '');
    return m ? new Date(+m[3], +m[2] - 1, +m[1], +m[4], +m[5]) : null;
  }
  function when(s) {
    var d = parseDate(s);
    if (!d) return s || '';
    var sec = Math.round((Date.now() - d.getTime()) / 1000);
    try {
      if (sec < 60) return T.now;
      var rt = new Intl.RelativeTimeFormat(loc, { numeric: 'auto' });
      if (sec < 3600) return rt.format(-Math.floor(sec / 60), 'minute');
      if (sec < 86400) return rt.format(-Math.floor(sec / 3600), 'hour');
      if (sec < 7 * 86400) return rt.format(-Math.floor(sec / 86400), 'day');
      return new Intl.DateTimeFormat(loc, { year: 'numeric', month: 'short', day: 'numeric' }).format(d);
    } catch (e) { return s; }
  }

  // ---- data -------------------------------------------------------------------------------------------------
  var recents = null, recovers = null;
  function compose() {
    if (recents === null || recovers === null) return;
    var list = recents.map(function (r) { return { src: r, recovery: false }; })
      .concat(recovers.map(function (r) { return { src: r, recovery: true }; }));
    // pinned first, otherwise keep the shell's order (most recent first); recovered documents last
    var rank = function (x) { return x.recovery ? 2 : (x.src.pin ? 0 : 1); };
    items = list.map(function (x, i) { x.i = i; return x; })
      .sort(function (a, b) { return rank(a) - rank(b) || a.i - b.i; });
    render();
  }
  var listening = false;
  function listen() {
    if (listening) return;
    listening = true;
    // the shell also pushes these when a file is opened elsewhere, so the list stays current without polling
    A.on('onupdaterecents', function (d) { recents = Array.isArray(d) ? d : []; compose(); });
    A.on('onupdaterecovers', function (d) { recovers = Array.isArray(d) ? d : []; compose(); });
  }
  function load() {
    listen();
    A.LocalFileRecents();
    A.LocalFileRecovers();
  }

  function openItem(it) {
    var r = it.src;
    cmd('open:recent', { id: r.id, name: splitName(r.path || '').stem, path: r.path, type: r.type, cloud: r.cloud || '', hash: r.hash, recovery: it.recovery });
  }
  function removeItem(it) {
    try { if (it.recovery) A.LocalFileRemoveRecover(parseInt(it.src.id, 10)); else A.LocalFileRemoveRecent(parseInt(it.src.id, 10)); } catch (e) { /* ignore */ }
    load();
  }
  function pinItem(it) {
    cmd('recent:pinned', { id: it.src.id, pinned: !it.src.pin });
    load();
  }
  function clearAll() {
    try { A.LocalFileRemoveAllRecents(); } catch (e) { /* ignore */ }
    asking = false;
    load();
  }

  // ---- rendering --------------------------------------------------------------------------------------------
  function closeMenu() {
    if (menuEl) { menuEl.remove(); menuEl = null; }
    var o = root && root.querySelector('.dl-menu-open');
    if (o) o.classList.remove('dl-menu-open');
  }
  function openMenu(it, row, anchor) {
    closeMenu();
    row.classList.add('dl-menu-open');
    var m = el('div');
    m.id = 'dl-menu';
    m.setAttribute('role', 'menu');
    var add = function (label, fn) {
      var b = el('button', null, label);
      b.type = 'button';
      b.setAttribute('role', 'menuitem');
      b.onclick = function (ev) { ev.stopPropagation(); closeMenu(); fn(); };
      m.appendChild(b);
    };
    if (!it.recovery) {
      add(T.folder, function () { cmd('files:explore', { path: it.src.path, id: it.src.id, hash: it.src.hash }); });
      add(it.src.pin ? T.unpin : T.pin, function () { pinItem(it); });
    }
    add(T.remove, function () { removeItem(it); });
    document.body.appendChild(m);
    var r = anchor.getBoundingClientRect();
    var w = m.offsetWidth, h = m.offsetHeight;
    m.style.left = Math.max(4, Math.min(r.right - w, window.innerWidth - w - 4)) + 'px';
    m.style.top = (r.bottom + h + 8 > window.innerHeight ? Math.max(4, r.top - h - 4) : r.bottom + 4) + 'px';
    menuEl = m;
    m.firstChild.focus();
  }

  function buildHead() {
    headEl.textContent = '';
    headEl.appendChild(el('span', null, T.name));
    // one list-wide "clear" control lives here and nowhere else; it asks once before it clears
    if (!asking || items.length === 0) {
      headEl.appendChild(el('span', null, T.place));
      headEl.appendChild(el('span', 'dl-date', T.last));
    }
    if (items.length === 0) return;
    if (!asking) {
      var c = el('button', 'dl-clear', T.clearAll);
      c.type = 'button';
      c.onclick = function () { asking = true; buildHead(); };
      headEl.appendChild(c);
    } else {
      var box = el('span', 'dl-confirm');
      box.appendChild(el('span', null, T.clearAsk));
      var y = el('button', 'dl-yes', T.yes); y.type = 'button'; y.onclick = clearAll;
      var n = el('button', 'dl-no', T.no); n.type = 'button'; n.onclick = function () { asking = false; buildHead(); };
      box.appendChild(y); box.appendChild(n);
      headEl.appendChild(box);
      n.focus();
    }
  }

  function render() {
    if (!root) return;
    closeMenu();
    if (items.length === 0) asking = false;
    buildHead();
    listEl.textContent = '';
    if (items.length === 0) {
      listEl.appendChild(el('div', 'dl-empty', T.empty));
      return;
    }
    items.forEach(function (it) {
      var r = it.src;
      var nm = splitName(r.path || '');
      var row = el('div', 'dl-row' + (r.exist === false ? ' dl-gone' : ''));
      row.tabIndex = 0;
      row.setAttribute('role', 'button');
      row.title = r.path || '';

      var name = el('div', 'dl-name');
      var ext = nm.ext.slice(1).toLowerCase();
      name.appendChild(EXT_ICON[ext] && ICONS[EXT_ICON[ext]] ? pic(EXT_ICON[ext]) : icon(ext));
      var t = el('span', 'dl-t');
      t.appendChild(document.createTextNode(nm.stem));
      t.appendChild(el('span', 'dl-x', nm.ext));
      name.appendChild(t);
      if (it.recovery) name.appendChild(el('span', 'dl-badge', T.recovered));
      if (r.pin) {
        var ns = 'http://www.w3.org/2000/svg';
        var s = document.createElementNS(ns, 'svg');
        s.setAttribute('class', 'dl-pin');
        s.setAttribute('aria-label', T.pinned);
        var u = document.createElementNS(ns, 'use');
        u.setAttribute('href', '#pinned');
        s.appendChild(u);
        name.appendChild(s);
      }
      row.appendChild(name);

      var path = el('div', 'dl-path');
      var bdi = el('bdi', null, parentOf(r.path || ''));
      path.appendChild(bdi);
      row.appendChild(path);

      row.appendChild(el('div', 'dl-date', when(r.modifyed)));

      var more = el('button', 'dl-more', '⋯');
      more.type = 'button';
      more.setAttribute('aria-label', T.more);
      more.onclick = function (ev) { ev.stopPropagation(); openMenu(it, row, more); };
      row.appendChild(more);

      row.onclick = function () { openItem(it); };
      row.onkeydown = function (ev) {
        if (ev.target !== row) return;
        if (ev.key === 'Enter') openItem(it);
        else if (ev.key === 'Delete') removeItem(it);
      };
      row.oncontextmenu = function (ev) { ev.preventDefault(); openMenu(it, row, more); };
      listEl.appendChild(row);
    });
  }

  function button(label, fn, iconName) {
    var b = el('button', 'dl-btn');
    b.type = 'button';
    if (iconName && ICONS[iconName]) b.appendChild(pic(iconName));
    b.appendChild(document.createTextNode(label));
    b.onclick = fn;
    return b;
  }
  function sep() { return el('span', 'dl-sep'); }

  function clickRail(sel) {
    var n = document.querySelector(sel);
    if (n) n.click();
  }

  var barEl = null, footEl = null;
  function group(title, cls) {
    var g = el('div', 'dl-group' + (cls ? ' ' + cls : ''));
    if (title) g.appendChild(el('div', 'dl-group-title', title));
    var row = el('div', 'dl-group-row');
    g.appendChild(row);
    return { g: g, row: row };
  }
  function buildBar() {
    barEl.textContent = '';
    var n = group(T.create);
    [['word', 'doc'], ['cell', 'xls'], ['slide', 'ppt'], ['form', 'pdf']].forEach(function (p) {
      n.row.appendChild(button(T[p[0]], function () { cmd('create:new', p[0]); }, p[1]));
    });
    barEl.appendChild(n.g);
    barEl.appendChild(sep());
    var o = group('');
    o.row.appendChild(button(T.open, function () { cmd('open:folder', ''); }, 'folder'));
    barEl.appendChild(o.g);
    barEl.appendChild(el('span', 'dl-grow'));
    var r = group('');
    r.row.appendChild(button(T.settings, function () { clickRail('.tool-menu a.cls-btn'); }, 'settings'));
    r.row.appendChild(button(T.about, function () { clickRail('.tool-menu button.menu-btn'); }, 'info'));
    barEl.appendChild(r.g);
  }
  function applyLang() {
    if (!setLang() || !root || !root.isConnected) return;
    closeMenu();
    buildBar();
    footEl.textContent = T.hint;
    if (closeEl) closeEl.setAttribute('aria-label', T.close);
    render();
  }

  function mount(panel) {
    root = el('div');
    root.id = 'dl-home';
    barEl = el('div', 'dl-bar');
    buildBar();
    root.appendChild(barEl);

    headEl = el('div', 'dl-head');
    root.appendChild(headEl);
    listEl = el('div', 'dl-list');
    root.appendChild(listEl);
    footEl = el('div', 'dl-foot', T.hint);
    root.appendChild(footEl);
    panel.appendChild(root);
    render();
  }

  // ---- wiring -----------------------------------------------------------------------------------------------
  // Settings and the other routes open as a modal dialog on top of the home page. While it is open the home page is
  // inert (no focus, no clicks) and Tab stays inside the dialog.
  function isHome() { return location.hash === '' || location.hash === '#/' || location.hash === '#'; }
  function dialogEl() {
    return document.querySelector('.col-center > :not(.home-panel):not(#dl-scrim):not(#dl-close)');
  }
  function setInert(on) {
    if (root && 'inert' in root) root.inert = on;
  }
  function onRoute() {
    var home = isHome();
    document.body.classList.toggle('dl-modal', !home);
    setInert(!home);
    if (home) {
      if (root) load();
    } else {
      closeMenu();
      setTimeout(function () { if (closeEl && !isHome()) closeEl.focus(); }, 50);
    }
  }
  function closeDialog() { location.hash = '#/'; }

  function start() {
    var panel = document.querySelector('.home-panel');
    var center = document.querySelector('.col-center');
    if (!panel || !center || typeof A.on !== 'function') return false;
    var fresh = false;
    if (!root || !root.isConnected) { mount(panel); fresh = true; }
    if (!scrimEl || !scrimEl.isConnected) {
      scrimEl = el('div');
      scrimEl.id = 'dl-scrim';
      center.appendChild(scrimEl);
      closeEl = el('button', null, '✕');
      closeEl.id = 'dl-close';
      closeEl.type = 'button';
      closeEl.setAttribute('aria-label', T.close);
      closeEl.onclick = closeDialog;
      center.appendChild(closeEl);
      fresh = true;
    }
    if (fresh) onRoute();   // only when something was (re)created: this runs from a MutationObserver
    return true;
  }

  document.addEventListener('click', function (ev) {
    if (menuEl && !menuEl.contains(ev.target)) closeMenu();
  }, true);
  document.addEventListener('keydown', function (ev) {
    if (ev.key === 'Escape') {
      if (menuEl) { closeMenu(); return; }
      // an open dropdown inside the dialog handles its own Escape first
      if (!isHome() && !ev.defaultPrevented && !document.querySelector('[role=listbox]')) closeDialog();
      return;
    }
    if (ev.key === 'Tab' && !isHome()) {
      var d = dialogEl();
      if (!d) return;
      var f = Array.prototype.slice.call(d.querySelectorAll('a[href],button,input,select,textarea,[tabindex]:not([tabindex="-1"])'))
        .filter(function (n) { return !n.disabled && n.offsetParent !== null; });
      f.push(closeEl);   // the close button follows the dialog in the DOM: keep the same order
      var i = f.indexOf(document.activeElement);
      if (ev.shiftKey && i <= 0) { ev.preventDefault(); f[f.length - 1].focus(); }
      else if (!ev.shiftKey && (i === f.length - 1 || i < 0)) { ev.preventDefault(); f[0].focus(); }
    }
  });
  var lastHash = null;
  function routeTick() { if (location.hash !== lastHash) { lastHash = location.hash; if (root && root.isConnected) onRoute(); } }
  ['pushState', 'replaceState'].forEach(function (k) {
    var o = history[k];
    history[k] = function () { var r = o.apply(this, arguments); routeTick(); return r; };
  });
  window.addEventListener('hashchange', routeTick);
  window.addEventListener('popstate', routeTick);
  setInterval(function () { routeTick(); applyLang(); }, 250);   // safety net
  new MutationObserver(applyLang).observe(document.body, { attributes: true, attributeFilter: ['applang'] });
  window.addEventListener('focus', function () { if (root && root.isConnected) load(); });
  window.addEventListener('blur', closeMenu);

  // the bundle renders after this script runs: wait for its panel, and re-mount if it is ever re-created
  var tries = 0;
  var mo = new MutationObserver(function () { start(); });
  function boot() {
    var r = document.getElementById('root') || document.body;
    mo.observe(r, { childList: true, subtree: true });
    start();
  }
  if (document.readyState === 'loading') document.addEventListener('DOMContentLoaded', boot); else boot();
  var iv = setInterval(function () { if (start() || ++tries > 200) clearInterval(iv); }, 100);
})();
