"""
Global configuration constants for the fire-smoke-detection project.

All tuneable parameters and paths are centralised here so that every
module imports from a single source of truth.
"""

# --- Video / Camera ---
FRAME_WIDTH = 640
FRAME_HEIGHT = 480

# --- Detection classes ---
LABELS = ["fire", "smoke"]

# --- Alert settings ---
ALERT_N_FRAMES = 5          # số frame liên tiếp phát hiện trước khi cảnh báo
ALERT_COOLDOWN_SEC = 3      # thời gian chờ giữa hai lần cảnh báo (giây)

# --- Paths ---
DATA_YAML = "data.yaml"
WEIGHTS_PATH = "yolo/weights/best.pt"

# --- GUI ---
WINDOW_TITLE = "Fire & Smoke Detection"
FPS_UPDATE_INTERVAL = 30    # cập nhật hiển thị FPS sau mỗi N frame
