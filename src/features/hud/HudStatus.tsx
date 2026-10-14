import type { StableGesture } from '../gestures/gestureTypes'
import type { HandTrackingStatus } from '../hand-tracking/handTrackingTypes'

interface HudStatusProps {
  gestures: StableGesture[]
  trackingStatus: HandTrackingStatus
  selectedName: string | null
}

const gestureLabels: Record<StableGesture['name'], string> = {
  point: 'Trỏ',
  pinch: 'Chụm',
  fist: 'Nắm tay',
  'open-palm': 'Mở tay',
}

export default function HudStatus({
  gestures,
  trackingStatus,
  selectedName,
}: HudStatusProps) {
  const primary = gestures[0]
  const confidence = primary ? Math.round(primary.confidence * 100) : 0
  const gestureLabel = primary
    ? gestureLabels[primary.name]
    : trackingStatus === 'tracking'
      ? 'Đang phân tích'
      : 'Chưa nhận diện'

  return (
    <header className="hud-status" data-hud>
      <div className="hud-brand hud-glass">
        <span className="status-dot" aria-hidden="true" />
        <h1>Holographic Studio</h1>
      </div>
      <div className="hud-chip hud-glass" aria-live="polite">
        <span>Cử chỉ</span>
        <strong>{gestureLabel}</strong>
        <span className="hud-chip-meter" aria-label={`Độ tin cậy ${confidence}%`}>
          <span style={{ width: `${confidence}%` }} />
        </span>
        <strong>{confidence}%</strong>
      </div>
      <div className="hud-chip hud-glass" aria-live="polite">
        <span>Đang chọn</span>
        <strong>{selectedName ?? 'Chưa chọn vật thể'}</strong>
      </div>
    </header>
  )
}
