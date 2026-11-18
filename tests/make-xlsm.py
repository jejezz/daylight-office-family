"""Make a minimal .xlsm (macro-enabled content type, no VBA part) for tests/xlsm-save.ps1, and inspect saved files.

  python tests/make-xlsm.py make  <out.xlsm>
  python tests/make-xlsm.py check <file.xlsm> <text>   -> exit 0 if macro-enabled and the text is in a cell
"""
import re
import sys
import zipfile

CT = ('<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'
      '<Types xmlns="http://schemas.openxmlformats.org/package/2006/content-types">'
      '<Default Extension="rels" ContentType="application/vnd.openxmlformats-package.relationships+xml"/>'
      '<Default Extension="xml" ContentType="application/xml"/>'
      '<Override PartName="/xl/workbook.xml" ContentType="application/vnd.ms-excel.sheet.macroEnabled.main+xml"/>'
      '<Override PartName="/xl/worksheets/sheet1.xml" '
      'ContentType="application/vnd.openxmlformats-officedocument.spreadsheetml.worksheet+xml"/>'
      '<Override PartName="/xl/worksheets/sheet2.xml" '
      'ContentType="application/vnd.openxmlformats-officedocument.spreadsheetml.worksheet+xml"/>'
      '</Types>')
RELS = ('<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'
        '<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">'
        '<Relationship Id="rId1" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/officeDocument" '
        'Target="xl/workbook.xml"/></Relationships>')
WB = ('<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'
      '<workbook xmlns="http://schemas.openxmlformats.org/spreadsheetml/2006/main" '
      'xmlns:r="http://schemas.openxmlformats.org/officeDocument/2006/relationships">'
      '<sheets><sheet name="Sheet1" sheetId="1" r:id="rId1"/><sheet name="Frozen" sheetId="2" r:id="rId2"/></sheets>'
      '</workbook>')
WB_RELS = ('<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'
           '<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">'
           '<Relationship Id="rId1" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/worksheet" '
           'Target="worksheets/sheet1.xml"/>'
           '<Relationship Id="rId2" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/worksheet" '
           'Target="worksheets/sheet2.xml"/></Relationships>')
# Second sheet (never shown during the test): frozen panes saved while scrolled, i.e. the frozen area starts at
# row 5 (sheetView topLeftCell A5), 3 rows x 2 columns frozen. The engine (patch sdkjs/0004) must save the same split;
# upstream wrote ySplit="-1" and Excel had to repair the file.
FROZEN = ('<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'
          '<worksheet xmlns="http://schemas.openxmlformats.org/spreadsheetml/2006/main"><sheetViews>'
          '<sheetView topLeftCell="A5" workbookViewId="0">'
          '<pane xSplit="2" ySplit="3" topLeftCell="C8" activePane="bottomRight" state="frozen"/>'
          '<selection pane="bottomRight" activeCell="C8" sqref="C8"/></sheetView></sheetViews><sheetData>'
          '<row r="1"><c r="A1" t="inlineStr"><is><t>frozen</t></is></c></row></sheetData></worksheet>')
FROZEN_SPLIT = ('2', '3')
SHEET = ('<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'
         '<worksheet xmlns="http://schemas.openxmlformats.org/spreadsheetml/2006/main"><sheetData>'
         '<row r="1"><c r="A1" t="inlineStr"><is><t>hello</t></is></c></row></sheetData></worksheet>')


def make(path):
    with zipfile.ZipFile(path, 'w', zipfile.ZIP_DEFLATED) as z:
        z.writestr('[Content_Types].xml', CT)
        z.writestr('_rels/.rels', RELS)
        z.writestr('xl/workbook.xml', WB)
        z.writestr('xl/_rels/workbook.xml.rels', WB_RELS)
        z.writestr('xl/worksheets/sheet1.xml', SHEET)
        z.writestr('xl/worksheets/sheet2.xml', FROZEN)


def frozen_split(z):
    """(xSplit, ySplit) of the sheet named 'Frozen' in a saved workbook."""
    wb = z.read('xl/workbook.xml').decode('utf-8')
    rels = z.read('xl/_rels/workbook.xml.rels').decode('utf-8')
    rid = re.search(r'<sheet [^>]*name="Frozen"[^>]*r:id="([^"]+)"', wb).group(1)
    rel = next(r for r in re.findall(r'<Relationship [^>]*>', rels) if f'Id="{rid}"' in r)
    part = 'xl/' + re.search(r'Target="([^"]+)"', rel).group(1).lstrip('/').replace('xl/', '', 1)
    pane = re.search(r'<pane [^>]*>', z.read(part).decode('utf-8')).group(0)
    g = lambda k: (re.search(k + r'="([^"]+)"', pane) or [None, None])[1]
    return g('xSplit'), g('ySplit')


def check(path, text):
    z = zipfile.ZipFile(path)
    macro = 'sheet.macroEnabled.main+xml' in z.read('[Content_Types].xml').decode('utf-8')
    cells = ''.join(z.read(n).decode('utf-8') for n in z.namelist()
                    if n.startswith('xl/sharedStrings') or n.startswith('xl/worksheets/'))
    found = text in re.findall(r'<t[^>]*>([^<]*)</t>', cells)
    split = frozen_split(z)
    print(f"macro-enabled={macro} text {text!r} found={found} frozen split={split} (expected {FROZEN_SPLIT})")
    return 0 if macro and found and split == FROZEN_SPLIT else 1


if __name__ == '__main__':
    if sys.argv[1] == 'make':
        make(sys.argv[2])
    else:
        sys.exit(check(sys.argv[2], sys.argv[3]))
