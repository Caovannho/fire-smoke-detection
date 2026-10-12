"""
Rule-based smoke detection using traditional computer vision techniques.

Approach:
    1. HSV thresholding  – Lọc vùng có màu xám/trắng nhạt đặc trưng của khói.
    2. Background subtraction (MOG2) – Cô lập vùng chuyển động, loại bỏ nền tĩnh.
    3. Morphological filtering – Lọc nhiễu nhỏ, nối các vùng khói liền kề.
    4. Edge-density analysis  – Khói thật có mật độ cạnh thấp (mờ, lan tỏa).
    5. Upward-motion heuristic – Khói có xu hướng bay lên; centroid frame sau
       phải cao hơn (y nhỏ hơn) hoặc ít nhất ngang bằng frame trước.

Pipeline interface
------------------
    detect(frame: np.ndarray) -> list[tuple[int,int,int,int,str,float]]

    Mỗi tuple: (x, y, w, h, "smoke", score)
    - frame đã resize 640×480 BGR.
"""

from __future__ import annotations

import sys
import warnings
from typing import List, Tuple

import cv2
import numpy as np

# ---------------------------------------------------------------------------
# Cố gắng import config dự án; nếu chạy standalone thì dùng giá trị mặc định
# ---------------------------------------------------------------------------
try:
    import config as _cfg
    _SMOKE_HSV_LOWER = np.array(_cfg.SMOKE_HSV_LOWER, dtype=np.uint8)
    _SMOKE_HSV_UPPER = np.array(_cfg.SMOKE_HSV_UPPER, dtype=np.uint8)
except (ImportError, ModuleNotFoundError):
    warnings.warn(
        "[smoke_detect] Không tìm thấy config.py – sử dụng ngưỡng HSV mặc định.",
        stacklevel=2,
    )
    _SMOKE_HSV_LOWER = np.array([0,   0,  90], dtype=np.uint8)
    _SMOKE_HSV_UPPER = np.array([180, 30, 220], dtype=np.uint8)

# ---------------------------------------------------------------------------
# Hằng số tinh chỉnh
# ---------------------------------------------------------------------------
_MIN_CONTOUR_AREA   = 1500    # Diện tích tối thiểu (px²) để giữ contour
_MAX_CONTOUR_AREA   = 250_000 # Diện tích tối đa – loại nhiễu toàn khung hình
_MORPH_KERNEL_SIZE  = (7, 7)  # Kernel cho morphological close / open
_EDGE_DENSITY_MAX   = 0.12    # Khói thật có edge-density ≤ ngưỡng này
_BG_HISTORY         = 500     # Số frame huấn luyện Background Subtractor
_BG_VAR_THRESHOLD   = 50      # Ngưỡng variance cho MOG2
_BG_DETECT_SHADOWS  = False   # Bỏ qua shadow (giảm false-positive)
_ASPECT_RATIO_MAX   = 6.0     # Loại các bbox quá dẹt hoặc quá dài
_CENTROID_MEMORY    = 30       # Số frame lưu centroid để theo dõi hướng bay


# ═══════════════════════════════════════════════════════════════════════════
# SmokeDetector – bộ phát hiện có trạng thái (stateful)
# ═══════════════════════════════════════════════════════════════════════════

