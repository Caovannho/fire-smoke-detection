"""
Rule-based smoke detection using traditional computer vision techniques.

Phương pháp áp dụng:
    1. HSV thresholding: Lọc vùng màu khói (xám/trắng nhạt, vàng xám, tùy chọn khói đen).
    2. Xác thực chuyển động theo vùng (Candidate Motion Validation):
       - Tránh lỗi băm nát khối khói của phép `bitwise_and` truyền thống.
       - Tìm ứng viên từ mặt nạ màu -> kiểm tra tỉ lệ chuyển động (MOG2) trong khối đó.
       - Loại bỏ hoàn toàn vật thể tĩnh (tường, bàn ghế, màn hình) sau 1-2 frame.
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
    _DEFAULT_HSV_LOWER = [0, 0, 75]
    _DEFAULT_HSV_UPPER = [180, 55, 230]

PARAMS: Dict[str, Any] = dict(
    # --- Khói xám / trắng / ánh vàng nhạt (HSV) ---
    h_min=_DEFAULT_HSV_LOWER[0],
    h_max=_DEFAULT_HSV_UPPER[0],
    s_min=_DEFAULT_HSV_LOWER[1],
    # Mở rộng s_max lên 55 để bắt khói dưới ánh đèn vàng/nắng mà không bị cắt
    s_max=max(_DEFAULT_HSV_UPPER[1], 55),
    # Hạ v_min xuống 75 để bắt khói dày hoặc vùng thiếu sáng
    v_min=min(_DEFAULT_HSV_LOWER[2], 75),
    v_max=235,

    # --- Hỗ trợ khói đen / khói tối màu (tùy chọn) ---
    enable_black_smoke=False, # Bật khi cần phát hiện cháy dầu/cao su
    black_s_max=45,           # Độ bão hòa thấp cho khói đen
    black_v_min=20,           # Tránh pixel tối đen tuyệt đối
    black_v_max=75,           # Độ sáng tối đa của khói đen

    # --- Hình thái học (Morphology) ---
    open_k=5,                 # Kernel size phép Mở (loại bỏ chấm nhiễu nhỏ)
    close_k=11,               # Kernel size phép Đóng (làm liền khối khói đầy đặn)

    # --- Lọc Contour (Diện tích & Tỉ lệ) ---
    min_area=600,             # Hạ từ 1200 xuống 600 để bắt khói sớm từ xa
    max_area=250000,          # Diện tích tối đa (tránh nhầm nền trời toàn khung hình)
    min_ratio=0.2,            # Tỉ lệ w/h tối thiểu
    max_ratio=5.0,            # Tỉ lệ w/h tối đa

    # --- Đánh giá mật độ cạnh (Edge Density) ---
    # Nới lỏng lên 0.22 vì khói mờ trong suốt thường để lộ hoa văn nền phía sau
    max_edge_density=0.22,
    canny_thresh1=40,
    canny_thresh2=120,

    # --- Trừ nền & Chuyển động (Motion Validation) ---
    use_bg_sub=True,          # Bật trừ nền khi chạy video/webcam; đặt False khi test ảnh tĩnh
    bg_history=500,           # Lịch sử MOG2
    bg_var_threshold=40,      # Ngưỡng variance MOG2
    bg_learning_rate=0.003,   # Tốc độ học nền chậm: Tránh MOG2 nuốt chửng khói vào nền
    min_motion_ratio=0.015,   # Tối thiểu 1.5% diện tích ứng viên có chuyển động
    check_upward=True,        # Kiểm tra xu hướng khói bốc lên
    upward_tolerance=45,      # Dung sai pixel cho chuyển động bay lên / tản ra

    # --- Điểm tin cậy tối thiểu ---
    min_score=0.15,           # Bỏ các ứng viên có score thấp hơn ngưỡng này
)

def color_mask(frame: np.ndarray, p: Dict[str, Any]) -> np.ndarray:
    hsv = cv2.cvtColor(frame, cv2.COLOR_BGR2HSV)

    # 1. Khói trắng / xám nhạt / vàng xám
    lower_white = np.array([p["h_min"], p["s_min"], p["v_min"]], dtype=np.uint8)
    upper_white = np.array([p["h_max"], p["s_max"], p["v_max"]], dtype=np.uint8)
    mask_white = cv2.inRange(hsv, lower_white, upper_white)

    # 2. Khói đen (tùy chọn)
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
    canny_t1: int = 40,
    canny_t2: int = 120,
) -> float:
    roi_gray = gray[y : y + h, x : x + w]
    if roi_gray.size == 0:
        return 1.0

    # Tạo mask cục bộ cho ROI chỉ lấy phần trong contour
    cnt_mask = np.zeros((h, w), dtype=np.uint8)
    shifted_cnt = contour - [x, y]
    cv2.drawContours(cnt_mask, [shifted_cnt], -1, 255, thickness=-1)

    cnt_area = cv2.countNonZero(cnt_mask)
    if cnt_area == 0:
        return 1.0

    # Phát hiện cạnh trong ROI
    edges = cv2.Canny(roi_gray, canny_t1, canny_t2)

    # Chỉ đếm số pixel cạnh nằm bên trong contour
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
            detectShadows=False,
        )
        self._prev_centroids: List[Tuple[int, int]] = []

    def _is_rising_or_spreading(
        self, cx: int, cy: int, tolerance: int = 45
    ) -> bool:
        if not self._prev_centroids:
            return True

        # Tìm centroid gần nhất trong frame trước
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

        # 1. Trích xuất mặt nạ màu khói (HSV)
        hsv_m = color_mask(frame, p)

        # 2. Cập nhật nền MOG2 với tốc độ học được kiểm soát
        fg_m = None
        if p["use_bg_sub"]:
            # Dùng learningRate nhỏ để MOG2 không nuốt khói quá nhanh
            lr = p.get("bg_learning_rate", 0.003)
            fg_raw = self._bg_sub.apply(frame, learningRate=lr)
            # Ngưỡng nhị phân hóa chuyển động mềm (150 thay vì 200)
            _, fg_m = cv2.threshold(fg_raw, 150, 255, cv2.THRESH_BINARY)

        # 3. Phân tích hình thái học TRÊN MẶT NẠ MÀU để giữ nguyên hình khối khói
        k_open = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (p["open_k"], p["open_k"]))
        k_close = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (p["close_k"], p["close_k"]))

        cleaned_m = cv2.morphologyEx(hsv_m, cv2.MORPH_OPEN, k_open, iterations=1)
        cleaned_m = cv2.morphologyEx(cleaned_m, cv2.MORPH_CLOSE, k_close, iterations=2)
        _, candidate_mask = cv2.threshold(cleaned_m, 127, 255, cv2.THRESH_BINARY)

        # 4. Tìm kiếm các khối ứng viên
        contours, _ = cv2.findContours(
            candidate_mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE
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

            # 5. Xác thực chuyển động (Region-Level Motion Verification)
            motion_ratio = 1.0
            if p["use_bg_sub"] and fg_m is not None:
                # Tạo mask riêng cho contour này để đếm số pixel chuyển động
                cnt_mask = np.zeros((h, w), dtype=np.uint8)
                shifted_cnt = cnt - [x, y]
                cv2.drawContours(cnt_mask, [shifted_cnt], -1, 255, thickness=-1)
                
                # Cắt ROI chuyển động tương ứng
                roi_fg = fg_m[y : y + h, x : x + w]
                moving_pixels = cv2.countNonZero(cv2.bitwise_and(cnt_mask, roi_fg))
                motion_ratio = float(moving_pixels) / (area + 1e-6)

                # Nếu khối hoàn toàn không chuyển động (vật thể tĩnh như tường, bàn) -> Loại bỏ!
                if motion_ratio < p["min_motion_ratio"]:
                    continue

            # 6. Đánh giá mật độ cạnh Canny bên trong contour
            edge_dens = compute_contour_edge_density(
                gray, cnt, x, y, w, h, p["canny_thresh1"], p["canny_thresh2"]
            )
            if edge_dens > p["max_edge_density"]:
                continue  # Bỏ qua nếu có quá nhiều cạnh sắc nét (vật thể rắn)

            # 7. Đánh giá xu hướng bốc lên / tản ra
            cx, cy = x + w // 2, y + h // 2
            is_rising = True
            if p["use_bg_sub"] and p["check_upward"]:
                is_rising = self._is_rising_or_spreading(cx, cy, p["upward_tolerance"])

            current_centroids.append((cx, cy))

            # 8. Tính Điểm tin cậy (Confidence Score) cân bằng và mượt mà
            area_score = min((area / frame_area) * 8.0, 0.35)
            edge_score = max(0.0, (1.0 - edge_dens / p["max_edge_density"])) * 0.35
            motion_score = min(motion_ratio * 4.0, 0.20) if p["use_bg_sub"] else 0.20
            rising_bonus = 0.10 if is_rising else 0.0

            total_score = round(float(np.clip(area_score + edge_score + motion_score + rising_bonus, 0.0, 1.0)), 4)

            if total_score >= p["min_score"]:
                results.append((int(x), int(y), int(w), int(h), "smoke", total_score))

        self._prev_centroids = current_centroids
        return results

    __call__ = detect

_detector = SmokeDetector()


def reset() -> None:
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


# Bí danh chuẩn theo giao diện chung của nhóm
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
