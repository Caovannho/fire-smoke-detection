from pathlib import Path
import json, csv, ast, re, textwrap
from PIL import Image, ImageDraw, ImageFont
from docx import Document
from docx.shared import Cm, Pt, RGBColor
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.enum.table import WD_TABLE_ALIGNMENT, WD_CELL_VERTICAL_ALIGNMENT
from docx.enum.section import WD_SECTION_START
from docx.oxml import OxmlElement
from docx.oxml.ns import qn

ROOT=Path(__file__).resolve().parents[2]
WORK=Path(__file__).resolve().parent
OUTPUT=ROOT/'report/BaoCao_DoAn_Fire_Smoke_Detection_Nhom4TV.docx'
facts=json.loads((WORK/'facts.json').read_text(encoding='utf-8'))
summary=json.loads((ROOT/'report/comparison_summary.json').read_text(encoding='utf-8'))
FONT='C:/Windows/Fonts/times.ttf'
BOLD='C:/Windows/Fonts/timesbd.ttf'
def font(size=32,bold=False):return ImageFont.truetype(BOLD if bold else FONT,size)

def flow(key, labels, subtitle='', cols=3):
    rows=(len(labels)+cols-1)//cols
    width=1500;height=rows*200+80
    im=Image.new('RGB',(width,height),'white');d=ImageDraw.Draw(im)
    bw=420;bh=130;gap=65;left=25;top=25
    centers=[]
    for i,label in enumerate(labels):
        row,col=divmod(i,cols);x=left+col*(bw+gap);y=top+row*200
        d.rounded_rectangle((x,y,x+bw,y+bh),radius=12,fill='#edf2f7',outline='#334155',width=3)
        lines=label.split('\n')
        for j,line in enumerate(lines):
            box=d.textbbox((0,0),line,font=font(30));tw=box[2]-box[0]
            d.text((x+(bw-tw)/2,y+22+j*36),line,font=font(30),fill='black')
        centers.append((x,y))
        if col>0:
            x0=x-gap+8;y0=y+bh//2;d.line((x0,y0,x-10,y0),fill='#334155',width=4)
            d.polygon(((x-10,y0),(x-25,y0-8),(x-25,y0+8)),fill='#334155')
    for row in range(rows-1):
        y=top+row*200+bh
        d.line((left+cols*(bw+gap)-gap-bw/2,y,left+cols*(bw+gap)-gap-bw/2,y+35),fill='#334155',width=3)
        d.line((left+bw/2,y+35,left+cols*(bw+gap)-gap-bw/2,y+35),fill='#334155',width=3)
        d.line((left+bw/2,y+35,left+bw/2,y+65),fill='#334155',width=3)
        d.polygon(((left+bw/2,y+65),(left+bw/2-8,y+50),(left+bw/2+8,y+50)),fill='#334155')
    if subtitle:d.text((30,height-45),subtitle,font=font(25),fill='#334155')
    im.save(WORK/(key+'.png'))

flow('architecture',['Nguồn ảnh và camera\nTV1 tích hợp','Pipeline dùng chung\nTV1','Detector truyền thống\nTV2 và TV3','YOLO và Hybrid\nTV4','Queue và GUI\nTV1','Cảnh báo âm thanh\nTV1'], 'Sơ đồ trách nhiệm chức năng không biểu diễn mọi lời gọi trực tiếp')
flow('modes',['Traditional\nFire + Smoke','YOLO\nModel đã xác thực','Combined\nYOLO + Fire + Smoke','NMS theo lớp\nƯu tiên thứ tự backend','Hybrid\nHSV ứng viên → YOLO','Kết quả chung\n(x y w h label score)'],'Combined là phép hợp có NMS còn Hybrid có bước xác nhận ứng viên')
flow('fire_flow',['BGR 640 × 480\nTiền xử lý tùy chọn','Mặt nạ HSV\nCam và lõi sáng','Opening rồi Closing\nKernel ellipse 5 × 5','Contour ngoài\nDiện tích và tỉ lệ','Mật độ mặt nạ\nScore theo ROI','FireDetector\nNhấp nháy mặc định tắt'])
flow('smoke_flow',['Mặt nạ HSV\nÍt bão hòa','Morphology\nOpen 5 Close 11','Contour ứng viên\nDiện tích và tỉ lệ','MOG2 theo vùng\nChỉ nguồn liên tục','Canny và centroid\nHeuristic theo vùng','Tổng điểm\nNgưỡng 0.15'])
flow('hybrid_flow',['HSV lửa hoặc khói\nOpening 5 × 5','Contour ≥ 150 px\nCó ứng viên hay không','Không ứng viên\nBỏ qua YOLO','Có ứng viên\nYOLO toàn frame','Giao trên box YOLO\nTỉ lệ ít nhất 15 phần trăm','Giữ dự đoán\nScore nhân 1.05'],'Các nhánh bỏ qua và chạy YOLO là lựa chọn loại trừ không phải các bước liên tiếp')
flow('yolo_arch',['Ảnh BGR\nTiền xử lý thư viện','Backbone\nTrích xuất đặc trưng','Neck\nDung hợp đa tỉ lệ','Head anchor free\nBox và lớp','Hậu xử lý\nConf và NMS','Wrapper dự án\nChuyển xyxy → xywh'],'Minh họa khái quát không thay cho sơ đồ cấu trúc model được xuất từ weights')
flow('stream_flow',['Mở nguồn\nKiểm tra capture','Nạp detector\nKiểm tra hủy','Đọc frame\nLetterbox và detect','Ánh xạ box\nVẽ lên ảnh gốc','Update cảnh báo\nTính FPS và tạo PIL','Queue mới nhất\nFinally stop và release'])
flow('image_flow',['Chọn ảnh\nĐọc và giải mã','Preview\nChưa gọi detector','Nhận diện ảnh\nNạp detector nền','Letterbox và detect\nÁnh xạ box về gốc','Queue và hiển thị\nGiữ tỷ lệ ảnh','Kết thúc tác vụ\nKhông update cảnh báo'],'Preview và nhận diện là hai tác vụ độc lập chia sẻ bước đọc ảnh')
flow('threads',['Main thread\nĐọc lựa chọn nguồn','Worker thread\nI O và detector','Queue frame\nTối đa một phần tử','Queue sự kiện\nLỗi và kết thúc','Main poll 15 ms\nKiểm tra mã phiên','PhotoImage và Label\nChỉ main thread'],'Mũi tên trình bày các thành phần trao đổi không phải một thuật toán tuần tự')
flow('lifecycle',['Sẵn sàng\nChưa có worker','Đang xử lý\nWorker thuộc một phiên','Có kết quả\nQueue và render','Dừng hoặc đổi nguồn\nEvent và tăng session','Chờ worker kết thúc\nRelease trong finally','Sẵn sàng hoặc đóng\nCó thể chạy phiên mới'])
flow('alert_flow',['Instance còn active\nKiểm tra detection','Rỗng → reset\nCó → counter tăng','Counter ít nhất 5\nChờ cooldown','Đủ 3 giây\nĐặt trạng thái cảnh báo','PlaySound async\nNOSTOP và owner','Stop\nInactive và PlaySound None'],'Nếu không đủ điều kiện hệ thống giữ hoặc trả trạng thái hiện tại')

