# Thư mục tài nguyên âm thanh cảnh báo (Audio Assets)

Thư mục này chứa file âm thanh cảnh báo còi báo cháy (`alarm.wav`) được sử dụng bởi hệ thống `fire-smoke-detection`.

## 1. Thông số kỹ thuật của file `alarm.wav`
- **Định dạng file:** RIFF WAV (Uncompressed PCM, 16-bit signed integer, Mono).
- **Tần số lấy mẫu (Sample Rate):** 44.1 kHz.
- **Thời lượng:** ~1.5 giây (Chuỗi xung cảnh báo âm tần kép 850 Hz - 1200 Hz chuẩn còi báo động khẩn cấp ISO 7731 / NFPA 72).
- **Tương thích:** Tương thích 100% với thư viện `winsound` trên hệ điều hành Windows và các trình phát đa phương tiện chuẩn.

## 2. Nguồn gốc & Bản quyền (License)
- **Nguồn gốc:** Âm thanh còi báo cháy được tổng hợp tự động trực tiếp bằng thuật toán dao động điều hòa (Digital Signal Synthesis) thông qua thư viện chuẩn `wave` và `math` của Python.
- **Bản quyền (License):** **Public Domain / MIT License**.
- **Quyền sử dụng:** Hoàn toàn miễn phí, được phép sử dụng, phân phối, chỉnh sửa và đóng gói trong đồ án môn học hoặc ứng dụng thực tế mà không vi phạm bản quyền.
