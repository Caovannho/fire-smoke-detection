"""
Rule-based smoke detection using traditional computer vision techniques.

Phương pháp áp dụng:
    1. HSV thresholding: Lọc màu khói trắng/xám và tùy chọn khói đen đặc.
    2. Background subtraction (MOG2): Cô lập các vùng chuyển động (tùy chọn bật/tắt).
    3. Phân tích hình thái học (Morphology): Lọc nhiễu đốm nhỏ và làm liền khối khói.
    4. Đánh giá mật độ cạnh (Edge Density): Tính Canny bên trong contour khói (khói mờ viền).
    5. Đánh giá hướng bay lên (Upward Motion): Theo dõi tọa độ centroid giữa các frame.

Giao diện tích hợp (Pipeline & Evaluation):
    - detect(frame: np.ndarray, params: dict | None = None) -> list[tuple[int, int, int, int, str, float]]
    - detect_smoke(frame, params)
    - classify_smoke_region(roi, params)
    - SmokeDetector(params) với hàm reset()
"""

from __future__ import annotations

import sys
import warnings
from pathlib import Path
from typing import List, Tuple, Dict, Any

# Thêm thư mục gốc vào sys.path để import config.py kể cả khi chạy trực tiếp
_PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(_PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(_PROJECT_ROOT))

import cv2
import numpy as np

# Nạp cấu hình HSV từ config.py nếu có
try:
    import config as _cfg
    _DEFAULT_HSV_LOWER = list(_cfg.SMOKE_HSV_LOWER)
    _DEFAULT_HSV_UPPER = list(_cfg.SMOKE_HSV_UPPER)
except (ImportError, ModuleNotFoundError, AttributeError):
    warnings.warn(
        "[smoke_detect] Không tìm thấy config.py – sử dụng ngưỡng HSV mặc định.",
        stacklevel=2,
    )
    _DEFAULT_HSV_LOWER = [0, 0, 90]
    _DEFAULT_HSV_UPPER = [180, 35, 220]

PARAMS: Dict[str, Any] = dict(
    h_min=_DEFAULT_HSV_LOWER[0],
    h_max=_DEFAULT_HSV_UPPER[0],
    s_min=_DEFAULT_HSV_LOWER[1],
    s_max=_DEFAULT_HSV_UPPER[1],
    v_min=_DEFAULT_HSV_LOWER[2],
    v_max=_DEFAULT_HSV_UPPER[2],


    enable_black_smoke=False, # Mặc định tắt để tránh nhầm nền tối; bật khi cần phát hiện cháy dầu/cao su
    black_s_max=40,          # Độ bão hòa thấp cho khói đen
    black_v_min=20,          # Tránh pixel tối đen tuyệt đối
    black_v_max=75,          # Độ sáng tối đa của khói đen

    open_k=5,                # Kernel size phép Mở (loại bỏ chấm nhiễu nhỏ)
    close_k=9,               # Kernel size phép Đóng (nối các mảng khói rời rạc)

    min_area=1200,           # Diện tích tối thiểu (pixel trên ảnh 640x480)
    max_area=240000,         # Diện tích tối đa (tránh nhầm nền trời toàn khung hình)
    min_ratio=0.2,           # Tỉ lệ w/h tối thiểu
    max_ratio=5.0,           # Tỉ lệ w/h tối đa

    max_edge_density=0.14,   # Khói có viền mờ -> mật độ cạnh trong contour thấp
    canny_thresh1=50,
    canny_thresh2=150,

    use_bg_sub=True,         # Đặt False khi đánh giá trên tập ảnh tĩnh độc lập (eval/evaluate.py)
    bg_history=500,          # Lịch sử MOG2
    bg_var_threshold=50,     # Ngưỡng variance MOG2
    bg_detect_shadows=False,
    check_upward=True,       # Kiểm tra xu hướng bay lên
    upward_tolerance=35,     # Dung sai pixel cho chuyển động bay lên

    min_score=0.15,          # Bỏ các ứng viên có score thấp hơn ngưỡng này
)



