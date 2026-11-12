import sys,json
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[2]))
import cv2,numpy as np
from traditional.fire_detect import color_mask,PARAMS,detect_fire
from traditional.smoke_detect import SmokeDetector
root=Path(__file__).resolve().parents[2];out=Path(__file__).parent
choices=[]
for f in sorted((root/'data/test/images').glob('*'))[::7]:
 lab=root/'data/test/labels'/f.with_suffix('.txt').name
 lines=lab.read_text().splitlines() if lab.exists() else []
 if not any(s.startswith('1 ') for s in lines):continue
 im=cv2.imread(str(f))
 if im is None or im.mean()<65:continue
 im=cv2.resize(im,(640,480));d=detect_fire(im)
 if d:choices.append((f,im,lines))
 if len(choices)>=12:break
from PIL import Image,ImageOps,ImageDraw
m=Image.new('RGB',(1200,600),'white')
for i,(f,im,_) in enumerate(choices):
 m.paste(Image.fromarray(cv2.cvtColor(im,cv2.COLOR_BGR2RGB)).resize((300,200)),((i%4)*300,(i//4)*200));ImageDraw.Draw(m).text(((i%4)*300,(i//4)*200),f.stem,fill='blue')
m.save(out/'candidates.jpg')
(out/'choices.json').write_text(json.dumps([str(c[0]) for c in choices]))