im=Image.new('RGB',(1500,650),'white');d=ImageDraw.Draw(im)
d.rectangle((50,80,670,430),fill='#dce8ee',outline='black',width=3)
d.text((70,35),'Ảnh gốc 1280 × 720',font=font(35,bold=True),fill='black')
d.rectangle((190,200,370,350),outline='#c52525',width=5)
d.rectangle((850,30,1330,510),fill='black')
d.rectangle((850,90,1330,450),fill='#dce8ee')
d.rectangle((958,210,1098,330),outline='#c52525',width=5)
d.text((840,530),'640 × 480 với padding trên dưới',font=font(30),fill='black')
d.text((55,480),'x gốc = (x model − left) / sx',font=font(32),fill='black')
d.text((55,535),'y gốc = (y model − top) / sy',font=font(32),fill='black')
d.line((700,270,815,270),fill='black',width=4);d.polygon(((815,270),(795,258),(795,282)),fill='black')
im.save(WORK/'letterbox.png')
im=Image.new('RGB',(1500,560),'white');d=ImageDraw.Draw(im)
d.rectangle((180,95,850,425),fill='#dbeafe',outline='#153f75',width=5)
d.rectangle((610,200,1250,480),fill=None,outline='#ad3232',width=6)
d.rectangle((610,200,850,425),fill='#d1c8dd')
d.text((200,110),'Hộp A',font=font(38,bold=True),fill='black')
d.text((1000,390),'Hộp B',font=font(38,bold=True),fill='black')
d.text((650,280),'Giao',font=font(32),fill='black')
d.text((160,505),'IoU = diện tích giao / diện tích hợp',font=font(34),fill='black');im.save(WORK/'iou.png')
im=Image.new('RGB',(1500,480),'white');d=ImageDraw.Draw(im)
for i,title in enumerate(('Mặt nạ ban đầu','Sau opening','Sau closing')):
 x=35+i*490;d.text((x+30,15),title,font=font(32,bold=True),fill='black');d.rectangle((x,70,x+430,420),fill='black')
 d.rectangle((x+100,150,x+300,330),fill='white')
 if i==0:
  for px,py in ((20,100),(360,260),(45,330),(335,130)):d.rectangle((x+px,py,x+px+10,py+10),fill='white')
 if i<2:d.rectangle((x+180,220,x+205,250),fill='black')
im.save(WORK/'morphology.png')

# A chart is computed only from the saved numeric result file.
im=Image.new('RGB',(1500,760),'white');d=ImageDraw.Draw(im)
labels=['Lửa TV2','Khói TV3','YOLO lửa TV4','Hybrid lửa TV4'];colors=['#315b8c','#c58b39','#4e7b5c']
for j,key in enumerate(('box_precision','box_recall','box_f1')):
 x0=80+j*480;d.text((x0+75,10),('Precision','Recall','F1')[j],font=font(36,bold=True),fill='black')
 for tick in (0,.25,.5,.75,1):
  y=590-int(tick*480);d.line((x0+50,y,x0+435,y),fill='#cccccc',width=2);d.text((x0-8,y-14),f'{tick:g}',font=font(23),fill='black')
 for i,values in enumerate(summary.values()):
  x=x0+70+i*88;v=values[key];y=590-int(v*480)
  d.rectangle((x,y,x+55,590),fill=colors[j]);d.text((x-1,y-35),f'{v:.3f}',font=font(23),fill='black')
  d.text((x-8,605),str(i+1),font=font(28),fill='black')
for i,label in enumerate(labels):d.text((65+i*365,690),f'{i+1} {label}',font=font(28),fill='black')
im.save(WORK/'benchmark_chart.png')

tables={}
def T(key,title,headers,rows,widths=None,source='Nguồn đối chiếu mã nguồn và tài liệu nhóm'):
 tables[key]=(title,headers,rows,widths,source)