def color_mask(frame: np.ndarray, p: Dict[str, Any]) -> np.ndarray:
    hsv = cv2.cvtColor(frame, cv2.COLOR_BGR2HSV)
    lower_white = np.array([p["h_min"], p["s_min"], p["v_min"]], dtype=np.uint8)
    upper_white = np.array([p["h_max"], p["s_max"], p["v_max"]], dtype=np.uint8)
    mask_white = cv2.inRange(hsv, lower_white, upper_white)

    if p.get("enable_black_smoke", False):
        lower_black = np.array([0, 0, p["black_v_min"]], dtype=np.uint8)
        upper_black = np.array([180, p["black_s_max"], p["black_v_max"]], dtype=np.uint8)
        mask_black = cv2.inRange(hsv, lower_black, upper_black)
        return cv2.bitwise_or(mask_white, mask_black)

    return mask_white

def compute_contour_edge_density(
    gray: np.ndarray,
    contour: np.ndarray,
    x: int,
    y: int,
    w: int,
    h: int,
    canny_t1: int = 50,
    canny_t2: int = 150,
) -> float:
    roi_gray = gray[y : y + h, x : x + w]
    if roi_gray.size == 0:
        return 1.0
    cnt_mask = np.zeros((h, w), dtype=np.uint8)
    shifted_cnt = contour - [x, y]
    cv2.drawContours(cnt_mask, [shifted_cnt], -1, 255, thickness=-1)

    cnt_area = cv2.countNonZero(cnt_mask)
    if cnt_area == 0:
        return 1.0

    edges = cv2.Canny(roi_gray, canny_t1, canny_t2)

    edges_in_contour = cv2.bitwise_and(edges, cnt_mask)
    edge_pixels = cv2.countNonZero(edges_in_contour)

    return float(edge_pixels) / float(cnt_area)

def classify_smoke_region(roi: np.ndarray, params: Dict[str, Any] | None = None) -> float:
    """Chấm điểm độ giống khói của một vùng ảnh (0.0 đến 1.0)."""
    if roi.size == 0:
        return 0.0
    p = {**PARAMS, **(params or {})}
    mask = color_mask(roi, p)
    return float(cv2.countNonZero(mask)) / float(roi.shape[0] * roi.shape[1])

class SmokeDetector:
    def __init__(self, params: Dict[str, Any] | None = None) -> None:
        self.params = params or {}
        self.reset()

    def reset(self) -> None:
        p = {**PARAMS, **self.params}
        self._bg_sub = cv2.createBackgroundSubtractorMOG2(
            history=p["bg_history"],
            varThreshold=p["bg_var_threshold"],
            detectShadows=p["bg_detect_shadows"],
        )
        self._prev_centroids: List[Tuple[int, int]] = []

    def _is_rising_or_spreading(
        self, cx: int, cy: int, tolerance: int = 35
    ) -> bool:
        if not self._prev_centroids:
            return True
        best_dist = float("inf")
        best_prev_cy = cy
        for pcx, pcy in self._prev_centroids:
            dist = abs(cx - pcx) + abs(cy - pcy)
            if dist < best_dist:
                best_dist = dist
                best_prev_cy = pcy

        return cy <= best_prev_cy + tolerance

    def detect(
        self, frame: np.ndarray, params: Dict[str, Any] | None = None
    ) -> List[Tuple[int, int, int, int, str, float]]:
        if frame is None or frame.size == 0:
            return []

        p = {**PARAMS, **self.params, **(params or {})}
        h_frame, w_frame = frame.shape[:2]
        frame_area = float(h_frame * w_frame)
        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)

        # 1. Lọc ngưỡng màu HSV
        hsv_m = color_mask(frame, p)

        # 2. Xử lý chuyển động (Background Subtraction)
        if p["use_bg_sub"]:
            fg_raw = self._bg_sub.apply(frame)
            _, fg_m = cv2.threshold(fg_raw, 200, 255, cv2.THRESH_BINARY)
            combined_m = cv2.bitwise_and(hsv_m, fg_m)
        else:
            # Chế độ ảnh tĩnh: Không dùng trừ nền
            combined_m = hsv_m

        # 3. Phân tích hình thái học (Morphology)
        k_open = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (p["open_k"], p["open_k"]))
        k_close = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (p["close_k"], p["close_k"]))

        cleaned_m = cv2.morphologyEx(combined_m, cv2.MORPH_OPEN, k_open, iterations=2)
        cleaned_m = cv2.morphologyEx(cleaned_m, cv2.MORPH_CLOSE, k_close, iterations=3)
        cleaned_m = cv2.GaussianBlur(cleaned_m, (5, 5), 0)
        _, final_mask = cv2.threshold(cleaned_m, 127, 255, cv2.THRESH_BINARY)

        # 4. Tìm kiếm Contour ứng viên
        contours, _ = cv2.findContours(
            final_mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE
        )

        results: List[Tuple[int, int, int, int, str, float]] = []
        current_centroids: List[Tuple[int, int]] = []

        for cnt in contours:
            area = cv2.contourArea(cnt)
            if area < p["min_area"] or area > p["max_area"]:
                continue

            x, y, w, h = cv2.boundingRect(cnt)
            aspect = max(w, h) / (min(w, h) + 1e-6)
            if aspect > p["max_ratio"] or (w / h) < p["min_ratio"]:
                continue

            # 5. Đánh giá mật độ cạnh Canny bên trong contour
            edge_dens = compute_contour_edge_density(
                gray, cnt, x, y, w, h, p["canny_thresh1"], p["canny_thresh2"]
            )
            if edge_dens > p["max_edge_density"]:
                continue  # Bỏ qua nếu có nhiều cạnh sắc (vật thể rắn)

            # 6. Đánh giá chuyển động bốc lên
            cx, cy = x + w // 2, y + h // 2
            is_rising = True
            if p["use_bg_sub"] and p["check_upward"]:
                is_rising = self._is_rising_or_spreading(cx, cy, p["upward_tolerance"])

            current_centroids.append((cx, cy))

            # 7. Tính Score tổng hợp
            area_score = min((area / frame_area) * 10.0, 0.4)
            edge_score = max(0.0, (1.0 - edge_dens / p["max_edge_density"])) * 0.35
            motion_score = 0.25 if is_rising else 0.0

            total_score = round(float(np.clip(area_score + edge_score + motion_score, 0.0, 1.0)), 4)

            if total_score >= p["min_score"]:
                results.append((int(x), int(y), int(w), int(h), "smoke", total_score))

        self._prev_centroids = current_centroids
        return results

    __call__ = detect
