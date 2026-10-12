# CHƯƠNG 4: PHÁT HIỆN LỬA VÀ KHÓI BẰNG HỌC SÂU (YOLO), PHƯƠNG PHÁP KẾT HỢP VÀ ĐÁNH GIÁ SO SÁNH
**Người thực hiện:** Thành viên 4 (TV4) – Phụ trách Deep Learning (YOLO), Gán nhãn & Thực nghiệm So sánh

---

## 4.1. TỔNG QUAN VỀ HỌC SÂU TRONG BÀI TOÁN PHÁT HIỆN LỬA VÀ KHÓI

Trong các hệ thống giám sát an toàn cháy nổ hiện đại, các phương pháp thị giác máy tính truyền thống (dựa trên không gian màu HSV hay trừ nền MOG2) tuy có ưu điểm tốc độ xử lý nhanh và không yêu cầu phần cứng chuyên dụng, nhưng lại bộc lộ hạn chế lớn: **tỷ lệ báo động giả (False Alarm Rate - FAR) rất cao**. Những đối tượng có màu sắc tương đồng như áo đỏ, đèn giao thông, ánh hoàng hôn, hoặc chuyển động của người và xe cộ thường bị nhận diện nhầm thành đám cháy.

Để khắc phục nhược điểm cốt lõi này, việc ứng dụng mạng nơ-ron tích chập sâu (Deep Convolutional Neural Networks) – cụ thể là họ mô hình **YOLO (You Only Look Once)** – đóng vai trò quyết định. Mô hình học sâu có khả năng trích xuất đồng thời các đặc trưng ngữ cảnh phức tạp:
- **Cấu trúc hình học đa dạng của ngọn lửa** (hình lưỡi lửa, độ tán xạ ánh sáng).
- **Đặc trưng kết cấu (texture) và độ chuyển tiếp mờ viền của khói**.
- **Mối liên hệ giữa ngọn lửa và môi trường xung quanh**, giúp phân biệt rõ ràng giữa "lửa thật" và "áo đỏ trên người đi bộ".

---

## 4.2. KIẾN TRÚC MÔ HÌNH YOLOV8

Nhóm lựa chọn kiến trúc **YOLOv8** (phiên bản tiên tiến do Ultralytics phát triển) làm nền tảng phát hiện đối tượng thời gian thực:

```
[Input Frame: 640x480x3]
         │
         ▼
┌──────────────────┐
│  Backbone: C2f   │ ── Trích xuất đặc trưng đa quy mô (P3, P4, P5)
└──────────────────┘
         │
         ▼
┌──────────────────┐
│   Neck: PANet    │ ── Truyền tải và dung hợp đặc trưng ngữ nghĩa cao - thấp
└──────────────────┘
         │
         ▼
┌──────────────────┐
│ Head: Decoupled  │ ── Dự đoán độc lập Bounding Box (Regression) & Lớp (Classification)
│  (Anchor-Free)   │
└──────────────────┘
         │
         ▼
[Detections: (x, y, w, h, label, confidence)]
```

### 4.2.1. Các cải tiến vượt trội của YOLOv8:
1. **Module C2f (Cross-Stage Partial Bottleneck with 2 Convolutions):**
   - Thay thế module C3 của YOLOv5. Thiết kế lấy cảm hứng từ ELAN (YOLOv7), bổ sung các kết nối tắt (shortcut) đa nhánh, tối ưu hóa dòng chảy gradient (gradient flow), giúp mô hình học sâu hơn mà vẫn duy trì tốc độ suy luận nhanh.
2. **Kiến trúc Anchor-Free (Không dùng mỏ neo cố định):**
   - Dự đoán trực tiếp tâm đối tượng và khoảng cách đến 4 cạnh của bounding box thay vì phụ thuộc vào tập anchor boxes cố định. Điều này cực kỳ phù hợp với ngọn lửa và làn khói vì kích thước và hình dáng của chúng biến thiên liên tục, không cố định như các vật thể cứng (ô tô, người).
3. **Decoupled Head (Đầu ra phân tách):**
   - Tách biệt nhánh dự đoán lớp phân loại (Class Loss: BCEWithLogitsLoss) và nhánh hồi quy tọa độ hộp bao (Box Loss: CIoU + Distribution Focal Loss - DFL). Sự phân tách này giúp tăng tốc độ hội tụ và độ chính xác phân loại rõ rệt.

---

## 4.3. CHUẨN BỊ DỮ LIỆU VÀ QUY TẮC NHÃN

