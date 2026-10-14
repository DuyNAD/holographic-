# Holographic Studio

Holographic Studio là MVP thiết kế 3D trên trình duyệt máy tính, cho phép người dùng tương tác với vật thể bằng chuyển động tay được webcam ghi nhận.

> **Bản desktop (khuyên dùng):** chạy trực tiếp trên máy từ VS Code, không cần trình duyệt.
> Xem [desktop/README.md](desktop/README.md). Phần còn lại của tài liệu này mô tả bản web cũ.

## Khả năng hiện tại

- Không gian 3D chiếm toàn bộ cửa sổ; giao diện HUD co giãn theo kích thước cửa sổ và không bao giờ cuộn trang.
- Camera hiển thị trong một ô nhỏ kèm khung xương bàn tay (tối đa hai tay, 21 landmark mỗi tay).
- Menu kiểu thực tế ảo: **Thêm vật thể**, **Xóa vật thể**, **Hướng dẫn** và nút **Thu gọn** menu. Mọi nút đều bấm được bằng tay: trỏ vào nút và giữ yên 1 giây.
- Thêm hình cơ bản (lập phương, cầu, trụ); vật mới tự tìm chỗ trống trong cảnh.
- Kho vật thể: file GLB (tối đa 25 MB) được lưu trên thiết bị một lần, sau đó lấy ra cảnh bao nhiêu lần tùy ý bằng cử chỉ, không cần tải lại.
- Xóa vật thể khỏi cảnh, có thông báo **Hoàn tác** ngay sau khi xóa; Undo/Redo cho mọi thao tác.
- Chọn, kéo, xoay và thay đổi kích thước vật thể bằng cử chỉ.
- Luồng hiệu chuẩn kiểm tra camera, bàn tay và thao tác chụm; có thể bỏ qua để dùng chuột và bàn phím.
- Tự lưu cảnh trên thiết bị.

| Cử chỉ                                   | Chức năng                              |
| ---------------------------------------- | -------------------------------------- |
| Trỏ ngón trỏ                             | Di chuyển con trỏ holographic          |
| Trỏ vào nút và giữ yên 1 giây            | Bấm nút trên menu và bảng              |
| Chụm ngón cái và ngón trỏ                | Chọn và kéo vật thể                    |
| Chọn vật thể, nắm tay rồi nghiêng cổ tay | Xoay vật thể theo hướng nghiêng tay    |
| Chụm bằng hai tay                        | Thay đổi kích thước                    |
| Mở lòng bàn tay                          | Thả vật thể                            |

| Chuột và bàn phím  | Chức năng            |
| ------------------ | -------------------- |
| Bấm chuột          | Chọn vật thể         |
| Phím mũi tên       | Di chuyển            |
| Q / E              | Xoay                 |
| − / =              | Thu phóng            |
| Delete             | Xóa vật thể đang chọn |
| Ctrl + Z / Ctrl + Y | Hoàn tác / Làm lại  |

Việc chọn file GLB để tải vào kho cần dùng chuột, vì trình duyệt chỉ mở hộp thoại chọn file khi người dùng bấm thật.

## Chạy dự án

Yêu cầu:

- Node.js 24 trở lên
- pnpm 11 trở lên
- Chrome hoặc Edge có hỗ trợ WebGL và `getUserMedia`
- Webcam

```bash
pnpm ci
pnpm dev
```

Mở `http://localhost:5173/` và làm theo hướng dẫn hiệu chuẩn.

Kiểm tra và tạo production build:

```bash
pnpm lint
pnpm test
pnpm build
pnpm preview
```

## Quyền riêng tư

Khung hình webcam được xử lý trong trình duyệt và không được ứng dụng tải lên máy chủ. Khi bật hand tracking lần đầu, trình duyệt tải WebAssembly và model MediaPipe từ nguồn phân phối công khai. Cảnh 3D và trạng thái hiệu chuẩn được lưu trong `localStorage` của trình duyệt.

File GLB do người dùng chọn được lưu cục bộ trong kho vật thể (IndexedDB) để dùng lại và phục hồi sau khi tải lại trang. Ứng dụng không gửi file lên máy chủ. File chỉ bị xóa khi người dùng xóa nó khỏi kho.

## Kiến trúc và phát hành

- [Kiến trúc hệ thống](docs/ARCHITECTURE.md)
- [Checklist release candidate](docs/RELEASE_CHECKLIST.md)

## Delivery gates

- G0 — Product contract: passed
- G1 — Project foundation: passed
- G2 — 3D vertical slice: passed
- G3 — Camera subsystem: passed
- G4 — Hand tracking: passed
- G5 — Gesture engine: passed
- G6 — 3D gesture interaction: passed
- G7 — Gesture panel: passed
- G8 — Calibration and onboarding: passed
- G9 — Product hardening: passed
- G10 — Release candidate: in progress


chạy lại bằng lệnh
pnpm dev trong terminal