T('roles','Phân công và sản phẩm của bốn thành viên',['Thành viên','Phạm vi chính','Sản phẩm và phối hợp'],[
 ['TV1 Trưởng nhóm','Kiến trúc và tích hợp','pipeline.py; GUI; đa luồng; cảnh báo; tổ chức và điều phối báo cáo chung'],
 ['TV2','Tiền xử lý và lửa','preprocess.py; fire_detect.py; evaluator; ablation; chương thuật toán lửa'],
 ['TV3','Khói và tổng hợp','smoke_detect.py; phân tích nhiễu; phối hợp ghép báo cáo và slide'],
 ['TV4','YOLO và thực nghiệm','train.py; yolo_detect.py; hybrid_detect.py; weights; so sánh và hồ sơ huấn luyện']], [2.8,4.3,8.9])
T('requirements','Yêu cầu chức năng và bằng chứng cần có',['Mã','Yêu cầu','Tiêu chí kiểm tra'],[
 ['F01','Nguồn liên tục','Mở webcam hoặc video; có frame và FPS'],['F02','Ảnh tĩnh','Preview và suy luận một lần; không còi'],['F03','Đổi detector','Traditional YOLO Combined dùng cùng hợp đồng'],['F04','Cảnh báo','5 frame; cooldown 3 giây; dừng ngắt âm thanh'],['F05','An toàn phiên','Không nhận frame cũ sau Dừng hoặc đổi nguồn'],['F06','Lỗi rõ ràng','Ảnh hỏng hoặc model lỗi có thông báo'],['F07','Giải phóng','Capture release; worker kết thúc trước đóng GUI']], [1.5,4.3,10.2])
T('contract','Hợp đồng đầu ra detector',['Trường','Kiểu và ý nghĩa','Ràng buộc'],[
 ['x y','Tọa độ góc trái trên','Theo ảnh detector nhận trước ánh xạ'],['w h','Kích thước hộp','Dương; clipping theo biên ảnh'],['label','Chuỗi','Chỉ fire hoặc smoke'],['score','Số thực','Hữu hạn trong [0,1]; ý nghĩa tùy backend'],['frame','NumPy BGR','Vùng suy luận 640 × 480']], [2.5,5.7,7.8])
T('config','Các cấu hình chung đang dùng',['Biến','Giá trị','Phạm vi'],[
 ['FRAME_WIDTH HEIGHT','640 và 480','Vùng xử lý và khung hiển thị'],['YOLO_WEIGHTS','yolo/weights/best.pt','Weights YOLO'],['CONF_THRESHOLD','0.45','Chỉ nhánh YOLO'],['IOU_THRESHOLD','0.45','YOLO và NMS pipeline'],['ALERT_N_FRAMES','5','Counter cảnh báo'],['ALERT_COOLDOWN_SEC','3','Khoảng cách lần kích hoạt'],['FPS_UPDATE_INTERVAL','30','Cửa sổ đo worker'],['LOG_FILE','alerts.log','Có khai báo chưa có ghi file trong AlertSystem']], [5,4,7])
T('preprocess','Các hàm tiền xử lý của TV2',['Hàm','Đầu ra','Điều kiện sử dụng'],[
 ['resize_frame','Ảnh đổi kích thước','Hàm hỗ trợ resize trực tiếp'],['normalize','float32 gần [0,1]','Không ở đường detect_fire mặc định'],['to_hsv to_gray','Ảnh HSV hoặc xám','Hàm chuyển màu'],['gaussian median','Ảnh lọc','Tham số 0 để tắt'],['equalize_v','BGR sau CLAHE trên V','clip = 0 để tắt'],['extract_roi','Vùng ảnh theo box','Không đổi hệ tọa độ box']], [4,5,7])
T('fire_params','Tham số lửa thực tế trong PARAMS',['Nhóm','Giá trị','Ý nghĩa'],[
 ['Màu chính','H ≤ 35; S ≥ 60; V ≥ 200','Ngưỡng uint8 OpenCV'],['Lõi sáng','white_v 245; halo_v 100; halo_r 15','Lõi trắng gần quầng cam'],['Morphology','open 5; close 5','Kernel ellipse'],['Diện tích','0.002 đến 0.8','Theo diện tích ảnh xử lý'],['Tỉ lệ','0.25 đến 4.0','Chiều rộng trên chiều cao'],['Score','min_score 0.0','Mật độ pixel hợp màu'],['Thời gian','flicker_min 0; warmup 5','Bộ lọc nhấp nháy mặc định tắt']], [3,6,7])
T('smoke_params','Các nhóm tham số khói đang dùng',['Nhóm','Giá trị','Ý nghĩa'],[
 ['HSV','S tối đa 55; V 75 đến 235','Lấy từ cấu hình và điều chỉnh PARAMS'],['Khói đen','enable_black_smoke False','Chưa bật mặc định'],['Morphology','open 5; close 11 hai lần','Làm sạch và nối vùng'],['Diện tích','600 đến 250000','Pixel contour trên ảnh xử lý'],['MOG2','history 500; var 40; lr 0.003','Mô hình nền từng phiên'],['Chuyển động','min_motion_ratio 0.015','Tỉ lệ tiền cảnh trong contour'],['Cạnh','Canny 40 120; density ≤ 0.22','Loại vùng nhiều cạnh'],['Centroid','Dung sai 45 pixel','Tạo thưởng bốc lên'],['Score','min_score 0.15','Tổng heuristic có chặn']], [3,6,7])
T('dataset','Thống kê dữ liệu local theo file nhãn',['Tập','Ảnh','Rỗng','Chỉ khói','Chỉ lửa','Cả hai'],[
 [split,str(v['images']),str(v['none']),str(v['smoke_only']),str(v['fire_only']),str(v['both'])]
 for split,v in facts['dataset'].items()], [2.1,2.6,2.6,2.9,2.7,3.1], 'Đếm local ngày 26/10/2026 đọc ảnh theo phần mở rộng và class ID trong nhãn không sửa dữ liệu')
