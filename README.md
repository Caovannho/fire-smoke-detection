# 🔥 Fire & Smoke Detection

Hệ thống phát hiện lửa và khói theo thời gian thực kết hợp hai phương pháp:
- **Traditional CV** – Phân tích màu sắc HSV, optical flow, phân tích contour
- **YOLO (Deep Learning)** – Mô hình YOLOv8/v11 được fine-tune trên tập dữ liệu lửa/khói

---

## 📁 Cấu trúc project

```
fire-smoke-detection/
├── data/
│   ├── fire/          # Ảnh/video chứa lửa (không commit)
│   ├── smoke/         # Ảnh/video chứa khói (không commit)
│   ├── noise/         # Ảnh nền / false-positive samples
│   └── videos/        # Video test đầu vào
├── traditional/       # Module phát hiện truyền thống
│   ├── preprocess.py  # Tiền xử lý ảnh
│   ├── fire_detect.py # Phát hiện lửa bằng HSV + contour
│   └── smoke_detect.py# Phát hiện khói bằng optical flow
├── yolo/              # Module YOLO deep learning
│   ├── yolo_detect.py # Wrapper Ultralytics YOLOv8
│   └── weights/       # Trọng số mô hình .pt (không commit)
├── eval/
│   └── evaluate.py    # Tính Precision, Recall, F1, mAP, FPS
├── gui/
│   ├── app.py         # Giao diện Tkinter hiển thị video
│   └── alert.py       # Hệ thống cảnh báo (âm thanh, log)
├── pipeline.py        # Entry point chạy toàn bộ pipeline
├── config.py          # Cấu hình toàn cục (kích thước, ngưỡng…)
├── requirements.txt
└── README.md
```

---

## ⚙️ Cài đặt môi trường

### Yêu cầu
- Python ≥ 3.9
- CUDA (khuyến nghị) hoặc CPU

### Các bước

```bash
# 1. Clone repository
git clone https://github.com/<your-org>/fire-smoke-detection.git
cd fire-smoke-detection

# 2. Tạo và kích hoạt virtual environment
python -m venv venv

# Windows
venv\Scripts\activate
# macOS / Linux
source venv/bin/activate

# 3. Cài đặt dependencies
pip install -r requirements.txt

# 4. (Tùy chọn) Tải trọng số YOLO về thư mục yolo/weights/
#    Ví dụ: yolov8n.pt từ Ultralytics, hoặc model đã fine-tune
```

---

## 🚀 Sử dụng

```bash
# Chạy với YOLO + webcam mặc định
python pipeline.py --mode yolo --source 0

# Chạy với phương pháp truyền thống trên video
python pipeline.py --mode traditional --source data/videos/test.mp4

# Chạy headless (không hiển thị cửa sổ) và lưu kết quả
python pipeline.py --mode yolo --source 0 --no-gui --save
```

---

## 📊 Đánh giá

```bash
python -m eval.evaluate --method yolo --dataset data/
```

Kết quả xuất ra console và file `outputs/metrics.csv`.

---

## 👥 Phân công thành viên

| Thành viên | Module phụ trách | Nhiệm vụ chính |
|---|---|---|
| **TV1** | `traditional/preprocess.py` & `traditional/fire_detect.py` | Xây dựng bộ tiền xử lý ảnh và thuật toán phát hiện lửa truyền thống (HSV, morphology, contour) |
| **TV2** | `traditional/smoke_detect.py` & `config.py` | Thuật toán phát hiện khói (optical flow, background subtraction) và quản lý tham số cấu hình |
| **TV3** | `yolo/yolo_detect.py` & `yolo/weights/` | Tích hợp Ultralytics YOLOv8, fine-tune mô hình, quản lý trọng số |
| **TV4** | `gui/app.py`, `gui/alert.py`, `eval/evaluate.py`, `pipeline.py` | Giao diện GUI, hệ thống cảnh báo, pipeline tích hợp và module đánh giá hiệu suất |

---

## 🔧 Cấu hình chính (`config.py`)

| Tham số | Giá trị mặc định | Mô tả |
|---|---|---|
| `FRAME_WIDTH` | `640` | Chiều rộng frame xử lý |
| `FRAME_HEIGHT` | `480` | Chiều cao frame xử lý |
| `LABELS` | `["fire", "smoke"]` | Nhãn phát hiện |
| `CONF_THRESHOLD` | `0.45` | Ngưỡng confidence YOLO |
| `IOU_THRESHOLD` | `0.45` | Ngưỡng IoU cho NMS |

---

## 📌 Lưu ý

- Thư mục `data/` và file `*.pt`, `*.mp4`, `*.jpg` **không được commit** (xem `.gitignore`).
- Đặt file ảnh/video test vào đúng thư mục `data/` tương ứng trước khi chạy.
- Mỗi thành viên tạo branch riêng theo quy ước: `feature/ten-module`.

---

## 📄 License

MIT License

