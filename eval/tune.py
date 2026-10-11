"""Tìm tham số cho fire_detect trên tập VAL (không dùng test để chỉnh).

Dùng: python eval/tune.py --limit 500
In 10 cấu hình có box_f1 cao nhất. Muốn thêm tham số thì sửa GRID.
"""
import os
import sys
import argparse
import itertools

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from evaluate import evaluate_method
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA = os.path.join(ROOT, "data")
from traditional.fire_detect import detect

GRID = {
    "v_min": [200, 220, 240],
    "s_min": [40, 60, 80],
    "min_area": [0.002, 0.003, 0.005],
    "kernel": [5, 9],
}

if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--limit", type=int, default=500)
    args = ap.parse_args()

    keys, rows = list(GRID), []
    combos = list(itertools.product(*GRID.values()))
    for i, vals in enumerate(combos, 1):
        p = dict(zip(keys, vals))
        r = evaluate_method(lambda f, p=p: detect(f, p), os.path.join(DATA, "val"), limit=args.limit)
        rows.append((r["box_f1"], r["box_recall"], r["box_precision"], r["img_fpr"], p))
        print(f"[{i}/{len(combos)}] {p} -> F1={r['box_f1']:.3f}", flush=True)

    rows.sort(key=lambda x: -x[0])
    print("\nTop 10 (F1 | recall | precision | img_fpr | tham số)")
    for f1, rc, pr, fpr, p in rows[:10]:
        print(f"{f1:.3f} | {rc:.3f} | {pr:.3f} | {fpr:.3f} | {p}")
