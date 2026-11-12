from pathlib import Path
from docx import Document
from docx.oxml import OxmlElement
from docx.oxml.ns import qn
from docx.shared import Pt

root = Path(__file__).resolve().parents[2]
src = Path(r'C:\Users\PC\Downloads\BaoCao_DoAn_Fire_Smoke_Detection_Nhom4TV.docx')
out = root/'report/BaoCao_DoAn_Fire_Smoke_Detection_Nhom4TV_DaChinhSua.docx'
d = Document(src)
p = d.paragraphs
changes = {
3: 'BỘ MÔN: KHOA HỌC DỮ LIỆU',
62: 'Từ khóa: phát hiện lửa; phát hiện khói; HSV; MOG2; YOLOv8; Tkinter; đa luồng; cảnh báo.',
228: 'Phiên bản được mô tả là commit 40ea155 của repository Caovannho/fire-smoke-detection [1]. Đường dẫn repository: https://github.com/Caovannho/fire-smoke-detection.',
229: p[229].text.strip(),
593: 'Thông tin trường, bộ môn, học phần, giảng viên, họ tên và mã sinh viên đã được bổ sung ở phần đầu báo cáo. Trước khi nộp, bốn thành viên cần kiểm tra lại thông tin này và xác nhận mức độ đóng góp. TV4 cần xác nhận bộ số liệu train và đối chiếu với JSON. TV2 và TV3 cần duyệt phần thuật toán, cách mô tả score và giao thức ảnh tĩnh. TV1 kiểm tra lại ảnh chụp GUI, kịch bản demo và mối liên hệ giữa commit, weights, dataset và kết quả.',
651: p[651].text.replace('tensor ảnh ở mức NumPy BGR', 'mảng ảnh NumPy theo thứ tự kênh BGR'),
691: '        if not (p["min_area"] * img_area <= cv2.contourArea(c)',
692: '                <= p["max_area"] * img_area):',
762: 'Thông tin trường, bộ môn, học phần, lớp học phần, giảng viên, họ tên và mã sinh viên của bốn thành viên đã được điền ở phần đầu báo cáo. Nhóm cần rà soát lần cuối tính chính xác và xác nhận mức độ đóng góp đã ghi. Từng thành viên duyệt các phần thuộc chuyên môn của mình, xác nhận nội dung cài đặt và số liệu được trích. TV1 điều phối bản cuối; TV3 phối hợp ghép chương, hình, tài liệu tham khảo và slide. Nhật ký bàn giao thực tế vẫn cần được nhóm xác nhận.',
}
def set_text(par, text):
    # Retain paragraph style and first run formatting.
    runs=par.runs
    if runs:
        runs[0].text=text
        for r in runs[1:]: r.text=''
    else: par.add_run(text)
for i,t in changes.items(): set_text(p[i],t)
for i in (15,17,18): set_text(p[i],p[i].text.replace('–  ','– '))
heading=p[232].insert_paragraph_before('1.5 Phân công và đóng góp của nhóm',style='Heading 2')
body=p[232].insert_paragraph_before('Nhóm gồm bốn thành viên: Cao Văn Nho (TV1, nhóm trưởng) phụ trách quản lý, Pipeline, GUI và cảnh báo; Nguyễn Quốc Khang (TV2) phụ trách tiền xử lý, phát hiện lửa truyền thống và đánh giá; Phạm Tấn Dương (TV3) phụ trách phát hiện khói truyền thống và tổng hợp báo cáo; Nguyễn Viết Khánh (TV4) phụ trách YOLOv8, gán nhãn và so sánh phương pháp. Công việc và sản phẩm bàn giao được trình bày trong bảng Nhật ký làm việc của nhóm ở phần đầu báo cáo.')
body.style='Normal'
body.paragraph_format.keep_with_next=False
# Correct stale status now that the user has filled the cover and member list.
d.tables[23].cell(1,2).text='Đã điền; chờ cả nhóm xác nhận'
for i,row in enumerate(d.tables[2].rows[1:],1): row.cells[0].text=str(i)
# Clean the edited assignment table without changing responsibilities.
table=d.tables[0]
for row in table.rows:
    for cell in row.cells:
        for par in cell.paragraphs:
            t=par.text.strip()
            t=t.replace('  ',' ')
            if t!=par.text: set_text(par,t)
            par.paragraph_format.space_before=Pt(0)
            par.paragraph_format.space_after=Pt(3)
            par.paragraph_format.line_spacing=1.0
for row in table.rows:
    trpr=row._tr.get_or_add_trPr()
    for node in list(trpr):
        if node.tag==qn('w:trHeight'): trpr.remove(node)
hdr=OxmlElement('w:tblHeader'); table.rows[0]._tr.get_or_add_trPr().append(hdr)
# Ask Word to refresh all navigation and sequence fields on open.
settings=d.settings.element
update=settings.find(qn('w:updateFields'))
if update is None:
    update=OxmlElement('w:updateFields'); settings.append(update)
update.set(qn('w:val'),'true')
d.save(out)
print(out)
print('Edited paragraphs:',len(changes),'Restored section 1.5; corrected table status and member numbering.')
