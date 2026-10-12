"""Khảo sát màu lửa trên tập train: histogram HSV/YCrCb, ngưỡng theo phân vị, so với nền.

Dùng: python traditional/color_survey.py --n 1500 --lo 5 --hi 95
Ra: ảnh histogram (mặc định report/color_hist.png) + bảng ngưỡng in ra terminal.
Lưu ý OpenCV: H trong 0-179, kênh YCrCb theo thứ tự Y, Cr, Cb.
"""
import os
import glob
import argparse
import cv2
import numpy as np

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
W, H = 640, 480
FIRE = 1  # class id: 0 = smoke, 1 = fire
EXTS = (".jpg", ".jpeg", ".png", ".bmp")
CH = ["H", "S", "V", "Y", "Cr", "Cb"]
RULES = (("HSV", [0, 1, 2]), ("YCrCb", [3, 4, 5]), ("HSV&YCrCb", list(range(6))), ("H+V", [0, 2]), ("H+V+Cr+Cb", [0, 2, 4, 5]))


def read_boxes(path):
    """Trả về [(class, x1, y1, x2, y2)] theo pixel 640x480."""
    out = []
    if os.path.exists(path):
        for line in open(path):
            p = line.split()
            if len(p) == 5:
                xc, yc, w, h = map(float, p[1:])
                x1, y1 = int(max(0, (xc - w / 2) * W)), int(max(0, (yc - h / 2) * H))
                x2, y2 = int(min(W, (xc + w / 2) * W)), int(min(H, (yc + h / 2) * H))
                if x2 > x1 and y2 > y1:
                    out.append((int(p[0]), x1, y1, x2, y2))
    return out


def feats(img):
    """Ảnh BGR -> mảng HxWx6 (H, S, V, Y, Cr, Cb)."""
    return np.concatenate([cv2.cvtColor(img, cv2.COLOR_BGR2HSV),
                           cv2.cvtColor(img, cv2.COLOR_BGR2YCrCb)], axis=2)


def sample(px, k, rng):
    return px[rng.choice(len(px), k, replace=False)] if len(px) > k else px


def collect(split_dir, n_images, k, rng):
    files = sorted(f for f in glob.glob(os.path.join(split_dir, "images", "*")) if f.lower().endswith(EXTS))
    rng.shuffle(files)
    fire, bg, used = [], [], 0
    for f in files:
        if used >= n_images:
            break
        boxes = read_boxes(os.path.join(split_dir, "labels", os.path.splitext(os.path.basename(f))[0] + ".txt"))
        if not any(b[0] == FIRE for b in boxes):
            continue
        img = cv2.imread(f)
        if img is None:
            continue
        ft = feats(cv2.resize(img, (W, H)))
        fire_m = np.zeros((H, W), bool)   # vùng lửa
        any_m = np.zeros((H, W), bool)    # vùng có nhãn (lửa hoặc khói)
        for c, x1, y1, x2, y2 in boxes:
            any_m[y1:y2, x1:x2] = True
            if c == FIRE:
                fire_m[y1:y2, x1:x2] = True
        fire.append(sample(ft[fire_m], k, rng))
        bg.append(sample(ft[~any_m], k, rng))
        used += 1
    if not fire:
        raise SystemExit(f"Không có ảnh lửa nào trong {split_dir} (tìm thấy {len(files)} ảnh). "
                         "Kiểm tra thư mục images/labels và nhãn class 1.")
    return np.concatenate(fire), np.concatenate(bg), used


def in_range(px, lo, hi, ch):
    return ((px[:, ch] >= lo[ch]) & (px[:, ch] <= hi[ch])).all(axis=1)


def thresholds(fire, lo_p, hi_p, hmax=None):
    """Ngưỡng theo phân vị; hmax (nếu có) ép H về 0..hmax để bỏ đoạn đỏ vòng ở H~170-179."""
    lo, hi = np.percentile(fire, lo_p, axis=0), np.percentile(fire, hi_p, axis=0)
    if hmax is not None:
        lo[0], hi[0] = 0, hmax
    return lo, hi


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--data", default=os.environ.get("FIRE_DATA", os.path.join(ROOT, "data")), help="thư mục chứa train/val/test")
    ap.add_argument("--split", default="train")
    ap.add_argument("--n", type=int, default=1500, help="số ảnh có lửa lấy mẫu")
    ap.add_argument("--k", type=int, default=300, help="số pixel tối đa mỗi vùng/ảnh")
    ap.add_argument("--lo", type=float, default=5)
    ap.add_argument("--hi", type=float, default=95)
    ap.add_argument("--hmax", type=int, default=None, help="ép H trong 0..hmax (vd 35)")
    ap.add_argument("--sweep", action="store_true", help="in bảng so sánh nhiều mức phân vị")
    ap.add_argument("--out", default=os.path.join(ROOT, "report", "color_hist.png"))
    args = ap.parse_args()

    rng = np.random.default_rng(0)
    fire, bg, used = collect(os.path.join(args.data, args.split), args.n, args.k, rng)
    print(f"{used} ảnh | {len(fire)} pixel lửa | {len(bg)} pixel nền")

    lo, hi = thresholds(fire, args.lo, args.hi, args.hmax)
    print(f"\nNgưỡng lửa (phân vị {args.lo:g}-{args.hi:g}" + (f", H ép 0..{args.hmax}" if args.hmax is not None else "") + "):")
    for i, c in enumerate(CH):
        print(f"  {c:3s} {lo[i]:6.1f} .. {hi[i]:6.1f}")

    print("\nQuy tắc            % pixel lửa giữ lại   % pixel nền lọt vào (FPR pixel)")
    for name, ch in RULES:
        print(f"  {name:14s}  {100 * in_range(fire, lo, hi, ch).mean():8.1f}  {100 * in_range(bg, lo, hi, ch).mean():20.1f}")

    if args.sweep:
        print("\nSweep phân vị, mỗi ô là: % lửa giữ lại / % nền lọt vào")
        print(f"  {'lo-hi':8s}" + "".join(f"{n:>15s}" for n, _ in RULES))
        for p in (5, 10, 15, 20, 25):
            l, h = thresholds(fire, p, 100 - p, args.hmax)
            cells = [f"{100 * in_range(fire, l, h, ch).mean():5.1f} / {100 * in_range(bg, l, h, ch).mean():5.1f}" for _, ch in RULES]
            print(f"  {p:2d}-{100 - p:<5d}" + "".join(f"{c:>15s}" for c in cells))

    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    fig, axs = plt.subplots(2, 3, figsize=(12, 6))
    for i, (ax, c) in enumerate(zip(axs.ravel(), CH)):
        top = 180 if c == "H" else 256
        ax.hist(fire[:, i], bins=top, range=(0, top), density=True, alpha=0.6, color="orangered", label="lửa")
        ax.hist(bg[:, i], bins=top, range=(0, top), density=True, alpha=0.5, color="gray", label="nền")
        ax.axvline(lo[i], color="k", ls="--", lw=1)
        ax.axvline(hi[i], color="k", ls="--", lw=1)
        ax.set_title(c)
    axs[0, 0].legend()
    fig.suptitle(f"Phân bố màu: lửa vs nền (nét đứt = phân vị {args.lo:g}/{args.hi:g} của lửa)")
    fig.tight_layout()
    os.makedirs(os.path.dirname(args.out), exist_ok=True)
    fig.savefig(args.out, dpi=150)
    print(f"\nĐã lưu histogram: {args.out}")


if __name__ == "__main__":
    main()
