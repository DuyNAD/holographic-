import HandLandmarkOverlay from '../hand-tracking/HandLandmarkOverlay'
import type { HandTrackingState } from '../hand-tracking/handTrackingTypes'
import type { CameraController, CameraStatus } from './useCamera'

const statusLabels: Record<CameraStatus, string> = {
  idle: 'Đang tắt',
  requesting: 'Đang kết nối',
  active: 'Đang hoạt động',
  denied: 'Thiếu quyền',
  unavailable: 'Không khả dụng',
  busy: 'Đang bận',
  error: 'Có lỗi',
}

interface CameraWindowProps {
  camera: CameraController
  handTracking: HandTrackingState
}

export default function CameraWindow({ camera, handTracking }: CameraWindowProps) {
  const { status, message, videoRef, start, stop } = camera
  const active = status === 'active'
  const requesting = status === 'requesting'

  return (
    <section
      className="camera-window hud-glass"
      aria-labelledby="camera-window-title"
      data-hud
    >
      <header className="camera-window-header">
        <h2 id="camera-window-title">Camera</h2>
        <span className={`camera-badge camera-badge--${status}`}>
          {statusLabels[status]}
        </span>
      </header>

      <div className={`camera-preview ${active ? 'is-active' : ''}`}>
        <video ref={videoRef} autoPlay muted playsInline aria-label="Xem trước camera" />
        {active && <HandLandmarkOverlay hands={handTracking.landmarks} />}
        {!active && (
          <p className="camera-placeholder" role="status">
            {message}
          </p>
        )}
      </div>

      <footer className="camera-window-footer">
        <p
          className={`tracking-status tracking-status--${active ? handTracking.status : 'idle'}`}
        >
          <span aria-hidden="true" />
          {active ? handTracking.message : 'Video chỉ xử lý trên thiết bị.'}
        </p>
        {active ? (
          <button
            className="camera-button"
            type="button"
            data-gesture-target
            onClick={stop}
          >
            Tắt camera
          </button>
        ) : (
          <button
            className="camera-button camera-button--primary"
            type="button"
            disabled={requesting}
            onClick={() => void start()}
          >
            {requesting ? 'Đang kết nối…' : 'Bật camera'}
          </button>
        )}
      </footer>
    </section>
  )
}