T('presets','Ba preset huấn luyện có trong train.py',['Preset','Model nền','Batch','lr0','Thiết lập đáng chú ý'],[
 ['1 Baseline','yolov8n.pt','16','0.01','imgsz 640; mặc định 50 epoch'],['2 Deeper','yolov8s.pt','8','0.01','So sánh kiến trúc lớn hơn'],['3 Augmented','yolov8n.pt','16','0.005','hsv_s 0.8; hsv_v 0.5; mosaic 1.0']], [3,3.4,1.5,1.8,6.3], 'Cấu hình trong mã không đồng nghĩa ba lượt train đã có đầy đủ hồ sơ')
T('alert_timeline','Ví dụ logic chuỗi năm frame không phải số đo thực nghiệm',['Frame','Có detection','Counter','Kết quả khi cooldown cho phép'],[
 ['1','Có','1','Chưa cảnh báo'],['2','Có','2','Chưa cảnh báo'],['3','Không','0','Reset'],['4 đến 7','Có liên tiếp','1 đến 4','Chưa đạt ngưỡng'],['8','Có','5','Kích hoạt'],['9','Có','6','Giữ trạng thái; chưa phát lại trong cooldown'],['10','Không','0','Xóa trạng thái nhưng giữ mốc thời gian']], [2,3.3,2.7,8], 'Ví dụ suy diễn từ update không phải log camera')
T('evidence','Phân loại nguồn bằng chứng sử dụng trong báo cáo',['Loại','Nguồn','Giới hạn'],[
 ['Mã nguồn','Commit 40ea155','Xác định cài đặt không chứng minh độ chính xác'],['Kết quả lưu sẵn','JSON và CSV trong repo','Thiếu manifest và metadata đầy đủ'],['Dữ liệu thật','Ảnh test và best.pt local','Một vài mẫu không đại diện toàn tập'],['Thiết bị thật','Log Tkinter và webcam','Thiếu ảnh chụp và hồ sơ phần cứng'],['Mô phỏng','Bộ 14 test','Có mock không thay xác nhận loa hoặc camera'],['Phản ánh vận hành','Tay mặt bị nhận nhầm','Chưa có frame đồng bộ và nguồn từng box']], [3,5,8])
T('benchmark','Kết quả lưu sẵn với 100 ảnh mỗi phương pháp',['Phương pháp','P box','R box','F1 box','FPR ảnh','FPS'],[
 [name.replace('Truyền thống ','').replace('Kết hợp ',''),*[f'{m[k]:.4f}' for k in ('box_precision','box_recall','box_f1','img_fpr')],f'{m["fps"]:.1f}']
 for name,m in summary.items()], [4.2,2.2,2.2,2.2,2.5,2.7], 'report/comparison_summary.json kết quả lịch sử không phải benchmark GUI mới')
with (ROOT/'eval/ablation_pre.csv').open(encoding='utf-8') as f:pre=list(csv.DictReader(f))
T('ablation_pre','Ablation tiền xử lý đang lưu',['Cấu hình','P box','R box','F1','FPR ảnh','FPS'],[
 [r['config'],*[f'{float(r[k]):.4f}' for k in ('box_precision','box_recall','box_f1','img_fpr')],f'{float(r["fps"]):.1f}']for r in pre], [5,2,2,2,2.5,2.5], 'eval/ablation_pre.csv chưa có metadata xác nhận limit của lượt chạy')
with (ROOT/'eval/ablation_filter.csv').open(encoding='utf-8') as f:filt=list(csv.DictReader(f))
T('ablation_filter','Ablation các bước lọc lửa đang lưu',['Bước','Precision','Recall','F1','FPR ảnh'],[
 [r['step'],*[f'{float(r[k]):.4f}' for k in ('box_precision','box_recall','box_f1','img_fpr')]]for r in filt], [6,2.5,2.5,2.5,2.5], 'eval/ablation_filter.csv không ghép cùng bảng 100 ảnh')
T('samples','Kết quả từng mẫu trong kiểm tra tích hợp',['Mẫu và nhãn','Traditional','YOLO','Combined'],[
 ['AoF07738 chỉ fire','1 smoke','1 fire và 1 smoke','1 fire và 2 smoke'],['AoF06978 chỉ smoke','1 smoke','Không detection','1 smoke'],['AoF06723 nhãn rỗng','1 smoke','Không detection','1 smoke']], [4.4,3.6,4,4], 'Log suy luận ngày 26/10/2026 không suy ra tỷ lệ đúng từ ba ảnh')
T('native_tests','Kết quả kiểm thử tích hợp đã ghi',['Tình huống','Quan sát','Mức bằng chứng'],[
 ['Image ba phương pháp','PhotoImage 640 × 360; có kết quả','Tkinter và model thật qua callback'],['Ảnh hỏng','Thông báo lỗi; không có ảnh kết quả','File thử thật'],['Video tổng hợp Traditional','Có hình; FPS tức thời 40.9','AVI lặp ảnh không phải cháy diễn biến'],['Webcam Traditional','Có frame; FPS tức thời 25.3','Camera thật; chưa có nhãn sự kiện'],['Webcam Combined','Có frame; FPS tức thời 9.0','Camera thật; một thời điểm'],['Webcam YOLO riêng','Chưa có hình trong khoảng chờ','Không kết luận nhánh này hoạt động đầy đủ'],['Camera IP','Chưa có log thiết bị','Chưa kiểm thử'],['Âm thanh nghe được','API đã được gọi; chưa có biên bản nghe','Cần người vận hành xác nhận']], [4.3,6.1,5.6], 'Các log native trong tv1-upgrade đọc lại không chạy webcam mới để viết báo cáo')
