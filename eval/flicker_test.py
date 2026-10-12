"""Đo độ nhấp nháy trên một video. Dùng: python eval/flicker_test.py --video data/videos/lua1.mp4"""
import os
import sys
import argparse
import cv2
import numpy as np

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from traditional.fire_detect import FireDetector

ap = argparse.ArgumentParser()
ap.add_argument("--video", required=True)
ap.add_argument("--step", type=int, default=1, help="đọc mỗi step frame (để chuẩn hóa theo fps)")
ap.add_argument("--max", type=int, default=0, help="số frame tối đa sau lấy mẫu (0 = hết video)")
ap.add_argument("--fmin", type=float, default=0.0, help="ngưỡng nhấp nháy (0 = không lọc)")
args = ap.parse_args()

cap = cv2.VideoCapture(args.video)
if not cap.isOpened():
    sys.exit(f"Không mở được video: {args.video}")
fps = cap.get(cv2.CAP_PROP_FPS)
det = FireDetector(flicker_min=args.fmin)
vals, used, with_box, i = [], 0, 0, -1
while True:
    ok, frame = cap.read()
    if not ok:
        break
    i += 1
    if i % args.step:
        continue
    if args.max and used >= args.max:
        break
    dets = det.detect(cv2.resize(frame, (640, 480)))
    used += 1
    if used > det.warmup:
        with_box += bool(dets)
        vals += [det.flicker(d) for d in dets]
cap.release()

n = max(used - det.warmup, 1)
print(f"video: {os.path.basename(args.video)} | fps gốc {fps:.1f} | step {args.step} | frame dùng {used}")
print(f"frame có vùng phát hiện: {with_box}/{n} ({with_box / n:.0%}) | số bbox: {len(vals)}")
if vals:
    v = np.array(vals)
    print(f"độ nhấp nháy: trung vị {np.median(v):.3f} | p25 {np.percentile(v, 25):.3f} | p75 {np.percentile(v, 75):.3f}")
else:
    print("Không có vùng nào được phát hiện.")