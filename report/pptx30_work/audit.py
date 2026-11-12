import zipfile,re,json,hashlib
from pathlib import Path
from lxml import etree as E
root=Path(__file__).resolve().parents[2];out=root/'report/output';work=Path(__file__).parent
final=out/'DoAn_PhatHienChayKhoi_30Slide_HoanChinh.pptx'
z=zipfile.ZipFile(final);texts=[]
for i in range(1,31):
 r=E.fromstring(z.read(f'ppt/slides/slide{i}.xml'));ts=r.xpath('//*[local-name()="t"]/text()');t='\n'.join(ts);assert not re.search(r'\bTV[1-4]\b',t);assert f'{i:02} / 30' in t;texts.append(t)
src=zipfile.ZipFile(out/'DoAn_PhatHienChayKhoi_NangCap_22Slide.pptx')
logos=[src.read(n) for n in src.namelist() if n.startswith('ppt/media/')]
logo=(work.parent/'pptx_work/image1.png').read_bytes()
assert any(z.read(n)==logo for n in z.namelist() if n.startswith('ppt/media/'))
report={'slides':30,'editable_charts':len([n for n in z.namelist() if re.search(r'/chart\d+.xml$',n)]),'embedded_workbooks':len([n for n in z.namelist() if n.endswith('.xlsx')]),'pptx_sha256':hashlib.sha256(final.read_bytes()).hexdigest(),'source_22_sha256':hashlib.sha256((out/'DoAn_PhatHienChayKhoi_NangCap_22Slide.pptx').read_bytes()).hexdigest(),'logo_unchanged':True,'all_page_numbers_present':True,'forbidden_member_codes':False}
(work/'delivery_audit.json').write_text(json.dumps(report,indent=2),encoding='utf-8');print(json.dumps(report))
