"""
YOLO inference wrapper for fire and smoke detection.

Uses the Ultralytics YOLO library to run object detection on individual
frames or video streams.

Shared Team Interface:
    detect(frame: np.ndarray) -> list[tuple[int, int, int, int, str, float]]
    Each tuple represents: (x, y, w, h, label, score)
    - x, y: Top-left coordinate in pixels
    - w, h: Width and height in pixels
    - label: "fire" or "smoke"
    - score: Confidence score in range [0.0, 1.0]
"""

import os
import sys
from typing import List, Tuple, Optional
import numpy as np

# Ensure root directory is in sys.path
ROOT_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if ROOT_DIR not in sys.path:
    sys.path.insert(0, ROOT_DIR)

try:
    import config
    DEFAULT_WEIGHTS = getattr(config, "YOLO_WEIGHTS", "yolo/weights/best.pt")
    DEFAULT_CONF = getattr(config, "CONF_THRESHOLD", 0.40)
    DEFAULT_IOU = getattr(config, "IOU_THRESHOLD", 0.45)
except ImportError:
    DEFAULT_WEIGHTS = "yolo/weights/best.pt"
    DEFAULT_CONF = 0.40
    DEFAULT_IOU = 0.45

# Class index to label string mapping (D-Fire dataset convention: 0=smoke, 1=fire)
CLASS_NAMES = {
    0: "smoke",
    1: "fire"
}


class YOLODetector:
    """
    Wrapper for YOLOv8 model inference on single frames or continuous video streams.
    """

    def __init__(
        self,
        weights_path: Optional[str] = None,
        conf_threshold: float = DEFAULT_CONF,
        iou_threshold: float = DEFAULT_IOU,
        device: Optional[str] = None
    ):
        """
        Initialize the YOLO detector.

        Parameters
        ----------
        weights_path : str, optional
            Path to .pt weights file. Defaults to config.YOLO_WEIGHTS or 'yolo/weights/best.pt'.
            If the custom weights file does not exist, falls back to 'yolov8n.pt'.
        conf_threshold : float
            Confidence threshold for filtering predictions.
        iou_threshold : float
            NMS IoU threshold.
        device : str, optional
            Computation device: 'cuda', 'cpu', or None (auto-detect).
        """
        self.conf = conf_threshold
        self.iou = iou_threshold
        self.device = device
        self.weights_path = weights_path or DEFAULT_WEIGHTS

        # Resolve path relative to project root if relative
        if not os.path.isabs(self.weights_path):
            self.weights_path = os.path.join(ROOT_DIR, self.weights_path)

        self.model = None
        self._load_model()

    def _load_model(self):
        """Load YOLO model via Ultralytics."""
        try:
            from ultralytics import YOLO
        except ImportError:
            raise ImportError(
                "Thư viện 'ultralytics' chưa được cài đặt! "
                "Vui lòng chạy: pip install ultralytics"
            )

        if os.path.exists(self.weights_path):
            print(f"[YOLODetector] Đang nạp weights từ: {self.weights_path}")
            self.model = YOLO(self.weights_path)
        else:
            fallback = "yolov8n.pt"
            print(
                f"[YOLODetector] [CẢNH BÁO] Không tìm thấy '{self.weights_path}'. "
                f"Tự động dùng model nền fallback: '{fallback}'"
            )
            self.model = YOLO(fallback)

    def detect(self, frame: np.ndarray) -> List[Tuple[int, int, int, int, str, float]]:
        """
        Detect fire and smoke in an input BGR image.

        Parameters
        ----------
        frame : np.ndarray
            BGR image of shape (H, W, 3).

        Returns
        -------
        list[tuple[int, int, int, int, str, float]]
            List of detected objects: (x, y, w, h, label, score)
        """
        if self.model is None or frame is None or frame.size == 0:
            return []

        # Run inference (verbose=False to avoid terminal clutter)
        results = self.model.predict(
            source=frame,
            conf=self.conf,
            iou=self.iou,
            device=self.device,
            verbose=False
        )

        detections = []
        if not results:
            return detections

        r = results[0]
        if r.boxes is None or len(r.boxes) == 0:
            return detections

        boxes = r.boxes.xyxy.cpu().numpy()      # [x1, y1, x2, y2]
        confs = r.boxes.conf.cpu().numpy()      # float score
        cls_ids = r.boxes.cls.cpu().numpy().astype(int)  # class index

        for box, score, cls_id in zip(boxes, confs, cls_ids):
            x1, y1, x2, y2 = box
            x = int(round(x1))
            y = int(round(y1))
            w = int(round(x2 - x1))
            h = int(round(y2 - y1))

            # Map class id to label string
            # Check model's built-in names first, fallback to CLASS_NAMES
            if hasattr(self.model, "names") and cls_id in self.model.names:
                model_label = str(self.model.names[cls_id]).lower()
                if "fire" in model_label:
                    label = "fire"
                elif "smoke" in model_label:
                    label = "smoke"
                else:
                    label = CLASS_NAMES.get(cls_id, model_label)
            else:
                label = CLASS_NAMES.get(cls_id, "fire" if cls_id == 1 else "smoke")

            detections.append((x, y, w, h, label, float(score)))

        return detections

    __call__ = detect


# ---------------------------------------------------------------------------
# Module-level singleton and default detect function for team pipeline
# ---------------------------------------------------------------------------
_default_detector: Optional[YOLODetector] = None


def get_detector() -> YOLODetector:
    """Lazy load singleton instance of YOLODetector."""
    global _default_detector
    if _default_detector is None:
        _default_detector = YOLODetector()
    return _default_detector


def detect(frame: np.ndarray) -> List[Tuple[int, int, int, int, str, float]]:
    """
    Standard interface function used by pipeline.py and eval/evaluate.py.

    Parameters
    ----------
    frame : np.ndarray
        BGR image frame (640x480).

    Returns
    -------
    list[tuple[int, int, int, int, str, float]]
        Detections: (x, y, w, h, label, score)
    """
    return get_detector().detect(frame)
