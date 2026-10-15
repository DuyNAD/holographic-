# Holographic Studio — bản desktop

Ứng dụng thiết kế 3D điều khiển bằng cử chỉ tay, chạy trực tiếp trên máy (không cần trình duyệt).
Nhận diện tay bằng **MediaPipe**, hiển thị 3D bằng **Panda3D**, đọc camera bằng **OpenCV**.
Sau một lần quét tay, con trỏ được thay bằng **bàn tay 3D** mô phỏng tay bạn và cầm vật bằng cách chạm.

## Chạy trong VS Code

### Máy mới (VS Code vừa cài, chưa có Python, chưa có kernel)

Chỉ cần Windows. Mở thư mục dự án trong VS Code rồi chọn **một** cách:

- **Terminal → Run Task… → holostudio: cài đặt máy mới**, hoặc
- bấm đúp `desktop/setup.cmd`, hoặc chạy `.\setup.cmd` trong terminal tại thư mục `desktop`.

`setup.cmd` (chạy `setup.ps1`) tự làm, bước nào đã có thì bỏ qua:

1. cài **Python 3.13** bằng winget nếu máy chưa có;
2. tạo `desktop/.venv` và cài thư viện;
3. tải model nhận diện tay và cơ thể (~14 MB, một lần);
4. đăng ký **kernel Jupyter "Holographic Studio (.venv)"**;
5. cài extension VS Code **Python** và **Jupyter** (bỏ qua bằng `setup.cmd -SkipExtensions`);
6. kiểm tra thư viện và Panda3D. Thêm `-Run` để mở ứng dụng ngay sau khi cài.

Sau đó mở **`desktop/HolographicStudio.ipynb`**, chọn kernel **Holographic Studio (.venv)** ở góc trên
bên phải và chạy từng ô: kiểm tra môi trường → tải model → gate → chạy thử toàn bộ → mở ứng dụng.

### Chạy ứng dụng

- Nhấn **F5**, chọn cấu hình **Holographic Studio (desktop)**.
- Hoặc **Terminal → Run Task… → holostudio: run**.
- Hoặc chạy lệnh: `.venv/Scripts/python.exe run.py`

Kiểm tra (gate): **Terminal → Run Task… → holostudio: gate (lint + test)**, hoặc

```bash
.venv/Scripts/python.exe -m ruff check .
.venv/Scripts/python.exe -m pytest
```

## Chức năng

- Không gian 3D chiếm toàn cửa sổ, HUD co giãn theo kích thước cửa sổ.
- Ô camera nhỏ kèm khung xương bàn tay (tối đa 2 tay).
- Menu: **Thêm vật thể**, **Xóa vật thể**, **Ghép khối**, **Tách khối**, **Quét tay**, **Hướng dẫn**, **Thu gọn**. Mọi nút bấm
  được bằng tay (trỏ vào nút, giữ yên 1 giây) hoặc bằng chuột.
- Thêm hình cơ bản (lập phương, cầu, trụ); vật mới tự tìm chỗ trống.
- Kho vật thể: file GLB (≤ 25 MB) lưu một lần trong `data/library/`, lấy ra cảnh bao nhiêu lần tùy ý.
  Không xóa được file khỏi kho khi cảnh hoặc lịch sử Hoàn tác còn dùng nó.
- Xóa vật thể kèm thông báo **Hoàn tác**; Undo/Redo cho mọi thao tác.
- Hiệu chuẩn lần đầu (camera, bàn tay, chụm), có thể bỏ qua; sau đó là **quét tay** cho bàn tay 3D.
- Tự lưu cảnh vào `data/scene.json`.
- Bàn tay 3D thay cho con trỏ, chạm và cầm vật trong không gian 3D (xem bên dưới).

### Ghép và tách khối

- Bấm **Ghép khối**: chụm tay (hoặc bấm chuột) vào từng khối để chọn hoặc bỏ chọn; khối đã chọn có
  **viền vàng**. Bấm **Ghép N khối** để gộp chúng thành một khối, di chuyển / xoay / thu phóng / xóa
  như một vật. Có thể ghép cả khối đã ghép (nhóm trong nhóm).
- Chọn một khối ghép rồi bấm **Tách khối**: các khối trở lại thành vật riêng, giữ nguyên vị trí và góc.
- Ghép và tách đều là một bước **Hoàn tác**.

### Bàn tay 3D (thay cho con trỏ)

- Lần đầu chạy (sau hiệu chuẩn), bảng **Quét bàn tay** tự mở: đưa một bàn tay vào **khung trắng** trên
  ô camera, xòe thẳng các ngón và giữ yên khoảng 1 giây cho đến khi thanh tiến độ đầy. Muốn quét lại
  lúc nào thì bấm **Quét tay**.
