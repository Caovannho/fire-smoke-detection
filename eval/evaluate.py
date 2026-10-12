"""Evaluation utilities for comparing detection methods (fire, class 1).

Dùng: python eval/evaluate.py --split val --limit 200
      python eval/evaluate.py --split test --noise --save eval/result_test.json --pr eval/pr_test.png
detector(frame): nhận ảnh BGR 640x480, trả về list (x, y, w, h, label, score).
Score (phần tử thứ 6) nên phản ánh độ tin cậy, nếu không đường PR/mAP chỉ còn là một điểm.
"""
import random
import os
import sys
import csv
import json
import time
import glob
import argparse
import cv2

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)

W, H = 640, 480
FIRE = 1  # class id trong nhãn YOLO (0 = smoke, 1 = fire)
EXTS = (".jpg", ".jpeg", ".png", ".bmp")


def _div(a, b):
    return a / b if b else 0.0


def compute_iou(box_a, box_b):
    """IoU của hai bbox (x, y, w, h)."""
    iw = max(0, min(box_a[0] + box_a[2], box_b[0] + box_b[2]) - max(box_a[0], box_b[0]))
    ih = max(0, min(box_a[1] + box_a[3], box_b[1] + box_b[3]) - max(box_a[1], box_b[1]))
    inter = iw * ih
    return _div(inter, box_a[2] * box_a[3] + box_b[2] * box_b[3] - inter)


def compute_precision_recall(tp, fp, fn):
    return _div(tp, tp + fp), _div(tp, tp + fn)


def compute_f1(precision, recall):
    return _div(2 * precision * recall, precision + recall)


def measure_fps(detector, frames, warmup=5):
    """FPS trung bình của riêng hàm detector, bỏ `warmup` frame đầu."""
    times = []
    for i, f in enumerate(frames):
        t = time.perf_counter()
        detector(f)
        if i >= warmup:
            times.append(time.perf_counter() - t)
    return _div(len(times), sum(times))


def load_gt(label_path):
    """Trả về (list bbox lửa theo pixel 640x480, tổng số dòng nhãn)."""
    boxes, n = [], 0
    if os.path.exists(label_path):
        for line in open(label_path):
            p = line.split()
            if len(p) != 5:
                continue
            n += 1
            if int(p[0]) == FIRE:
                xc, yc, w, h = map(float, p[1:])
                boxes.append(((xc - w / 2) * W, (yc - h / 2) * H, w * W, h * H))
    return boxes, n


def _flags(preds, gts, thr):
    """Ghép tham lam theo score giảm dần. Trả về [(score, is_tp), ...]."""
    used, out = set(), []
    for p in sorted(preds, key=lambda d: -d[5]):
        best, bi = 0.0, -1
        for i, g in enumerate(gts):
            if i not in used:
                v = compute_iou(p[:4], g)
                if v > best:
                    best, bi = v, i
        ok = bi >= 0 and best >= thr
        if ok:
            used.add(bi)
        out.append((p[5], ok))
    return out


def match(preds, gts, thr):
    """Trả về (TP, FP, FN) của một ảnh."""
    tp = sum(ok for _, ok in _flags(preds, gts, thr))
    return tp, len(preds) - tp, len(gts) - tp


def compute_pr(predictions, ground_truth, iou_thr=0.5):
    """Đường Precision-Recall. predictions/ground_truth: list theo từng ảnh."""
    recs = [x for pr, gt in zip(predictions, ground_truth) for x in _flags(pr, gt, iou_thr)]
    n_gt = sum(len(g) for g in ground_truth)
    recs.sort(key=lambda x: -x[0])
    tp = fp = 0
    precisions, recalls = [], []
    for _, ok in recs:
        tp, fp = tp + ok, fp + (not ok)
        precisions.append(_div(tp, tp + fp))
        recalls.append(_div(tp, n_gt))
    return precisions, recalls


def compute_ap(precisions, recalls):
    """AP = diện tích dưới đường PR (nội suy mọi điểm, kiểu VOC)."""
    mp, mr = [0.0] + list(precisions) + [0.0], [0.0] + list(recalls) + [1.0]
    for i in range(len(mp) - 2, -1, -1):
        mp[i] = max(mp[i], mp[i + 1])
    return sum((mr[i] - mr[i - 1]) * mp[i] for i in range(1, len(mr)))


def compute_map(predictions, ground_truth, iou_thrs=(0.3, 0.5)):
    """AP tại từng ngưỡng IoU và mAP (trung bình). Một class nên mAP = mean AP."""
    aps = {f"AP@{t}": compute_ap(*compute_pr(predictions, ground_truth, t)) for t in iou_thrs}
    aps["mAP"] = _div(sum(aps.values()), len(aps))
    return aps


def plot_pr_curve(precisions, recalls, output_path=None, title="Precision-Recall (fire)"):
    """Vẽ đường PR. Có output_path thì lưu ảnh, không thì hiện cửa sổ."""
    import matplotlib
    if output_path:
        matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    plt.figure(figsize=(5, 4))
    plt.plot(recalls, precisions)
    plt.xlim(0, 1.02)
    plt.ylim(0, 1.02)
    plt.xlabel("Recall")
    plt.ylabel("Precision")
    plt.title(title)
    plt.grid(alpha=0.3)
    plt.tight_layout()
    if output_path:
        plt.savefig(output_path, dpi=150)
        plt.close()
    else:
        plt.show()