T('test_matrix','Các nhóm kiểm thử trong bộ 14 test',['Nhóm','Kiểm tra','Kết quả và loại'],[
 ['Hình học','Ảnh ngang dọc lẻ; clipping padding','Đạt; dữ liệu tổng hợp'],['Model','Thiếu file và names không đúng','Đạt; lỗi có kiểm soát'],['Combined','Dispatch và ưu tiên NMS','Đạt; output backend mô phỏng'],['Ảnh','Bốn định dạng và tên tiếng Việt','Đạt; file thử thật'],['Phiên','Smoke riêng; hủy nạp model','Đạt; có mock điều phối'],['Cảnh báo','5 frame; 2.999 và 3 giây; fallback','Đạt; mock PlaySound'],['GUI worker','Image không còi; lỗi detector; FPS','Đạt; capture và widget mock'],['Vòng đời','10 vòng start stop; frame cũ; close','Đạt; mô phỏng nguồn']], [3.4,6.4,6.2], 'Bộ test_tv1.py đã chạy 14 tests OK trong lượt cập nhật trước')
T('roadmap','Hướng phát triển và trách nhiệm phối hợp',['Ưu tiên','Đầu mối','Sản phẩm cần có'],[
 ['Chuẩn hóa đánh giá','TV2 cùng TV3 TV4','Manifest và evaluator thống nhất ảnh video'],['Giảm FP màu da','TV2','Hard negatives và ablation có Recall'],['Khói khó và hơi nước','TV3','Video có nhãn; nền và tracking vùng'],['Hồ sơ train','TV4','args results weights hash và hardware'],['Fusion và log sự kiện','TV1','Nguồn box và event latency có kiểm thử'],['Bản nộp và demo','TV1 điều phối TV3 phối hợp','Ảnh GUI; xác nhận đóng góp; tài liệu hoàn chỉnh']], [4.2,4.2,7.6])
T('files','Các module thực tế và người phụ trách',['Đường dẫn','Vai trò','Phụ trách'],[
 ['pipeline.py','Hợp đồng gộp và hình học','TV1'],['gui/app.py','GUI worker queue phiên','TV1'],['gui/alert.py','Counter cooldown âm thanh','TV1'],['config.py data.yaml','Cấu hình chung và dataset','TV1 phối hợp'],['traditional/preprocess.py','Các phép tiền xử lý','TV2'],['traditional/fire_detect.py','Luật lửa và flicker tùy chọn','TV2'],['traditional/smoke_detect.py','Khói MOG2 cạnh centroid','TV3'],['eval/evaluate.py','Metric và evaluator','TV2'],['yolo/train.py','Huấn luyện và preset','TV4'],['yolo/yolo_detect.py','Suy luận YOLO','TV4'],['yolo/hybrid_detect.py','Ứng viên và xác nhận YOLO','TV4'],['report/','Báo cáo chung và minh chứng','TV1 điều phối TV3 phối hợp']], [6.2,6.3,3.5])
T('glossary','Các ký hiệu và từ viết tắt',['Ký hiệu','Diễn giải'],[
 ['BGR RGB HSV','Các cách biểu diễn màu'],['ROI','Vùng quan tâm trong ảnh'],['IoU NMS','Độ giao trên hợp và loại hộp trùng'],['TP FP FN TN','Đúng dương sai dương sai âm đúng âm'],['AP mAP','Diện tích PR và giá trị trung bình theo quy ước'],['MOG2','Mô hình nền hỗn hợp Gaussian thích nghi'],['FPS','Số frame xử lý trên giây trong cửa sổ đo'],['H W','Chiều cao và rộng ảnh'],['Event Queue','Cờ hủy và hàng đợi đồng bộ'],['Union Cascade','Phép hợp kết quả và chuỗi xác nhận ứng viên']], [4.2,11.8])
T('demo','Bảng kiểm tra trước buổi demo',['Mục','Điều kiện đạt','Xác nhận'],[
 ['Môi trường','Interpreter thuộc fire-smoke','[Cần điền]'],['Model','File đúng hash và names','[Cần điền]'],['Ảnh','Có dương âm và ảnh lỗi','[Cần điền]'],['Webcam','Đủ thời gian mở; frame và FPS','[Cần điền]'],['Còi','Nghe được và Dừng ngắt','[Cần điền]'],['Nguồn và phiên','Đổi nguồn không hiện ảnh cũ','[Cần điền]'],['Nội dung trình bày','Giải thích FP và giới hạn','[Cần điền]']], [3,9.8,3.2])
T('missing','Minh chứng cần hoàn thiện và người xác nhận',['Nội dung','Đầu mối','Trạng thái'],[
 ['Họ tên mã SV giảng viên trường','TV1 và cả nhóm','Cần điền'],['Log train và liên kết preset weights','TV4','Cần bổ sung'],['Metadata benchmark 100 ảnh','TV2 TV3 TV4','Chưa đầy đủ'],['Người bình thường và điện thoại','TV1 phối hợp cả nhóm','Thiếu frame đối chứng'],['Camera IP','TV1','Chưa kiểm thử'],['Khói loãng hơi nước video dài','TV3 TV4','Chưa có bộ test đầy đủ'],['Ảnh chụp GUI và xác nhận loa','TV1','Cần bổ sung'],['Kết quả benchmark Combined riêng','TV1 TV2 TV4','Chưa có trong JSON'],['Bảng lịch sử sáu cấu hình TV4','TV4','Chưa xác minh với log']], [7.7,3.3,5])

import runpy
runpy.run_path(str(WORK/"accurate_diagrams.py"))

doc=Document()
sec=doc.sections[0]
for section in doc.sections:
 section.page_width=Cm(21);section.page_height=Cm(29.7)
 section.top_margin=Cm(2.5);section.bottom_margin=Cm(2.5)
 section.left_margin=Cm(3);section.right_margin=Cm(2)
 section.header_distance=Cm(1.15);section.footer_distance=Cm(1.25)
