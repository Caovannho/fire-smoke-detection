"""Phát hiện lửa bằng xử lý ảnh truyền thống (rule-based).

Cách làm: ngưỡng màu HSV (cam/vàng) -> hình thái học (open/close) -> phân tích contour (diện tích, tỉ lệ)
-> chấm điểm vùng. Độ nhấp nháy (frame differencing) sẽ thêm vào FireDetector ở bước sau.

Điểm vào:
  detect_fire(frame)       trả về list (x, y, w, h, "fire", score), frame BGR 640x480
  detect                   bí danh của detect_fire (giao diện chung của nhóm, evaluate.py dùng tên này)
  classify_fire_region(roi) điểm 0..1 cho một vùng ảnh
  FireDetector             lớp bọc, dùng khi cần giữ trạng thái giữa các frame
Lọc màu chỉ dùng H và V (S tùy chọn): khảo sát cho thấy Cr/Cb không giúp thêm gì.
"""
import cv2
import numpy as np

PARAMS = dict(
    h_max=35,        # H trong [0, h_max]: cam-vàng (bỏ đoạn đỏ vòng ở H ~170-179)
    s_min=60,        # độ bão hòa tối thiểu (0 = tắt)
    v_min=200,       # độ sáng tối thiểu (loại pixel tối)
    blur=0,          # kích thước Gaussian (0 = tắt), sau này thay bằng preprocess.py
    kernel=5,        # kích thước phần tử cấu trúc cho open/close
    min_area=0.002,  # diện tích contour tối thiểu (tỉ lệ diện tích ảnh)
    max_area=0.8,    # diện tích contour tối đa
    min_ratio=0.25,  # tỉ lệ rộng/cao của bbox
    max_ratio=4.0,
    min_score=0.0,   # bỏ vùng có điểm thấp hơn mức này
)


def color_mask(frame, p):
    hsv = cv2.cvtColor(frame, cv2.COLOR_BGR2HSV)
    return cv2.inRange(hsv, np.array([0, p["s_min"], p["v_min"]]), np.array([p["h_max"], 255, 255]))


def classify_fire_region(roi, params=None):
    """Điểm 0..1 của một vùng: tỉ lệ pixel đạt màu lửa. Dùng làm score cho bbox."""
    p = {**PARAMS, **(params or {})}
    if roi.size == 0:
        return 0.0
    return cv2.countNonZero(color_mask(roi, p)) / (roi.shape[0] * roi.shape[1])


def detect_fire(frame, params=None):
    p = {**PARAMS, **(params or {})}
    if p["blur"]:
        frame = cv2.GaussianBlur(frame, (p["blur"], p["blur"]), 0)
    mask = color_mask(frame, p)

    k = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (p["kernel"], p["kernel"]))
    mask = cv2.morphologyEx(mask, cv2.MORPH_OPEN, k)
    mask = cv2.morphologyEx(mask, cv2.MORPH_CLOSE, k)

    img_area = frame.shape[0] * frame.shape[1]
    out = []
    contours, _ = cv2.findContours(mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    for c in contours:
        if not p["min_area"] * img_area <= cv2.contourArea(c) <= p["max_area"] * img_area:
            continue
        x, y, w, h = cv2.boundingRect(c)
        if not p["min_ratio"] <= w / h <= p["max_ratio"]:
            continue
        score = classify_fire_region(frame[y:y + h, x:x + w], p)
        if score >= p["min_score"]:
            out.append((x, y, w, h, "fire", float(score)))
    return out


detect = detect_fire


class FireDetector:
    """Bộ phát hiện theo từng frame. Hiện chưa lưu trạng thái; phần nhấp nháy sẽ thêm ở đây."""

    def __init__(self, params=None):
        self.params = params

    def detect(self, frame):
        return detect_fire(frame, self.params)

    __call__ = detect