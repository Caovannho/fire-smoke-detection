import sys,json,hashlib,wave
from pathlib import Path
root=Path(__file__).resolve().parents[2];out=Path(__file__).parent
sys.path.insert(0,str(root));sys.dont_write_bytecode=True
import cv2,numpy as np
from traditional.preprocess import preprocess
from traditional.fire_detect import detect_fire,color_mask,PARAMS
from traditional.smoke_detect import SmokeDetector,PARAMS as SP,color_mask as smask
from pipeline import _draw_detection,load_detector,detect_frame
from ultralytics import YOLO
def save(name,im):cv2.imwrite(str(out/name),im)
im=cv2.imread(str(root/'data/test/images/WEB10532.jpg'));im=cv2.resize(im,(640,480))
for name,kw in [('gaussian',{'blur':5}),('median',{'median_k':5}),('clahe',{'clahe':2.0})]:save(name+'.png',preprocess(im,**kw))
found=[]
for f in sorted((root/'data/test/images').glob('*')):
 lab=root/'data/test/labels'/f.with_suffix('.txt').name
 if not lab.exists() or any(l.startswith('1 ') for l in lab.read_text().splitlines()):continue
 im=cv2.imread(str(f))
 if im is None or im.mean()<65:continue
 im=cv2.resize(im,(640,480));ds=detect_fire(im)
 if not ds:continue
 if max(d[2]*d[3] for d in ds)<2000:continue
 found.append((str(f),ds));save(f'fp{len(found)}_original.png',im);save(f'fp{len(found)}_mask.png',color_mask(im,PARAMS))
 for d in ds:_draw_detection(im,*d)
 save(f'fp{len(found)}_result.png',im)
 if len(found)==8:break
model=YOLO(str(root/'yolo/weights/best.pt'))
ckpt=model.ckpt
meta={k:ckpt.get(k) for k in ['epoch','date','version','train_args','train_metrics','train_results']}
meta['weights_sha256']=hashlib.sha256((root/'yolo/weights/best.pt').read_bytes()).hexdigest()
meta['names']=model.names;meta['fp_candidates']=found
with wave.open(str(root/'assets/alarm.wav')) as w:meta['wav']={'seconds':w.getnframes()/w.getframerate(),'sample_rate':w.getframerate(),'channels':w.getnchannels()}
# Smoke masks from the same real still. MOG2 is documented separately on the video slide.
sm=cv2.imread(str(root/'data/test/images/AoF06978.jpg'));sm=cv2.resize(sm,(640,480));m=smask(sm,SP)
ko=cv2.getStructuringElement(cv2.MORPH_ELLIPSE,(5,5));kc=cv2.getStructuringElement(cv2.MORPH_ELLIPSE,(11,11))
op=cv2.morphologyEx(m,cv2.MORPH_OPEN,ko);cl=cv2.morphologyEx(op,cv2.MORPH_CLOSE,kc,iterations=2)
save('smoke_color.png',m);save('smoke_clean.png',cl)
det=load_detector('yolo',image_mode=True)
for name in ['AoF06978','AoF06723']:
 f=next((root/'data/test/images').glob(name+'.*'));im=cv2.imread(str(f));ds=detect_frame(im,det);save(name+'_original.png',im)
 for d in ds:_draw_detection(im,*d)
 save(name+'_yolo.png',im);meta[name+'_yolo']=ds
 if name=='AoF06723':
  im=cv2.resize(cv2.imread(str(f)),(640,480));sd=SmokeDetector({'use_bg_sub':False}).detect(im)
  for x,y,w,h,label,score in sd:
   cv2.rectangle(im,(max(x,1),max(y,1)),(min(x+w,638),min(y+h,478)),(0,140,255),3)
   cv2.putText(im,f'{label} {score:.2f}',(max(x+5,5),max(y+25,25)),cv2.FONT_HERSHEY_SIMPLEX,.7,(0,140,255),2)
  save('negative_smoke.png',im);meta['negative_smoke']=sd
(out/'evidence.json').write_text(json.dumps(meta,ensure_ascii=False,default=str,indent=2),encoding='utf-8')
from PIL import Image,ImageOps,ImageDraw
sheet=Image.new('RGB',(1200,400),'white')
for i,(f,ds) in enumerate(found):
 a=Image.open(out/f'fp{i+1}_result.png');sheet.paste(a.resize((300,200)),((i%4)*300,(i//4)*200));ImageDraw.Draw(sheet).text(((i%4)*300,(i//4)*200),Path(f).stem,fill='blue')
sheet.save(out/'fp_candidates.jpg')
print(json.dumps(meta,ensure_ascii=True,default=str)[:6000])
