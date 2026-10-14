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

Lần chạy đầu tiên tải các model về `desktop/data/models/` (một lần duy nhất, ~52 MB): nhận diện tay
và cơ thể (MediaPipe), phát hiện và nhận dạng khuôn mặt (OpenCV YuNet + SFace).

Kiểm tra (gate): **Terminal → Run Task… → holostudio: gate (lint + test)**, hoặc

```bash
.venv/Scripts/python.exe -m ruff check .
.venv/Scripts/python.exe -m pytest
```

## Chức năng

- Không gian 3D chiếm toàn cửa sổ, HUD co giãn theo kích thước cửa sổ.
- Ô camera nhỏ kèm khung xương bàn tay (tối đa 2 tay).
- Menu: **Thêm vật thể**, **Xóa vật thể**, **Hướng dẫn**, **Người thiết kế**, **Thu gọn**. Mọi nút bấm
  được bằng tay (trỏ vào nút, giữ yên 1 giây) hoặc bằng chuột.
- Thêm hình cơ bản (lập phương, cầu, trụ); vật mới tự tìm chỗ trống.
- Kho vật thể: file GLB (≤ 25 MB) lưu một lần trong `data/library/`, lấy ra cảnh bao nhiêu lần tùy ý.
  Không xóa được file khỏi kho khi cảnh hoặc lịch sử Hoàn tác còn dùng nó.
- Xóa vật thể kèm thông báo **Hoàn tác**; Undo/Redo cho mọi thao tác.
- Hiệu chuẩn lần đầu (camera, bàn tay, chụm), có thể bỏ qua.
- Tự lưu cảnh vào `data/scene.json`.

### Người thiết kế (khi có nhiều người trước camera)

- Mỗi lần mở ứng dụng, **cử chỉ tay bị khóa** cho tới khi chọn người thiết kế.
- Bấm **Người thiết kế** trên menu (bằng tay hoặc chuột): camera ghi nhận khuôn mặt **người gần camera
  nhất** và hiện **khung vàng** quanh mặt người đó cùng hộp thoại **Khóa người thiết kế?**
  - **Xác nhận** (hoặc phím Enter): khóa người đó; khung chuyển sang **xanh**, người khác có khung xám.
  - **Chọn lại**: ghi nhận lại người gần camera nhất.
  - **Hủy** (hoặc Esc): bỏ qua; nếu trước đó đã có người thiết kế thì giữ nguyên người cũ.
  - Chỉ **chính người vừa được ghi nhận** (hoặc chuột) bấm được các nút này; không ai xác nhận trong
    20 giây thì tự hủy.
- Từ đó **chỉ tay của người thiết kế** điều khiển; tay người khác bị bỏ qua. Người thiết kế đi khỏi
  khung hình thì thao tác tạm dừng ("Không thấy người thiết kế") và tự tiếp tục khi họ quay lại.
- Bấm lại nút để chọn người khác. Người thiết kế chỉ được giữ trong phiên đang chạy; dữ liệu khuôn mặt
  chỉ nằm trong bộ nhớ, không lưu xuống ổ đĩa.
- Chuột và bàn phím luôn dùng được, kể cả khi chưa chọn người thiết kế.

| Cử chỉ | Chức năng |
| --- | --- |
| Trỏ ngón trỏ | Di chuyển con trỏ |
| Trỏ vào nút, giữ yên 1 giây | Bấm nút |
| Chụm ngón cái và ngón trỏ | Chọn và kéo vật thể |
| Một tay **nắm** giữ vật, tay kia **mở và phẩy** | Xoay vật theo hướng phẩy (3D, liên tục) |
| Chụm bằng hai tay | Thay đổi kích thước |
| Mở bàn tay đang nắm hoặc chụm | Thả vật thể |
| Người gần camera nhất bấm **Người thiết kế**, rồi **Xác nhận** | Khóa điều khiển cho người đó |

| Phím | Chức năng |
| --- | --- |
| Bấm chuột | Chọn vật thể |
| Mũi tên | Di chuyển |
| Q / E | Xoay |
| − / = | Thu phóng |
| Delete | Xóa vật thể |
| Ctrl + Z / Ctrl + Y | Hoàn tác / Làm lại |
| Enter | Xác nhận người thiết kế vừa ghi nhận |
| Esc | Đóng bảng / bỏ qua hiệu chuẩn / hủy chọn người thiết kế |

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
| `holostudio/identity/` | Người thiết kế: khuôn mặt (YuNet + SFace), cơ thể (MediaPipe Pose), tay nào của ai — chạy song song trên luồng riêng |
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
các model. Khuôn mặt người thiết kế chỉ được giữ trong bộ nhớ của phiên đang chạy. Mọi dữ liệu nằm trong `desktop/data/` (đổi bằng biến môi trường `HOLOSTUDIO_DATA`;
chọn camera khác bằng `HOLOSTUDIO_CAMERA`).