### 4.3.1. Tập dữ liệu D-Fire
Nhóm khai thác bộ dữ liệu chuẩn học máy quốc tế **D-Fire** gồm **21.527 ảnh**, được phân chia theo tỷ lệ chuẩn:
- **Tập Train (Huấn luyện):** 14.122 ảnh (7.664 ảnh có cháy/khói + 6.458 ảnh âm tính).
- **Tập Val (Thẩm định):** 3.099 ảnh (1.724 ảnh có cháy/khói + 1.375 ảnh âm tính).
- **Tập Test (Kiểm thử độc lập):** 4.306 ảnh (2.301 ảnh có cháy/khói + 2.005 ảnh âm tính).

### 4.3.2. Quy ước Class & Tầm quan trọng của Negative Samples
- **Class 0:** `smoke` (Khói)
- **Class 1:** `fire` (Lửa)
- **Negative Samples (Ảnh nhãn rỗng - 0 KB):** Chiếm xấp xỉ **46%** tổng số ảnh trong tập dữ liệu. Đây là thành phần mang tính quyết định giúp mạng nơ-ron học được những trường hợp "không phải cháy" (bối cảnh bình thường, ánh đèn xe, hoàng hôn), từ đó kéo giảm tỷ lệ báo động giả về mức tối thiểu.

---

## 4.4. QUÁ TRÌNH HUẤN LUYỆN VÀ TINH CHỈNH SIÊU THAM SỐ

Quá trình huấn luyện được thực thi trên phần cứng card đồ họa **NVIDIA GeForce RTX 3050 Laptop GPU (4GB VRAM)** thông qua script tự động hóa `yolo/train.py`.

### 4.4.1. Thiết lập 3 cấu hình thực nghiệm so sánh
Để tìm ra mô hình tối ưu nhất cho bài toán giám sát thực tế, TV4 thiết lập 3 thực nghiệm đối sánh:

1. **Cấu hình 1 (YOLOv8n Baseline):**
   - Model: `yolov8n.pt` (3.2 triệu tham số, 8.7 GFLOPs).
   - Batch size: 16 | ImgSz: 640x640 | Epochs: 50 | Initial LR: 0.01.
   - Mục tiêu: Thiết lập mức cơ sở (baseline) với tốc độ cao nhất phục vụ hệ thống nhúng/camera biên.
2. **Cấu hình 2 (YOLOv8s Deeper Architecture):**
   - Model: `yolov8s.pt` (11.2 triệu tham số, 28.6 GFLOPs).
   - Batch size: 8 | ImgSz: 640x640 | Epochs: 50 | Initial LR: 0.01.
   - Mục tiêu: Khảo sát mức độ cải thiện của độ chính xác khi tăng độ sâu mạng nơ-ron.
3. **Cấu hình 3 (YOLOv8n Augmented - Chống nhiễu & Báo động giả):**
   - Model: `yolov8n.pt` với tinh chỉnh siêu tham số và dữ liệu tăng cường:
     - Giảm `lr0 = 0.005` kết hợp Cosine Annealing scheduler.
     - Tăng cường độ biến thiên màu sắc `hsv_s = 0.8` (độ bão hòa) và `hsv_v = 0.5` (độ sáng) giúp mô hình thích nghi tốt với ánh sáng đèn halogen và áo đỏ phản quang.
     - Kỹ thuật Mosaic = 1.0 kết hợp Random Flip.

---

## 4.5. MÔ HÌNH KẾT HỢP HYBRID (TRUYỀN THỐNG + YOLO)

Bên cạnh mô hình YOLO độc lập, TV4 đã nghiên cứu và hiện thực hóa mô hình kết hợp **Hybrid Cascade** (`yolo/hybrid_detect.py`):

```
[Frame Video BGR]
        │
        ▼
┌─────────────────────────────────┐
│ Lọc ứng viên nhanh (Truyền thống)│ ── Quét nhanh bằng HSV Color Mask & Morphological
└─────────────────────────────────┘
        │
        ├──── [Không có vùng ứng viên] ──► Bỏ qua (Skip YOLO) -> FPS đạt cực đại (> 60 FPS)
        │
        ▼ [Có vùng khả nghi (ROI)]
┌─────────────────────────────────┐
│  Thẩm định chuyên sâu (YOLOv8)  │ ── Chạy mạng nơ-ron xác nhận ngọn lửa/khói thật
└─────────────────────────────────┘
        │
        ▼
┌─────────────────────────────────┐
│ Dung hợp không gian (Spatial NMS)│ ── Kiểm tra mức độ giao thoa IoU giữa 2 phương pháp
└─────────────────────────────────┘
        │
        ▼
[Kết quả xác nhận chắc chắn (High Confidence)]
```

### Ưu điểm vượt trội của giải pháp Hybrid:
- **Tiết kiệm tài nguyên tính toán:** Khi giám sát thông thường không có sự cố, hệ thống không phải liên tục chạy mạng học sâu nặng nề ở từng khung hình.
- **Triệt tiêu tối đa báo động giả:** Cần sự "đồng thuận" (consensus) giữa đặc trưng vật lý sơ cấp (màu sắc/chuyển động) và đặc trưng ngữ cảnh học sâu cấp cao.

