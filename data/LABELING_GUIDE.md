# 🏷️ HƯỚNG DẪN GÁN NHÃN DỮ LIỆU – DỰ ÁN PHÁT HIỆN LỬA & KHÓI
**Người phụ trách / Điều phối:** TV4 (YOLO & Dữ liệu)  
**Áp dụng cho:** Toàn bộ thành viên nhóm (TV1, TV2, TV3, TV4)

---

## 1. Mục tiêu & Phân chia công việc gán nhãn

Mặc dù nhóm đã sử dụng tập dữ liệu **D-Fire** (~21.000 ảnh đã chia sẵn train/val/test), cả nhóm vẫn cần:
1. **Kiểm tra và chuẩn hóa nhãn** nếu bổ sung thêm ảnh thực tế từ camera trường/nhà, video YouTube.
2. **Gán nhãn tập ảnh nhiễu (Negative samples)**: áo đỏ, đèn đường, hoàng hôn, khói xe, sương mù, mây trắng để kiểm thử tỷ lệ báo động giả (False Alarm Rate).
3. **Phân chia khối lượng gán nhãn bổ sung:** Mỗi thành viên phụ trách **1/4 số lượng ảnh** được thu thập thêm.

---

## 2. Quy định Classes & Định dạng nhãn (YOLO Format)

Dự án thống nhất sử dụng chuẩn nhãn **YOLO Text Format**:

### 2.1. Bảng ID Lớp (Classes ID)
| Class ID | Tên Lớp (`label`) | Mô tả |
| :---: | :---: | :--- |
| **`0`** | `smoke` | Vùng khói (khói trắng, khói xám, khói đen bốc lên) |
| **`1`** | `fire` | Vùng ngọn lửa (lửa đỏ, cam, vàng, ánh lửa bốc cháy) |

> ⚠️ **Cực kỳ quan trọng:** Thứ tự class phải đúng tuyệt đối: `0 = smoke`, `1 = fire` (khớp với file `data.yaml` của project).

### 2.2. Định dạng file nhãn `.txt`
Mỗi ảnh `image_name.jpg` sẽ có một file nhãn tương ứng `image_name.txt` cùng tên nằm trong thư mục `labels/`.
Mỗi dòng đại diện cho một bounding box với 5 giá trị:
```text
<class_id> <x_center> <y_center> <width> <height>
```
- Các tọa độ đều được **chuẩn hóa trong khoảng [0.0, 1.0]** tương đối so với kích thước ảnh:
  - `x_center = x_tam / image_width`
  - `y_center = y_tam / image_height`
  - `width = box_width / image_width`
  - `height = box_height / image_height`

### 2.3. Quy ước ảnh không có lửa/khói (Negative Samples / Ảnh nhiễu)
- Nếu ảnh **không chứa lửa và không chứa khói** (ví dụ: ảnh người mặc áo đỏ, đèn giao thông, phòng học bình thường):
  - **BẮT BUỘC tạo file nhãn `.txt` rỗng (dung lượng 0 KB)**.
  - **KHÔNG ĐƯỢC XÓA FILE NHÃN**: YOLO cần file nhãn rỗng để hiểu rằng ảnh này là ảnh âm tính, từ đó học cách không bắt nhầm nhiễu.

---

## 3. Quy tắc vẽ Bounding Box (Bounding Box Guidelines)

1. **Bao bọc sát đối tượng:**
   - Kéo khung vừa khít ngọn lửa hoặc đám khói. Không vẽ quá rộng ôm cả vùng nền không liên quan.
   - Không cắt cụt ngọn lửa.
2. **Xử lý khói phân tán:**
   - Khói có đặc tính mờ viền và lan tỏa. Vẽ bao quanh vùng khói có mật độ nhìn thấy rõ ràng. Nếu đám khói quá loãng hòa vào mây thì chỉ vẽ phần lõi khói dày đặc.
3. **Lửa và Khói xuất hiện cùng nhau:**
   - Vẽ 2 bounding box riêng biệt: 1 box cho ngọn lửa (class 1) và 1 box cho đám khói phía trên (class 0). Nếu chúng đè lên nhau, cho phép 2 box chồng lấn (overlap).
4. **Đối tượng kích thước quá nhỏ:**
   - Ngọn lửa/tàn lửa nhỏ hơn 10x10 pixel có thể bỏ qua nếu quá mờ nhạt để tránh gây nhiễu cho mô hình.

---

## 4. Công cụ gán nhãn khuyến nghị

### Cách 1: Sử dụng Roboflow (Khuyến nghị cho làm việc nhóm trực tuyến)
1. TV4 tạo Project trên [Roboflow](https://roboflow.com/) và gửi link mời nhóm vào workspace.
2. Cài đặt 2 class: `smoke` (0), `fire` (1).
3. Các thành viên đăng nhập, vào mục Assign Images để gán nhãn phần ảnh được giao.
4. Export định dạng: **YOLOv8 PyTorch**.

### Cách 2: Sử dụng phần mềm offline (LabelImg / AnyLabeling)
- Cài đặt nhanh bằng python:
  ```bash
  pip install labelImg
  labelImg
  ```
- Chọn **Open Dir** trỏ vào thư mục ảnh.
- Chọn **Change Save Dir** trỏ vào thư mục `labels`.
- Chuyển chế độ lưu sang **YOLO** (thay vì PascalVOC).
- Thêm file `classes.txt` gồm 2 dòng:
  ```text
  smoke
  fire
  ```

---

## 5. Quy trình nộp nhãn và ghép dữ liệu
1. Mỗi thành viên sau khi gán nhãn xong nén thư mục ảnh và nhãn của mình gửi cho TV4.
2. TV4 chạy script kiểm tra định dạng nhãn (`test_labels.py`) để đảm bảo không có class ID sai (ngoài 0 và 1) và không có tọa độ vượt quá [0, 1].
3. TV4 tổng hợp vào tập `data/` chính thức của dự án.
