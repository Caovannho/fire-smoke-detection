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
YOLO_WEIGHTS   = "yolo/weights/best.pt"
CONF_THRESHOLD = 0.45
IOU_THRESHOLD  = 0.45

# --- Traditional CV thresholds (HSV) ---
# Fire: orange-red hue range
FIRE_HSV_LOWER = [0,   120, 70]
FIRE_HSV_UPPER = [35,  255, 255]

# Smoke: low-saturation grey range
SMOKE_HSV_LOWER = [0,   0,  90]
SMOKE_HSV_UPPER = [180, 30, 220]

# --- Alert settings ---
ALERT_N_FRAMES     = 5   # consecutive positive frames before alarm fires
ALERT_COOLDOWN_SEC = 3   # minimum seconds between two consecutive alarms

# --- Paths ---
DATA_DIR   = "data"
OUTPUT_DIR = "outputs"
LOG_FILE   = "alerts.log"
DATA_YAML  = "data.yaml"
WEIGHTS_PATH = "yolo/weights/best.pt"

# --- GUI ---
WINDOW_TITLE        = "Fire & Smoke Detection"
FPS_UPDATE_INTERVAL = 30   # update FPS display every N frames
