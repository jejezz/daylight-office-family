"""Create build/testdata/big.docx: about 400 pages of Korean/English paragraphs with 40 inline images (not committed;
tests/big-doc.ps1 calls this). Usage: python tests/make-bigdoc.py [pages]"""
import io
import os
import random
import sys
import zipfile

from PIL import Image

pages = int(sys.argv[1]) if len(sys.argv) > 1 else 400
paras_n = pages * 40
random.seed(1)
CT = ('<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'
      '<Types xmlns="http://schemas.openxmlformats.org/package/2006/content-types">'
      '<Default Extension="rels" ContentType="application/vnd.openxmlformats-package.relationships+xml"/>'
      '<Default Extension="xml" ContentType="application/xml"/><Default Extension="png" ContentType="image/png"/>'
      '<Override PartName="/word/document.xml" ContentType="application/vnd.openxmlformats-officedocument.wordprocessingml.document.main+xml"/>'
      '</Types>')
RELS = ('<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'
        '<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">'
        '<Relationship Id="rId1" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/officeDocument" Target="word/document.xml"/>'
        '</Relationships>')
NIMG = 40
DRELS = ('<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'
         '<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">'
         + ''.join('<Relationship Id="img%d" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/image" Target="media/i%d.png"/>' % (i, i) for i in range(NIMG))
         + '</Relationships>')
LINES = [
    '대한민국 헌법 제1조 대한민국은 민주공화국이다. 대한민국의 주권은 국민에게 있고, 모든 권력은 국민으로부터 나온다.',
    'The quick brown fox jumps over the lazy dog. 0123456789 가나다라마바사아자차카타파하.',
    '가족 모임 일정: 12월 25일 오후 3시, 장소는 할머니 댁입니다. 음식은 각자 한 가지씩 준비해 오세요.',
]


def para(t):
    return '<w:p><w:r><w:t xml:space="preserve">%s</w:t></w:r></w:p>' % t


def image(i):
    emu = 1800000  # 5 cm
    return ('<w:p><w:r><w:drawing><wp:inline xmlns:wp="http://schemas.openxmlformats.org/drawingml/2006/wordprocessingDrawing" distT="0" distB="0" distL="0" distR="0">'
            '<wp:extent cx="%d" cy="%d"/><wp:docPr id="%d" name="Picture %d"/>'
            '<a:graphic xmlns:a="http://schemas.openxmlformats.org/drawingml/2006/main"><a:graphicData uri="http://schemas.openxmlformats.org/drawingml/2006/picture">'
            '<pic:pic xmlns:pic="http://schemas.openxmlformats.org/drawingml/2006/picture"><pic:nvPicPr><pic:cNvPr id="%d" name="i%d.png"/><pic:cNvPicPr/></pic:nvPicPr>'
            '<pic:blipFill><a:blip xmlns:r="http://schemas.openxmlformats.org/officeDocument/2006/relationships" r:embed="img%d"/><a:stretch><a:fillRect/></a:stretch></pic:blipFill>'
            '<pic:spPr><a:xfrm><a:off x="0" y="0"/><a:ext cx="%d" cy="%d"/></a:xfrm><a:prstGeom prst="rect"><a:avLst/></a:prstGeom></pic:spPr></pic:pic>'
            '</a:graphicData></a:graphic></wp:inline></w:drawing></w:r></w:p>') % (emu, emu, i + 1, i + 1, i + 1, i, i, emu, emu)


body = []
step = max(1, paras_n // NIMG)
k = 0
for i in range(1, paras_n + 1):
    body.append(para('%d. %s' % (i, LINES[i % 3])))
    if i % step == 0 and k < NIMG:
        body.append(image(k))
        k += 1
DOC = ('<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'
       '<w:document xmlns:w="http://schemas.openxmlformats.org/wordprocessingml/2006/main"><w:body>'
       + ''.join(body) + '<w:sectPr><w:pgSz w:w="11906" w:h="16838"/></w:sectPr></w:body></w:document>')
out = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'build', 'testdata', 'big.docx')
os.makedirs(os.path.dirname(out), exist_ok=True)
with zipfile.ZipFile(out, 'w', zipfile.ZIP_DEFLATED) as z:
    z.writestr('[Content_Types].xml', CT)
    z.writestr('_rels/.rels', RELS)
    z.writestr('word/document.xml', DOC)
    z.writestr('word/_rels/document.xml.rels', DRELS)
    for i in range(NIMG):
        im = Image.effect_noise((600, 600), 80).convert('RGB')  # noisy: does not compress well
        b = io.BytesIO()
        im.save(b, 'PNG')
        z.writestr('word/media/i%d.png' % i, b.getvalue())
print('wrote', out, os.path.getsize(out) // 1024, 'KB,', paras_n, 'paragraphs,', k, 'images')
