"""Create tests/data/hello.docx and tests/data/table.docx (minimal valid docx). Run once; the output is committed."""
import os
import zipfile

CT = ('<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'
      '<Types xmlns="http://schemas.openxmlformats.org/package/2006/content-types">'
      '<Default Extension="rels" ContentType="application/vnd.openxmlformats-package.relationships+xml"/>'
      '<Default Extension="xml" ContentType="application/xml"/>'
      '<Override PartName="/word/document.xml" ContentType="application/vnd.openxmlformats-officedocument.wordprocessingml.document.main+xml"/>'
      '</Types>')
RELS = ('<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'
        '<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">'
        '<Relationship Id="rId1" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/officeDocument" Target="word/document.xml"/>'
        '</Relationships>')


def para(text):
    return '<w:p><w:r><w:t xml:space="preserve">%s</w:t></w:r></w:p>' % text


BODY = ''.join(para(t) for t in [
    'Daylight smoke test document',
    '한글 표시 시험: 대한민국 가나다라마바사',
    'The quick brown fox jumps over the lazy dog. 0123456789',
])
DOC = ('<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'
       '<w:document xmlns:w="http://schemas.openxmlformats.org/wordprocessingml/2006/main"><w:body>'
       + BODY + '<w:sectPr><w:pgSz w:w="11906" w:h="16838"/></w:sectPr></w:body></w:document>')

out = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'data', 'hello.docx')
os.makedirs(os.path.dirname(out), exist_ok=True)
with zipfile.ZipFile(out, 'w', zipfile.ZIP_DEFLATED) as z:
    z.writestr('[Content_Types].xml', CT)
    z.writestr('_rels/.rels', RELS)
    z.writestr('word/document.xml', DOC)
print('wrote', out)


# table.docx: an empty 3x3 table (for tests/korean-table.ps1)
def cell():
    return '<w:tc><w:tcPr><w:tcW w:w="2800" w:type="dxa"/></w:tcPr><w:p/></w:tc>'


ROW = '<w:tr>' + cell() * 3 + '</w:tr>'
TBL = ('<w:tbl><w:tblPr><w:tblW w:w="0" w:type="auto"/><w:tblBorders>'
       + ''.join('<w:%s w:val="single" w:sz="4" w:space="0" w:color="000000"/>' % e
                 for e in ('top', 'left', 'bottom', 'right', 'insideH', 'insideV'))
       + '</w:tblBorders></w:tblPr><w:tblGrid>' + '<w:gridCol w:w="2800"/>' * 3 + '</w:tblGrid>'
       + ROW * 3 + '</w:tbl>')
DOC2 = ('<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'
        '<w:document xmlns:w="http://schemas.openxmlformats.org/wordprocessingml/2006/main"><w:body>'
        + TBL + '<w:p/><w:sectPr><w:pgSz w:w="11906" w:h="16838"/></w:sectPr></w:body></w:document>')
out2 = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'data', 'table.docx')
with zipfile.ZipFile(out2, 'w', zipfile.ZIP_DEFLATED) as z:
    z.writestr('[Content_Types].xml', CT)
    z.writestr('_rels/.rels', RELS)
    z.writestr('word/document.xml', DOC2)
print('wrote', out2)


# long.docx: ~100 pages of mixed Korean/English paragraphs plus a few tables (for tests/long-doc.ps1)
LINES = [
    '대한민국 헌법 제1조 대한민국은 민주공화국이다. 대한민국의 주권은 국민에게 있고, 모든 권력은 국민으로부터 나온다.',
    'The quick brown fox jumps over the lazy dog. 0123456789 가나다라마바사아자차카타파하.',
    '가족 모임 일정: 12월 25일 오후 3시, 장소는 할머니 댁입니다. 음식은 각자 한 가지씩 준비해 오세요.',
]
paras = []
for i in range(1, 2201):
    paras.append(para('%d. %s' % (i, LINES[i % 3])))
    if i % 450 == 0:
        paras.append(TBL.replace('<w:p/>', '<w:p><w:r><w:t>표 %d 칸</w:t></w:r></w:p>' % i))
        paras.append('<w:p/>')
DOC3 = ('<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'
        '<w:document xmlns:w="http://schemas.openxmlformats.org/wordprocessingml/2006/main"><w:body>'
        + ''.join(paras) + '<w:sectPr><w:pgSz w:w="11906" w:h="16838"/></w:sectPr></w:body></w:document>')
out3 = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'data', 'long.docx')
with zipfile.ZipFile(out3, 'w', zipfile.ZIP_DEFLATED) as z:
    z.writestr('[Content_Types].xml', CT)
    z.writestr('_rels/.rels', RELS)
    z.writestr('word/document.xml', DOC3)
print('wrote', out3)