styles=doc.styles
for name in ('Normal','Title','Subtitle','Heading 1','Heading 2','Heading 3','Caption'):
 style=styles[name];style.font.name='Times New Roman';style.font.color.rgb=RGBColor(0,0,0)
 style.element.get_or_add_rPr().get_or_add_rFonts().set(qn('w:eastAsia'),'Times New Roman')
 style.font.size=Pt(13)
normal=styles['Normal'];normal.paragraph_format.line_spacing=1.5
normal.paragraph_format.alignment=WD_ALIGN_PARAGRAPH.JUSTIFY
normal.paragraph_format.first_line_indent=Cm(0.8)
normal.paragraph_format.space_after=Pt(2)
normal.paragraph_format.widow_control=True
for name,size in (('Title',19),('Heading 1',17),('Heading 2',14),('Heading 3',13)):
 st=styles[name];st.font.size=Pt(size);st.font.bold=True
 st.paragraph_format.first_line_indent=Cm(0);st.paragraph_format.keep_with_next=True
 st.paragraph_format.space_before=Pt(8);st.paragraph_format.space_after=Pt(5)
 st.paragraph_format.line_spacing=1.25
styles['Caption'].font.size=Pt(12);styles['Caption'].font.italic=True
styles['Caption'].paragraph_format.alignment=WD_ALIGN_PARAGRAPH.CENTER
styles['Caption'].paragraph_format.first_line_indent=Cm(0)
styles['Caption'].paragraph_format.line_spacing=1.15
for style_name in ('TOC 1','TOC 2','TOC 3'):
 if style_name in styles:
  styles[style_name].font.name='Times New Roman';styles[style_name].font.size=Pt(12)
  styles[style_name].paragraph_format.line_spacing=1.15

def field(paragraph,instruction,display='1'):
 run=paragraph.add_run();b=OxmlElement('w:fldChar');b.set(qn('w:fldCharType'),'begin');run._r.append(b)
 t=OxmlElement('w:instrText');t.set(qn('xml:space'),'preserve');t.text=' '+instruction+' ';run._r.append(t)
 sep=OxmlElement('w:fldChar');sep.set(qn('w:fldCharType'),'separate');run._r.append(sep)
 paragraph.add_run(display)
 end=OxmlElement('w:fldChar');end.set(qn('w:fldCharType'),'end');paragraph.add_run()._r.append(end)

def page_number(section,fmt,start):
 pr=section._sectPr.find(qn('w:pgNumType'))
 if pr is None:pr=OxmlElement('w:pgNumType');section._sectPr.append(pr)
 pr.set(qn('w:fmt'),fmt);pr.set(qn('w:start'),str(start))

def setup_section(section):
 section.page_width=Cm(21);section.page_height=Cm(29.7)
 section.top_margin=Cm(2.5);section.bottom_margin=Cm(2.5);section.left_margin=Cm(3);section.right_margin=Cm(2)
 section.header_distance=Cm(1.15);section.footer_distance=Cm(1.25)
 section.header.is_linked_to_previous=False;section.footer.is_linked_to_previous=False
 h=section.header.paragraphs[0];h.alignment=WD_ALIGN_PARAGRAPH.CENTER
 h.paragraph_format.first_line_indent=Cm(0);r=h.add_run('FIRE & SMOKE DETECTION FROM CAMERA  |  NHÓM 4 THÀNH VIÊN');r.font.size=Pt(9)
 f=section.footer.paragraphs[0];f.alignment=WD_ALIGN_PARAGRAPH.CENTER;f.paragraph_format.first_line_indent=Cm(0)
 field(f,'PAGE')

def para(text,style=None):
 p=doc.add_paragraph(text,style)
 return p
def centered(text,size=14,bold=False,space=12):
 p=para(text);p.alignment=WD_ALIGN_PARAGRAPH.CENTER;p.paragraph_format.first_line_indent=Cm(0)
 p.paragraph_format.space_after=Pt(space)
 for r in p.runs:r.font.size=Pt(size);r.bold=bold
 return p

# Cover is followed by a separately numbered preliminary section.
centered('[TÊN TRƯỜNG]',15,True,4);centered('[KHOA HOẶC VIỆN]',14,True,4)
centered('[MÔN HỌC VÀ LỚP HỌC PHẦN]',13,False,40)
centered('BÁO CÁO ĐỒ ÁN NHÓM',16,True,24)
p=para('Fire & Smoke Detection from Camera','Title');p.alignment=WD_ALIGN_PARAGRAPH.CENTER
centered('PHÁT HIỆN LỬA VÀ KHÓI TỪ CAMERA',16,True,30)
centered('Nhóm thực hiện gồm 4 thành viên',14,True,12)
for x in ('TV1 Trưởng nhóm  [Họ tên]  [Mã sinh viên]','TV2  [Họ tên]  [Mã sinh viên]','TV3  [Họ tên]  [Mã sinh viên]','TV4  [Họ tên]  [Mã sinh viên]'):
 centered(x,13,False,5)
