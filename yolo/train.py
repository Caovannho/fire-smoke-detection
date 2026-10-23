"""
Training and fine-tuning script for YOLOv8 on the Fire & Smoke dataset.

Supports:
- Baseline training (yolov8n.pt, yolov8s.pt)
- Custom hyperparameter tuning & data augmentation
- Automated checkpoint saving to yolo/weights/best.pt
- 3 Pre-set experiment configurations for comparison (STT 3)

Usage Examples:
    # 1. Train baseline YOLOv8n on GPU
    python yolo/train.py --model yolov8n.pt --epochs 50 --batch 16 --name exp_yolov8n_baseline

    # 2. Train YOLOv8s (deeper model)
    python yolo/train.py --model yolov8s.pt --epochs 50 --batch 8 --name exp_yolov8s

    # 3. Train with configuration presets
    python yolo/train.py --config-preset 1   # Config 1: YOLOv8n standard
    python yolo/train.py --config-preset 2   # Config 2: YOLOv8s deeper architecture
    python yolo/train.py --config-preset 3   # Config 3: YOLOv8n + tuned augmentation (anti-false alarm)
"""

import os
import sys
import shutil
import argparse
from pathlib import Path
import torch

ROOT_DIR = Path(__file__).resolve().parent.parent
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))


def get_default_device() -> str:
    """Return '0' if NVIDIA GPU with CUDA is available, else 'cpu'."""
    if torch.cuda.is_available():
        gpu_name = torch.cuda.get_device_name(0)
        print(f"[train.py] Phát hiện GPU: {gpu_name} -> Sử dụng device='0'")
        return "0"
    print("[train.py] Không tìm thấy CUDA GPU -> Sử dụng CPU")
    return "cpu"


def train_yolo(
    model_name: str = "yolov8n.pt",
    data_yaml: str = "data.yaml",
    epochs: int = 50,
    batch: int = 16,
    imgsz: int = 640,
    device: str = "0",
    lr0: float = 0.01,
    hsv_h: float = 0.015,
    hsv_s: float = 0.7,
    hsv_v: float = 0.4,
    mosaic: float = 1.0,
    project: str = "runs/train",
    name: str = "exp",
    copy_to_weights: bool = True
):
    """
    Execute YOLO fine-tuning with Ultralytics API.
    """
    from ultralytics import YOLO

    data_path = ROOT_DIR / data_yaml
    if not data_path.exists():
        raise FileNotFoundError(
            f"Không tìm thấy file cấu hình dataset: {data_path}\n"
            f"Vui lòng đảm bảo data.yaml nằm ở thư mục gốc của project."
        )

    print(f"\n{'='*70}")
    print(f"🚀 BẮT ĐẦU HUẤN LUYỆN YOLOv8: {name}")
    print(f"- Base Model  : {model_name}")
    print(f"- Dataset     : {data_path}")
    print(f"- Epochs      : {epochs} | Batch: {batch} | ImgSz: {imgsz}")
    print(f"- Device      : {device}")
    print(f"- Initial LR  : {lr0}")
    print(f"{'='*70}\n")

    # Load base model
    model = YOLO(model_name)

    # Train model
    results = model.train(
        data=str(data_path),
        epochs=epochs,
        batch=batch,
        imgsz=imgsz,
        device=device,
        project=project,
        name=name,
        lr0=lr0,
        hsv_h=hsv_h,
        hsv_s=hsv_s,
        hsv_v=hsv_v,
        mosaic=mosaic,
        plots=True,
        save=True,
        exist_ok=True,
        workers=2
    )

    # Locate best.pt
    run_dir = ROOT_DIR / project / name
    best_weights = run_dir / "weights" / "best.pt"

    print(f"\n{'='*70}")
    print(f"✅ HOÀN THÀNH HUẤN LUYỆN: {name}")
    print(f"- Kết quả lưu tại: {run_dir}")
    print(f"- File weights tốt nhất: {best_weights}")
    print(f"{'='*70}\n")

    # Copy best weights to project target directory
    if copy_to_weights and best_weights.exists():
        dest_dir = ROOT_DIR / "yolo" / "weights"
        dest_dir.mkdir(parents=True, exist_ok=True)

        target_file = dest_dir / "best.pt"
        backup_named_file = dest_dir / f"{name}_best.pt"

        shutil.copy2(best_weights, target_file)
        shutil.copy2(best_weights, backup_named_file)
        print(f"[train.py] Đã sao chép best weights tới:")
        print(f"  -> {target_file} (dùng cho pipeline mặc định)")
        print(f"  -> {backup_named_file}")

    return results