_detector = SmokeDetector()

def reset() -> None:
    """Reset trạng thái bộ phát hiện singleton (gọi khi đổi nguồn video)."""
    _detector.reset()

def detect_smoke(
    frame: np.ndarray, params: Dict[str, Any] | None = None
) -> List[Tuple[int, int, int, int, str, float]]:
    """Phát hiện khói trong frame ảnh BGR 640x480."""
    try:
        return _detector.detect(frame, params=params)
    except Exception as exc:
        print(f"[smoke_detect] Lỗi khi xử lý frame: {exc}", file=sys.stderr)
        return []

detect = detect_smoke

if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(
        description="Smoke Detection (Traditional CV) - Standalone Demo"
    )
    parser.add_argument(
        "--source", default="0",
        help="Webcam index (e.g. 0) hoặc đường dẫn file video/ảnh. Mặc định: 0",
    )
    parser.add_argument(
        "--no-bg", action="store_true",
        help="Tắt Background Subtraction (chế độ ảnh tĩnh)",
    )
    args = parser.parse_args()

    # Kiểm tra nguồn là webcam, video hay ảnh
    src_val = int(args.source) if args.source.isdigit() else args.source
    custom_params = {"use_bg_sub": not args.no_bg}

    cap = cv2.VideoCapture(src_val)
    if not cap.isOpened():
        print(f"[smoke_detect] Không thể mở nguồn: {src_val!r}")
        sys.exit(1)

    print("[smoke_detect] Đang chạy... Nhấn 'q' để thoát, 'r' để reset bộ đệm.")

    while True:
        ret, raw = cap.read()
        if not ret:
            print("[smoke_detect] Hết stream hoặc không đọc được frame.")
            break

        raw = cv2.resize(raw, (640, 480))
        detections = detect(raw, params=custom_params)

        for (bx, by, bw, bh, label, score) in detections:
            cv2.rectangle(raw, (bx, by), (bx + bw, by + bh), (128, 128, 128), 2)
            cv2.putText(
                raw, f"{label} {score:.2f}",
                (bx, by - 8), cv2.FONT_HERSHEY_SIMPLEX, 0.6,
                (255, 255, 255), 2, cv2.LINE_AA,
            )

        cv2.imshow("Smoke Detection (Traditional)", raw)
        key = cv2.waitKey(1) & 0xFF
        if key == ord("q"):
            break
        elif key == ord("r"):
            reset()
            print("[smoke_detect] Đã reset bộ đệm MOG2 và centroid.")

    cap.release()
    cv2.destroyAllWindows()
    print("[smoke_detect] Đã giải phóng tài nguyên.")