centered('Giảng viên hướng dẫn  [Họ tên giảng viên]',13,False,30)
centered('Năm thực hiện 2026',13,False,4)
front=doc.add_section(WD_SECTION_START.NEW_PAGE);setup_section(front);page_number(front,'lowerRoman',1)
centered('TÓM TẮT ĐỀ TÀI',16,True)
para('Báo cáo trình bày nguyên mẫu phát hiện lửa và khói bằng camera của nhóm bốn thành viên. Hệ thống kết hợp các detector truyền thống của TV2 và TV3, nhánh YOLOv8 và Hybrid của TV4 với kiến trúc, Pipeline, GUI Tkinter, đa luồng và cảnh báo do TV1 tích hợp. Người dùng có thể phân tích ảnh một lần hoặc giám sát nguồn liên tục. Kết quả được hiển thị bằng hộp bao, nhãn và điểm số theo từng phương pháp.')
para('Kết quả triển khai cho thấy đường xử lý ảnh, model và giao diện có thể hoạt động trong môi trường fire-smoke trên Windows. Tuy nhiên, chất lượng nhận diện vẫn chịu ảnh hưởng của nhiễu màu, khói khó và chính sách kết hợp. Combined dạng union có thể giữ dự đoán sai của Traditional; quy tắc năm khung hình và cooldown ba giây không loại được nhiễu kéo dài. Báo cáo phân tích các giới hạn này bằng mã nguồn, dữ liệu kết quả đang lưu và log kiểm thử có phân biệt thật với mô phỏng.')
para('Các giá trị Precision, Recall, F1 và FPS được dẫn đúng nguồn và phạm vi. Kết quả benchmark lịch sử không được gọi là phép đo mới của GUI; các thông tin huấn luyện chưa có log xác nhận được đánh dấu cần bổ sung. Mục tiêu của hệ thống là hỗ trợ học thuật và quan sát trực quan, chưa phải sản phẩm báo cháy thương mại được chứng nhận.')
para('Từ khóa: phát hiện lửa; phát hiện khói; HSV; MOG2; YOLOv8; Tkinter; đa luồng; cảnh báo.')
para('Phiên bản mã đối chiếu: 40ea155. Ngày tổng hợp: 26/10/2026. TV1 điều phối báo cáo chung; TV3 phối hợp tổng hợp; mỗi thành viên chịu trách nhiệm xác nhận phần chuyên môn của mình.')
doc.add_page_break();centered('MỤC LỤC',16,True)
field(para(''),r'TOC \o "1-2" \h \z \u','Mục lục sẽ được cập nhật bằng trường Word')
doc.add_page_break();centered('DANH MỤC HÌNH',16,True)
field(para(''),r'TOC \h \z \c "Hinh"','Danh mục hình')
doc.add_page_break();centered('DANH MỤC BẢNG',16,True)
field(para(''),r'TOC \h \z \c "Bang"','Danh mục bảng')

body=doc.add_section(WD_SECTION_START.NEW_PAGE);setup_section(body);page_number(body,'decimal',1)

fig_count=table_count=0;fig_inventory=[];table_inventory=[]
def caption(label,seq,title):
 p=doc.add_paragraph(style='Caption');p.add_run(label+' ')
 field(p,'SEQ '+seq+' \\* ARABIC',str(fig_count if seq=='Hinh' else table_count))
 p.add_run('  '+title)
 return p

def add_table(key):
 global table_count
 title,headers,rows,widths,source=tables[key];table_count+=1
 cp=caption('Bảng','Bang',title);cp.paragraph_format.keep_with_next=True
 t=doc.add_table(rows=1,cols=len(headers));t.alignment=WD_TABLE_ALIGNMENT.CENTER;t.autofit=False
 widths=widths or [16/len(headers)]*len(headers)
 for col,w in zip(t.columns,widths):col.width=Cm(w)
 for i,text in enumerate(headers):t.rows[0].cells[i].text=text
 for row in rows:
  cells=t.add_row().cells
  for i,text in enumerate(row):cells[i].text=str(text)
 for ri,row in enumerate(t.rows):
  pr=row._tr.get_or_add_trPr();cant=OxmlElement('w:cantSplit');pr.append(cant)
  if ri==0:repeat=OxmlElement('w:tblHeader');pr.append(repeat)
  for ci,c in enumerate(row.cells):
   c.width=Cm(widths[ci]);c.vertical_alignment=WD_CELL_VERTICAL_ALIGNMENT.CENTER
   tcPr=c._tc.get_or_add_tcPr();border=OxmlElement('w:tcBorders')
   for edge in ('top','left','bottom','right'):
    e=OxmlElement('w:'+edge);e.set(qn('w:val'),'single');e.set(qn('w:sz'),'5');e.set(qn('w:color'),'D9D9D9');border.append(e)
   tcPr.append(border)
   shading=OxmlElement('w:shd');shading.set(qn('w:fill'),'DDE6EF' if ri==0 else ('F7F9FB' if ri%2==0 else 'FFFFFF'));tcPr.append(shading)
   margins=OxmlElement('w:tcMar')
   for edge in ('top','left','bottom','right'):
    m=OxmlElement('w:'+edge);m.set(qn('w:w'),'75');m.set(qn('w:type'),'dxa');margins.append(m)
   tcPr.append(margins)
   for p in c.paragraphs:
    p.paragraph_format.first_line_indent=Cm(0);p.paragraph_format.space_after=Pt(0);p.paragraph_format.space_before=Pt(0)
    p.paragraph_format.line_spacing=1.5
    p.paragraph_format.keep_with_next=(ri==0)
    p.alignment=WD_ALIGN_PARAGRAPH.LEFT if ci==0 or len(c.text)>30 else WD_ALIGN_PARAGRAPH.CENTER
    for r in p.runs:r.font.name='Times New Roman';r.font.size=Pt(13);r.bold=(ri==0)
 p=para(source);p.paragraph_format.first_line_indent=Cm(0);p.paragraph_format.line_spacing=1.15
 for r in p.runs:r.italic=True;r.font.size=Pt(10)
 table_inventory.append({'number':table_count,'key':key,'title':title,'rows':len(rows)})

