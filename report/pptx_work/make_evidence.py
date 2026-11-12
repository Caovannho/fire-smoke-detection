import sys,json,time
from pathlib import Path
root=Path(__file__).resolve().parents[2];out=Path(__file__).parent;sys.path.insert(0,str(root))
import cv2,numpy as np
from traditional.fire_detect import color_mask,PARAMS,detect_fire
from traditional.smoke_detect import SmokeDetector,PARAMS as SP,color_mask as smoke_mask
from ultralytics import YOLO
from pipeline import load_detector,detect_frame,_draw_detection
f=root/'data/test/images/WEB10532.jpg'
if not f.exists():f=next((root/'data/test/images').glob('WEB10532.*'))
im=cv2.imread(str(f));im=cv2.resize(im,(640,480));cv2.imwrite(str(out/'fire_original.png'),im)
cv2.imwrite(str(out/'fire_gaussian.png'),cv2.GaussianBlur(im,(5,5),0))
m=color_mask(im,PARAMS);cv2.imwrite(str(out/'fire_hsv.png'),m)
k=cv2.getStructuringElement(cv2.MORPH_ELLIPSE,(5,5));op=cv2.morphologyEx(m,cv2.MORPH_OPEN,k);cl=cv2.morphologyEx(op,cv2.MORPH_CLOSE,k)
cv2.imwrite(str(out/'fire_open.png'),op);cv2.imwrite(str(out/'fire_close.png'),cl)
ann=im.copy();ct,_=cv2.findContours(cl,cv2.RETR_EXTERNAL,cv2.CHAIN_APPROX_SIMPLE);cv2.drawContours(ann,ct,-1,(255,255,0),2)
for d in detect_fire(im):_draw_detection(ann,*d)
cv2.imwrite(str(out/'fire_contour.png'),ann)
model=load_detector('yolo');d=detect_frame(im,model);ann=im.copy()
for box in d:_draw_detection(ann,*box)
cv2.imwrite(str(out/'fire_yolo.png'),ann)
gt=im.copy();lab=root/'data/test/labels'/f.with_suffix('.txt').name
for line in lab.read_text().splitlines():
 c,x,y,w,h=map(float,line.split());_draw_detection(gt,*(int((x-w/2)*640),int((y-h/2)*480),int(w*640),int(h*480),'smoke' if c==0 else 'fire',1.0))
cv2.imwrite(str(out/'ground_truth.png'),gt)
# Real video frames, with sequential background learning, not repeated still images.
records=[]
for v in (root/'data/video').glob('*.mp4'):
 cap=cv2.VideoCapture(str(v));det=SmokeDetector();idx=0;best=None
 while idx<180:
  ok,fr=cap.read()
  if not ok:break
  fr=cv2.resize(fr,(640,480));ds=det.detect(fr)
  if idx>30 and ds and fr.mean()>55:
   best=(fr.copy(),ds,idx);break
  idx+=1
 cap.release()
 if best:
  fr,ds,idx=best;cm=smoke_mask(fr,SP);fg=det._bg_sub.apply(fr,learningRate=0)
  cv2.imwrite(str(out/'smoke_original.png'),fr);cv2.imwrite(str(out/'smoke_hsv.png'),cm);cv2.imwrite(str(out/'smoke_mog2.png'),fg)
  ann=fr.copy()
  for d in ds:_draw_detection(ann,*d)
  cv2.imwrite(str(out/'smoke_result.png'),ann);records.append({'video':v.name,'frame_index':idx,'detections':ds});break
(out/'evidence.json').write_text(json.dumps({'fire_image':f.name,'fire_detections':d,'smoke':records},default=str),encoding='utf-8')
print(records)