- Chỉ lưu **số đo xương tay** (độ dài 20 đốt, tính bằng mét) vào `data/hand_profile.json`, không lưu
  hình ảnh. Nút **Tắt tay 3D, dùng con trỏ** xóa số đo và quay về con trỏ cũ.
- Sau khi quét, mỗi bàn tay hiện thành một **bàn tay 3D có da**, cử động từng ngón theo tay thật
  (MediaPipe đo hình dạng 3D, độ dài đốt lấy từ lần quét để giữ đúng tỉ lệ tay của bạn).
- **Vị trí và độ to**: bàn tay 3D nằm đúng chỗ bàn tay trong ô camera (như soi gương). Khi tay ở đúng
  khoảng cách lúc quét, nó nằm ngang tâm cảnh; đưa tay **lại gần camera** thì tay 3D tiến về phía bạn
  (trông to hơn), **lùi ra xa** thì nó đi sâu vào cảnh (trông nhỏ hơn). Khoảng cách được tính từ độ to
  nhỏ của bàn tay trong khung hình so với lúc quét.
- **Chạm thật trong 3D**: đưa tay tới vật, **chụm khi đầu ngón chạm vào vật** để cầm (tay chuyển sang
  màu xanh nhạt khi chạm được). Kéo tay sang ngang, lên xuống **và xa gần** — vật đi theo cả ba chiều.
  Chụm vào khoảng không trước vật thì không cầm gì. Mở tay để thả; cả lần kéo là một bước Hoàn tác.
- Nắm + phẩy để xoay, chụm hai tay để thu phóng, giữ 1 giây để bấm nút vẫn như cũ (đầu ngón trỏ vẫn
  có một vòng nhỏ để bấm nút).

### Chỉ người gần camera nhất điều khiển

- Ứng dụng tự nhận ra **người đứng gần camera nhất** (vai rộng nhất trong hình) và chỉ dùng **tay của
  người đó**. Tay người đứng xa hơn bị bỏ qua và hiện **màu xám** trong ô camera.
- Hai người đứng gần như ngang nhau thì quyền điều khiển không bị nhảy qua lại; chỉ chuyển khi người
  kia tiến lại gần rõ rệt (≥ 15% trong 0,5 giây).
- Không thấy cơ thể ai (ví dụ ngồi rất sát camera): dùng những bàn tay to nhất, tức gần camera nhất.
- Không dùng khuôn mặt; chuột và bàn phím luôn dùng được.

| Cử chỉ | Chức năng |
| --- | --- |
| Trỏ ngón trỏ | Di chuyển con trỏ (khi có tay 3D: vòng nhỏ ở đầu ngón trỏ) |
| Trỏ vào nút, giữ yên 1 giây | Bấm nút |
| Chụm ngón cái và ngón trỏ | Chọn và kéo vật thể (chưa quét tay: chụm vào vật trên màn hình) |
| Một tay **nắm** giữ vật, tay kia **mở và phẩy** | Xoay vật theo hướng phẩy (3D, liên tục) |
| Chụm bằng hai tay | Thay đổi kích thước |
| Mở bàn tay đang nắm hoặc chụm | Thả vật thể |
| Bấm **Ghép khối**, chụm vào từng khối, rồi **Ghép N khối** | Gộp các khối thành một khối |
| Bấm **Quét tay**, xòe tay yên trong khung trên ô camera | Tạo bàn tay 3D theo tay của bạn |
| Tay 3D: chụm khi đầu ngón chạm vật | Cầm và kéo vật cả xa gần |

| Phím | Chức năng |
| --- | --- |
| Bấm chuột | Chọn vật thể |
| Mũi tên | Di chuyển |
| Q / E | Xoay |
| − / = | Thu phóng |
| Delete | Xóa vật thể |
| Ctrl + Z / Ctrl + Y | Hoàn tác / Làm lại |
| Esc | Đóng bảng / bỏ qua hiệu chuẩn / thoát chế độ ghép hoặc quét tay |

## Kiến trúc: mỗi khâu xử lý một thư mục

```text
camera/  →  tracking/  →  gestures/  →  interaction/  →  scene/  →  rendering/ + hud/
 webcam      MediaPipe      cử chỉ        con trỏ, giữ     trạng thái,   3D Panda3D,
 (luồng      tay 2D + 3D    ổn định       để bấm, kéo/     Undo/Redo,    menu, bảng,
  riêng)     (luồng riêng)     │          xoay/thu phóng   lưu trữ       ô camera
                               ↓               ↑
                            avatar/  ──────────┘
                            quét tay, khoảng cách, tư thế và lưới bàn tay 3D
```

