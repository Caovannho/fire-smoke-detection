# TÀI LIỆU THAM KHẢO
[1] Nhóm thực hiện. Fire Smoke Detection from Camera. Repository Caovannho/fire-smoke-detection, commit 40ea155fb9ecab6bcfb97b04cebab6d6c0a4dd0b, ngày 26/10/2026. Mã nguồn pipeline.py, gui, traditional, yolo, eval và config.py. https://github.com/Caovannho/fire-smoke-detection/tree/40ea155fb9ecab6bcfb97b04cebab6d6c0a4dd0b
[2] OpenCV. Changing Colorspaces. Tài liệu OpenCV 4.x. Truy cập ngày 26/10/2026. https://docs.opencv.org/4.x/df/d9d/tutorial_py_colorspaces.html
[3] OpenCV. Morphological Transformations. Tài liệu OpenCV 4.x. Truy cập ngày 26/10/2026. https://docs.opencv.org/4.x/d9/d61/tutorial_py_morphological_ops.html
[4] OpenCV. How to Use Background Subtraction Methods. Tài liệu OpenCV 4.x. Truy cập ngày 26/10/2026. https://docs.opencv.org/4.x/d1/dc5/tutorial_background_subtraction.html
[5] Redmon, J., Divvala, S., Girshick, R. và Farhadi, A. You Only Look Once Unified Real Time Object Detection. CVPR 2016; bản arXiv:1506.02640. https://arxiv.org/abs/1506.02640
[6] Ultralytics. Explore Ultralytics YOLOv8. Tài liệu mô hình YOLOv8. Truy cập ngày 26/10/2026. https://docs.ultralytics.com/models/yolov8/
[7] Ultralytics. Model Training with Ultralytics YOLO. Tài liệu tham số huấn luyện; cần đối chiếu phiên bản thư viện dự án. Truy cập ngày 26/10/2026. https://docs.ultralytics.com/modes/train/
[8] Ultralytics. Model Prediction with Ultralytics YOLO. Tài liệu nguồn ảnh, kết quả và tham số suy luận. Truy cập ngày 26/10/2026. https://docs.ultralytics.com/modes/predict/
[9] Python Software Foundation. tkinter Python interface to Tcl Tk. Mục threading model và vòng lặp sự kiện. Truy cập ngày 26/10/2026. https://docs.python.org/3/library/tkinter.html
[10] Python Software Foundation. winsound Sound playing interface for Windows. Tài liệu PlaySound, SND_ASYNC, SND_NOSTOP và đối số None. Truy cập ngày 26/10/2026. https://docs.python.org/3/library/winsound.html
[11] Gaia Solutions on Demand. D Fire Dataset. Repository và mô tả bộ dữ liệu lửa khói. Truy cập ngày 26/10/2026. https://github.com/gaia-solutions-on-demand/DFireDataset
[12] TV1. Chuong_TV1_BaoCao.docx. Tài liệu báo cáo cũ do nhóm cung cấp ngày 26/10/2026; sử dụng để đối chiếu, không thay cho mã nguồn hiện hành.
[13] Nhóm thực hiện. 123_ngaynang (2).html. Tài liệu phân công, kế hoạch và cấu trúc project do nhóm cung cấp ngày 26/10/2026. Các mục kế hoạch được phân biệt với chức năng đã cài đặt.
[14] TV4. report/chapters/chuong_yolo.md. Chương học sâu, Hybrid và so sánh. Bảng kết quả và một số mô tả cần xác minh lại với log huấn luyện và mã nguồn.
[15] Nhóm thực hiện. report/comparison_summary.json. Hồ sơ kết quả bốn phương pháp, n_images = 100 mỗi phương pháp, giữ nguyên tại commit khảo sát. Không có metadata đầy đủ để xác nhận là benchmark của bản GUI hiện tại.
[16] TV2. eval/ablation_pre.csv, eval/ablation_filter.csv, eval/val_tuned.json và eval/val_whitecore.json. Hồ sơ ablation và đánh giá validation đang lưu trong repository.
[17] TV1. native-results.json, native-stream-results.json, native-webcam-modes-results.json. Log kiểm thử tích hợp ngày 26/10/2026, lưu ngoài repository trong thư mục tv1-upgrade. Không phải tập benchmark độ chính xác.
[18] TV1. test_tv1.py. Bộ 14 kiểm thử logic và worker đã chạy đạt ngày 26/10/2026; có sử dụng mock. Kết quả kiểm tra không thay thế việc nghe âm thanh và xác nhận hình ảnh trực tiếp.

