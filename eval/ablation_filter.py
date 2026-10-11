"""Ablation từng bước lọc, thêm dần. Dùng: python eval/ablation_filter.py [--limit 800]"""
import os
import sys
import csv
import argparse

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from evaluate import evaluate_method, ROOT
from traditional.fire_detect import detect

OFF = dict(open_k=1, close_k=1, min_area=0.0, max_area=1.0, min_ratio=0.0, max_ratio=1e9)
STEPS = [
    ("Chỉ mặt nạ màu (có lõi trắng)", dict(OFF)),
    ("+ close 5x5",                   dict(OFF, close_k=5)),
    ("+ open 5x5",                    dict(OFF, close_k=5, open_k=5)),
    ("+ lọc diện tích tối thiểu",     dict(OFF, close_k=5, open_k=5, min_area=0.002)),
    ("+ lọc diện tích tối đa",        dict(OFF, close_k=5, open_k=5, min_area=0.002, max_area=0.8)),
    ("+ lọc tỉ lệ rộng/cao (hiện tại)", dict(close_k=5, open_k=5, min_area=0.002, max_area=0.8, min_ratio=0.25, max_ratio=4.0)),
    ("Hiện tại, bỏ lõi trắng",        dict(white_v=0)),
]

ap = argparse.ArgumentParser()
ap.add_argument("--limit", type=int, default=None)
args = ap.parse_args()

rows = []
print(f"{'Bước':36s} {'F1':>6s} {'Prec':>6s} {'Rec':>6s} {'FPR_ảnh':>8s}")
for name, p in STEPS:
    r = evaluate_method(lambda f, p=p: detect(f, p), os.path.join("data", "val"), limit=args.limit)
    rows.append([name, r["box_f1"], r["box_precision"], r["box_recall"], r["img_fpr"]])
    print(f"{name:36s} {r['box_f1']:6.3f} {r['box_precision']:6.3f} {r['box_recall']:6.3f} {r['img_fpr']:8.3f}", flush=True)

out = os.path.join(ROOT, "eval", "ablation_filter.csv")
with open(out, "w", newline="", encoding="utf-8") as f:
    w = csv.writer(f)
    w.writerow(["step", "box_f1", "box_precision", "box_recall", "img_fpr"])
    w.writerows(rows)
print("Đã lưu", out)