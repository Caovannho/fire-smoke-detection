from pathlib import Path
from PIL import Image,ImageDraw,ImageFont
import math
WORK=Path(__file__).parent
font=ImageFont.truetype('C:/Windows/Fonts/times.ttf',29)
def diagram(key, nodes, edges, size=(1500,620)):
 im=Image.new('RGB',size,'white');d=ImageDraw.Draw(im)
 def arrow(a,b,label=''):
  d.line((a,b),fill='#334155',width=3)
  angle=math.atan2(b[1]-a[1],b[0]-a[0]);length=15
  d.polygon((b,(b[0]-length*math.cos(angle-.45),b[1]-length*math.sin(angle-.45)),(b[0]-length*math.cos(angle+.45),b[1]-length*math.sin(angle+.45))),fill='#334155')
  if label:d.text(((a[0]+b[0])/2+8,(a[1]+b[1])/2-30),label,font=font,fill='black')
 for a,b,label in edges:arrow(a,b,label)
 for x,y,w,h,text in nodes:
  d.rounded_rectangle((x,y,x+w,y+h),radius=9,fill='#edf2f7',outline='#334155',width=3)
  lines=text.split('\n');start=y+(h-len(lines)*34)/2
  for i,line in enumerate(lines):
   box=d.textbbox((0,0),line,font=font);d.text((x+(w-box[2])/2,start+i*34),line,font=font,fill='black')
 im.save(WORK/(key+'.png'))

nodes=[];edges=[]
for i,(name,backend,rule) in enumerate((('Traditional','Fire và Smoke','NMS theo lớp'),('YOLO','YOLO đã xác thực','NMS theo lớp'),('Combined','YOLO Fire Smoke','Union và NMS'),('Hybrid','HSV ứng viên và YOLO','Phủ box ít nhất 15%'))):
 x=20+i*375
 for y,text in ((15,name),(190,backend),(365,rule)):nodes.append((x,y,335,105,text))
 edges.extend([((x+167,120),(x+167,190),''),((x+167,295),(x+167,365),'')])
diagram('modes',nodes,edges,size=(1500,510))
diagram('architecture',[
 (510,15,480,95,'GUI main thread TV1'),(510,170,480,95,'Worker và Pipeline TV1'),
 (20,335,430,100,'Fire TV2 và Smoke TV3'),(535,335,430,100,'YOLO và Hybrid TV4'),
 (1050,335,430,100,'Kiểm tra và gộp TV1'),(80,510,570,90,'Queue ảnh → GUI main thread'),
 (850,510,570,90,'Detection → AlertSystem TV1')],
 [((750,110),(750,170),''),((620,265),(240,335),'chọn'),((750,265),(750,335),'chọn'),
 ((450,385),(1050,385),''),((965,385),(1050,385),''),((1200,435),(365,510),''),((1265,435),(1135,510),'')])
diagram('image_flow',[
 (500,10,500,95,'Chọn ảnh và đọc OpenCV'),(70,190,570,100,'Tác vụ Preview\nKhông nạp detector'),
 (870,190,570,100,'Tác vụ Nhận diện\nNạp detector theo lựa chọn'),(870,365,570,95,'Letterbox Detect và vẽ box'),
 (350,515,800,90,'Queue → main thread hiển thị\nCả hai nhánh đều không update cảnh báo')],
 [((650,105),(355,190),'preview'),((850,105),(1155,190),'image'),((355,290),(600,515),''),
 ((1155,290),(1155,365),''),((1155,460),(950,515),'')])
diagram('hybrid_flow',[
 (50,30,500,105,'HSV và morphology\nTìm contour ứng viên'),(850,30,550,105,'Có ứng viên hay không'),
 (850,230,550,95,'Không có → trả kết quả rỗng'),(50,230,500,95,'Có → YOLO toàn frame'),
 (50,430,500,110,'Kiểm tra phủ box YOLO\nÍt nhất 15% diện tích box'),(850,430,550,110,'Giữ dự đoán đạt điều kiện\nScore nhân 1.05 và chặn 1')],
 [((550,82),(850,82),''),((1125,135),(1125,230),'không'),((850,125),(300,230),'có'),
 ((300,325),(300,430),''),((550,485),(850,485),'')])
diagram('threads',[
 (30,30,460,120,'Main thread\nNguồn nút và mã phiên'),(1010,30,460,120,'Worker thread\nCapture và detector'),
 (530,230,440,100,'Queue ảnh tối đa một\nQueue sự kiện riêng'),(30,430,460,130,'Poll trên main thread\nKiểm tra phiên rồi\nPhotoImage và widget'),
 (1010,430,460,130,'Event và AlertSystem\nDừng hợp tác và\nrelease trong finally')],
 [((490,90),(1010,90),'khởi chạy'),((1230,150),(970,250),'xuất'),((530,280),(260,430),'đọc'),
 ((490,490),(1010,490),'Dừng'),((1230,150),(1230,430),'')])
diagram('alert_flow',[
 (20,30,430,100,'Kiểm tra active\nInactive → trả False'),(535,30,430,100,'Detection rỗng hay có'),
 (1050,30,430,100,'Rỗng → reset counter\nXóa trạng thái'),(535,230,430,100,'Có → tăng counter\nĐạt ít nhất 5 frame'),
 (20,430,430,125,'Đủ cooldown 3 giây\nCập nhật trạng thái\nPlaySound ASYNC NOSTOP'),
 (1050,430,430,125,'Stop dưới cùng khóa\nInactive và ngắt âm thanh\nKhông nhận cảnh báo mới')],
 [((450,80),(535,80),''),((965,80),(1050,80),'rỗng'),((750,130),(750,230),'có'),
 ((535,310),(235,430),'đủ điều kiện')])