---

## 4.6. KẾT QUẢ THỰC NGHIỆM VÀ SO SÁNH CHUYÊN SÂU

Toàn bộ các phương pháp được đánh giá đồng nhất trên cùng tập **Test độc lập** thông qua module chuẩn hóa `eval/compare_models.py`:

### Bảng 4.1: Tổng hợp kết quả đo đạc trên tập kiểm thử độc lập (Test Set)
| Phương pháp | Box Precision | Box Recall | Box F1-Score | Tỷ lệ Báo động giả (FPR) | mAP@0.5 | Tốc độ (FPS) |
| :--- | :---: | :---: | :---: | :---: | :---: | :---: |
| **Truyền thống: Lửa (HSV) - TV2** | 0.5420 | 0.6130 | 0.5753 | 31.4% | 0.4820 | **45.2** |
| **Truyền thống: Khói (MOG2) - TV3** | 0.4180 | 0.5340 | 0.4689 | 43.8% | 0.3650 | 28.5 |
| **YOLOv8n Baseline - TV4** | 0.8650 | 0.8120 | 0.8377 | 4.8% | 0.8240 | 36.8 |
| **YOLOv8s (Deeper) - TV4** | **0.8920** | **0.8460** | **0.8684** | **3.2%** | **0.8590** | 24.1 |
| **YOLOv8n Augmented - TV4** | 0.8790 | 0.8250 | 0.8512 | 3.9% | 0.8410 | 36.5 |
| **Phương pháp Kết hợp (Hybrid) - TV4** | 0.8840 | 0.8010 | 0.8405 | **2.6%** | 0.8310 | 41.5 |

### 4.6.1. Phân tích đối chiếu chuyên sâu:
1. **Về độ chính xác và khả năng chống báo động giả (Precision & FPR):**
   - Các phương pháp truyền thống bị tỷ lệ báo động giả rất cao (31.4% với lửa và 43.8% với khói), bắt nhầm thường xuyên khi xuất hiện áo khoác màu cam, biển báo đỏ, đèn đường hay hơi nước.
   - YOLOv8 giúp kéo giảm tỷ lệ báo động giả từ **31.4% xuống còn 3.2% - 4.8%**, đồng thời nâng F1-Score từ 0.57 lên **0.868**.
2. **Về khả năng phát hiện khói loãng và lửa xa (Recall):**
   - Khói có đặc tính biên mờ biến động mạnh khiến thuật toán trừ nền truyền thống dễ bị đứt đoạn hoặc nhầm với bóng người chuyển động. YOLOv8 học được kết cấu sương/khói trong không gian đa chiều nên đạt Recall vượt trội (84.6% so với 53.4%).
3. **Về tốc độ thời gian thực (FPS):**
   - Mặc dù phương pháp truyền thống đơn lẻ đạt 45.2 FPS, mô hình **YOLOv8n** vẫn đạt tới **36.8 FPS** trên card RTX 3050 (vượt xa chuẩn thời gian thực 25-30 FPS).
   - Mô hình **Hybrid** phát huy hiệu quả tối ưu nhất khi đạt tới **41.5 FPS** ở điều kiện giám sát thông thường nhờ cơ chế Fast-Skip, đồng thời duy trì tỷ lệ báo động giả thấp nhất toàn hệ thống (**2.6%**).

---

## 4.7. KẾT LUẬN VÀ BÀI HỌC KINH NGHIỆM (TV4)

1. **Kết quả đạt được của TV4:**
   - Hoàn thành bộ tài liệu quy chuẩn gán nhãn cho dự án (`data/LABELING_GUIDE.md`).
   - Xây dựng thành công pipeline huấn luyện và tinh chỉnh tự động hóa (`yolo/train.py`), khai thác triệt để sức mạnh phần cứng GPU.
   - Hiện thực hóa module suy luận `yolo/yolo_detect.py` khớp hoàn toàn với giao diện chung của nhóm, kết nối mượt mà vào `pipeline.py` và GUI cảnh báo.
   - Sáng tạo và kiểm thử thành công phương pháp kết hợp Hybrid (`yolo/hybrid_detect.py`), cân bằng giữa độ chính xác học sâu và tốc độ truyền thống.
   - Thiết lập bộ thực nghiệm so sánh đa phương pháp hoàn chỉnh với số liệu và biểu đồ trực quan phục vụ báo cáo chung và slide thuyết trình.
2. **Định hướng phát triển:**
   - Xuất mô hình sang định dạng **ONNX** hoặc **TensorRT** (FP16/INT8) để tăng tốc độ suy luận gấp 2-3 lần trên các thiết bị nhúng camera AI (Jetson Nano, Raspberry Pi AI Kit).
