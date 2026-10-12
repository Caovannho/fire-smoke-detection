"""Chẩn đoán vì sao box recall thấp."""
import os
import sys
import glob
import random
import argparse
import numpy as np
import cv2

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from evaluate import load_gt, compute_iou, W, H, EXTS, ROOT
from traditional.fire_detect import detect

BEST = dict(v_min=200, s_min=60, min_area=0.002, kernel=5)

ap = argparse.ArgumentParser()
ap.add_argument("--limit", type=int, default=800)
ap.add_argument("--save", type=int, default=12)
args = ap.parse_args()

img_dir = os.path.join(ROOT, "data", "val", "images")
lbl_dir = os.path.join(ROOT, "data", "val", "labels")
files = sorted(f for f in glob.glob(os.path.join(img_dir, "*")) if f.lower().endswith(EXTS))
if args.limit and args.limit < len(files):
    files = sorted(random.Random(0).sample(files, args.limit))

out_dir = os.path.join(ROOT, "data", "diag")   # data/ đã bị .gitignore chặn
os.makedirs(out_dir, exist_ok=True)

hit = part = miss = saved = 0
areas, ratios = [], []

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

    bad = False
    for g in gts:
        areas.append(g[2] * g[3] / (W * H))
        best, bp = 0.0, None
        for p in preds:
            v = compute_iou(p[:4], g)
            if v > best:
                best, bp = v, p
        if best >= 0.3:
            hit += 1
        elif best > 0:
            part += 1
            ratios.append(bp[2] * bp[3] / (g[2] * g[3]))
            bad = True
        else:
            miss += 1
            bad = True

    if bad and saved < args.save:
        vis = img.copy()
        for g in gts:
            cv2.rectangle(vis, (int(g[0]), int(g[1])), (int(g[0] + g[2]), int(g[1] + g[3])), (0, 255, 0), 2)
        for p in preds:
            cv2.rectangle(vis, (p[0], p[1]), (p[0] + p[2], p[1] + p[3]), (0, 0, 255), 2)
        cv2.imwrite(os.path.join(out_dir, name + ".jpg"), vis)
        saved += 1

n = hit + part + miss
print(f"Tổng ô lửa thật: {n}")
print(f"  khớp (IoU >= 0.3)        : {hit} ({hit / n:.1%})")
print(f"  chạm nhưng IoU < 0.3     : {part} ({part / n:.1%})")
print(f"  trượt hoàn toàn (IoU = 0): {miss} ({miss / n:.1%})")
a = np.array(areas)
print(f"Cỡ ô nhãn (tỉ lệ diện tích ảnh): trung vị {np.median(a):.4f}, "
      f"{(a < 0.002).mean():.0%} nhỏ hơn min_area, {(a < 0.01).mean():.0%} nhỏ hơn 1%")
if ratios:
    print(f"Với ô 'chạm': diện tích bbox dự đoán / ô nhãn, trung vị {np.median(ratios):.2f} "
          f"(dưới 1 là bbox nhỏ hơn nhãn, trên 1 là lớn hơn)")
print(f"Đã lưu {saved} ảnh lỗi vào {out_dir} (xanh = nhãn, đỏ = dự đoán)")