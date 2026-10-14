import { useState } from 'react'
import type { CameraStatus } from '../camera/useCamera'
import type { StableGesture } from '../gestures/gestureTypes'
import type { HandTrackingStatus } from '../hand-tracking/handTrackingTypes'

interface CalibrationWizardProps {
  cameraStatus: CameraStatus
  trackingStatus: HandTrackingStatus
  gestures: StableGesture[]
  onStartCamera: () => void
  onComplete: () => void
}

const steps = ['Giới thiệu', 'Camera', 'Bàn tay', 'Cử chỉ', 'Sẵn sàng']

export default function CalibrationWizard({
  cameraStatus,
  trackingStatus,
  gestures,
  onStartCamera,
  onComplete,
}: CalibrationWizardProps) {
  const [step, setStep] = useState(0)
  const cameraReady = cameraStatus === 'active'
  const handReady = trackingStatus === 'tracking'
  const pinchReady = gestures.some(({ name }) => name === 'pinch')

  return (
    <div className="calibration-backdrop" role="presentation">
      <section
        className="calibration-dialog"
        role="dialog"
        aria-modal="true"
        aria-labelledby="calibration-title"
      >
        <div className="calibration-progress" aria-label="Tiến trình hiệu chuẩn">
          {steps.map((label, index) => (
            <span
              className={index <= step ? 'is-complete' : ''}
              key={label}
              title={label}
            />
          ))}
        </div>

        {step === 0 && (
          <div className="calibration-step">
            <p className="eyebrow">Thiết lập lần đầu</p>
            <h2 id="calibration-title">Sẵn sàng điều khiển không gian 3D?</h2>
            <p>
              Quá trình hiệu chuẩn sẽ kiểm tra camera, vị trí bàn tay và cử chỉ
              chụm. Video chỉ được xử lý trên thiết bị của bạn.
            </p>
            <button type="button" onClick={() => setStep(1)}>
              Bắt đầu hiệu chuẩn
            </button>
          </div>
        )}

        {step === 1 && (
          <div className="calibration-step">
            <p className="eyebrow">Bước 1 / 3</p>
            <h2 id="calibration-title">Kết nối camera</h2>
            <p>
              Đặt camera ngang tầm mắt và đảm bảo khuôn hình đủ sáng. Ứng dụng
              cần quyền camera để đọc chuyển động tay.
            </p>
            <div className={`calibration-check ${cameraReady ? 'is-ready' : ''}`}>
              <span aria-hidden="true">{cameraReady ? '✓' : '○'}</span>
              {cameraReady ? 'Camera đã sẵn sàng' : 'Camera chưa kết nối'}
            </div>
            {!cameraReady && (
              <button
                type="button"
                disabled={cameraStatus === 'requesting'}
                onClick={onStartCamera}
              >
                {cameraStatus === 'requesting' ? 'Đang kết nối…' : 'Bật camera'}
              </button>
            )}
            {cameraReady && (
              <button type="button" onClick={() => setStep(2)}>
                Tiếp tục
              </button>
            )}
          </div>
        )}

        {step === 2 && (
          <div className="calibration-step">
            <p className="eyebrow">Bước 2 / 3</p>
            <h2 id="calibration-title">Đưa tay vào khung hình</h2>
            <p>
              Giữ bàn tay cách camera khoảng một cánh tay, mở lòng bàn tay và
              tránh để các ngón bị che khuất.
            </p>
            <div className={`calibration-hand-target ${handReady ? 'is-ready' : ''}`}>
              <span aria-hidden="true">✦</span>
              <strong>{handReady ? 'Đã nhận diện bàn tay' : 'Đang tìm bàn tay…'}</strong>
            </div>
            <button type="button" disabled={!handReady} onClick={() => setStep(3)}>
              {handReady ? 'Tay đã ở đúng vị trí' : 'Đưa tay vào camera'}
            </button>
          </div>
        )}

        {step === 3 && (
          <div className="calibration-step">
            <p className="eyebrow">Bước 3 / 3</p>
            <h2 id="calibration-title">Thử cử chỉ chụm</h2>
            <p>
              Chụm đầu ngón cái và ngón trỏ trong một giây. Đây là cử chỉ dùng
              để chọn và kéo vật thể.
            </p>
            <div className={`calibration-pinch ${pinchReady ? 'is-ready' : ''}`}>
              <span aria-hidden="true">◇</span>
              <strong>{pinchReady ? 'Chụm thành công' : 'Đang chờ cử chỉ chụm…'}</strong>
            </div>
            <button type="button" disabled={!pinchReady} onClick={() => setStep(4)}>
              {pinchReady ? 'Hoàn tất hiệu chuẩn' : 'Hãy thử chụm hai ngón'}
            </button>
          </div>
        )}

        {step === 4 && (
          <div className="calibration-step calibration-complete">
            <span className="complete-mark" aria-hidden="true">✓</span>
            <p className="eyebrow">Hiệu chuẩn hoàn tất</p>
            <h2 id="calibration-title">Bạn đã sẵn sàng</h2>
            <p>
              Bảng cử chỉ bên phải sẽ hướng dẫn và phản hồi thao tác theo thời
              gian thực.
            </p>
            <button type="button" onClick={onComplete}>
              Vào không gian thiết kế
            </button>
          </div>
        )}
      </section>
    </div>
  )
}

