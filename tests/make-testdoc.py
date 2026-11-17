"""Create tests/data/hello.docx (minimal valid docx, Korean + English text). Run once; the output is committed."""
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
