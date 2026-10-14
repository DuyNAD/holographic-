# Holographic Studio — bản desktop

Ứng dụng thiết kế 3D điều khiển bằng cử chỉ tay, chạy trực tiếp trên máy (không cần trình duyệt).
Nhận diện tay bằng **MediaPipe**, hiển thị 3D bằng **Panda3D**, đọc camera bằng **OpenCV**.

## Chạy trong VS Code

Lần đầu (một lần duy nhất), mở terminal trong VS Code tại thư mục `desktop`:

```bash
py -3.13 -m venv .venv
.venv/Scripts/python.exe -m pip install -r requirements-dev.txt
```

Sau đó chọn một trong các cách:

- Nhấn **F5**, chọn cấu hình **Holographic Studio (desktop)**.
- Hoặc **Terminal → Run Task… → holostudio: run**.
- Hoặc chạy lệnh: `.venv/Scripts/python.exe run.py`

Lần chạy đầu tiên tải model nhận diện tay (~8 MB) về `desktop/data/models/`; các lần sau dùng file đã lưu.

Kiểm tra (gate): **Terminal → Run Task… → holostudio: gate (lint + test)**, hoặc

```bash
.venv/Scripts/python.exe -m ruff check .
.venv/Scripts/python.exe -m pytest
```

## Chức năng

- Không gian 3D chiếm toàn cửa sổ, HUD co giãn theo kích thước cửa sổ.
- Ô camera nhỏ kèm khung xương bàn tay (tối đa 2 tay).
- Menu: **Thêm vật thể**, **Xóa vật thể**, **Hướng dẫn**, **Thu gọn**. Mọi nút bấm được bằng tay
  (trỏ vào nút, giữ yên 1 giây) hoặc bằng chuột.
- Thêm hình cơ bản (lập phương, cầu, trụ); vật mới tự tìm chỗ trống.
- Kho vật thể: file GLB (≤ 25 MB) lưu một lần trong `data/library/`, lấy ra cảnh bao nhiêu lần tùy ý.
  Không xóa được file khỏi kho khi cảnh hoặc lịch sử Hoàn tác còn dùng nó.
- Xóa vật thể kèm thông báo **Hoàn tác**; Undo/Redo cho mọi thao tác.
- Hiệu chuẩn lần đầu (camera, bàn tay, chụm), có thể bỏ qua.
- Tự lưu cảnh vào `data/scene.json`.

| Cử chỉ | Chức năng |
| --- | --- |
| Trỏ ngón trỏ | Di chuyển con trỏ |
| Trỏ vào nút, giữ yên 1 giây | Bấm nút |
| Chụm ngón cái và ngón trỏ | Chọn và kéo vật thể |
| Một tay **nắm** giữ vật, tay kia **mở và phẩy** | Xoay vật theo hướng phẩy (3D, liên tục) |
| Chụm bằng hai tay | Thay đổi kích thước |
| Mở bàn tay đang nắm hoặc chụm | Thả vật thể |

| Phím | Chức năng |
| --- | --- |
| Bấm chuột | Chọn vật thể |
| Mũi tên | Di chuyển |
| Q / E | Xoay |
| − / = | Thu phóng |
| Delete | Xóa vật thể |
| Ctrl + Z / Ctrl + Y | Hoàn tác / Làm lại |
| Esc | Đóng bảng / bỏ qua hiệu chuẩn |

## Kiến trúc: mỗi khâu xử lý một thư mục

```text
camera/  →  tracking/  →  gestures/  →  interaction/  →  scene/  →  rendering/ + hud/
 webcam      MediaPipe      cử chỉ        con trỏ, giữ     trạng thái,   3D Panda3D,
 (luồng      (luồng         ổn định       để bấm, kéo/     Undo/Redo,    menu, bảng,
  riêng)      riêng)                      xoay/thu phóng   lưu trữ       ô camera
```

| Thư mục | Vai trò |
| --- | --- |
| `holostudio/camera/` | Đọc webcam trên luồng riêng, báo mất kết nối |
| `holostudio/tracking/` | Tải model một lần, chạy MediaPipe HandLandmarker trên luồng riêng |
| `holostudio/gestures/` | Làm mượt điểm mốc (theo tay trái/phải), phân loại cử chỉ, chống rung |
| `holostudio/interaction/` | Con trỏ tay, giữ 1 giây để bấm, kéo / xoay (nắm + phẩy) / thu phóng vật thể |
| `holostudio/scene/` | Trạng thái cảnh, lịch sử Undo/Redo, lưu JSON |
| `holostudio/assets/` | Kho GLB: kiểm tra, lưu, đọc model |
| `holostudio/rendering/` | Cảnh 3D Panda3D, chọn vật bằng tia |
| `holostudio/hud/` | Bố cục HUD (dữ liệu thuần), vẽ HUD, ô camera |
| `holostudio/calibration/` | Luồng hiệu chuẩn |
| `holostudio/app/` | Ghép các khâu; `controller.py` là nơi duy nhất biến mọi đầu vào thành hành động |

Chuột, bàn phím và cử chỉ tay đều đi qua `StudioController.press` / `key`, nên luôn cho cùng một kết quả.

`python -m holostudio.app.smoke` chạy toàn bộ ứng dụng không cần cửa sổ, với một bàn tay ảo theo
kịch bản, rồi in kết quả kiểm tra và thời gian mỗi khung hình.

## Quyền riêng tư

Video camera chỉ được xử lý trên máy, không gửi đi đâu. Ứng dụng chỉ kết nối mạng một lần để tải
model MediaPipe. Mọi dữ liệu nằm trong `desktop/data/` (đổi bằng biến môi trường `HOLOSTUDIO_DATA`;
chọn camera khác bằng `HOLOSTUDIO_CAMERA`).
