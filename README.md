# Dataset

## Mã Nguồn
https://github.com/gaiasd/DFireDataset

## Nguồn: D-Fire (Kaggle)
Link tải gốc: https://www.kaggle.com/datasets/sayedgamal99/smoke-fire-detection-yolo

## Link backup (Google Drive)
https://drive.google.com/file/d/1O6GQUslmqAfhAOgGzhH6N3nfLlUuJk7b/view?usp=drive_link


## Cấu trúc thư mục sau khi tải về

```
archive/
└── data/
    ├── train/
    │   ├── images/
    │   └── labels/
    ├── val/
    │   ├── images/
    │   └── labels/
    ├── test/
    │   ├── images/
    │   └── labels/
    └── data.yaml
```
## Hướng dẫn tải

1. Tải file `archive.zip` từ link Google Drive ở trên
2. Giải nén coppy data thư mục `data/` của project
3. Kiểm tra cấu trúc sau khi giải nén 

fire-smoke-detection/
└── data.yml
└── data/
    ├── train/           
    │   ├── images/
    │   └── labels/
    ├── val/           
    │   ├── images/
    │   └── labels/
    ├── test/            
    │   ├── images/
    │   └── labels/
    ├── data.yaml
    └── README.md
4. Mở file data.yaml (ở project root) và thay toàn bộ nội dung bằng:
## Cấu hình data.yaml
Copy từ path   đến hết ]

```yaml
# Dataset D-Fire
path: .
train: train/images
val: val/images
test: test/images

nc: 2
names: ['smoke', 'fire']
```
## Số lượng
- Train: 14.122 ảnh
- Val: 3.099 ảnh
- Test: 4.306 ảnh

## Classes
- 0: smoke
- 1: fire

## Lưu ý

- **Không commit** ảnh / video vào Git vì file khá nặng do dung lượng lớn (~3 GB, vượt giới hạn GitHub).
- Dataset đã chia sẵn train/val/test → TV4 dùng trực tiếp để train YOLO

- TV2 và TV3 lấy ảnh từ tập `test/` để đánh giá detector truyền thống.
  Tập test bao gồm cả ảnh có lửa/khói (positive) và ảnh "None" (negative).

- D-Fire có sẵn **9.838 ảnh "None"** (không lửa, không khói) dùng làm negative samples.
  Tuy nhiên, các loại nhiễu đặc thù như **áo đỏ, đèn giao thông, hoàng hôn, màn hình phát lửa**
  có thể chưa có đủ trong D-Fire →  nên tìm thêm để test báo động giả đa dạng hơn.