Bàn tay 3D, từng bước mỗi khung hình:

1. **tracking/**: MediaPipe trả về 21 điểm của tay trong ảnh và cùng 21 điểm đó tính bằng mét (hình 3D).
2. **gestures/**: làm mượt cả hai; đo "độ to trong ảnh / độ to thật" trên dữ liệu gốc để biết tay
   gần hay xa camera so với lúc quét.
3. **avatar/**: đặt lòng bàn tay trên tia camera đi qua vị trí tay trong ảnh, ở độ sâu tỉ lệ với
   khoảng cách đó; hướng từng đốt lấy từ hình 3D, độ dài đốt lấy từ lần quét; dựng lưới tay có da.
4. **interaction/**: chụm khi điểm giữa ngón cái và ngón trỏ chạm bề mặt vật (trong 2 cm) thì cầm;
   vật đi theo tâm lòng bàn tay nên mở tay để thả không làm vật bị giật.

| Thư mục | Vai trò |
| --- | --- |
| `holostudio/camera/` | Đọc webcam trên luồng riêng, báo mất kết nối |
| `holostudio/tracking/` | Tải model một lần, chạy MediaPipe HandLandmarker trên luồng riêng |
| `holostudio/identity/` | Người dùng gần nhất: cơ thể (MediaPipe Pose), tay nào của ai — chạy song song trên luồng riêng |
| `holostudio/gestures/` | Làm mượt điểm mốc 2D và 3D (theo từng bàn tay), phân loại cử chỉ, chống rung |
| `holostudio/avatar/` | Bàn tay 3D: quét và lưu số đo, ước lượng khoảng cách, tính tư thế trong cảnh, dựng lưới tay |
| `holostudio/interaction/` | Con trỏ tay, giữ 1 giây để bấm, kéo / xoay (nắm + phẩy) / thu phóng vật thể |
| `holostudio/scene/` | Trạng thái cảnh, lịch sử Undo/Redo, lưu JSON |
| `holostudio/assets/` | Kho GLB: kiểm tra, lưu, đọc model |
| `holostudio/rendering/` | Cảnh 3D Panda3D, chọn vật bằng tia hoặc bằng chạm 3D, vẽ bàn tay 3D |
| `holostudio/hud/` | Bố cục HUD (dữ liệu thuần), vẽ HUD, ô camera |
| `holostudio/calibration/` | Luồng hiệu chuẩn |
| `holostudio/app/` | Ghép các khâu; `controller.py` là nơi duy nhất biến mọi đầu vào thành hành động |

Chuột, bàn phím và cử chỉ tay đều đi qua `StudioController.press` / `key`, nên luôn cho cùng một kết quả.

`python -m holostudio.app.smoke` chạy toàn bộ ứng dụng không cần cửa sổ, với một bàn tay ảo theo
kịch bản (cả quét tay và chạm 3D), rồi in kết quả kiểm tra và thời gian mỗi khung hình.

## Dữ liệu trên máy

| File trong `desktop/data/` | Nội dung |
| --- | --- |
| `scene.json` | Cảnh hiện tại (tự lưu) |
| `settings.json` | Đã hiệu chuẩn hay chưa |
| `hand_profile.json` | Số đo 20 đốt xương tay (mét) từ lần quét; xóa file này = quét lại |
| `library/` | Các file GLB đã nhập |
| `models/` | Model MediaPipe nhận diện tay và cơ thể |

## Khi gặp vấn đề

- **Tay 3D quá to hoặc quá nhỏ**: tay 3D có cùng độ to trên màn hình như tay bạn trong ô camera.
  Quét lại ở khoảng cách bạn hay ngồi; đứng xa hơn khi quét thì tay 3D nhỏ hơn.
- **Quét không chạy**: cả bàn tay phải nằm trong khung trắng, các ngón xòe thẳng, giữ yên; dòng chữ
  trong bảng **Quét bàn tay** cho biết đang thiếu điều gì.
- **Không cầm được vật**: đưa tay xa / gần camera cho tới khi tay 3D chạm vật (tay chuyển màu xanh
  nhạt) rồi mới chụm.
- **Muốn dùng lại con trỏ**: **Quét tay → Tắt tay 3D, dùng con trỏ**.

## Quyền riêng tư

Video camera chỉ được xử lý trên máy, không gửi đi đâu. Lần quét tay chỉ lưu số đo xương, không lưu
hình ảnh. Ứng dụng chỉ kết nối mạng một lần để tải
các model. Mọi dữ liệu nằm trong `desktop/data/` (đổi bằng biến môi trường `HOLOSTUDIO_DATA`;
chọn camera khác bằng `HOLOSTUDIO_CAMERA`).
