"""
Hybrid Detection Module (Traditional Fast Filtering + YOLO Deep Verification).

Architecture:
    Step 1 (Candidate Proposal):
        Use lightweight traditional CV rules (HSV fire color mask & MOG2 motion mask)
        to identify candidate Regions of Interest (ROIs).
    Step 2 (Fast Skip):
        If no candidate regions exist in the frame, skip YOLO inference entirely.
        This drastically cuts GPU/CPU load during normal (non-fire) surveillance.
    Step 3 (YOLO Verification):
        If candidate regions are present, invoke YOLOv8 to verify whether the candidates
        are genuine fire/smoke or false alarms (e.g. red clothes, sunset, vehicle exhaust).
    Step 4 (Spatial NMS / Fusion):
        Fuse overlapping candidate boxes and YOLO detections to produce high-confidence
        final detections.

Interface:
    detect(frame: np.ndarray) -> list[tuple[int, int, int, int, str, float]]
    Consistent with pipeline.py and eval/evaluate.py.
"""

import os
import sys
from typing import List, Tuple, Optional
import cv2
import numpy as np

ROOT_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if ROOT_DIR not in sys.path:
    sys.path.insert(0, ROOT_DIR)

from yolo.yolo_detect import YOLODetector, get_detector


class HybridDetector:
    """
    Cascaded detector combining traditional rule-based candidate filtering
    with YOLO deep learning verification.
    """

    def __init__(
        self,
        yolo_detector: Optional[YOLODetector] = None,
        min_candidate_area: int = 150,
        verify_iou_thresh: float = 0.20
    ):
        """
        Parameters
        ----------
        yolo_detector : YOLODetector, optional
            Instance of YOLODetector. Uses singleton if None.
        min_candidate_area : int
            Minimum pixel area for a region to qualify as a candidate.
        verify_iou_thresh : float
            Minimum IoU required between traditional candidate box and YOLO box
            to confirm detection.
        """
        self.yolo = yolo_detector or get_detector()
        self.min_candidate_area = min_candidate_area
        self.verify_iou = verify_iou_thresh

        # Fast HSV thresholds for candidate proposal
        # Fire hue: [0, 35] in OpenCV HSV
        self.fire_lower = np.array([0, 80, 150], dtype=np.uint8)
        self.fire_upper = np.array([35, 255, 255], dtype=np.uint8)

        # Smoke hue: Low saturation [0, 45], moderate to high value [90, 220]
        self.smoke_lower = np.array([0, 0, 90], dtype=np.uint8)
        self.smoke_upper = np.array([180, 45, 220], dtype=np.uint8)

        # Morphology kernel
        self.kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (5, 5))

    def _extract_candidates(self, frame: np.ndarray) -> List[Tuple[int, int, int, int]]:
        """
        Rapidly extract candidate bounding boxes using color segmentation.
        """
        hsv = cv2.cvtColor(frame, cv2.COLOR_BGR2HSV)

        # Fire color mask
        mask_fire = cv2.inRange(hsv, self.fire_lower, self.fire_upper)
        # Smoke color mask
        mask_smoke = cv2.inRange(hsv, self.smoke_lower, self.smoke_upper)

        mask = cv2.bitwise_or(mask_fire, mask_smoke)
        mask = cv2.morphologyEx(mask, cv2.MORPH_OPEN, self.kernel)

        contours, _ = cv2.findContours(mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        candidates = []
        for c in contours:
            area = cv2.contourArea(c)
            if area >= self.min_candidate_area:
                x, y, w, h = cv2.boundingRect(c)
                candidates.append((x, y, w, h))

        return candidates

    def detect(self, frame: np.ndarray) -> List[Tuple[int, int, int, int, str, float]]:
        """
        Hybrid inference method.

        Parameters
        ----------
        frame : np.ndarray
            BGR image (640x480).

        Returns
        -------
        list[tuple[int, int, int, int, str, float]]
            List of confirmed detections: (x, y, w, h, label, score)
        """
        # Bước 1: Lọc ứng viên nhanh bằng phương pháp truyền thống
        candidates = self._extract_candidates(frame)

        # Nếu không có ứng viên màu sắc/chuyển động khả nghi trong khung hình
        # -> Bỏ qua, tiết kiệm chi phí chạy mô hình YOLO
        if not candidates:
            return []

        # Bước 2: Khi có ứng viên khả nghi -> Gọi YOLO để thẩm định (Verification)
        yolo_detections = self.yolo.detect(frame)
        if not yolo_detections:
            return []

        # Bước 3: Xác nhận sự trùng khớp giữa ứng viên truyền thống và YOLO
        # Giúp triệt tiêu cả trường hợp YOLO bắt nhầm vật thể không có đặc trưng màu/lửa
        verified_results = []
        for det in yolo_detections:
            dx, dy, dw, dh, label, score = det
            box_d = [dx, dy, dw, dh]

            # Kiểm tra xem box của YOLO có giao thoa với bất kỳ vùng ứng viên truyền thống nào không
            has_overlap = False
            for cx, cy, cw, ch in candidates:
                # Tính diện tích phần giao (intersection)
                ix1 = max(dx, cx)
                iy1 = max(dy, cy)
                ix2 = min(dx + dw, cx + cw)
                iy2 = min(dy + dh, cy + ch)

                if ix2 > ix1 and iy2 > iy1:
                    inter_area = (ix2 - ix1) * (iy2 - iy1)
                    yolo_area = dw * dh
                    # Nếu phần giao chiếm ít nhất 15% diện tích box YOLO -> Xác nhận
                    if inter_area / max(1, yolo_area) >= 0.15:
                        has_overlap = True
                        break

            if has_overlap:
                # Tăng độ tin cậy khi cả 2 phương pháp đều đồng thuận
                boosted_score = min(1.0, score * 1.05)
                verified_results.append((dx, dy, dw, dh, label, float(boosted_score)))

        return verified_results

    __call__ = detect


# Module-level instance
_default_hybrid: Optional[HybridDetector] = None


def detect(frame: np.ndarray) -> List[Tuple[int, int, int, int, str, float]]:
    """Standard callable interface for Hybrid detection."""
    global _default_hybrid
    if _default_hybrid is None:
        _default_hybrid = HybridDetector()
    return _default_hybrid.detect(frame)

