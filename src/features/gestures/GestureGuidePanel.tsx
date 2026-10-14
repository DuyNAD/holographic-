import type { GestureName, StableGesture } from './gestureTypes'

interface GestureGuidePanelProps {
  gestures: StableGesture[]
}

interface GestureDefinition {
  id: Exclude<GestureName, 'none'> | 'two-hand-pinch' | 'dwell'
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
    id: 'dwell',
    icon: '◔',
    name: 'Giữ để bấm',
    instruction: 'Trỏ vào nút và giữ yên 1 giây',
    action: 'Bấm nút trên menu và bảng',
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
    instruction: 'Chọn vật thể trước, nắm tay rồi nghiêng cổ tay',
    action: 'Xoay vật thể theo hướng nghiêng tay',
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

export default function GestureGuidePanel({ gestures }: GestureGuidePanelProps) {
  const pinchCount = gestures.filter(({ name }) => name === 'pinch').length

  const isActive = (id: GestureDefinition['id']) => {
    if (id === 'two-hand-pinch') return pinchCount >= 2
    if (id === 'dwell') return gestures.some(({ name }) => name === 'point')
    return gestures.some(({ name }) => name === id)
  }

  return (
    <div className="gesture-list">
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
  )
}
