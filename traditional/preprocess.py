"""Tiền xử lý ảnh cho phát hiện lửa/khói. Hàm nhận ảnh BGR và không sửa ảnh gốc.

Khung hàm của TV1: resize_frame, normalize, to_hsv, to_gray, denoise, extract_roi.
Thêm cho thí nghiệm ablation: gaussian, median, equalize_v, preprocess.
Mỗi bước có tham số 0 = tắt.
"""
import cv2
import numpy as np


def resize_frame(frame, width=640, height=480):
    return cv2.resize(frame, (width, height))


def normalize(frame):
    """Đưa giá trị pixel về [0, 1] (float32)."""
    return frame.astype(np.float32) / 255.0


def to_hsv(frame):
    return cv2.cvtColor(frame, cv2.COLOR_BGR2HSV)


def to_gray(frame):
    return cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)


def gaussian(frame, k):
    """Lọc Gaussian, k lẻ. k = 0 thì bỏ qua."""
    return cv2.GaussianBlur(frame, (k, k), 0) if k else frame


def median(frame, k):
    """Lọc Median, k lẻ. k = 0 thì bỏ qua."""
    return cv2.medianBlur(frame, k) if k else frame


def denoise(frame, k=5):
    return gaussian(frame, k)


def equalize_v(frame, clip):
    """Cân bằng sáng bằng CLAHE trên kênh V. clip = 0 thì bỏ qua."""
    if not clip:
        return frame
    hsv = to_hsv(frame)
    hsv[..., 2] = cv2.createCLAHE(clipLimit=clip, tileGridSize=(8, 8)).apply(hsv[..., 2])
    return cv2.cvtColor(hsv, cv2.COLOR_HSV2BGR)


def extract_roi(frame, bbox):
    x, y, w, h = bbox
    return frame[y:y + h, x:x + w]


def preprocess(frame, blur=0, median_k=0, clahe=0):
    """Gaussian -> Median -> CLAHE. Các tham số bằng 0 thì bước đó bị tắt."""
    return equalize_v(median(gaussian(frame, blur), median_k), clahe)