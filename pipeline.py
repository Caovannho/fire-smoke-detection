"""
End-to-end detection pipeline entry point.

Orchestrates the full workflow:
    1. Load configuration from config.py
    2. Initialize the chosen detector (Traditional, YOLO, or Combined)
    3. Open input source (webcam index or video file path)
    4. Process frames in a loop:
        a. Resize frame to (FRAME_WIDTH, FRAME_HEIGHT)
        b. Run detector → list of (x, y, w, h, label, score) tuples
        c. Draw bounding boxes and labels on frame
        d. Compute and display FPS every FPS_UPDATE_INTERVAL frames
        e. Show annotated frame in a named window
    5. Release resources on exit ('q' to quit)

Usage:
    python pipeline.py --source 0 --method combined
    python pipeline.py --source data/videos/test.mp4 --method yolo
    python pipeline.py --source 0 --method traditional
"""

import argparse
import time
import math
from pathlib import Path

import cv2
import numpy as np

import config

# ---------------------------------------------------------------------------
# Colour palette for bounding boxes
# ---------------------------------------------------------------------------
_BBOX_COLOR = {
    "fire":  (0, 0, 255),       # red   (BGR)
    "smoke": (128, 128, 128),   # grey  (BGR)
}
_DEFAULT_COLOR = (0, 255, 0)    # green fallback for unknown labels


# ---------------------------------------------------------------------------
# Detector loader
# ---------------------------------------------------------------------------

def filter_detections(detections, shape):
    """Validate the common contract and clip boxes, without changing thresholds."""
    height, width = shape[:2]
    result = []
    for det in detections:
        if len(det) != 6:
            raise ValueError("Detector phải trả (x, y, w, h, label, score).")
        x, y, w, h, label, score = det
        label = str(label).strip().lower()
        if label not in ("fire", "smoke"):
            raise ValueError(f"Nhãn detector không hợp lệ: {label!r}")
        if not all(math.isfinite(float(v)) for v in (x, y, w, h, score)):
            raise ValueError("Detector trả tọa độ hoặc score không hữu hạn.")
        if not 0 <= score <= 1:
            raise ValueError("Score detector phải nằm trong [0, 1].")
        x1, y1 = max(0, int(round(x))), max(0, int(round(y)))
        x2, y2 = min(width, int(round(x + w))), min(height, int(round(y + h)))
        if w > 0 and h > 0 and x2 > x1 and y2 > y1:
            result.append((x1, y1, x2-x1, y2-y1, label, float(score)))
    return result


def suppress_duplicates(detections, iou_threshold=config.IOU_THRESHOLD):
    """Class-aware NMS in input priority order; scores are never boosted."""
    kept = []
    for det in detections:
        x, y, w, h, label, _ = det
        duplicate = False
        for px, py, pw, ph, plabel, _ in kept:
            if label != plabel:
                continue
            intersection = max(0, min(x+w, px+pw)-max(x, px)) * max(
                0, min(y+h, py+ph)-max(y, py))
            union = w*h + pw*ph - intersection
            if union > 0 and intersection / union > iou_threshold:
                duplicate = True
                break
        if not duplicate:
            kept.append(det)
    return kept


def _load_checked_yolo():
    """Guard TV4's loader so its COCO fallback cannot be reached from TV1."""
    weights = Path(config.YOLO_WEIGHTS)
    if not weights.is_absolute():
        weights = Path(__file__).resolve().parent / weights
    if not weights.is_file() or weights.stat().st_size == 0:
        raise FileNotFoundError(f"Không tìm thấy model hợp lệ: {weights}")
    from yolo.yolo_detect import YOLODetector
    detector = YOLODetector(weights_path=str(weights))
    names = detector.model.names
    if isinstance(names, (list, tuple)):
        names = dict(enumerate(names))
    normalized = {int(k): str(v).strip().lower() for k, v in names.items()}
    if len(normalized) != 2 or set(normalized.values()) != {"fire", "smoke"}:
        raise ValueError(f"Model không phải mô hình fire/smoke: names={names!r}")
    print(f"[TV1] Weights: {weights}; model.names: {names}")
    return detector


