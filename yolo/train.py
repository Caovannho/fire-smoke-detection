"""
Training script for YOLOv8 fine-tuning on the fire/smoke dataset.

Workflow:
    1. Load a pre-trained YOLOv8 base model (e.g. yolov8n.pt, yolov8s.pt)
    2. Configure dataset via a YAML descriptor pointing to data/fire & data/smoke
    3. Set hyperparameters (epochs, batch size, image size, learning rate, etc.)
    4. Launch training with Ultralytics train() API
    5. Export the best checkpoint to yolo/weights/best.pt

Usage (planned):
    python yolo/train.py --base yolov8n.pt --data dataset.yaml --epochs 50

Arguments planned:
    --base      Base YOLO weights to fine-tune (default: yolov8n.pt)
    --data      Path to dataset YAML file        (default: dataset.yaml)
    --epochs    Number of training epochs        (default: 50)
    --batch     Batch size                       (default: 16)
    --imgsz     Input image size                 (default: 640)
    --device    Training device: 0 (GPU) / cpu   (default: 0)
    --project   Output directory for runs        (default: runs/train)

Outputs:
    runs/train/exp/weights/best.pt   – Best checkpoint (copy to yolo/weights/)
    runs/train/exp/results.csv       – Per-epoch loss and metric logs
    runs/train/exp/confusion_matrix.png
"""

# TODO: TV4 implement