def evaluate_method(detector, dataset_path="data/test", iou_thr=0.3, limit=None, warmup=5, raw=None):
    """Đánh giá detector trên dataset_path (thư mục có images/ và labels/).
    raw: dict rỗng, nếu truyền vào sẽ được điền predictions/ground_truth để vẽ đường PR."""
    if not os.path.isabs(dataset_path):
        dataset_path = os.path.join(ROOT, dataset_path)
    img_dir = os.path.join(dataset_path, "images")
    lbl_dir = os.path.join(dataset_path, "labels")
    files = sorted(f for f in glob.glob(os.path.join(img_dir, "*")) if f.lower().endswith(EXTS))
    if limit and limit < len(files):
        files = sorted(random.Random(0).sample(files, limit))
    tp = fp = fn = 0                  # mức bounding box
    itp = ifp = ifn = itn = 0         # mức ảnh
    none_n = none_fp = 0              # riêng ảnh "None" (nhãn rỗng)
    times = []
    all_preds, all_gts = [], []

    for i, f in enumerate(files):
        img = cv2.imread(f)
        if img is None:
            continue
        img = cv2.resize(img, (W, H))

        t = time.perf_counter()
        dets = detector(img)
        if i >= warmup:
            times.append(time.perf_counter() - t)

        preds = [d for d in dets if d[4] == "fire"]
        name = os.path.splitext(os.path.basename(f))[0] + ".txt"
        gts, n_lines = load_gt(os.path.join(lbl_dir, name))

        all_preds.append(preds)
        all_gts.append(gts)
        a, b, c = match(preds, gts, iou_thr)
        tp, fp, fn = tp + a, fp + b, fn + c

        has_gt, has_pred = bool(gts), bool(preds)
        itp += has_gt and has_pred
        ifn += has_gt and not has_pred
        ifp += (not has_gt) and has_pred
        itn += (not has_gt) and not has_pred
        if n_lines == 0:
            none_n += 1
            none_fp += has_pred

    p, r = compute_precision_recall(tp, fp, fn)
    if raw is not None:
        raw.update(predictions=all_preds, ground_truth=all_gts)
    res = {
        "n_images": len(files),
        "box_precision": p,
        "box_recall": r,
        "box_f1": compute_f1(p, r),
        "img_precision": _div(itp, itp + ifp),
        "img_recall": _div(itp, itp + ifn),
        "img_fpr": _div(ifp, ifp + itn),      # mọi ảnh không có lửa (gồm ảnh chỉ có khói)
        "none_fpr": _div(none_fp, none_n),    # chỉ ảnh "None"
        "fps": _div(len(times), sum(times)),
    }
    res.update(compute_map(all_preds, all_gts))
    return res


def evaluate_noise(detector, noise_dir=None):
    """Số ảnh nhiễu bị báo cháy sai, tính riêng từng thư mục con của data/noise."""
    noise_dir = noise_dir or os.path.join(ROOT, "data", "noise")
    if not os.path.isdir(noise_dir):
        return {}
    subs = [os.path.join(noise_dir, s) for s in sorted(os.listdir(noise_dir))
            if os.path.isdir(os.path.join(noise_dir, s))] or [noise_dir]
    out = {}
    for d in subs:
        files = [f for f in glob.glob(os.path.join(d, "*")) if f.lower().endswith(EXTS)]
        flagged = 0
        for f in files:
            img = cv2.imread(f)
            if img is not None:
                flagged += any(x[4] == "fire" for x in detector(cv2.resize(img, (W, H))))
        out[os.path.basename(d)] = (flagged, len(files))
    return out


def save_report(metrics, output_path):
    """Lưu metrics ra .json hoặc .csv (theo đuôi file)."""
    if output_path.lower().endswith(".json"):
        json.dump(metrics, open(output_path, "w", encoding="utf-8"), indent=2, ensure_ascii=False)
    else:
        with open(output_path, "w", newline="", encoding="utf-8") as f:
            w = csv.writer(f)
            w.writerow(["metric", "value"])
            w.writerows(metrics.items())


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--split", default="val", choices=["train", "val", "test"])
    ap.add_argument("--iou", type=float, default=0.3)
    ap.add_argument("--limit", type=int, default=None)
    ap.add_argument("--noise", action="store_true")
    ap.add_argument("--save", default=None, help="đường dẫn .json hoặc .csv")
    ap.add_argument("--pr", default=None, help="lưu đường PR ra file .png (tại --iou)")
    args = ap.parse_args()

    from traditional.fire_detect import detect

    raw = {}
    res = evaluate_method(detect, os.path.join("data", args.split), args.iou, args.limit, raw=raw)
    for k, v in res.items():
        print(f"{k:15s} {v:.4f}" if isinstance(v, float) else f"{k:15s} {v}")
    if args.save:
        save_report(res, args.save)
    if args.pr:
        plot_pr_curve(*compute_pr(raw["predictions"], raw["ground_truth"], args.iou), args.pr)
    if args.noise:
        for name, (fl, n) in evaluate_noise(detect).items():
            print(f"noise/{name}: {fl}/{n} ảnh báo cháy sai (FPR={_div(fl, n):.2f})")