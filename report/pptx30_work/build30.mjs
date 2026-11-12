import fs from 'node:fs/promises';
import path from 'node:path';
import {applyPresentationChartFont} from 'file:///C:/Users/PC/.codex/plugins/cache/openai-primary-runtime/presentations/26.1105.12137/skills/presentations/container_tools/artifact_tool_utils.mjs';
import {Presentation,PresentationFile,FileBlob} from 'file:///C:/Program%20Files/WindowsApps/OpenAI.CodexPrimaryRuntime.v26-1105-1297-0_26.1105.1297.0_x64__3k8sg7r9htsxt/dependencies/node/node_modules/@oai/artifact-tool/dist/artifact_tool.mjs';
const dir=path.resolve('report/pptx30_work'),prev=path.resolve('report/pptx_work');
const source='report/output/DoAn_PhatHienChayKhoi_NangCap_22Slide.pptx';
const imported=await PresentationFile.importPptx(await FileBlob.load(source));
const proto=imported.toProto(),originals=proto.slides;
const text=e=>(e.paragraphs??[]).flatMap(p=>(p.runs??[]).map(r=>r.text??'')).join('');
function settext(e,t){const r=e.paragraphs[0].runs[0];e.paragraphs=[{...e.paragraphs[0],runs:[{...r,text:t}]}];}
function old(n){return structuredClone(originals[n-1]);}
function blank(t){let s=old(2);s.id='new'+Math.random().toString(36).slice(2,10);s.elements=s.elements.slice(0,5);settext(s.elements[0],t);return s;}
const slides=[old(1),old(2),old(3),old(4),old(5),old(6),blank('So sánh Gaussian, Median và CLAHE'),old(7),old(8),blank('False Positive của phát hiện lửa truyền thống'),old(9),old(10),blank('Khói: từ mặt nạ màu đến bounding box'),old(11),blank('YOLOv8 và nguyên lý nhận diện'),old(13),blank('Quy trình gán nhãn và định dạng YOLO'),old(14),blank('Loss và mAP từ lịch sử huấn luyện thật'),old(15),old(16),blank('Pipeline xử lý và trao đổi giữa các luồng'),old(18),blank('Demo Video và thao tác Webcam'),old(19),old(20),blank('Phát alarm.wav và dừng cảnh báo'),old(21),blank('Phân tích chỉ số và các lỗi nhận diện'),old(22)];
function walk(elements,fn){for(const e of elements){fn(e);walk(e.children??[],fn);}}
for(let i=0;i<slides.length;i++){
 slides[i].index=i;
 walk(slides[i].elements,e=>{let t=text(e);if(/^\d{2} \/ 22$/.test(t))settext(e,`${String(i+1).padStart(2,'0')} / 30`);else if(/TV[1-4]/.test(t))settext(e,t.replace(/TV1/g,'Tích hợp').replace(/TV2/g,'Lửa').replace(/TV3/g,'Khói').replace(/TV4/g,'YOLO'));});
}
// Keep the cover identities exactly, widen the name/ID boxes, and contain its navy strip.
for(const e of slides[0].elements){const t=text(e);if(/^204524\d+$/.test(t)){e.bbox.widthEmu=2700000;e.bbox.heightEmu=420000;}if(['Phạm Tấn Dương','Nguyễn Quốc Khang','Nguyễn Viết Khánh','Cao Văn Nho'].includes(t)){e.bbox.widthEmu=3900000;e.bbox.heightEmu=450000;}if(!t&&e.bbox?.xEmu===0&&e.bbox?.heightEmu>10287000)e.bbox.heightEmu=10287000;}
// Consolidate limitations in the experiment analysis; retain useful technical statements.
for(const [idx,find,repl] of [
 [17,'Có script và best.pt.','Checkpoint hiện tại: exp1_yolov8n_baseline, batch 16, imgsz 640, lr0 0,01; lịch sử gồm 50 epoch.'],
 [18,'',''],
 [24,'Ảnh và video đã có','Image xử lý một lần. Video và Webcam chạy liên tục, với trạng thái nền riêng cho mỗi phiên.'],
 [27,'100 ảnh / phương pháp','100 ảnh / phương pháp trong bảng lịch sử. Precision, Recall và F1 ở mức bounding box.'],
 [27,'FPS đo detector','FPS đo tại detector sau warmup 5 ảnh. Phần đọc nguồn, vẽ ảnh và GUI không nằm trong phép đo.']
]){if(find)for(const e of slides[idx].elements)if(text(e).startsWith(find))settext(e,repl);}
proto.slides=slides;const p=Presentation.load(proto);
const NAVY='#17365D',ORANGE='#E8862E',INK='#283747',BLUE='#4F7FAE';
function tx(s,t,x,y,w,h,size=36,bold=false,color=INK){const e=s.shapes.add({geometry:'textbox',name:t.slice(0,60),position:{left:x,top:y,width:w,height:h},fill:'none',line:{fill:'none',width:0}});e.text=t;e.text.style={fontFamily:'Times New Roman',fontSize:size,bold,color};e.text.insets=0;return e;}
function heading(s,t,x,y,w=800){return tx(s,t,x,y,w,65,40,true,NAVY);}
function cap(s,t,y=934){return tx(s,t,120,y,1670,62,29,false,NAVY);}
async function img(s,f,x,y,w,h,base=dir){const b=await fs.readFile(path.join(base,f));return s.images.add({blob:b.buffer.slice(b.byteOffset,b.byteOffset+b.byteLength),contentType:/jpe?g$/.test(f)?'image/jpeg':'image/png',alt:f,fit:'contain',position:{left:x,top:y,width:w,height:h}});}
function note(s,t){s.speakerNotes.text=t;}
function table(s,vals,x,y,w,h,widths,size=32){const a=s.tables.add({rows:vals.length,columns:vals[0].length,left:x,top:y,width:w,height:h,values:vals,columnWidths:widths});for(let r=0;r<vals.length;r++)for(let c=0;c<vals[0].length;c++){const cell=a.getCell(r,c);cell.text.style={fontFamily:'Times New Roman',fontSize:size,color:r===0?'#FFFFFF':INK,bold:r===0};cell.fill=r===0?NAVY:r%2?'#F1F5F8':'#FFFFFF';}return a;}
function box(s,t,x,y,w,h,size=36){const e=s.shapes.add({geometry:'roundRect',position:{left:x,top:y,width:w,height:h},fill:'#EAF1F7',line:{fill:'#A3B5C8',width:1.4},name:t});e.text=t;e.text.style={fontFamily:'Times New Roman',fontSize:size,bold:true,color:NAVY,alignment:'center',verticalAlignment:'middle'};e.text.insets=18;return e;}
function connect(s,a,b,from='right',to='left'){s.shapes.connect(a,b,{kind:'elbow',fromSide:from,toSide:to,line:{fill:NAVY,width:2},tail:{type:'triangle',width:'med',length:'med'}});}
function chart(s,type,title,categories,series,x,y,w,h,max){return s.charts.add(type,{position:{left:x,top:y,width:w,height:h},title,titleTextStyle:{fontSize:28,bold:true,fill:NAVY},categories,series,hasLegend:true,legend:{position:'bottom',overlay:false,textStyle:{fontSize:25,fill:INK}},chartFill:'#FFFFFF',plotAreaFill:'#FFFFFF',xAxis:{title:'Epoch',textStyle:{fontSize:22,fill:INK},majorGridlines:null},yAxis:{min:0,...(max?{max}:{}),numberFormatCode:'0.0',textStyle:{fontSize:22,fill:INK},majorGridlines:{fill:'#DCE4EB',width:1}},lineOptions:{smooth:false},dataLabels:{showValue:false}});}
const evidence=JSON.parse(await fs.readFile(path.join(dir,'evidence.json'),'utf8'));
// New slide 7: real image filters plus the repository's ablation rows.
{
const s=p.slides.items[6];for(const [i,f,label] of [[0,'gaussian.png','Gaussian 5 × 5'],[1,'median.png','Median 5 × 5'],[2,'clahe.png','CLAHE 2,0']]){heading(s,label,130+i*565,205,520);await img(s,f,130+i*565,275,510,300);}
table(s,[['Cấu hình','Precision','Recall','F1','FPS'],['Không tiền xử lý','0,2180','0,1962','0,2065','149,3'],['Gaussian 5','0,2213','0,1985','0,2093','126,5'],['Median 5','0,2130','0,2008','0,2067','113,4'],['CLAHE 2,0','0,1856','0,2362','0,2078','105,9']],130,615,1640,280,[580,265,265,265,265],30);
cap(s,'Gaussian làm mượt. Median dùng trung vị cục bộ. CLAHE tăng tương phản trên kênh V và có thể khuếch đại nhiễu.');
note(s,'Nguồn: traditional/preprocess.py; eval/ablation_pre.csv. Chọn bốn hàng nguyên gốc, làm tròn 4 chữ số metric và 1 chữ số FPS. Ảnh WEB10532 qua bộ lọc thực, không phải ảnh nhận diện được tạo giả. Các cấu hình không thay đổi dữ liệu hoặc ngưỡng detector mặc định.');
}
// New slide 10: genuine false positive with sunset and no fire label.
{
const s=p.slides.items[9];heading(s,'Traditional: fire, score ≈ 0,45',130,220,820);heading(s,'Mặt nạ màu HSV',1010,220,780);
await img(s,'fp_sunset_result.png',130,300,760,350);await img(s,'fp_sunset_mask.png',1010,300,760,350);
tx(s,'AoF06728: không có nhãn fire, nhưng detector báo fire với score ≈ 0,45.',140,700,1630,90,40,true,NAVY);
tx(s,'Ánh hoàng hôn thỏa ngưỡng màu và độ sáng. Lọc diện tích, tỉ lệ hộp vẫn giữ vùng này.',140,810,1610,95,37);
cap(s,'Score truyền thống là mật độ pixel hợp màu trong ROI. Giá trị cao không xác nhận đó là ngọn lửa.');
note(s,'Nguồn: data/test/images/AoF06728.jpg và labels/AoF06728.txt; chạy detect_fire với PARAMS hiện tại. Detection (215,8,425,138,fire,0.452770673486786), ảnh resize 640x480. Hai hình cắt cùng vùng y=0..250 để nhìn rõ ánh mặt trời và mặt nạ. Không thay ngưỡng, không thêm box giả.');
}
// New slide 13: actual same-image color/morphology/output, distinct from MOG2 video example.
{
const s=p.slides.items[12];const entries=[['smoke_still.png','01  Ảnh đầu vào',prev],['smoke_color.png','02  Lọc màu HSV',dir],['smoke_clean.png','03  Opening / Closing',dir],['smoke_still_result.png','04  Contour và bounding box',prev]];
for(let i=0;i<entries.length;i++){let x=130+(i%2)*880,y=205+Math.floor(i/2)*345;heading(s,entries[i][1],x,y,760);await img(s,entries[i][0],x,y+65,760,290,entries[i][2]);}
cap(s,'Video bổ sung MOG2 để kiểm tra chuyển động trong contour. Ảnh tĩnh dùng chuỗi màu và hình thái học.');
note(s,'Nguồn: ảnh AoF06978, SmokeDetector(use_bg_sub=False), thông số HSV S<=55,V75..235, open5, close11 iterations2. MOG2 không được áp dụng giả lên ảnh tĩnh. Sau morphology: diện tích, aspect ratio, motion ratio (video), Canny, centroid, score.');
}
// Editable replacement of the source YOLO overview, retaining its technical content.
{
const s=p.slides.items[14];const a=box(s,'Ảnh BGR\nTiền xử lý thư viện',130,255,480,145),b=box(s,'Backbone\nTrích đặc trưng',720,255,480,145),c=box(s,'Neck\nHợp nhất đa tỉ lệ',1310,255,480,145);
const d=box(s,'Head anchor-free\nDự đoán box và lớp',130,570,480,145),e=box(s,'Hậu xử lý\nConfidence và NMS',720,570,480,145),f=box(s,'Wrapper dự án\nxyxy thành xywh',1310,570,480,145);
connect(s,a,b);connect(s,b,c);connect(s,c,d,'bottom','top');connect(s,d,e);connect(s,e,f);
tx(s,'Mô hình học đặc trưng từ ảnh và dự đoán vùng fire / smoke trong một lượt suy luận.',140,800,1640,100,41,true,NAVY);
cap(s,'Wrapper lọc theo confidence, ánh xạ hộp về ảnh gốc và trả cùng định dạng với detector truyền thống.');
note(s,'Kế thừa slide12 của bản22, dựng lại sơ đồ thành các đối tượng native để toàn bộ nhãn chỉnh sửa được. Nguồn: báo cáo Word mới nhất và yolo/yolo_detect.py; pipeline.py.');
}
// New slide 17: real label example, with editable text and formulas.
{
const s=p.slides.items[16];const a=box(s,'Chọn ảnh\nVà kiểm tra lớp',130,220,365,120,33),b=box(s,'Vẽ box sát\nLửa hoặc khói',565,220,365,120,33),c=box(s,'Xuất nhãn\nYOLO .txt',1000,220,365,120,33),d=box(s,'Kiểm tra ID\nVà tọa độ',1435,220,365,120,33);connect(s,a,b);connect(s,b,c);connect(s,c,d);
heading(s,'Ảnh và nhãn phải cùng tên',140,405,1600);tx(s,'images/WEB10532.jpg       labels/WEB10532.txt',140,485,1640,65,40,true,NAVY);
tx(s,'class_id    x_center    y_center    width    height',140,585,1640,60,38,true,ORANGE);
tx(s,'1    0.301613    0.562366    0.406452    0.337634',140,660,1640,65,40);
tx(s,'x_center = x_tâm / W       y_center = y_tâm / H\nwidth = w_box / W           height = h_box / H',140,760,1100,125,37);
tx(s,'0 = smoke\n1 = fire',1400,765,370,110,41,true,NAVY);
cap(s,'Một dòng cho mỗi đối tượng. Ảnh âm tính dùng file nhãn rỗng. Tọa độ thuộc [0,1].');
note(s,'Nguồn: data/LABELING_GUIDE.md; data.yaml; nhãn WEB10532.txt. Dòng ví dụ là dòng fire lớn trong file thật, làm tròn đến 6 chữ số. Quy trình nêu cách gán nhãn/kiểm tra dữ liệu, không khẳng định nhóm gán lại toàn bộ D-Fire.');
}
// New slide 19: full 50-epoch history embedded in actual checkpoint, never synthetic.
{
const s=p.slides.items[18],r=evidence.train_results,epochs=r.epoch.map(String);
tx(s,'exp1_yolov8n_baseline     50 epoch     batch 16     imgsz 640     lr0 0,01',140,205,1660,65,38,true,NAVY);
chart(s,'line','Box loss: train và validation',epochs,[{name:'Train',values:r['train/box_loss'],line:{fill:NAVY,width:3}},{name:'Validation',values:r['val/box_loss'],line:{fill:ORANGE,width:3}}],110,315,820,470);
chart(s,'line','mAP trên validation',epochs,[{name:'mAP50',values:r['metrics/mAP50(B)'],line:{fill:NAVY,width:3}},{name:'mAP50–95',values:r['metrics/mAP50-95(B)'],line:{fill:ORANGE,width:3}}],985,315,820,470,1);
tx(s,'Epoch 47 đạt mAP50–95 = 0,4460, phù hợp fitness lưu trong best.pt.',140,825,1630,70,39,true,NAVY);
cap(s,'Nguồn biểu đồ: train_results trong best.pt. Metric validation của checkpoint được tách khỏi benchmark 100 ảnh.');
note(s,'Nguồn đọc trực tiếp YOLO(yolo/weights/best.pt).ckpt: train_results có epoch1..50, train/box_loss,val/box_loss,metrics/mAP50(B),metrics/mAP50-95(B). train_args.name=exp1_yolov8n_baseline,model/resume trỏ last.pt,epochs50,batch16,imgsz640,lr0 .01,device0. Ultralytics metadata8.4.175,date2026-10-12. Checkpoint epoch=-1 sau strip, không dùng trường này để suy số epoch. Epoch47 có fitness .446, train_metrics mAP50 .76521,mAP50-95 .446. SHA256 '+evidence.weights_sha256+'. Dữ liệu literal nguyên bản trong biểu đồ native, không nội suy/smooth.');
}
// Editable reconstruction of source pipeline diagram and thread responsibilities.
{
const s=p.slides.items[21];const a=box(s,'Mở nguồn\nKiểm tra capture',130,250,480,140),b=box(s,'Nạp detector\nKiểm tra hủy phiên',720,250,480,140),c=box(s,'Đọc frame\nLetterbox và detect',1310,250,480,140),d=box(s,'Ánh xạ box\nVẽ trên ảnh gốc',130,555,480,140),e=box(s,'Cập nhật cảnh báo\nTính FPS, tạo ảnh PIL',720,555,480,140),f=box(s,'Queue mới nhất\nGUI cập nhật ảnh',1310,555,480,140);connect(s,a,b);connect(s,b,c);connect(s,c,d,'bottom','top');connect(s,d,e);connect(s,e,f);
tx(s,'Worker: đọc nguồn, suy luận, cảnh báo. Main thread: nhận queue và cập nhật Tkinter.',140,785,1640,100,39,true,NAVY);
cap(s,'Queue ảnh có kích thước 1. Khi kết thúc, finally dừng cảnh báo và giải phóng capture.');
note(s,'Kế thừa đầy đủ nội dung slide17 của bản22, dựng lại native. Nguồn: gui/app.py worker/poll_frames, pipeline.py. Queue ảnh mới nhất và queue sự kiện tách biệt, mã phiên ngăn kết quả cũ cập nhật GUI. Đa luồng giữ GUI phản hồi, không tự tăng tốc suy luận.');
}
// Source GUI slide becomes an actionable Image demo while retaining screenshot and functions.
{
const s=p.slides.items[22];for(const e of s.shapes.items){if(String(e.text).includes('Chọn nguồn ảnh / video'))e.text='1. Chọn Image và Chọn ảnh\n\n2. Xem ảnh preview\n\n3. Chọn phương pháp\n\n4. Nhấn Nhận diện ảnh\n\n5. Đọc box, nhãn, score';}
note(s,'Ảnh chụp GUI thật từ bản22, mẫu WEB10532, yolo. Demo Image xử lý một lần, không bật âm thanh. GUI giữ các chức năng chọn nguồn, phương pháp, nhận diện, bắt đầu/dừng.');
}
// New slide 24: real video UI plus reproducible Webcam demo steps.
{
const s=p.slides.items[23];await img(s,'gui_video.jpg',130,205,1100,760);
heading(s,'Video file',1280,235,500);tx(s,'Chọn Video và file MP4.\nNhấn Bắt đầu để đọc frame.\nTheo dõi FPS và trạng thái.\nNhấn Dừng để nhả nguồn.',1280,315,510,240,36);
heading(s,'Webcam',1280,620,500);tx(s,'Chọn Webcam, chỉ số 0.\nChọn phương pháp.\nBắt đầu, quan sát khung hình.\nDừng trước khi đổi nguồn.',1280,700,510,240,36);
note(s,'Nguồn: screenshot FireSmokeApp chạy video data/video/253436_medium.mp4, phương pháp yolo, ngày09/11/2026. Đây là video phong cảnh, dùng kiểm tra đường xử lý, không giả thành video cháy. Các bước Webcam dựa trên GUI thật và báo cáo mục8.10. Không suy diễn FPS ảnh chụp thành tốc độ trung bình.');
}
// New slide 27: native sound lifecycle diagram with actual WAV metadata.
{
const s=p.slides.items[26];const a=box(s,'Có detection\nĐủ 5 frame liên tiếp',130,245,480,140),b=box(s,'Cooldown đạt 3 giây\nKể từ lần kích hoạt trước',720,245,480,140,33),c=box(s,'Phát assets/alarm.wav\nPlaySound bất đồng bộ',1310,245,480,140,33);connect(s,a,b);connect(s,b,c);
tx(s,'SND_ASYNC: trả về ngay, giữ vòng xử lý ảnh tiếp tục chạy.',140,450,1630,75,39,true,NAVY);
tx(s,'SND_NOSTOP: không thay thế âm thanh đang phát. Thiếu WAV thì dùng SystemExclamation.',140,540,1630,100,36);
const stop=box(s,'Dừng / đóng GUI',130,725,480,120),off=box(s,'_active = False\nXóa bộ đếm',720,725,480,120,33),cancel=box(s,'PlaySound(None, 0)\nNgắt âm thanh của phiên',1310,725,480,120,33);connect(s,stop,off);connect(s,off,cancel);
cap(s,'alarm.wav: mono, 44.100 Hz, dài khoảng 1,35 giây. Cơ chế âm thanh dùng winsound trên Windows.');
note(s,'Nguồn: gui/alert.py; config.py; metadata wave.open assets/alarm.wav: '+JSON.stringify(evidence.wav)+'. RLock đồng bộ các instance và chủ sở hữu kênh âm thanh. Frame rỗng reset counter nhưng không gọi stop sound trong update; lệnh Stop/close mới gọi PlaySound(None,0). Thiếu winsound thì bỏ phát. Không khẳng định đã nghe loa.');
}
// New slide 29: native quantitative chart and exact metric interpretation.
{
const s=p.slides.items[28],summary=JSON.parse(await fs.readFile('report/comparison_summary.json','utf8'));
const rows=Object.entries(summary).filter(([k])=>!k.includes('Khói')).map(([,v])=>v);
const ch=s.charts.add('bar',{position:{left:100,top:225,width:980,height:620},title:'So sánh cùng lớp mục tiêu: lửa',titleTextStyle:{fontSize:30,bold:true,fill:NAVY},categories:['Traditional','YOLOv8','Hybrid'],series:[{name:'Precision',values:rows.map(r=>Number(r.box_precision.toFixed(4))),fill:NAVY},{name:'Recall',values:rows.map(r=>Number(r.box_recall.toFixed(4))),fill:ORANGE},{name:'F1',values:rows.map(r=>Number(r.box_f1.toFixed(4))),fill:BLUE}],barOptions:{direction:'column',grouping:'clustered',gapWidth:90},hasLegend:true,legend:{position:'bottom',textStyle:{fontSize:26}},xAxis:{textStyle:{fontSize:26}},yAxis:{min:0,max:1,majorUnit:.25,numberFormatCode:'0.00',textStyle:{fontSize:24},majorGridlines:{fill:'#DCE4EB',width:1}},dataLabels:{showValue:true,position:'outEnd',numberFormatCode:'0.000',textStyle:{fontSize:22}},chartFill:'#FFFFFF',plotAreaFill:'#FFFFFF'});
heading(s,'Cách đọc chỉ số',1160,225,640);tx(s,'Precision = TP / (TP + FP)\nRecall = TP / (TP + FN)\nF1 = 2PR / (P + R)',1160,310,640,200,36);
tx(s,'YOLO lửa: P cao, R ≈ 0,486.\nHybrid: R còn 0,300.\nKhói phải đánh giá riêng.',1160,555,640,170,36,true,NAVY);
tx(s,'Lỗi minh họa: hoàng hôn báo fire, khói loãng bị bỏ sót, box khói ôm cả nền.',1160,760,640,155,35);
cap(s,'Bảng 100 ảnh thiếu metadata thiết bị/manifest và benchmark Combined. Ablation và metric train dùng giao thức riêng.');
note(s,'Nguồn: report/comparison_summary.json, giá trị chart làm tròn 4 chữ số theo bảng, số liệu gốc lưu tại JSON, 3 hàng cùng lớp fire. Lỗi: AoF06728 từ thực chạy mới; AoF06978 YOLO rỗng và Traditional box rộng; AoF06723 có nhãn rỗng nhưng Traditional smoke. IoU evaluator mặc định .3, JSON không ghi threshold của lượt cũ; FPS chỉ detector, khác FPS GUI. Metric validation 2 lớp trong checkpoint không so trực tiếp bảng100 ảnh.');
}
// Update metadata-derived training context and limit repeated caveats to experiments.
for(const s of p.slides.items){for(const ch of s.charts.items)applyPresentationChartFont(ch,{fontFamily:'Times New Roman',availableFonts:['Times New Roman']});let n=String(s.speakerNotes.text??'');s.speakerNotes.text=n.replace(/TV1/g,'Tích hợp hệ thống').replace(/TV2/g,'Phát hiện lửa').replace(/TV3/g,'Phát hiện khói').replace(/TV4/g,'YOLO và dữ liệu');}
await fs.writeFile(path.join(dir,'deck.proto.json'),JSON.stringify(p.toProto()));
await(await PresentationFile.exportPptx(p)).save(path.join(dir,'candidate.pptx'));
for(let i=0;i<p.slides.items.length;i++){await fs.writeFile(path.join(dir,`slide-${String(i+1).padStart(2,'0')}.png`),new Uint8Array(await(await p.export({slide:p.slides.items[i],format:'png',scale:.75})).arrayBuffer()));}
console.log('Built',p.slides.items.length);