# PHỤ LỤC A DANH MỤC MODULE VÀ CẤU HÌNH
## A.1 Các file và trách nhiệm bảo trì
!TABLE files
Danh mục trên mô tả vị trí thực tế. Các thư mục dataset hoặc models trong bản Word cũ không được dùng làm đường dẫn chuẩn của bản hiện tại. data.yaml nằm cùng cấp thư mục data; weights phục vụ suy luận ở yolo/weights/best.pt. Khi chia sẻ máy demo, cần chuyển model bằng kênh riêng và kiểm tra hash trước khi chạy; không đưa weights hoặc ảnh dataset vào commit mã nguồn chỉ để người khác có thể chạy ngay.
## A.2 Từ viết tắt và ký hiệu
!TABLE glossary
## A.3 Nguồn tham số và khả năng tái lập
Các thông số cảnh báo 5 frame và 3 giây được lấy trực tiếp từ config.py. Các tham số lửa và khói được lấy từ PARAMS trong module tương ứng, không suy ra từ tên biến chung trong config. Bảng benchmark lấy từ JSON và bảng ablation lấy từ CSV mà không chạy lại script có thể ghi đè kết quả. Những giá trị tính từ kích thước, chẳng hạn diện tích 614,4 pixel, được ghi là phép tính suy ra chứ không phải số đo trên dataset.
SHA256 của best.pt tại thời điểm đọc là 73542b2f7847dc7c5b2ff9c456d24b3b37365af2d72bf05c288f641ddbcd8503. Hash dùng để phân biệt file, không xác nhận chất lượng model. Đường dẫn và hash của weights cần được ghi cùng phiên bản mã và môi trường cho mỗi lượt benchmark. Khi thay model sau này, phải cập nhật hồ sơ thực nghiệm và chạy đối chứng thay vì tái sử dụng số liệu cũ như thể cùng một phiên bản.

# PHỤ LỤC B MÃ NGUỒN MINH HỌA
## B.1 Kiểm tra hợp đồng kết quả detector
Đoạn trích sau lấy từ pipeline.py ở phiên bản khảo sát. Hàm nhận danh sách detection và shape của ảnh, kiểm tra nhãn, miền số, clipping và bỏ hộp không có diện tích. Nó không điều chỉnh confidence threshold. Khi một module trả dữ liệu sai hợp đồng, việc ném lỗi giúp GUI hiển thị lỗi tích hợp thay vì nhận một đối tượng không hợp lệ làm cảnh báo.
!CODE pipeline.py|filter_detections|Kiểm tra đầu ra chung trước khi gộp và vẽ
## B.2 Xử lý tọa độ ảnh
prepare_frame trả tensor ảnh ở mức NumPy BGR cùng bộ biến đổi. detect_frame áp biến đổi ngược cho từng box, sau đó kiểm tra lại theo kích thước ảnh gốc. Hai hàm này là điểm cần kiểm thử với ảnh ngang, dọc và kích thước lẻ. Các đoạn mã được chép từ source, không phải phiên bản rút gọn tự thay đổi logic.
!CODE pipeline.py|prepare_frame|Letterbox và lưu tỉ lệ thực tế sau làm tròn
!CODE pipeline.py|detect_frame|Ánh xạ hộp từ vùng suy luận về ảnh gốc
## B.3 Thuật toán lửa của TV2
detect_fire là chuỗi luật màu, morphology và hình học của TV2. Các tham số tùy biến được ghép trên PARAMS, giúp script ablation chỉ thay một nhóm biến mà không phải chép thuật toán. Trích đoạn giữ nguyên nguồn để người đọc phân biệt phần detector với phần tích hợp TV1.
!CODE traditional/fire_detect.py|detect_fire|Phát hiện lửa truyền thống của TV2
## B.4 Quy tắc cảnh báo của TV1
update đồng bộ trạng thái bằng RLock; stop đánh dấu instance không hoạt động và có thể ngắt kênh âm thanh thuộc instance đó. Chúng được trình bày cùng nhau vì một lỗi cuộc đua thường chỉ xuất hiện khi xét cả hai đường đi. Chế độ Image không gọi update, dù có dùng chung bộ khung tạo phiên.
!CODE gui/alert.py|update|Đếm frame và kiểm tra cooldown
!CODE gui/alert.py|stop|Ngắt âm thanh và vô hiệu hóa instance

