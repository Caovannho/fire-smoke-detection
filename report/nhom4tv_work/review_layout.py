from pathlib import Path
from docx import Document
from docx.shared import Cm,Pt
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.oxml import OxmlElement
from docx.oxml.ns import qn
p=Path(__file__).resolve().parents[2]/'report/BaoCao_DoAn_Fire_Smoke_Detection_Nhom4TV_DaChinhSua.docx'
d=Document(p)
for par in d.paragraphs:
    if par.text.startswith('Phiên bản được mô tả là commit'):
        for h in list(par._p.findall(qn('w:hyperlink'))): par._p.remove(h)
    if par.text.strip() in ('BẢNG TỔNG HỢP','MỨC ĐỘ ĐÓNG GÓP VÀ ĐIỂM CỦA CÁC THÀNH VIÊN TRONG NHÓM'):
        outline=par._p.get_or_add_pPr().find(qn('w:outlineLvl'))
        if outline is None: outline=OxmlElement('w:outlineLvl');par._p.get_or_add_pPr().append(outline)
        outline.set(qn('w:val'),'9')
t=d.tables[0];t.autofit=False
widths=[0.9,2.4,2.2,2.7,5.0,3.2]
for col,w in zip(t.columns,widths):col.width=Cm(w)
for row in t.rows:
    for c,w in zip(row.cells,widths):
        c.width=Cm(w)
        for par in c.paragraphs:
            par.alignment=WD_ALIGN_PARAGRAPH.LEFT
            for r in par.runs:r.font.size=Pt(10)
work=[
'Quản lý tiến độ; thu thập và phân chia dữ liệu; xây dựng Pipeline; thiết kế GUI; tích hợp thuật toán và cảnh báo; kiểm thử tổng thể.',
'Tiền xử lý ảnh; nghiên cứu và triển khai phát hiện lửa truyền thống; xây dựng công cụ đánh giá.',
'Phát hiện khói bằng MOG2, màu sắc, hình dạng và chuyển động; phân tích nhiễu, báo động giả; tổng hợp báo cáo Word và slide.',
'Điều phối gán nhãn; huấn luyện YOLOv8 phát hiện lửa và khói; tối ưu tham số; xây dựng detect(frame); thử nghiệm Hybrid và so sánh phương pháp.'
]
for row,txt in zip(t.rows[1:],work):
    par=row.cells[4].paragraphs[0];par.text=txt
    for r in par.runs:r.font.size=Pt(10)
# Avoid leaving the lecturer's heading separated from its assessment table.
for par in d.paragraphs:
    if par.text.startswith('NHẬN XÉT CỦA GIẢNG VIÊN'):
        par.paragraph_format.keep_with_next=True
        par.paragraph_format.page_break_before=True
d.save(p)