def load_detector(method: str = "combined", *, image_mode: bool = False):
    """Create session-local detectors. Dependency/model errors propagate to the UI.

    Combined is a union, not Hybrid verification: YOLO boxes take priority over
    overlapping traditional boxes of the same class. Traditional heuristic scores
    are not calibrated probabilities; each backend retains its existing threshold.
    """
    if method not in ("traditional", "yolo", "combined", "hybrid"):
        raise ValueError(f"Phương pháp không hợp lệ: {method}")
    backends = []
    if method in ("yolo", "combined", "hybrid"):
        yolo = _load_checked_yolo()
        if method == "hybrid":
            from yolo.hybrid_detect import HybridDetector
            backends.append(HybridDetector(yolo_detector=yolo).detect)
        else:
            backends.append(yolo.detect)
    if method in ("traditional", "combined"):
        from traditional.fire_detect import FireDetector
        from traditional.smoke_detect import SmokeDetector
        fire = FireDetector()
        smoke = SmokeDetector(params={"use_bg_sub": not image_mode})
        backends.extend((fire.detect, smoke.detect))

    def detect(frame):
        results = []
        for backend in backends:
            # Sort within each backend only; never compare heuristic scores to YOLO.
            batch = filter_detections(backend(frame), frame.shape)
            results.extend(sorted(batch, key=lambda d: d[5], reverse=True))
        return suppress_duplicates(results)
    return detect


def prepare_frame(frame):
    """Letterbox BGR input without distortion; retain exact rounded scale/offset."""
    if frame is None or frame.size == 0:
        raise ValueError("Ảnh rỗng hoặc không hợp lệ.")
    height, width = frame.shape[:2]
    scale = min(config.FRAME_WIDTH / width, config.FRAME_HEIGHT / height)
    rw, rh = max(1, round(width*scale)), max(1, round(height*scale))
    left, top = (config.FRAME_WIDTH-rw)//2, (config.FRAME_HEIGHT-rh)//2
    prepared = np.zeros((config.FRAME_HEIGHT, config.FRAME_WIDTH, 3), dtype=np.uint8)
    prepared[top:top+rh, left:left+rw] = cv2.resize(frame, (rw, rh))
    return prepared, (rw/width, rh/height, left, top)


def detect_frame(frame, detector):
    """Infer in BGR, then map boxes back to the original image coordinates."""
    prepared, (sx, sy, left, top) = prepare_frame(frame)
    detections = filter_detections(detector(prepared), prepared.shape)
    original = [( (x-left)/sx, (y-top)/sy, w/sx, h/sy, label, score)
                for x, y, w, h, label, score in detections]
    return filter_detections(original, frame.shape)


def read_image(path):
    """Read Unicode Windows paths without cv2.imread's path encoding limitations."""
    path = Path(path)
    if path.suffix.lower() not in (".jpg", ".jpeg", ".png", ".bmp"):
        raise ValueError("Chỉ hỗ trợ JPG, JPEG, PNG và BMP.")
    data = np.fromfile(str(path), dtype=np.uint8)
    image = cv2.imdecode(data, cv2.IMREAD_COLOR) if data.size else None
    if image is None:
        raise ValueError(f"Ảnh bị lỗi hoặc không hợp lệ: {path.name}")
    return image


# ---------------------------------------------------------------------------
# Drawing helpers
# ---------------------------------------------------------------------------

