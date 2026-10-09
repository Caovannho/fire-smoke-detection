"""
End-to-end detection pipeline entry point.

Orchestrates the full workflow:
    1. Load configuration from config.py
    2. Initialize the chosen detector (Traditional, YOLO, or Combined)
    3. Open input source (webcam index or video file path)
    4. Process frames in a loop:
        a. Resize frame to (FRAME_WIDTH, FRAME_HEIGHT)
        b. Run detector → list of (label, score, bbox) tuples
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

def load_detector(method: str = "combined"):
    """
    Return a callable  detect(frame) -> list[tuple[int,int,int,int,str,float]]
    where each tuple is  (x, y, w, h, label, confidence).

    If the required modules are not yet implemented (ImportError), a warning
    is printed and a no-op detector that always returns [] is returned instead.

    Parameters
    ----------
    method : str
        One of  "traditional" | "yolo" | "combined".

    Raises
    ------
    ValueError
        If *method* is not one of the supported options.
    """
    try:
        if method == "traditional":
            from traditional import fire_detect, smoke_detect

            def _traditional_detect(frame):
                results = []
                results.extend(fire_detect.detect(frame))
                results.extend(smoke_detect.detect(frame))
                return results

            return _traditional_detect

        elif method == "yolo":
            from yolo import yolo_detect

            return yolo_detect.detect

        elif method == "combined":
            from traditional import fire_detect, smoke_detect
            from yolo import yolo_detect

            def _combined_detect(frame):
                results = []
                results.extend(fire_detect.detect(frame))
                results.extend(smoke_detect.detect(frame))
                results.extend(yolo_detect.detect(frame))
                return results

            return _combined_detect

        else:
            raise ValueError(
                f"Unknown detection method '{method}'. "
                "Choose from: 'traditional', 'yolo', 'combined'."
            )

    except ImportError as e:
        print(f"[WARN] Detector chưa có: {e}")
        return lambda frame: []


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
        raise RuntimeError(f"Cannot open video source: {source!r}")

    frame_count = 0
    fps = 0.0
    t_start = time.time()

    print(f"[pipeline] Running '{method}' detector on source={source!r}. "
          f"Press 'q' to quit.")

    try:
        while True:
            ret, frame = cap.read()
            if not ret:
                print("[pipeline] End of stream or cannot read frame.")
                break

            # Resize to configured dimensions
            frame = cv2.resize(
                frame,
                (config.FRAME_WIDTH, config.FRAME_HEIGHT)
            )

            # Run detection
            detections = detector(frame)   # [(x, y, w, h, label, score), ...]

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
                elapsed = time.time() - t_start
                fps = config.FPS_UPDATE_INTERVAL / elapsed if elapsed > 0 else 0.0
                t_start = time.time()

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
        choices=["traditional", "yolo", "combined"],
        default="combined",
        help="Detection method to use. Default: combined"
    )
    args = parser.parse_args()

    # Convert source to int if it represents a webcam index
    source = int(args.source) if args.source.isdigit() else args.source

    run(source=source, method=args.method, show=True)
