"""Let the desktop app save .xlsm (macro-enabled workbook) in place and offer it in Save As.

  python tools/formats/apply.py --app build/app [--dry-run]

Why (upstream 10.0.0.169, sources: ONLYOFFICE/desktop-sdk and desktop-apps at the same tag):
  - desktop-sdk cefview.cpp LocalFile_GetSupportSaveFormats() lists the formats a spreadsheet can be saved to.
    XLSM is missing, so an opened .xlsm is treated like .xls: Ctrl+S always opens Save As with xlsx preselected.
  - desktop-apps cfiledialog.cpp m_mapFilters (format -> dialog label) has no XLSM entry either, so even when the
    editor asks for XLSM the dialog returns format 0 and the save fails ("This file cannot be saved or created").
  The converter (x2t) and the editor engine already write xlsm correctly. We reuse the XLTM (macro-enabled template,
  0x107) slot for XLSM (0x105) in both tables: XLTM can no longer be chosen in Save As (rarely used), XLSM can.

Every rule must match exactly the expected number of times, so an upstream upgrade stops the build instead of
patching the wrong bytes (re-derive the patterns from the sources above).
"""
import argparse
import os
import sys
import zlib

ZWSP = '​'   # zero-width space: pads a shorter label to the original length (Qt .qm records keep their size)


def h(s):
    return bytes.fromhex(s)


def u16be(s):
    return s.encode('utf-16-be')


def qm_label(old, new):
    """A .qm translation record (tag 3, be32 byte length, UTF-16BE text) with the text replaced, same length."""
    if len(new) > len(old):
        raise SystemExit(f"label longer than original: {new!r}")
    new = new + ZWSP * (len(old) - len(new))
    n = len(u16be(old)).to_bytes(4, 'big')
    return b'\x03' + n + u16be(old), b'\x03' + n + u16be(new)


# (file, description, old bytes, new bytes, expected count in the raw file)
RAW_RULES = [
    # LocalFile_GetSupportSaveFormats, spreadsheet branch: arFormats.push_back(XLTM) inlined as
    #   mov dword [rbp+10h], 107h ; cmp rdx,[rbx+10h] ; je ... ; mov dword [rdx], 107h
    ('ascdocumentscore.dll', 'save-format list: XLTM -> XLSM',
     h('c7451007010000483b5310740dc70207010000'),
     h('c7451005010000483b5310740dc70205010000'), 1),
    # CFileDialogWrapper ctor: m_mapFilters[XLTM] = tr("Macro-enabled spreadsheet template") + " (*.xltm)"
    #   mov dword [rbp+128h], 107h ; mov dword [rsp+20h], -1 ; xor r9d,r9d ; lea r8, <label>
    ('editors.exe', 'save dialog filter key: XLTM -> XLSM',
     h('c78528010000070100' '00c7442420ffffffff4533c94c8d05'),
     h('c78528010000050100' '00c7442420ffffffff4533c94c8d05'), 1),
    ('editors.exe', 'save dialog filter pattern',
     b'\x00 (*.xltm)\x00', b'\x00 (*.xlsm)\x00', 1),
    # Korean label (uncompressed ko .qm resource), same wording style as the pptm entry
    ('editors.exe', 'save dialog label (ko)',
     *qm_label('매크로 지원 스프레드시트 템플릿', '매크로 지원 스프레드시트'), 1),
]

# English label: inside zlib-compressed Qt resources (the English .qm files and languages that kept the English text)
EN_LABEL = qm_label('Macro-enabled Spreadsheet Template', 'Macro-enabled Spreadsheet')
EN_RESOURCES = 5
QM_MAGIC = h('3cb86418caef9c95cd211cbf60a1bddd')


def patch_raw(buf, desc, old, new, want, log):
    n = buf.count(old)
    if n != want:
        raise SystemExit(f"{desc}: expected {want} match(es), found {n} (upstream changed? re-derive the pattern)")
    if len(old) != len(new):
        raise SystemExit(f"{desc}: replacement must keep the length")
    i = buf.find(old)
    while i >= 0:
        buf[i:i + len(old)] = new
        i = buf.find(old, i + len(new))
    log.append(f"  {desc}: x{n}")


def patch_compressed_qm(buf, old, new, want, log):
    """Qt rcc compressed resource: [be32 uncompressed size][zlib stream] inside a fixed slot; recompress in place."""
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
            out = d.decompress(data[i:i + 4000000])
        except Exception:
            continue
        if out[:16] == QM_MAGIC and old in out:
            used = len(data[i:i + 4000000]) - len(d.unused_data)
            hits.append((i, out, used))
    if len(hits) != want:
        raise SystemExit(f"English .qm label: expected {want} resource(s), found {len(hits)}")
    for i, out, used in hits:
        if out.count(old) != 1:
            raise SystemExit(f"English .qm at {i:#x}: label found {out.count(old)} times")
        z = zlib.compress(out.replace(old, new), 9)
        if len(z) > used:
            raise SystemExit(f"English .qm at {i:#x}: recompressed {len(z)} B does not fit the slot ({used} B)")
        buf[i:i + used] = z + b'\x00' * (used - len(z))
    log.append(f"  save dialog label (en): x{len(hits)} compressed .qm")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--app', required=True)
    ap.add_argument('--dry-run', action='store_true')
    a = ap.parse_args()
    log = ['formats: save .xlsm']
    bufs = {}
    for f, desc, old, new, want in RAW_RULES:
        if f not in bufs:
            bufs[f] = bytearray(open(os.path.join(a.app, f), 'rb').read())
        patch_raw(bufs[f], desc, old, new, want, log)
    patch_compressed_qm(bufs['editors.exe'], *EN_LABEL, EN_RESOURCES, log)
    if not a.dry_run:
        for f, b in bufs.items():
            open(os.path.join(a.app, f), 'wb').write(bytes(b))
    print('\n'.join(log))


if __name__ == '__main__':
    sys.stdout.reconfigure(encoding='utf-8')
    main()