def _draw_detection(frame: np.ndarray, x: int, y: int, w: int, h: int,
                    label: str, score: float) -> None:
    """Draw a single bounding box with label and confidence score.

    Parameters
    ----------
    frame : np.ndarray  BGR image to draw on (modified in-place).
    x, y  : int         Top-left corner of the bounding box.
    w, h  : int         Width and height of the bounding box.
    label : str         Detection class label (e.g. "fire", "smoke").
    score : float       Confidence score in [0, 1].
    """
    color = _BBOX_COLOR.get(label.lower(), _DEFAULT_COLOR)

    # Bounding box
    cv2.rectangle(frame, (x, y), (x + w, y + h), color, 2)

    # Label text above the box
    text = f"{label} {score:.2f}"
    (tw, th), baseline = cv2.getTextSize(text, cv2.FONT_HERSHEY_SIMPLEX,
                                         0.55, 1)
    # Filled rectangle behind text for readability
    cv2.rectangle(frame,
                  (x, y - th - baseline - 4),
                  (x + tw + 2, y),
                  color, cv2.FILLED)
    cv2.putText(frame, text,
                (x + 1, y - baseline - 2),
                cv2.FONT_HERSHEY_SIMPLEX, 0.55,
                (255, 255, 255), 1, cv2.LINE_AA)


def _draw_fps(frame: np.ndarray, fps: float) -> None:
    """Overlay FPS counter at the top-left corner of the frame."""
    cv2.putText(frame, f"FPS: {fps:.1f}",
                (10, 25),
                cv2.FONT_HERSHEY_SIMPLEX, 0.7,
                (0, 255, 0), 2, cv2.LINE_AA)


# ---------------------------------------------------------------------------
# Main pipeline loop
# ---------------------------------------------------------------------------

def run(source=0, method: str = "combined", show: bool = True) -> None:
    """
    Open *source*, run the selected detector on every frame, and display
    the annotated result.

    Parameters
    ----------
    source : int | str
        Webcam index (int) or path to a video file (str).
    method : str
        Detection method – "traditional", "yolo", or "combined".
    show : bool
        Whether to open a cv2 display window (set False for headless runs).
    """
    detector = load_detector(method)

    cap = cv2.VideoCapture(source)
    if not cap.isOpened():
        cap.release()
        raise RuntimeError(f"Cannot open video source: {source!r}")

    frame_count = 0
    fps = 0.0
    t_start = time.monotonic()

    print(f"[pipeline] Running '{method}' detector on source={source!r}. "
          f"Press 'q' to quit.")

    try:
        while True:
            ret, frame = cap.read()
            if not ret:
                print("[pipeline] End of stream or cannot read frame.")
                break

            # Infer on a letterboxed frame and draw in original coordinates.
            detections = detect_frame(frame, detector)

            # Draw detections
            for det in detections:
                x, y, w, h, label, score = det
                _draw_detection(frame, x, y, w, h, label, score)

            # Debug
            if frame_count % 30 == 0:
                print(f"[pipeline] frame {frame_count}, detections: {len(detections)}")

            # Compute FPS every N frames
            frame_count += 1
            if frame_count % config.FPS_UPDATE_INTERVAL == 0:
                elapsed = time.monotonic() - t_start
                fps = config.FPS_UPDATE_INTERVAL / elapsed if elapsed > 0 else 0.0
                t_start = time.monotonic()

            # Overlay FPS
            _draw_fps(frame, fps)

            if show:
                cv2.imshow(config.WINDOW_TITLE, frame)
                if cv2.waitKey(1) & 0xFF == ord("q"):
                    print("[pipeline] 'q' pressed – exiting.")
                    break

    finally:
        cap.release()
        if show:
            cv2.destroyAllWindows()
        print("[pipeline] Resources released.")


# ---------------------------------------------------------------------------
# CLI entry point
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Fire & Smoke Detection Pipeline"
    )
    parser.add_argument(
        "--source",
        default="0",
        help="Webcam index (e.g. 0) or path to a video file. Default: 0"
    )
    parser.add_argument(
        "--method",
        choices=["traditional", "yolo", "combined", "hybrid"],
        default="combined",
        help="Detection method to use. Default: combined"
    )
    args = parser.parse_args()

    # Convert source to int if it represents a webcam index
    source = int(args.source) if args.source.isdigit() else args.source

    run(source=source, method=args.method, show=True)
