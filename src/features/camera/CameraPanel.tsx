import HandLandmarkOverlay from '../hand-tracking/HandLandmarkOverlay'
import { MAX_TRACKED_HANDS } from '../hand-tracking/handTrackingConfig'
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

interface CameraPanelProps {
  camera: CameraController
  handTracking: HandTrackingState
}

export default function CameraPanel({
  camera,
  handTracking,
}: CameraPanelProps) {
  const { status, message, videoRef, start, stop } = camera
  const active = status === 'active'
  const requesting = status === 'requesting'

  return (
    <section className="camera-panel" aria-labelledby="camera-panel-title">
      <div className="camera-heading">
        <div>
          <p className="panel-kicker">Nguồn chuyển động</p>
          <h2 id="camera-panel-title">Camera</h2>
        </div>
        <span className={`camera-badge camera-badge--${status}`}>
          {statusLabels[status]}
        </span>
      </div>

      <div className={`camera-preview ${active ? 'is-active' : ''}`}>
        <video ref={videoRef} autoPlay muted playsInline aria-label="Xem trước camera" />
        {active && <HandLandmarkOverlay hands={handTracking.landmarks} />}
        {!active && (
          <div className="camera-placeholder" aria-hidden="true">
            <span className="camera-icon">◎</span>
            <span>Camera preview</span>
          </div>
        )}
      </div>

      <p className="camera-message" role="status">
        {message}
      </p>

      {active && (
        <div className={`tracking-status tracking-status--${handTracking.status}`}>
          <span aria-hidden="true" />
          <p>{handTracking.message}</p>
        </div>
      )}

      {active ? (
        <button className="camera-button" type="button" onClick={stop}>
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

      <p className="privacy-note">Video được xử lý cục bộ và không tải lên mạng.</p>
      <p className="tracking-capacity">Hỗ trợ tối đa {MAX_TRACKED_HANDS} bàn tay.</p>
    </section>
  )
}

