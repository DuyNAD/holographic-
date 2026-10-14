# Holographic Studio

Holographic Studio là MVP thiết kế 3D trên trình duyệt máy tính, cho phép người dùng tương tác với vật thể bằng chuyển động tay được webcam ghi nhận.

## Khả năng hiện tại

- Nhận diện tối đa hai bàn tay và hiển thị 21 landmark trên mỗi tay.
- Chọn, kéo, xoay và thay đổi kích thước vật thể 3D bằng cử chỉ.
- Tải file GLB tối đa 25 MB để thêm vật thể riêng vào cảnh.
- Bảng chức năng phản hồi cử chỉ và độ tin cậy theo thời gian thực.
- Luồng hiệu chuẩn bắt buộc kiểm tra camera, bàn tay và thao tác chụm.
- Điều khiển chuột/bàn phím dự phòng, Undo/Redo và đặt lại cảnh.
- Tự lưu cảnh trên thiết bị.

| Cử chỉ                        | Chức năng                     |
| ------------------------------- | ------------------------------- |
| Trỏ ngón trỏ                 | Di chuyển con trỏ holographic |
| Chụm ngón cái và ngón trỏ | Chọn và kéo vật thể        |
| Nắm tay                        | Xoay vật thể đang chọn      |
| Chụm bằng hai tay             | Thay đổi kích thước        |
| Mở lòng bàn tay              | Thả vật thể                  |

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

Mở `http://127.0.0.1:5173/` và làm theo hướng dẫn hiệu chuẩn.

Kiểm tra và tạo production build:

```bash
pnpm lint
pnpm test
pnpm build
pnpm preview
```

## Quyền riêng tư

Khung hình webcam được xử lý trong trình duyệt và không được ứng dụng tải lên máy chủ. Khi bật hand tracking lần đầu, trình duyệt tải WebAssembly và model MediaPipe từ nguồn phân phối công khai. Cảnh 3D và trạng thái hiệu chuẩn được lưu trong `localStorage` của trình duyệt.

File GLB do người dùng chọn được lưu cục bộ bằng IndexedDB để có thể phục hồi sau khi tải lại trang. Ứng dụng không gửi file lên máy chủ.

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