def run_preset(preset_num: int, epochs: int, device: str):
    """
    Run predefined experiment configurations for STT 3 comparison.
    """
    if preset_num == 1:
        # Cấu hình 1: YOLOv8n chuẩn (nhẹ, nhanh, phù hợp nhúng/realtime)
        print("📌 Chạy Cấu hình 1: YOLOv8n Baseline (Chuẩn)")
        train_yolo(
            model_name="yolov8n.pt",
            epochs=epochs,
            batch=16,
            imgsz=640,
            device=device,
            lr0=0.01,
            name="exp1_yolov8n_baseline"
        )
    elif preset_num == 2:
        # Cấu hình 2: YOLOv8s (mô hình sâu hơn, tăng độ chính xác)
        print("📌 Chạy Cấu hình 2: YOLOv8s Kiến trúc sâu hơn (Higher Accuracy)")
        train_yolo(
            model_name="yolov8s.pt",
            epochs=epochs,
            batch=8,     # Giảm batch vì model lớn hơn trên GPU 4GB VRAM
            imgsz=640,
            device=device,
            lr0=0.01,
            name="exp2_yolov8s_deeper"
        )
    elif preset_num == 3:
        # Cấu hình 3: YOLOv8n + Data Augmentation tinh chỉnh (chống báo động giả)
        print("📌 Chạy Cấu hình 3: YOLOv8n + Tinh chỉnh Augmentation (Anti-False-Alarm)")
        train_yolo(
            model_name="yolov8n.pt",
            epochs=epochs,
            batch=16,
            imgsz=640,
            device=device,
            lr0=0.005,   # lr nhỏ hơn giúp hội tụ ổn định
            hsv_s=0.8,   # Tăng biến thiên saturation để phân biệt lửa và đèn vàng/áo đỏ
            hsv_v=0.5,   # Tăng biến thiên brightness để nhận diện trong các điều kiện sáng khác nhau
            mosaic=1.0,
            name="exp3_yolov8n_augmented"
        )
    else:
        raise ValueError(f"Unknown preset number: {preset_num}. Chọn 1, 2, hoặc 3.")


def main():
    parser = argparse.ArgumentParser(description="YOLOv8 Training for Fire & Smoke Detection")
    parser.add_argument("--model", type=str, default="yolov8n.pt", help="Base weights: yolov8n.pt, yolov8s.pt")
    parser.add_argument("--data", type=str, default="data.yaml", help="Path to data.yaml")
    parser.add_argument("--epochs", type=int, default=50, help="Number of epochs (mặc định: 50)")
    parser.add_argument("--batch", type=int, default=16, help="Batch size (mặc định: 16)")
    parser.add_argument("--imgsz", type=int, default=640, help="Image size (mặc định: 640)")
    parser.add_argument("--device", type=str, default=None, help="Device: '0' for GPU or 'cpu'")
    parser.add_argument("--lr0", type=float, default=0.01, help="Initial learning rate")
    parser.add_argument("--project", type=str, default="runs/train", help="Run save directory")
    parser.add_argument("--name", type=str, default="exp_yolov8", help="Experiment name")
    parser.add_argument("--config-preset", type=int, choices=[1, 2, 3], default=None,
                        help="Chạy 1 trong 3 cấu hình so sánh chuẩn (1: yolov8n, 2: yolov8s, 3: augmented)")

    args = parser.parse_args()

    device = args.device if args.device is not None else get_default_device()

    if args.config_preset:
        run_preset(args.config_preset, args.epochs, device)
    else:
        train_yolo(
            model_name=args.model,
            data_yaml=args.data,
            epochs=args.epochs,
            batch=args.batch,
            imgsz=args.imgsz,
            device=device,
            lr0=args.lr0,
            project=args.project,
            name=args.name
        )


if __name__ == "__main__":
    main()
