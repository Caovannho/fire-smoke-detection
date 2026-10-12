"""Ablation tiền xử lý trên cả tập val. Dùng: python eval/ablation_pre.py"""
import os
import sys
import csv
import argparse

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from evaluate import evaluate_method, ROOT
from traditional.fire_detect import detect

CONFIGS = [
    ("Không tiền xử lý",             dict(blur=0, median=0, clahe=0)),
    ("Gaussian 3",                   dict(blur=3, median=0, clahe=0)),
    ("Gaussian 5",                   dict(blur=5, median=0, clahe=0)),
    ("Median 5",                     dict(blur=0, median=5, clahe=0)),
    ("Gaussian 3 + Median 5",        dict(blur=3, median=5, clahe=0)),
    ("CLAHE 2.0",                    dict(blur=0, median=0, clahe=2.0)),
    ("Gaussian 3 + Median 5 + CLAHE", dict(blur=3, median=5, clahe=2.0)),
]

ap = argparse.ArgumentParser()
ap.add_argument("--limit", type=int, default=None)
args = ap.parse_args()

rows = []
print(f"{'Cấu hình':32s} {'F1':>6s} {'Prec':>6s} {'Rec':>6s} {'FPR_ảnh':>8s} {'FPS':>7s}")
for name, p in CONFIGS:
    r = evaluate_method(lambda f, p=p: detect(f, p), os.path.join("data", "val"), limit=args.limit)
    rows.append([name, r["box_f1"], r["box_precision"], r["box_recall"], r["img_fpr"], r["fps"]])
    print(f"{name:32s} {r['box_f1']:6.3f} {r['box_precision']:6.3f} {r['box_recall']:6.3f} "
          f"{r['img_fpr']:8.3f} {r['fps']:7.0f}", flush=True)

out = os.path.join(ROOT, "eval", "ablation_pre.csv")
with open(out, "w", newline="", encoding="utf-8") as f:
    w = csv.writer(f)
    w.writerow(["config", "box_f1", "box_precision", "box_recall", "img_fpr", "fps"])
    w.writerows(rows)
print("Đã lưu", out)