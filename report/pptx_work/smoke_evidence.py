import sys,json
from pathlib import Path
root=Path(__file__).resolve().parents[2];out=Path(__file__).parent;sys.path.insert(0,str(root))
import cv2
from traditional.smoke_detect import SmokeDetector,color_mask,PARAMS
from pipeline import _draw_detection
im=cv2.imread(str(root/'data/test/images/AoF06978.jpg'));im=cv2.resize(im,(640,480))
d=SmokeDetector({'use_bg_sub':False}).detect(im)
cv2.imwrite(str(out/'smoke_still.png'),im);cv2.imwrite(str(out/'smoke_still_mask.png'),color_mask(im,PARAMS))
for x,y,w,h,label,score in d:
 cv2.rectangle(im,(x+1,y+1),(x+w-2,y+h-1),(0,140,255),3)
 cv2.putText(im,f'{label} {score:.2f}',(x+10,max(y+25,25)),cv2.FONT_HERSHEY_SIMPLEX,.7,(0,140,255),2)
cv2.imwrite(str(out/'smoke_still_result.png'),im)
print(d)
