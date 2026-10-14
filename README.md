# Holographic Studio

Ứng dụng thiết kế 3D điều khiển bằng cử chỉ tay qua webcam, chạy trực tiếp trên máy từ VS Code
(Python, MediaPipe, Panda3D, OpenCV).

Toàn bộ mã nguồn, hướng dẫn cài đặt, cách dùng và kiến trúc nằm trong
[desktop/README.md](desktop/README.md).

## Chạy nhanh

Mở thư mục này trong VS Code rồi nhấn **F5** và chọn **Holographic Studio (desktop)**.

Lần đầu trên máy mới: **Terminal → Run Task… → holostudio: install**.

## Thông số đã khóa

Các thông số đã được duyệt nằm trong `desktop/tests/test_tuning_lock.py`; gate kiểm tra
(**Terminal → Run Task… → holostudio: gate**) báo lỗi nếu có thông số nào bị đổi.

## Lịch sử

Bản web (React + Vite) trước đây đã được gỡ khỏi repo; vẫn xem lại được trong lịch sử git
(ví dụ tag `tuning-lock-v1`).
