import zipfile
from pathlib import Path
from lxml import etree as E
work=Path(__file__).resolve().parent
source=work/'candidate_with_workbooks.pptx'
ns={'p':'http://schemas.openxmlformats.org/presentationml/2006/main','a':'http://schemas.openxmlformats.org/drawingml/2006/main'}
def label(e):return ''.join(e.xpath('.//a:t/text()',namespaces=ns))
with zipfile.ZipFile(source) as z,zipfile.ZipFile(work/'candidate_repaired.pptx','w',zipfile.ZIP_DEFLATED) as out:
 for item in z.infolist():
  b=z.read(item.filename)
  if item.filename=='ppt/slides/slide21.xml':
   r=E.fromstring(b)
   for s in r.xpath('//p:sp',namespaces=ns):
    if label(s) in ['TRADITIONAL','HYBRID','COMBINED','YOLOV8']:
     x=s.find('p:spPr/a:xfrm/a:ext',ns)
     if x is not None:x.set('cx',str(650*9525));x.set('cy',str(65*9525))
   b=E.tostring(r,xml_declaration=True,encoding='UTF-8',standalone=True)
  elif item.filename=='ppt/slides/slide13.xml':
   r=E.fromstring(b)
   for s in r.xpath('//p:sp',namespaces=ns):
    if label(s).startswith(('03  ','04  ')):
     tr=s.find('p:spPr/a:xfrm',ns)
     if tr is not None:tr.find('a:off',ns).set('y',str(565*9525));tr.find('a:ext',ns).set('cy',str(50*9525))
   for pic in r.xpath('//p:pic',namespaces=ns):
    tr=pic.find('p:spPr/a:xfrm',ns)
    if tr is not None:
     off=tr.find('a:off',ns);ext=tr.find('a:ext',ns)
     y=int(off.get('y'))/9525
     # Keep the same aspect ratio and centered placement, add breathing room.
     if y>500:off.set('y',str(int(off.get('y'))+15*9525))
     old_h=int(ext.get('cy'));old_w=int(ext.get('cx'));new_h=old_h-20*9525;new_w=round(old_w*new_h/old_h)
     off.set('x',str(int(off.get('x'))+(old_w-new_w)//2));ext.set('cx',str(new_w));ext.set('cy',str(new_h))
   b=E.tostring(r,xml_declaration=True,encoding='UTF-8',standalone=True)
  out.writestr(item,b)
print('Repaired slide13 spacing and slide21 heading widths; workbook parts unchanged.')
