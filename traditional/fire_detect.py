"""Phát hiện lửa bằng xử lý ảnh truyền thống (rule-based).

Cách làm: ngưỡng màu HSV (cam/vàng, tùy chọn thêm lõi trắng sáng có quầng cam) -> hình thái học (open/close)
-> phân tích contour (diện tích, tỉ lệ) -> chấm điểm vùng. Độ nhấp nháy sẽ thêm vào FireDetector ở bước sau.

Điểm vào:
  detect_fire(frame)        trả về list (x, y, w, h, "fire", score), frame BGR 640x480
  detect                    bí danh của detect_fire (giao diện chung của nhóm, evaluate.py dùng tên này)
  classify_fire_region(roi) điểm 0..1 cho một vùng ảnh
  FireDetector              lớp bọc, dùng khi cần giữ trạng thái giữa các frame
Lọc màu chỉ dùng H và V (S tùy chọn): khảo sát cho thấy Cr/Cb không giúp thêm gì.
"""
import cv2
import numpy as np
from traditional.preprocess import preprocess

PARAMS = dict(
    h_max=35,        # H trong [0, h_max]: cam-vàng (bỏ đoạn đỏ vòng ở H ~170-179)
    s_min=60,        # độ bão hòa tối thiểu (0 = tắt)
    v_min=200,       # độ sáng tối thiểu (loại pixel tối)
    white_v=245,       # 0 = tắt. >0: nhận thêm pixel rất sáng (V >= white_v), S thấp, nếu có quầng cam gần đó
    halo_v=100,      # độ sáng tối thiểu của quầng cam
    halo_r=15,       # bán kính (pixel) tìm quầng cam quanh lõi trắng
    blur=0,          # Gaussian (0 = tắt)
    median=0,        # Median (0 = tắt)
    clahe=0,         # cân bằng sáng CLAHE trên kênh V (0 = tắt)
    open_k=5,        # phần tử cấu trúc cho open (1 = tắt)
    close_k=5,       # phần tử cấu trúc cho close
    min_area=0.002,  # diện tích contour tối thiểu (tỉ lệ diện tích ảnh)
    max_area=0.8,    # diện tích contour tối đa
    min_ratio=0.25,  # tỉ lệ rộng/cao của bbox
    max_ratio=4.0,
    min_score=0.0,   # bỏ vùng có điểm thấp hơn mức này
    h_min_red=180,   # 180 = tắt. Nhỏ hơn 180: thêm dải đỏ H trong [h_min_red, 179]
)


def color_mask(frame, p):
    hsv = cv2.cvtColor(frame, cv2.COLOR_BGR2HSV)
    mask = cv2.inRange(hsv, np.array([0, p["s_min"], p["v_min"]]), np.array([p["h_max"], 255, 255]))
    if p["h_min_red"] < 180:
        red = cv2.inRange(hsv, np.array([p["h_min_red"], p["s_min"], p["v_min"]]), np.array([179, 255, 255]))
        mask = cv2.bitwise_or(mask, red)
    if p["white_v"]:
        core = cv2.inRange(hsv, np.array([0, 0, p["white_v"]]), np.array([179, max(p["s_min"] - 1, 0), 255]))
        halo = cv2.inRange(hsv, np.array([0, p["s_min"], p["halo_v"]]), np.array([p["h_max"], 255, 255]))
        r = 2 * p["halo_r"] + 1
        halo = cv2.dilate(halo, cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (r, r)))
        mask = cv2.bitwise_or(mask, cv2.bitwise_and(core, halo))
    return mask


def classify_fire_region(roi, params=None):
    """Điểm 0..1 của một vùng: tỉ lệ pixel đạt màu lửa. Dùng làm score cho bbox."""
    p = {**PARAMS, **(params or {})}
    if roi.size == 0:
        return 0.0
    return cv2.countNonZero(color_mask(roi, p)) / (roi.shape[0] * roi.shape[1])


def detect_fire(frame, params=None):
    p = {**PARAMS, **(params or {})}
    frame = preprocess(frame, p["blur"], p["median"], p["clahe"])
    mask = color_mask(frame, p)

    ko = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (p["open_k"], p["open_k"]))
    kc = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (p["close_k"], p["close_k"]))
    mask = cv2.morphologyEx(mask, cv2.MORPH_OPEN, ko)
    mask = cv2.morphologyEx(mask, cv2.MORPH_CLOSE, kc)

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
    """Bộ phát hiện giữ trạng thái giữa các frame (video, camera cố định).

    flicker_min = 0 (mặc định): không lọc, kết quả y hệt detect_fire.
    flicker_min > 0: sau `warmup` frame, bỏ vùng có độ nhấp nháy thấp hơn ngưỡng.
    Độ nhấp nháy của vùng = tỉ lệ pixel trong bbox mà mặt nạ màu đổi giữa hai frame liền nhau,
    lấy trung bình trượt với hệ số alpha.
    """

    def __init__(self, params=None, flicker_min=0.0, warmup=5, alpha=0.3):
        self.params = params
        self.flicker_min = flicker_min
        self.warmup = warmup
        self.alpha = alpha
        self.reset()

    def reset(self):
        """Gọi khi đổi nguồn video."""
        self.prev = None
        self.act = None
        self.n = 0

    def flicker(self, box):
        if self.act is None:
            return 0.0
        x, y, w, h = box[:4]
        return float(self.act[y:y + h, x:x + w].mean())

    def detect(self, frame):
        p = {**PARAMS, **(self.params or {})}
        dets = detect_fire(frame, self.params)
        mask = color_mask(preprocess(frame, p["blur"], p["median"], p["clahe"]), p)
        if self.prev is not None and self.prev.shape != mask.shape:
            self.reset()
        if self.prev is not None:
            change = cv2.bitwise_xor(mask, self.prev).astype(np.float32) / 255.0
            self.act = change if self.act is None else (1 - self.alpha) * self.act + self.alpha * change
        self.prev = mask
        self.n += 1
        if self.flicker_min <= 0 or self.n <= self.warmup:
            return dets
        return [d for d in dets if self.flicker(d) >= self.flicker_min]

    __call__ = detect