def add_figure(key,title,source):
 global fig_count
 fig_count+=1
 p=para('');p.alignment=WD_ALIGN_PARAGRAPH.CENTER;p.paragraph_format.first_line_indent=Cm(0);p.paragraph_format.keep_with_next=True
 p.paragraph_format.line_spacing=1;p.paragraph_format.space_after=Pt(3)
 r=p.add_run();pic=r.add_picture(str(WORK/(key+'.png')),width=Cm(13.0 if key=='fire_masks' else 15.6))
 pic._inline.docPr.set('descr',title)
 caption('Hình','Hinh',title).paragraph_format.keep_with_next=True
 p=para(source);p.paragraph_format.first_line_indent=Cm(0);p.paragraph_format.line_spacing=1.15
 for r in p.runs:r.italic=True;r.font.size=Pt(10)
 fig_inventory.append({'number':fig_count,'key':key,'title':title})

def code_snippet(file,func,title):
 text=(ROOT/file).read_text(encoding='utf-8');tree=ast.parse(text)
 node=next(n for n in ast.walk(tree) if isinstance(n,(ast.FunctionDef,ast.AsyncFunctionDef)) and n.name==func)
 lines=text.splitlines()[node.lineno-1:node.end_lineno]
 p=para(f'{file}  hàm {func}  dòng {node.lineno} đến {node.end_lineno}');p.paragraph_format.first_line_indent=Cm(0);p.paragraph_format.keep_with_next=True
 for r in p.runs:r.bold=True;r.font.size=Pt(11)
 snippet=textwrap.dedent('\n'.join(lines))
 for line in snippet.splitlines():
  # Long code lines are wrapped visually; the source is preserved in the repository.
  for part in textwrap.wrap(line,width=87,replace_whitespace=False,drop_whitespace=False) or ['']:
   cp=para(part);cp.paragraph_format.first_line_indent=Cm(0);cp.paragraph_format.space_after=Pt(0);cp.paragraph_format.line_spacing=1
   for r in cp.runs:r.font.name='Consolas';r.font.size=Pt(8.5)
 p=para(title);p.paragraph_format.first_line_indent=Cm(0)
 for r in p.runs:r.italic=True;r.font.size=Pt(11)

contents='\n\n'.join((WORK/f).read_text(encoding='utf-8') for f in ('content.md','chapters456.md','chapters789.md','endmatter.md'))
contents=contents.replace('ảnh thực tế từ camera','ảnh thực tế từ camera')
contents=contents.replace('đánh giá hệ thống, không suy ra','đánh giá hệ thống, không suy ra')
contents=contents.replace('kích thước mà evaluator dùng; không được lấy tọa độ chuẩn hóa làm pixel trực tiếp [9].','kích thước mà evaluator dùng; không được lấy tọa độ chuẩn hóa làm pixel trực tiếp [11].')
first=True
for line in contents.splitlines():
 line=line.strip()
 if not line:continue
 if line.startswith('# '):
  heading=para(line[2:],'Heading 1')
  heading.paragraph_format.page_break_before = not first
  first=False
 elif line.startswith('## '):para(line[3:],'Heading 2')
 elif line.startswith('### '):para(line[4:],'Heading 3')
 elif line.startswith('!TABLE '):add_table(line[7:])
 elif line.startswith('!FIG '):add_figure(*line[5:].split('|'))
 elif line.startswith('!CODE '):code_snippet(*line[6:].split('|'))
 elif line.startswith('!EQ '):
  p=para('');p.alignment=WD_ALIGN_PARAGRAPH.CENTER;p.paragraph_format.first_line_indent=Cm(0)
  omath=OxmlElement('m:oMath');mr=OxmlElement('m:r');mt=OxmlElement('m:t');mt.text=line[4:];mr.append(mt);omath.append(mr);p._p.append(omath)
 elif line.startswith('!SHELL '):
  p=para(line[7:]);p.paragraph_format.first_line_indent=Cm(0);p.paragraph_format.line_spacing=1.15
  for r in p.runs:r.font.name='Consolas';r.font.size=Pt(10)
 else:
  p=para(line)
  if re.match(r'^\[\d+\]',line):
   p.paragraph_format.first_line_indent=Cm(0);p.paragraph_format.line_spacing=1.2
   for r in p.runs:r.font.size=Pt(11)

settings=doc.settings.element
u=OxmlElement('w:updateFields');u.set(qn('w:val'),'true');settings.append(u)
doc.core_properties.title='Fire & Smoke Detection from Camera'
doc.core_properties.subject='Báo cáo đồ án nhóm bốn thành viên'
doc.core_properties.author='Nhóm 4 thành viên TV1 TV2 TV3 TV4'
doc.core_properties.keywords='Fire Smoke YOLOv8 HSV MOG2 Tkinter Pipeline'
# Remove theme font overrides and the template's decorative title border.
for style in doc.styles:
    if style.type in (1, 2):
        rpr=style.element.get_or_add_rPr()
        rf=rpr.find(qn('w:rFonts'))
        if rf is None:
            rf=OxmlElement('w:rFonts');rpr.insert(0,rf)
        for key in list(rf.attrib):
            if 'Theme' in key or 'theme' in key:del rf.attrib[key]
        for attr in ('ascii','hAnsi','eastAsia','cs'):rf.set(qn('w:'+attr),'Times New Roman')
for root in (doc.element,doc.styles.element):
    for border in list(root.iter(qn('w:pBdr'))):border.getparent().remove(border)
for paragraph in doc.paragraphs:
    for run in paragraph.runs:
        rf=run._r.find('.//'+qn('w:rFonts'))
        if rf is not None:
            for key in list(rf.attrib):
                if 'Theme' in key or 'theme' in key:del rf.attrib[key]
doc.save(OUTPUT)
(WORK/'inventory.json').write_text(json.dumps({'figures':fig_inventory,'tables':table_inventory,'paragraphs':len(doc.paragraphs),'body_characters':len(contents),'output':str(OUTPUT)},ensure_ascii=False,indent=2),encoding='utf-8')
print(OUTPUT)
print('Figures',fig_count,'Tables',table_count,'Paragraphs',len(doc.paragraphs),'Characters',len(contents))
