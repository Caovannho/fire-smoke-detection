import fs from 'node:fs/promises';
import path from 'node:path';
import {pathToFileURL} from 'node:url';
import {Presentation,PresentationFile,FileBlob} from 'file:///C:/Program%20Files/WindowsApps/OpenAI.CodexPrimaryRuntime.v26-1105-1297-0_26.1105.1297.0_x64__3k8sg7r9htsxt/dependencies/node/node_modules/@oai/artifact-tool/dist/artifact_tool.mjs';
const dir=path.resolve('report/pptx_work');
const imported=await PresentationFile.importPptx(await FileBlob.load('report/DoAn_PhatHienChayKhoi.pptx.pptx'));
const proto=imported.toProto();
const originals=proto.slides;
const text=e=>(e.paragraphs??[]).flatMap(p=>(p.runs??[]).map(r=>r.text??'')).join('');
function settext(e,t){let r=e.paragraphs[0].runs[0];e.paragraphs=[{...e.paragraphs[0],runs:[{...r,text:t}]}];}
function old(n){return structuredClone(originals[n-1]);}
function blank(title){let s=old(2);s.id='new'+Math.random().toString(36).slice(2,10);s.elements=s.elements.slice(0,5);settext(s.elements[0],title);return s;}
const order=[old(1),old(2),old(3),old(4),old(5),blank('Quy trình tiền xử lý ảnh'),blank('Lửa truyền thống: từ mặt nạ màu đến hộp bao'),blank('Thực nghiệm lửa qua từng bước xử lý'),old(7),blank('MOG2 và kiểm tra chuyển động theo vùng'),blank('Thực nghiệm phát hiện khói'),blank('YOLOv8 và nguyên lý nhận diện'),blank('Bộ dữ liệu và định dạng gán nhãn'),blank('Quá trình huấn luyện YOLOv8'),blank('Kết quả nhận diện bằng YOLOv8'),old(9),old(10),blank('Giao diện GUI thực tế và các chức năng'),blank('Nhận diện ảnh tĩnh, video và webcam'),old(11),blank('Kết quả thực nghiệm: Precision, Recall, F1 và FPS'),old(15)];
for(let i=0;i<order.length;i++){order[i].index=i;for(let e of order[i].elements){if(/^\d{2} \/ 15$/.test(text(e)))settext(e,`${String(i+1).padStart(2,'0')} / 22`);}}
// Cover: retain every identity string, expand the student-number boxes.
for(let e of order[0].elements){if(/^204524\d+$/.test(text(e))){e.bbox.widthEmu=2200000;e.bbox.heightEmu=400000;}}
// Describe the actual letterbox input rather than stretching the source image.
for(let e of order[4].elements){if(text(e).includes('frame: BGR'))settext(e,'Đầu ra: (x, y, w, h, label, score) · fire / smoke · BGR letterbox 640 × 480');}
proto.slides=order;
const p=Presentation.load(proto);
const NAVY='#17365D',ORANGE='#E8862E',INK='#283747';
function tx(s,t,x,y,w,h,size=36,bold=false,color=INK){let a=s.shapes.add({name:t.slice(0,45),geometry:'textbox',position:{left:x,top:y,width:w,height:h},fill:'none',line:{fill:'none',width:0}});a.text=t;a.text.style={fontFamily:'Times New Roman',fontSize:size,bold,color};a.text.insets=0;return a;}
async function img(s,f,x,y,w,h){let b=await fs.readFile(path.join(dir,f));s.images.add({blob:b.buffer.slice(b.byteOffset,b.byteOffset+b.byteLength),contentType:f.endsWith('.jpg')?'image/jpeg':'image/png',alt:f,fit:'contain',position:{left:x,top:y,width:w,height:h}});}
function note(s,t){s.speakerNotes.text=t;}
function caption(s,t,y=934){tx(s,t,120,y,1660,60,27,false,NAVY);}
function heading(s,t,x,y,w=750){tx(s,t,x,y,w,65,40,true,NAVY);}
function row(s,label,body,y){tx(s,label,125,y,480,65,38,true,NAVY);tx(s,body,630,y,1140,115,36);}
function table(s,values,x,y,w,h,widths){let a=s.tables.add({rows:values.length,columns:values[0].length,left:x,top:y,width:w,height:h,values,columnWidths:widths});for(let r=0;r<values.length;r++)for(let c=0;c<values[0].length;c++){let cell=a.getCell(r,c);cell.text.style={fontFamily:'Times New Roman',fontSize:32,color:r===0?'#FFFFFF':INK,bold:r===0};cell.fill=r===0?NAVY:r%2?'#F1F5F8':'#FFFFFF';}return a;}
// 6: before/after and optional filtering, based on actual image processing.
{
let s=p.slides.items[5];heading(s,'Ảnh gốc',140,225);heading(s,'Gaussian 5 × 5',1010,225);
await img(s,'fire_original.png',140,300,730,450);await img(s,'fire_gaussian.png',1010,300,730,450);
tx(s,'Giữ tỉ lệ ảnh bằng letterbox 640 × 480 trước suy luận.',140,780,1630,60,37,true,NAVY);
tx(s,'Gaussian, Median và CLAHE là các tùy chọn khảo sát. Mặc định detector lửa tắt cả ba.',140,855,1630,85,34);
note(s,'Nguồn: traditional/preprocess.py; pipeline.prepare_frame; traditional/fire_detect.py PARAMS. Ảnh test WEB10532.jpg, Gaussian thực chạy với kernel 5x5. Cặp ảnh minh họa bộ lọc tùy chọn, không phải cấu hình mặc định.');
}
// 7: keep source algorithm and parameter values, replace dark evidence.
{
let s=p.slides.items[6];let steps=[['01  Lọc màu HSV','H ≤ 35, S ≥ 60, V ≥ 200'],['02  Opening / Closing','Kernel ellipse 5 × 5'],['03  Lọc contour','Diện tích 0,2–80% ảnh, w/h 0,25–4'],['04  Chấm điểm ROI','Tỉ lệ pixel hợp màu trong hộp bao']];
steps.forEach(([a,b],i)=>{heading(s,a,130,235+i*145,780);tx(s,b,130,300+i*145,790,65,34);});
await img(s,'fire_contour.png',1000,245,760,570);
caption(s,'Lõi trắng sáng được bổ sung khi có quầng cam. Màu da, áo cam và ánh sáng vẫn có thể gây nhầm.');
note(s,'Nguồn: traditional/fire_detect.py PARAMS và color_mask/detect_fire; white_v=245, halo_v=100, halo_r=15. Kết quả contour và box chạy trên WEB10532.jpg. Flicker mặc định tắt.');
}
{
let s=p.slides.items[7];let files=['fire_original.png','fire_hsv.png','fire_open.png','fire_close.png','fire_contour.png'];let labels=['Ảnh đầu vào','Mặt nạ màu HSV','Sau opening','Sau closing','Contour và bounding box'];
for(let i=0;i<5;i++){let x=i<3?125+i*565:405+(i-3)*760,y=i<3?230:590,w=i<3?535:680,h=i<3?275:285;tx(s,labels[i],x,y,w,50,34,true,NAVY);await img(s,files[i],x,y+55,w,h);}
note(s,'Nguồn: ảnh test WEB10532.jpg; các bước thực chạy từ traditional/fire_detect.py. Không thay ngưỡng để làm đẹp kết quả. Contour màu cyan, box theo đầu ra detect_fire.');
}
{
let s=p.slides.items[9];heading(s,'Frame video thật',130,220,750);heading(s,'Mặt nạ tiền cảnh MOG2',1010,220,780);
await img(s,'smoke_original.png',130,295,760,445);await img(s,'smoke_mog2.png',1010,295,760,445);
tx(s,'Kiểm tra tỉ lệ pixel chuyển động trong từng contour màu, giữ vùng có motion_ratio ≥ 0,015.',140,775,1620,100,38,true,NAVY);
caption(s,'history 500, varThreshold 40, learning rate 0,003. Tiền cảnh thể hiện chuyển động, chưa xác nhận khói.');
note(s,'Nguồn: traditional/smoke_detect.py. Frame chỉ số 31 (đếm từ 0) của data/video/253436_medium.mp4. Học nền tuần tự từ frame đầu, mask lấy bằng apply learningRate=0 sau suy luận. Đây là video phong cảnh không gán nhãn khói, chỉ minh họa MOG2 trên nguồn thật. Không dùng kết quả này làm true positive. Ảnh tĩnh tắt trừ nền.');
}
{
let s=p.slides.items[10];heading(s,'Ảnh khói trong tập test',125,225,820);heading(s,'Kết quả Traditional',1000,225,820);
await img(s,'smoke_still.png',125,300,760,410);await img(s,'smoke_still_result.png',1000,300,760,410);
tx(s,'AoF06978: nhãn có smoke, detector trả một vùng khói rộng.',125,750,1610,70,37,true,NAVY);
tx(s,'Ảnh tĩnh tắt trừ nền. Box rộng chưa đồng nghĩa với định vị chính xác đối tượng.',125,835,1620,85,35);
note(s,'Nguồn: data/test/images/AoF06978.jpg và nhãn; chạy SmokeDetector(use_bg_sub=False). Kết quả (0,0,640,269,smoke,0.7991) tại lượt minh họa. Ground truth theo dataset, ví dụ đơn lẻ không suy ra tỷ lệ lỗi.');
}
{
let s=p.slides.items[11];await img(s,'word_image3.png',145,235,1610,480);
tx(s,'Dự đoán trực tiếp bounding box và nhãn từ đặc trưng ảnh.',140,755,1600,70,42,true,NAVY);
tx(s,'Backbone trích đặc trưng, Neck hợp nhất đa tỉ lệ, Head dự đoán. Lọc confidence và NMS sau suy luận.',140,845,1600,90,36);
note(s,'Nguồn: báo cáo Word hiện hành, sơ đồ nguyên lý YOLOv8; yolo/yolo_detect.py. Sơ đồ tổng hợp. Wrapper dùng model.predict, conf=0.45, iou=0.45.');
}
{
let s=p.slides.items[12];table(s,[['Tập dữ liệu','Số ảnh','Tỉ lệ'],['Train','14.122','65,6%'],['Validation','3.099','14,4%'],['Test','4.306','20,0%']],125,240,750,390,[310,220,220]);
tx(s,'Tổng 21.527 ảnh',130,670,730,65,43,true,NAVY);tx(s,'Hai lớp: smoke = 0, fire = 1',130,760,730,90,36);
await img(s,'ground_truth.png',975,245,790,590);
tx(s,'class_id  x_center  y_center  width  height',960,850,820,55,31,true,NAVY);
caption(s,'Tọa độ nhãn chuẩn hóa về [0,1]. Box bên phải lấy từ file nhãn của WEB10532, không phải dự đoán.');
note(s,'Nguồn: data.yaml; báo cáo Word mới nhất, mục 8.2: 14122/3099/4306; tỉ lệ tính trên tổng 21527. Ảnh và bounding box ground truth đọc từ data/test/images/WEB10532.jpg và labels/WEB10532.txt. Nhãn score 1 trên hình chỉ dùng để hiển thị ground truth.');
}
{
let s=p.slides.items[13];table(s,[['Preset trong mã','Mô hình','Batch','Learning rate'],['1. Baseline','YOLOv8n','16','0,01'],['2. Mô hình lớn hơn','YOLOv8s','8','0,01'],['3. Augmentation','YOLOv8n','16','0,005']],130,235,1640,390,[600,400,230,410]);
tx(s,'Thiết lập mặc định: 50 epoch, imgsz 640, workers 2',140,675,1610,65,40,true,NAVY);
tx(s,'model.train() lưu checkpoint, chọn best.pt và sao chép vào yolo/weights để suy luận.',140,765,1610,100,36);
caption(s,'Có script và best.pt. Chưa có log train đầy đủ để khẳng định preset nào tạo ra weights hiện tại.');
note(s,'Nguồn: yolo/train.py, tham số mặc định và run_preset. Preset 3 hsv_s=.8, hsv_v=.5, mosaic=1.0. Không khẳng định thực tế đã huấn luyện đủ 50 epoch, không tự tạo loss curve hay mAP50-95.');
}
{
let s=p.slides.items[14];await img(s,'fire_yolo.png',130,235,1050,650);
heading(s,'WEB10532',1270,280,510);tx(s,'Một vùng fire\nconfidence ≈ 0,79',1270,365,510,170,43,true,NAVY);
tx(s,'conf = 0,45\nIoU NMS = 0,45\nweights: best.pt',1270,575,510,170,36);
caption(s,'Có khói trong ảnh nhưng lượt suy luận này không trả nhãn smoke. Một ví dụ đúng vẫn có thể kèm bỏ sót.');
note(s,'Nguồn: chạy pipeline.load_detector(yolo), pipeline.detect_frame trên ảnh WEB10532 (đưa về 640x480 cho minh họa). Weights yolo/weights/best.pt, lớp {0:smoke,1:fire}. Không dùng ví dụ đơn lẻ để tính Precision/Recall.');
}
{
let s=p.slides.items[17];await img(s,'gui_real.jpg',130,220,1120,730);
heading(s,'Thao tác chính',1300,260,470);tx(s,'Chọn nguồn ảnh / video\n\nChọn Traditional, YOLO hoặc Combined\n\nNhận diện ảnh một lần\n\nBắt đầu / Dừng nguồn liên tục',1300,345,475,510,35);
note(s,'Nguồn: ảnh chụp cửa sổ FireSmokeApp thật ngày 09/11/2026, sau gọi callback nhận diện ảnh, phương pháp yolo, mẫu WEB10532. Ảnh chụp bằng Computer Use. Không phải mockup GUI. Hybrid chỉ có ở pipeline dòng lệnh.');
}
{
let s=p.slides.items[18];table(s,[['Nguồn','Cách xử lý','Cảnh báo'],['Ảnh tĩnh','Preview và nhận diện một lần','Tắt'],['Video file','Đọc frame đến hết file','5 frame, cooldown 3 s'],['Webcam','Đọc liên tục theo chỉ số camera','5 frame, cooldown 3 s'],['Camera IP','OpenCV mở địa chỉ nguồn','Chưa kiểm thử thiết bị IP']],130,245,1640,470,[380,780,480]);
tx(s,'Ảnh và video đã có minh chứng tích hợp. Webcam có lượt chạy trong báo cáo.',140,775,1630,100,39,true,NAVY);
caption(s,'FPS hiển thị theo cửa sổ 30 frame của worker. Không đồng nhất với FPS chỉ đo tại detector.');
note(s,'Nguồn: gui/app.py; config.py; báo cáo Word mục 7 và 8.10. Lượt video trước dùng video tổng hợp, webcam Traditional 25.3 FPS và Combined 9.0 chỉ là đo tức thời, không được coi tốc độ trung bình. Camera IP chưa có thử nghiệm trên thiết bị.');
}
{
let s=p.slides.items[20];table(s,[['Phương pháp / lớp','Precision','Recall','F1','FPS'],['Traditional / lửa','0,2763','0,3000','0,2877','159,8'],['Traditional / khói','0,0441','0,0625','0,0517','94,3'],['YOLOv8 / lửa','0,8718','0,4857','0,6239','116,6'],['Hybrid / lửa','0,8750','0,3000','0,4468','98,7']],130,230,1640,420,[640,260,260,260,220]);
tx(s,'YOLO lửa có Precision cao hơn, nhưng Recall vẫn còn hạn chế.',135,705,1630,70,40,true,NAVY);
tx(s,'100 ảnh / phương pháp trong JSON lưu sẵn. Combined chưa có benchmark riêng. Khói là lớp mục tiêu riêng.',135,800,1630,100,35);
caption(s,'FPS đo detector sau warmup 5 ảnh, không gồm GUI. Thiếu manifest và thiết bị, chưa khẳng định tái lập tốc độ.');
note(s,'Nguồn: report/comparison_summary.json và eval/compare_models.py, eval/evaluate.py; báo cáo Word mục 8.5. Precision/Recall/F1 mức box. Evaluator mặc định IoU .3 nhưng JSON không ghi ngưỡng lần chạy. Benchmark kéo giãn 640x480 khác letterbox GUI hiện tại. Không gọi đây là benchmark mới; không xếp hạng trực tiếp khói với lửa.');
}
// Add local provenance to inherited slides and correct assertion in the alert slide.
for(let i of [0,1,2,3,4,8,15,16,19,21]){note(p.slides.items[i],`Kế thừa nội dung và thiết kế từ slide ${[1,2,3,4,5,7,9,10,11,15][[0,1,2,3,4,8,15,16,19,21].indexOf(i)]} bản gốc. Đối chiếu báo cáo Word BaoCao_DoAn_HoanThien_KhongGhiChu.docx và mã nguồn repository. `+(i===19?'gui/alert.py: đếm frame có danh sách detection không rỗng, không theo dõi cùng một đối tượng. Frame rỗng reset counter; đủ 5 frame và cách lần còi trước ít nhất 3 giây mới yêu cầu âm thanh; stop ngắt và vô hiệu hóa instance. Ảnh tĩnh không gọi alerts.update.':'') );}
await fs.writeFile(path.join(dir,'draft.proto.json'),JSON.stringify(p.toProto()));
await (await PresentationFile.exportPptx(p)).save(path.join(dir,'candidate.pptx'));
for(let i=0;i<p.slides.items.length;i++)await fs.writeFile(path.join(dir,`final-${i+1}.png`),new Uint8Array(await(await p.export({slide:p.slides.items[i],format:'png',scale:0.75})).arrayBuffer()));
console.log('Built',p.slides.items.length);
