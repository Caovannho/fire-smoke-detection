"""
Global configuration constants for the fire-smoke-detection project.

All tuneable parameters and paths are centralised here so that every
module imports from a single source of truth.
"""

# --- Video / Camera ---
FRAME_WIDTH  = 640
FRAME_HEIGHT = 480

# --- Detection classes ---
LABELS = ["fire", "smoke"]

# --- YOLO settings ---
YOLO_WEIGHTS   = "yolo/weights/best.pt"   # path to trained YOLOv8 weights
CONF_THRESHOLD = 0.45                      # minimum confidence to report a detection
IOU_THRESHOLD  = 0.45                      # NMS IoU threshold

# --- Traditional CV thresholds (HSV) ---
# Fire: orange-red hue range
FIRE_HSV_LOWER = [0,   120, 70]
FIRE_HSV_UPPER = [35,  255, 255]

# Smoke: low-saturation grey range
SMOKE_HSV_LOWER = [0, 0,  90]
SMOKE_HSV_UPPER = [180, 30, 220]

# --- Paths ---
DATA_DIR   = "data"
OUTPUT_DIR = "outputs"
LOG_FILE   = "alerts.log"

# TODO: TVx implement

