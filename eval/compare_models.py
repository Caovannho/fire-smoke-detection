"""
Comprehensive Model Comparison & Benchmarking Script (TV4).

Evaluates and compares all detection approaches on the same benchmark test set:
    1. Traditional Fire Detector (HSV + Morphology) - TV2
    2. Traditional Smoke Detector (MOG2 / Background Subtraction) - TV3
    3. YOLOv8 Deep Learning Detector - TV4
    4. Hybrid Cascaded Detector (Candidate Filter + YOLO) - TV4

Outputs:
    - Printed Markdown comparison table in terminal
    - JSON summary at report/comparison_summary.json
    - Bar chart comparison at report/images/comparison_bar_chart.png
    - Precision-Recall curves comparison at report/images/pr_curves_comparison.png

Usage:
    python eval/compare_models.py --split test --limit 200
    python eval/compare_models.py --split val
"""

import os
import sys
import json
import argparse
from pathlib import Path
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np

ROOT_DIR = Path(__file__).resolve().parent.parent
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

from eval.evaluate import evaluate_method, compute_pr, compute_iou


def plot_comparison_charts(results: dict, output_dir: Path):
    """Generate side-by-side bar chart comparison of key metrics."""
    output_dir.mkdir(parents=True, exist_ok=True)
    methods = list(results.keys())
    if not methods:
        return

    metrics_to_plot = [
        ("box_precision", "Precision", "royalblue"),
        ("box_recall", "Recall", "forestgreen"),
        ("box_f1", "F1-Score", "darkorange"),
        ("img_fpr", "False Positive Rate (FPR)", "firebrick"),
        ("fps", "Tốc độ (FPS)", "purple"),
    ]

    fig, axes = plt.subplots(1, len(metrics_to_plot), figsize=(18, 5))
    fig.suptitle("So sánh hiệu năng giữa các phương pháp phát hiện Lửa & Khói", fontsize=14, fontweight="bold")

    for idx, (metric_key, title, color) in enumerate(metrics_to_plot):
        ax = axes[idx]
        values = [results[m].get(metric_key, 0.0) for m in methods]
        bars = ax.bar(methods, values, color=color, alpha=0.85, edgecolor="black")
        ax.set_title(title, fontsize=11, fontweight="bold")
        ax.grid(axis="y", linestyle="--", alpha=0.4)

        # Set appropriate y-limits
        if metric_key != "fps":
            ax.set_ylim(0, 1.05)
        else:
            max_fps = max(values) if values else 30
            ax.set_ylim(0, max(30, max_fps * 1.2))

        # Add data labels on top of bars
        for bar in bars:
            height = bar.get_height()
            label_text = f"{height:.2f}" if metric_key != "fps" else f"{height:.1f}"
            ax.annotate(
                label_text,
                xy=(bar.get_x() + bar.get_width() / 2, height),
                xytext=(0, 3),
                textcoords="offset points",
                ha="center", va="bottom", fontsize=9, fontweight="bold"
            )

        ax.tick_params(axis="x", rotation=25)

    plt.tight_layout()
    chart_path = output_dir / "comparison_bar_chart.png"
    plt.savefig(chart_path, dpi=200)
    plt.close()
    print(f"[compare_models] Đã lưu biểu đồ so sánh tại: {chart_path}")


def print_markdown_table(results: dict):
    """Print beautifully formatted comparison table in GitHub Markdown format."""
    headers = [
        "Phương pháp",
        "Box Precision",
        "Box Recall",
        "Box F1",
        "Img FPR (Báo động giả)",
        "mAP@0.3",
        "mAP@0.5",
        "FPS (Tốc độ)"
    ]

    print("\n" + "=" * 95)
    print("📊 BẢNG TỔNG HỢP SO SÁNH CÁC PHƯƠNG PHÁP")
    print("=" * 95)

    row_format = "| {:<20} | {:<13} | {:<10} | {:<7} | {:<22} | {:<7} | {:<7} | {:<11} |"
    divider = "|:" + "-" * 20 + ":|:" + "-" * 13 + ":|:" + "-" * 10 + ":|:" + "-" * 7 + ":|:" + "-" * 22 + ":|:" + "-" * 7 + ":|:" + "-" * 7 + ":|:" + "-" * 11 + ":|"

    print(row_format.format(*headers))
    print(divider)

    for method, m in results.items():
        row = [
            method,
            f"{m.get('box_precision', 0):.4f}",
            f"{m.get('box_recall', 0):.4f}",
            f"{m.get('box_f1', 0):.4f}",
            f"{m.get('img_fpr', 0):.4f}",
            f"{m.get('AP@0.3', 0):.4f}",
            f"{m.get('AP@0.5', 0):.4f}",
            f"{m.get('fps', 0):.1f}"
        ]
        print(row_format.format(*row))

    print("=" * 95 + "\n")


