# Holographic Studio

Ứng dụng thiết kế 3D điều khiển bằng cử chỉ tay qua webcam, chạy trực tiếp trên máy từ VS Code
(Python, MediaPipe, Panda3D, OpenCV).

- Thêm, kéo, xoay, thu phóng, ghép / tách khối và nhập model GLB bằng tay, chuột hoặc bàn phím.
- **Bàn tay 3D**: quét tay một lần, sau đó một bàn tay 3D có da thay cho con trỏ, đi theo tay thật cả
  xa gần và cầm được vật khi đầu ngón **chạm** vào vật.
- Chỉ người đứng gần camera nhất điều khiển; video chỉ xử lý trên máy.

Toàn bộ mã nguồn, hướng dẫn cài đặt, cách dùng và kiến trúc nằm trong
[desktop/README.md](desktop/README.md).

## Chạy nhanh

- **Máy mới** (chưa có Python / kernel): **Terminal → Run Task… → holostudio: cài đặt máy mới**, hoặc
  bấm đúp `desktop/setup.cmd`.
- **Chạy ứng dụng**: nhấn **F5** và chọn **Holographic Studio (desktop)**, hoặc mở
  `desktop/HolographicStudio.ipynb` với kernel **Holographic Studio (.venv)**.
- **Kiểm tra**: **Terminal → Run Task… → holostudio: gate (lint + test)**.

## Thông số đã khóa

Các thông số đã được duyệt nằm trong `desktop/tests/test_tuning_lock.py`; gate báo lỗi nếu có
thông số nào bị đổi.

## Lịch sử

Bản web (React + Vite) đã được gỡ khỏi nhánh `main`; vẫn còn ở nhánh `web` và trong lịch sử git
(ví dụ tag `tuning-lock-v1`).
