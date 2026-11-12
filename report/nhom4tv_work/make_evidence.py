"""Read-only inference on three existing examples; outputs only under report work."""
import os
import sys
from pathlib import Path
import json

ROOT = Path(__file__).resolve().parents[2]
WORK = Path(__file__).resolve().parent
(WORK / 'yolo_config').mkdir(exist_ok=True)
os.environ['YOLO_CONFIG_DIR'] = str(WORK / 'yolo_config')
os.environ['YOLO_AUTOINSTALL'] = 'false'
os.environ['YOLO_OFFLINE'] = 'true'
sys.path.insert(0, str(ROOT))
import cv2
from PIL import Image, ImageDraw, ImageFont
from pipeline import load_detector, detect_frame, prepare_frame, _draw_detection
from traditional.fire_detect import color_mask, PARAMS

font = ImageFont.truetype('C:/Windows/Fonts/arial.ttf', 24)
samples = {'sample_fire':'AoF07738', 'sample_smoke':'AoF06978', 'sample_negative':'AoF06723'}
records = {}
detectors = {method: load_detector(method, image_mode=True)
             for method in ('traditional', 'yolo', 'combined')}
for key, name in samples.items():
    frame = cv2.imread(str(ROOT / 'data/test/images' / (name + '.jpg')))
    canvas = Image.new('RGB', (1280, 810), 'white')
    records[name] = {}
    for index, method in enumerate(('original','traditional','yolo','combined')):
        annotated = frame.copy()
        if method != 'original':
            detections = detect_frame(frame, detectors[method])
            records[name][method] = detections
            for x,y,w,h,label,score in detections:
                _draw_detection(annotated,x,y,w,h,label,score)
        pic = Image.fromarray(cv2.cvtColor(annotated,cv2.COLOR_BGR2RGB)).resize((640,360))
        x,y=(index % 2)*640,(index//2)*405
        canvas.paste(pic,(x,y+40))
        ImageDraw.Draw(canvas).text((x+12,y+7),f'{method} | {name}',font=font,fill='black')
    canvas.save(WORK / (key+'.png'))

frame=cv2.imread(str(ROOT/'data/test/images/AoF07738.jpg'))
prepared,_=prepare_frame(frame)
mask=color_mask(prepared,PARAMS)
kernel=cv2.getStructuringElement(cv2.MORPH_ELLIPSE,(5,5))
opened=cv2.morphologyEx(mask,cv2.MORPH_OPEN,kernel)
closed=cv2.morphologyEx(opened,cv2.MORPH_CLOSE,kernel)
canvas=Image.new('RGB',(1280,1040),'white')
for idx,(name,pic) in enumerate((('BGR input displayed in RGB',cv2.cvtColor(prepared,cv2.COLOR_BGR2RGB)),('HSV mask',mask),('After opening',opened),('After closing',closed))):
    x,y=(idx%2)*640,(idx//2)*520
    canvas.paste(Image.fromarray(pic).convert('RGB'),(x,y+35))
    ImageDraw.Draw(canvas).text((x+12,y+4),name,font=font,fill='black')
canvas.save(WORK/'fire_masks.png')
(WORK/'image_predictions.json').write_text(json.dumps(records,ensure_ascii=False,indent=2),encoding='utf-8')
print(json.dumps(records,ensure_ascii=True))
