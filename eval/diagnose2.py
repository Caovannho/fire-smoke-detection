"""Phân loại nguyên nhân bỏ sót lửa."""
import os
import sys
import glob
import random
import argparse
import numpy as np
import cv2

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from evaluate import load_gt, compute_iou, W, H, EXTS, ROOT
from traditional.fire_detect import detect, color_mask, PARAMS

BEST = dict(v_min=200, s_min=60, min_area=0.002, kernel=5)
P = {**PARAMS, **BEST}

ap = argparse.ArgumentParser()
ap.add_argument("--limit", type=int, default=800)
args = ap.parse_args()

img_dir = os.path.join(ROOT, "data", "val", "images")
lbl_dir = os.path.join(ROOT, "data", "val", "labels")
files = sorted(f for f in glob.glob(os.path.join(img_dir, "*")) if f.lower().endswith(EXTS))
if args.limit and args.limit < len(files):
    files = sorted(random.Random(0).sample(files, args.limit))

hit = touch = 0
cats = {"nho": 0, "mau": 0, "khac": 0}
white, warm = [], []   # trong nhóm "mau": tỉ lệ pixel trắng sáng / pixel cam sáng

for f in files:
    name = os.path.splitext(os.path.basename(f))[0]
    gts, _ = load_gt(os.path.join(lbl_dir, name + ".txt"))
    if not gts:
        continue
    img = cv2.imread(f)
    if img is None:
        continue
    img = cv2.resize(img, (W, H))
    preds = [d for d in detect(img, BEST) if d[4] == "fire"]
    mask = color_mask(img, P)
    hsv = cv2.cvtColor(img, cv2.COLOR_BGR2HSV)

    for g in gts:
        best = max([compute_iou(p[:4], g) for p in preds], default=0.0)
        if best >= 0.3:
            hit += 1
            continue
        if best > 0:
            touch += 1
            continue
        x0, y0 = max(0, int(g[0])), max(0, int(g[1]))
        x1, y1 = min(W, int(g[0] + g[2]) + 1), min(H, int(g[1] + g[3]) + 1)
        if x1 <= x0 or y1 <= y0:
            continue
        if g[2] * g[3] < P["min_area"] * W * H:
            cats["nho"] += 1
            continue
        cov = cv2.countNonZero(mask[y0:y1, x0:x1]) / ((x1 - x0) * (y1 - y0))
        if cov < 0.02:
            cats["mau"] += 1
            roi = hsv[y0:y1, x0:x1]
            bright = roi[..., 2] >= P["v_min"]
            n = roi.shape[0] * roi.shape[1]
            white.append(np.count_nonzero(bright & (roi[..., 1] < P["s_min"])) / n)
            warm.append(np.count_nonzero(bright & (roi[..., 1] >= P["s_min"]) & (roi[..., 0] <= P["h_max"])) / n)
        else:
            cats["khac"] += 1

miss = sum(cats.values())
n = hit + touch + miss
print(f"Tổng ô lửa thật: {n} | khớp {hit} | chạm {touch} | trượt hoàn toàn {miss}")
print("Trong nhóm trượt hoàn toàn:")
print(f"  ô nhãn nhỏ hơn min_area              : {cats['nho']} ({cats['nho'] / max(miss, 1):.0%})")
print(f"  mặt nạ màu gần như trống trong ô     : {cats['mau']} ({cats['mau'] / max(miss, 1):.0%})")
print(f"  mặt nạ có nhưng mất ở open/close,")
print(f"  contour hoặc lọc tỉ lệ               : {cats['khac']} ({cats['khac'] / max(miss, 1):.0%})")
if white:
    print(f"Nhóm 'mặt nạ trống': trung vị tỉ lệ pixel sáng nhưng S thấp (trắng) = {np.median(white):.1%}, "
          f"pixel sáng cam đạt S = {np.median(warm):.1%}")