class SmokeDetector:
    """Bộ phát hiện khói dựa trên các kỹ thuật CV truyền thống.

    Giữ trạng thái giữa các frame (background subtractor, lịch sử
    centroid) để cải thiện chất lượng phát hiện qua thời gian.
    """

    def __init__(self) -> None:
        # --- Background Subtractor (MOG2) ---
        self._bg_sub = cv2.createBackgroundSubtractorMOG2(
            history=_BG_HISTORY,
            varThreshold=_BG_VAR_THRESHOLD,
            detectShadows=_BG_DETECT_SHADOWS,
        )

        # --- Morphological kernels ---
        self._morph_kernel = cv2.getStructuringElement(
            cv2.MORPH_ELLIPSE, _MORPH_KERNEL_SIZE
        )

        # --- Centroid history: {contour_id: deque_of_(cx, cy)]} ---
        # Dùng list đơn giản: lưu centroid tất cả vùng khói ở frame trước
        self._prev_centroids: List[Tuple[int, int]] = []

    # ------------------------------------------------------------------
    # Bước 1: HSV thresholding
    # ------------------------------------------------------------------
    def _hsv_mask(self, frame: np.ndarray) -> np.ndarray:
        """Tạo binary mask cho các pixel có màu khói (xám / trắng nhạt).

        Parameters
        ----------
        frame : np.ndarray
            Ảnh BGR đầu vào.

        Returns
        -------
        np.ndarray
            Mask nhị phân (uint8, 0 hoặc 255).
        """
        hsv = cv2.cvtColor(frame, cv2.COLOR_BGR2HSV)
        mask = cv2.inRange(hsv, _SMOKE_HSV_LOWER, _SMOKE_HSV_UPPER)
        return mask

    # ------------------------------------------------------------------
    # Bước 2: Background subtraction
    # ------------------------------------------------------------------
    def _fg_mask(self, frame: np.ndarray) -> np.ndarray:
        """Trả về foreground mask bằng MOG2 background subtractor.

        Chỉ giữ lại các vùng *chuyển động* – loại bỏ nền tĩnh (tường,
        mây, v.v.) có thể trùng màu khói.

        Parameters
        ----------
        frame : np.ndarray
            Ảnh BGR đầu vào.

        Returns
        -------
        np.ndarray
            Foreground mask nhị phân (uint8, 0 hoặc 255).
        """
        fg = self._bg_sub.apply(frame)
        # MOG2 trả về 0/127/255 nếu detectShadows=True;
        # với detectShadows=False luôn là 0/255.
        _, fg = cv2.threshold(fg, 200, 255, cv2.THRESH_BINARY)
        return fg

    # ------------------------------------------------------------------
    # Bước 3: Kết hợp mask + morphology
    # ------------------------------------------------------------------
    @staticmethod
    def _combine_and_clean(
        hsv_mask: np.ndarray,
        fg_mask: np.ndarray,
        kernel: np.ndarray,
    ) -> np.ndarray:
        """AND hai mask rồi áp dụng morphological open → close để lọc nhiễu.

        Parameters
        ----------
        hsv_mask : np.ndarray
            Mask màu khói.
        fg_mask : np.ndarray
            Mask vùng chuyển động.
        kernel : np.ndarray
            Structuring element cho morphology.

        Returns
        -------
        np.ndarray
            Mask đã lọc sạch (uint8).
        """
        combined = cv2.bitwise_and(hsv_mask, fg_mask)

        # Morphological OPEN: loại bỏ đốm nhiễu nhỏ
        cleaned = cv2.morphologyEx(combined, cv2.MORPH_OPEN, kernel, iterations=2)
        # Morphological CLOSE: lấp lỗ hổng, nối các vùng khói gần nhau
        cleaned = cv2.morphologyEx(cleaned, cv2.MORPH_CLOSE, kernel, iterations=3)

        # Làm mịn cạnh bằng GaussianBlur rồi threshold lại
        cleaned = cv2.GaussianBlur(cleaned, (5, 5), 0)
        _, cleaned = cv2.threshold(cleaned, 127, 255, cv2.THRESH_BINARY)

        return cleaned

    # ------------------------------------------------------------------
    # Bước 4: Tính edge density trong một ROI
    # ------------------------------------------------------------------
    @staticmethod
    def _edge_density(gray_roi: np.ndarray) -> float:
        """Tính tỉ lệ pixel cạnh trên tổng pixel trong vùng ROI.

        Khói thật thường mờ → edge density thấp.
        Vật thể rắn (xe cộ, tòa nhà) → edge density cao.

        Parameters
        ----------
        gray_roi : np.ndarray
            ROI ảnh grayscale.

        Returns
        -------
        float
            Giá trị từ 0.0 đến 1.0.
        """
        if gray_roi.size == 0:
            return 1.0  # Trả về cao để loại bỏ ROI rỗng

        edges = cv2.Canny(gray_roi, 50, 150)
        return float(np.count_nonzero(edges)) / edges.size

    # ------------------------------------------------------------------
    # Bước 5: Đánh giá hướng bay lên (upward motion heuristic)
    # ------------------------------------------------------------------
    def _is_rising_or_spreading(
        self, cx: int, cy: int, tolerance: int = 30
    ) -> bool:
        """Kiểm tra xem centroid hiện tại có xu hướng bay lên so với frame trước.

        Khói tự nhiên bay lên trên (cy giảm) hoặc lan rộng sang ngang.
        Nếu không có lịch sử (frame đầu tiên), mặc định trả True.

        Parameters
        ----------
        cx, cy : int
            Tọa độ centroid hiện tại.
        tolerance : int
            Sai số pixel cho phép (khói có thể dao động nhẹ).

        Returns
        -------
        bool
            True nếu vùng khói bay lên / lan tỏa hợp lý.
        """
        if not self._prev_centroids:
            return True  # Chưa có lịch sử → chấp nhận

        # Tìm centroid gần nhất ở frame trước (nearest-neighbor đơn giản)
        best_dist = float("inf")
        best_prev_cy = cy
        for pcx, pcy in self._prev_centroids:
            d = abs(cx - pcx) + abs(cy - pcy)  # Manhattan distance
            if d < best_dist:
                best_dist = d
                best_prev_cy = pcy

        # Chấp nhận nếu: bay lên (cy ≤ prev_cy) hoặc dao động trong tolerance
        return cy <= best_prev_cy + tolerance

    # ------------------------------------------------------------------
    # Tính confidence score
    # ------------------------------------------------------------------
    @staticmethod
    def _compute_score(
        contour_area: float,
        edge_dens: float,
        is_rising: bool,
        frame_area: float,
    ) -> float:
        """Tính điểm tin cậy tổng hợp cho một vùng khói ứng viên.

        Score dựa trên:
            - Tỉ lệ diện tích contour / frame (vùng lớn hơn → tin cậy hơn,
              nhưng saturate để tránh false positive toàn khung hình).
            - Edge density thấp → tăng điểm.
            - Bay lên → bonus.

        Parameters
        ----------
        contour_area : float
            Diện tích contour (px²).
        edge_dens : float
            Edge density trong ROI (0–1).
        is_rising : bool
            Contour có đang bay lên không.
        frame_area : float
            Tổng diện tích frame.

        Returns
        -------
        float
            Score trong [0, 1].
        """
        # --- Thành phần 1: diện tích tương đối (0 → 0.4) ---
        area_ratio = contour_area / frame_area if frame_area > 0 else 0
        area_score = min(area_ratio * 10.0, 0.4)  # cap tại 0.4

        # --- Thành phần 2: edge density thấp → điểm cao (0 → 0.35) ---
        #     edge_dens = 0   → 0.35   (rất mờ, rất giống khói)
        #     edge_dens = 0.12 → 0.0
        edge_score = max(0.0, (1.0 - edge_dens / _EDGE_DENSITY_MAX)) * 0.35

        # --- Thành phần 3: hướng bay lên (0 hoặc 0.25) ---
        motion_score = 0.25 if is_rising else 0.0

        score = area_score + edge_score + motion_score
        return round(float(np.clip(score, 0.0, 1.0)), 4)

    # ==================================================================
    # PUBLIC API: detect()
    # ==================================================================
    def detect(
        self, frame: np.ndarray
    ) -> List[Tuple[int, int, int, int, str, float]]:
        """Phát hiện khói trong một frame BGR (640×480).

        Parameters
        ----------
        frame : np.ndarray
            Ảnh BGR đã resize 640×480.

        Returns
        -------
        list[tuple[int, int, int, int, str, float]]
            Danh sách ``(x, y, w, h, "smoke", score)`` cho mỗi vùng
            khói phát hiện được.  Trả ``[]`` nếu không phát hiện.
        """
        # Kiểm tra đầu vào cơ bản
        if frame is None or frame.size == 0:
            return []

        h_frame, w_frame = frame.shape[:2]
        frame_area = float(h_frame * w_frame)

        # Ảnh grayscale dùng cho edge-density
        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)

        # ----- Bước 1: HSV mask (vùng màu khói) -----
        hsv_mask = self._hsv_mask(frame)

        # ----- Bước 2: Foreground mask (vùng chuyển động) -----
        fg_mask = self._fg_mask(frame)

        # ----- Bước 3: Kết hợp + Morphology -----
        final_mask = self._combine_and_clean(hsv_mask, fg_mask, self._morph_kernel)

        # ----- Bước 4: Tìm contours -----
        contours, _ = cv2.findContours(
            final_mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE
        )

        results: List[Tuple[int, int, int, int, str, float]] = []
        current_centroids: List[Tuple[int, int]] = []

        for cnt in contours:
            area = cv2.contourArea(cnt)

            # Lọc theo diện tích
            if area < _MIN_CONTOUR_AREA or area > _MAX_CONTOUR_AREA:
                continue

            x, y, w, h = cv2.boundingRect(cnt)

            # Lọc aspect ratio bất thường
            aspect = max(w, h) / (min(w, h) + 1e-6)
            if aspect > _ASPECT_RATIO_MAX:
                continue

            # ----- Bước 4a: Edge density -----
            roi_gray = gray[y : y + h, x : x + w]
            e_dens = self._edge_density(roi_gray)
            if e_dens > _EDGE_DENSITY_MAX:
                continue  # Vùng có cạnh sắc → không phải khói

            # ----- Bước 5: Hướng bay lên -----
            cx = x + w // 2
            cy = y + h // 2
            rising = self._is_rising_or_spreading(cx, cy)
            current_centroids.append((cx, cy))

            # ----- Tính score -----
            score = self._compute_score(area, e_dens, rising, frame_area)

            # Chỉ giữ nếu score đủ cao
            if score < 0.15:
                continue

            results.append((int(x), int(y), int(w), int(h), "smoke", score))

        # Cập nhật lịch sử centroid cho frame tiếp theo
        self._prev_centroids = current_centroids

        return results


