import zipfile,json
from pathlib import Path
from lxml import etree as E
root=Path(__file__).resolve().parents[1]
out=root/'pptx_work'
ns={'a':'http://schemas.openxmlformats.org/drawingml/2006/main','p':'http://schemas.openxmlformats.org/presentationml/2006/main'}
z=zipfile.ZipFile(root/'DoAn_PhatHienChayKhoi.pptx.pptx')
print(z.read('ppt/presentation.xml').decode()[-600:])
for i in range(1,16):
 r=E.fromstring(z.read(f'ppt/slides/slide{i}.xml'))
 print('\nSLIDE',i)
 for s in r.xpath('//p:sp',namespaces=ns):
  print(' / '.join(s.xpath('.//a:t/text()',namespaces=ns)),s.xpath('.//a:xfrm/*/@*',namespaces=ns))
for name in z.namelist():
 if name.startswith('ppt/media/'):
  (out/Path(name).name).write_bytes(z.read(name))
d=zipfile.ZipFile(root/'BaoCao_DoAn_HoanThien_KhongGhiChu.docx')
r=E.fromstring(d.read('word/document.xml'))
text='\n'.join(''.join(p.itertext()) for p in r.xpath('//*[local-name()="p"]'))
(out/'word_text.txt').write_text(text,encoding='utf-8')
for name in d.namelist():
 if name.startswith('word/media/'):
  (out/('word_'+Path(name).name)).write_bytes(d.read(name))
print('WORD',len(text))