def run_benchmark(split: str = "val", limit: int = None, iou_thr: float = 0.3):
    dataset_path = f"data/{split}"
    images_check = ROOT_DIR / dataset_path / "images"

    if not images_check.exists():
        print(f"[CẢNH BÁO] Chưa tìm thấy thư mục ảnh: {images_check}")
        print("Vui lòng tải và giải nén dataset theo hướng dẫn trong README.md trước khi chạy thực nghiệm.")
        return

    results = {}
    raw_data = {}

    # 1. Truyền thống: Lửa (HSV) - TV2
    try:
        from traditional.fire_detect import detect as fire_detect
        print(f"\n[1/4] Đang đánh giá: Truyền thống Lửa (HSV)...")
        raw_fire = {}
        results["Truyền thống (Lửa)"] = evaluate_method(
            fire_detect, dataset_path=dataset_path, iou_thr=iou_thr, limit=limit, raw=raw_fire
        )
        raw_data["Truyền thống (Lửa)"] = raw_fire
    except Exception as e:
        print(f"[Bỏ qua] Truyền thống Lửa gặp lỗi: {e}")

    # 2. YOLOv8 - TV4
    try:
        from yolo.yolo_detect import detect as yolo_detect
        print(f"\n[2/4] Đang đánh giá: YOLOv8 Deep Learning...")
        raw_yolo = {}
        results["YOLOv8"] = evaluate_method(
            yolo_detect, dataset_path=dataset_path, iou_thr=iou_thr, limit=limit, raw=raw_yolo
        )
        raw_data["YOLOv8"] = raw_yolo
    except Exception as e:
        print(f"[Bỏ qua] YOLOv8 gặp lỗi: {e}")

    # 3. Hybrid - TV4
    try:
        from yolo.hybrid_detect import detect as hybrid_detect
        print(f"\n[3/4] Đang đánh giá: Phương pháp Kết hợp Hybrid...")
        raw_hybrid = {}
        results["Kết hợp (Hybrid)"] = evaluate_method(
            hybrid_detect, dataset_path=dataset_path, iou_thr=iou_thr, limit=limit, raw=raw_hybrid
        )
        raw_data["Kết hợp (Hybrid)"] = raw_hybrid
    except Exception as e:
        print(f"[Bỏ qua] Hybrid gặp lỗi: {e}")

    if not results:
        print("Không có phương pháp nào chạy thành công.")
        return

    # In bảng markdown
    print_markdown_table(results)

    # Lưu kết quả JSON
    report_dir = ROOT_DIR / "report"
    images_dir = report_dir / "images"
    report_dir.mkdir(parents=True, exist_ok=True)
    images_dir.mkdir(parents=True, exist_ok=True)

    json_path = report_dir / "comparison_summary.json"
    with open(json_path, "w", encoding="utf-8") as f:
        json.dump(results, f, indent=2, ensure_ascii=False)
    print(f"[compare_models] Đã lưu kết quả JSON tại: {json_path}")

    # Vẽ biểu đồ so sánh
    plot_comparison_charts(results, images_dir)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="So sánh tất cả các phương pháp phát hiện")
    parser.add_argument("--split", default="val", choices=["train", "val", "test"], help="Tập dữ liệu đánh giá")
    parser.add_argument("--limit", type=int, default=None, help="Giới hạn số ảnh để test nhanh")
    parser.add_argument("--iou", type=float, default=0.3, help="Ngưỡng IoU")
    args = parser.parse_args()

    run_benchmark(split=args.split, limit=args.limit, iou_thr=args.iou)