# ═══════════════════════════════════════════════════════════════════════════
# Module-level stateful detector instance
# ═══════════════════════════════════════════════════════════════════════════
# Pipeline gọi  smoke_detect.detect(frame)  →  cần một hàm module-level.
# Dùng singleton SmokeDetector để giữ state giữa các frame.

_detector = SmokeDetector()


def detect(frame: np.ndarray) -> List[Tuple[int, int, int, int, str, float]]:
    """Module-level wrapper – pipeline gọi hàm này.

    Parameters
    ----------
    frame : np.ndarray
        Ảnh BGR 640×480.

    Returns
    -------
    list[tuple[int, int, int, int, str, float]]
        ``[(x, y, w, h, "smoke", score), ...]``
    """
    try:
        return _detector.detect(frame)
    except Exception as exc:
        # Không để exception làm crash pipeline; log và trả danh sách rỗng.
        print(f"[smoke_detect] Lỗi khi xử lý frame: {exc}", file=sys.stderr)
        return []


# ═══════════════════════════════════════════════════════════════════════════
# Chạy standalone – demo nhanh với webcam hoặc video
# ═══════════════════════════════════════════════════════════════════════════
if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(
        description="Smoke Detection – standalone demo (traditional CV)"
    )
    parser.add_argument(
        "--source", default="0",
        help="Webcam index (e.g. 0) hoặc đường dẫn video. Mặc định: 0",
    )
    args = parser.parse_args()

    source = int(args.source) if args.source.isdigit() else args.source
    cap = cv2.VideoCapture(source)
    if not cap.isOpened():
        print(f"[smoke_detect] Không mở được nguồn: {source!r}")
        sys.exit(1)

    print("[smoke_detect] Nhấn 'q' để thoát.")

    while True:
        ret, raw = cap.read()
        if not ret:
            print("[smoke_detect] Hết stream hoặc không đọc được frame.")
            break

        raw = cv2.resize(raw, (640, 480))
        detections = detect(raw)

        for (bx, by, bw, bh, label, score) in detections:
            cv2.rectangle(raw, (bx, by), (bx + bw, by + bh), (128, 128, 128), 2)
            cv2.putText(
                raw, f"{label} {score:.2f}",
                (bx, by - 8), cv2.FONT_HERSHEY_SIMPLEX, 0.6,
                (255, 255, 255), 2, cv2.LINE_AA,
            )

        cv2.imshow("Smoke Detection (Traditional)", raw)
        if cv2.waitKey(1) & 0xFF == ord("q"):
            break

    cap.release()
    cv2.destroyAllWindows()
    print("[smoke_detect] Đã giải phóng tài nguyên.")