# PHỤ LỤC C HƯỚNG DẪN VẬN HÀNH VÀ DEMO
## C.1 Chuẩn bị môi trường
Mở terminal tại thư mục gốc dự án, kích hoạt môi trường fire-smoke đã có rồi xác nhận python trỏ vào môi trường đó. Không nên chạy lệnh cài đặt lại toàn bộ requirements chỉ để xử lý một lỗi chọn nhầm interpreter. File requirements chưa khóa phiên bản; khi cần tái lập trên máy khác, nhóm nên xuất một hồ sơ môi trường đã được kiểm tra riêng, tránh vô tình thay đổi môi trường đang demo ổn định.
!SHELL conda activate fire-smoke
!SHELL python -c "import sys; print(sys.executable)"
!SHELL python -B gui/app.py
Lệnh GUI được xác nhận từ phần hướng dẫn và entry point trong gui/app.py. Trước khi chạy, kiểm tra best.pt hiện có và đúng hai nhãn; bản tích hợp sẽ báo lỗi nếu thiếu model. Không tải fallback COCO để thay thế âm thầm. Camera 0 có thể cần vài giây khởi tạo; các log trước cho thấy chờ quá ngắn dễ bị hiểu nhầm là webcam không hoạt động.
## C.2 Trình diễn Image
Chọn loại nguồn Image, bấm Chọn ảnh rồi kiểm tra preview có giữ tỷ lệ. Chọn Traditional, YOLO hoặc Combined và bấm Nhận diện ảnh; radio đổi phương pháp sẽ dừng phiên hiện hành, sau đó người dùng có thể nhận diện lại. Trình diễn một ảnh có fire, một ảnh có smoke và một ảnh âm tính. Kiểm tra cả trường hợp không detection và file hỏng để cho thấy hệ thống phân biệt kết quả rỗng với lỗi dữ liệu.
Image không có còi. Nếu cần minh họa âm thanh, chuyển sang nguồn liên tục và giải thích rõ đó là một chế độ khác. Không phát video lửa trên điện thoại rồi gọi là đám cháy thật. Khi dùng hình có người, cần tránh đưa thông tin cá nhân hoặc hình ảnh chưa được đồng ý sử dụng vào bản báo cáo nộp công khai.
## C.3 Trình diễn Webcam Video và Camera IP
Với Webcam, chọn nguồn Webcam và nhập chỉ số 0. Bắt đầu, chờ frame xuất hiện, quan sát FPS rồi thử Dừng và Bắt đầu lại. Với Video, dùng nút chọn video và giải thích nếu tệp là video thử tổng hợp. Đối với Camera IP, chỉ nhập URL của thiết bị mà nhóm có quyền truy cập; báo cáo chưa có thử nghiệm thiết bị IP, nên không hứa hẹn mọi RTSP đều được hỗ trợ hoặc thời gian dừng luôn ngắn.
CLI là một đường kiểm tra detector khác. Có thể chạy lệnh sau để hiển thị OpenCV, nhưng CLI hiện không có hệ thống còi như GUI. Cần đứng tại gốc dự án để các đường dẫn dữ liệu tương đối hoạt động đúng. Nhấn q để thoát cửa sổ OpenCV và release nguồn.
!SHELL python pipeline.py --source 0 --method yolo
!SHELL python pipeline.py --source 0 --method hybrid
## C.4 Bảng kiểm tra trước khi trình bày
!TABLE demo
Các mục cần xác nhận bằng người vận hành gồm nghe được WAV, Dừng ngắt còi, hình ảnh không méo và lỗi nhận diện trên người trong bối cảnh demo cụ thể. Log đã có không thay thế các xác nhận đó. Nếu Traditional báo nhầm, nên dùng chính tình huống đó để giải thích giới hạn luật màu và chính sách union, thay vì điều chỉnh threshold ngay trước buổi demo mà không đo lại.

# PHỤ LỤC D CÁC NỘI DUNG CẦN BỔ SUNG TRƯỚC KHI NỘP
## D.1 Hồ sơ học thuật và xác nhận đóng góp
Cần điền tên trường, khoa, môn học, lớp học phần, giảng viên, họ tên và mã sinh viên của bốn thành viên. Từng thành viên cần duyệt các phần thuộc chuyên môn của mình, xác nhận nội dung cài đặt và số liệu được trích. TV1 điều phối bản cuối; TV3 phối hợp ghép chương, hình, tài liệu tham khảo và slide. Phân công ban đầu trong HTML là kế hoạch, nên nhật ký bàn giao thực tế vẫn cần được nhóm xác nhận.
## D.2 Bằng chứng thực nghiệm còn thiếu
!TABLE missing
## D.3 Mẫu biên bản thực nghiệm cho lần đo tiếp theo
Mỗi lượt đo nên ghi mã thí nghiệm, ngày giờ, commit, hash weights, manifest dữ liệu, phương pháp, image_mode, conf, IoU, quy tắc fusion, thiết bị, số frame warmup và cách tính thời gian. Kết quả cần có TP, FP, FN hoặc dự đoán thô để tính lại metric, không chỉ một hình biểu đồ. Dữ liệu gốc được giữ nguyên; đầu ra mới lưu vào thư mục riêng có tên phiên để không ghi đè kết quả của thành viên khác.
Đối với video, bổ sung thời điểm bắt đầu và kết thúc sự kiện thật, thời điểm detection đầu tiên, thời điểm còi đầu tiên và số đợt báo sai trong thời gian âm tính. Đối với ảnh người hoặc màn hình, chạy cả ba chế độ trên cùng frame đã lưu, giữ toàn bộ box và score từng backend. Đây là điều kiện để xác định được một box sai xuất phát từ TV2, TV3, TV4 hay từ logic gộp của TV1, thay vì suy đoán theo một giá trị confidence.
