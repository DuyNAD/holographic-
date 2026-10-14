import { useState } from 'react'
import type { HandTrackingStatus } from '../hand-tracking/handTrackingTypes'
import type { GestureName, StableGesture } from './gestureTypes'

interface GestureGuidePanelProps {
  gestures: StableGesture[]
  trackingStatus: HandTrackingStatus
}

interface GestureDefinition {
  id: Exclude<GestureName, 'none'> | 'two-hand-pinch'
  icon: string
  name: string
  instruction: string
  action: string
}

const gestureDefinitions: GestureDefinition[] = [
  {
    id: 'point',
    icon: '⌁',
    name: 'Trỏ',
    instruction: 'Giơ ngón trỏ',
    action: 'Di chuyển con trỏ',
  },
  {
    id: 'pinch',
    icon: '◇',
    name: 'Chụm',
    instruction: 'Chụm ngón cái và ngón trỏ',
    action: 'Chọn và kéo vật thể',
  },
  {
    id: 'fist',
    icon: '●',
    name: 'Nắm tay',
    instruction: 'Khép các ngón tay',
    action: 'Xoay vật thể đang chọn',
  },
  {
    id: 'open-palm',
    icon: '✦',
    name: 'Mở tay',
    instruction: 'Mở rộng lòng bàn tay',
    action: 'Thả vật thể',
  },
  {
    id: 'two-hand-pinch',
    icon: '↔',
    name: 'Hai tay chụm',
    instruction: 'Chụm ngón trên hai tay',
    action: 'Thay đổi kích thước',
  },
]

const gestureLabels: Record<StableGesture['name'], string> = {
  point: 'Trỏ',
  pinch: 'Chụm',
  fist: 'Nắm tay',
  'open-palm': 'Mở tay',
}

export default function GestureGuidePanel({
  gestures,
  trackingStatus,
}: GestureGuidePanelProps) {
  const [expanded, setExpanded] = useState(true)
  const pinchCount = gestures.filter(({ name }) => name === 'pinch').length
  const primaryGesture = gestures[0]
  const confidence = primaryGesture
    ? Math.round(primaryGesture.confidence * 100)
    : 0

  const isActive = (id: GestureDefinition['id']) =>
    id === 'two-hand-pinch'
      ? pinchCount >= 2
      : gestures.some(({ name }) => name === id)

  return (
    <section className="gesture-guide" aria-labelledby="gesture-guide-title">
      <div className="gesture-guide-heading">
        <div>
          <p className="panel-kicker">Điều khiển bằng tay</p>
          <h2 id="gesture-guide-title">Bảng cử chỉ</h2>
        </div>
        <button
          className="collapse-button"
          type="button"
          aria-expanded={expanded}
          aria-controls="gesture-guide-content"
          onClick={() => setExpanded((value) => !value)}
        >
          {expanded ? 'Thu gọn' : 'Mở rộng'}
        </button>
      </div>

      <div className="current-gesture" aria-live="polite">
        <div>
          <span>Cử chỉ hiện tại</span>
          <strong>
            {primaryGesture
              ? gestureLabels[primaryGesture.name]
              : trackingStatus === 'tracking'
                ? 'Đang phân tích'
                : 'Chưa nhận diện'}
          </strong>
        </div>
        <div className="confidence-value">
          <span>Độ tin cậy</span>
          <strong>{confidence}%</strong>
        </div>
        <div className="confidence-track" aria-hidden="true">
          <span style={{ width: `${confidence}%` }} />
        </div>
      </div>

      {expanded && (
        <div id="gesture-guide-content" className="gesture-list">
          {gestureDefinitions.map((gesture) => {
            const active = isActive(gesture.id)
            return (
              <article
                className={`gesture-item ${active ? 'is-active' : ''}`}
                key={gesture.id}
                data-gesture={gesture.id}
              >
                <span className="gesture-icon" aria-hidden="true">
                  {gesture.icon}
                </span>
                <div>
                  <div className="gesture-name-row">
                    <h3>{gesture.name}</h3>
                    <span>{active ? 'Đang hoạt động' : 'Sẵn sàng'}</span>
                  </div>
                  <p>{gesture.instruction}</p>
                  <small>{gesture.action}</small>
                </div>
              </article>
            )
          })}
        </div>
      )}
    </section>
  )
}

