import GestureGuidePanel from '../gestures/GestureGuidePanel'
import type { StableGesture } from '../gestures/gestureTypes'

interface GuidePanelProps {
  gestures: StableGesture[]
  onRecalibrate: () => void
}

const shortcuts = [
  ['Chọn vật thể', 'Bấm chuột'],
  ['Di chuyển', 'Phím mũi tên'],
  ['Xoay', 'Q / E'],
  ['Thu phóng', '− / ='],
  ['Xóa vật thể', 'Delete'],
  ['Hoàn tác / Làm lại', 'Ctrl + Z / Ctrl + Y'],
] as const

export default function GuidePanel({ gestures, onRecalibrate }: GuidePanelProps) {
  return (
    <div className="guide-panel">
      <section aria-labelledby="gesture-guide-title">
        <h3 id="gesture-guide-title" className="hud-section-title">
          Cử chỉ tay
        </h3>
        <GestureGuidePanel gestures={gestures} />
      </section>

      <section aria-labelledby="shortcut-title">
        <h3 id="shortcut-title" className="hud-section-title">
          Chuột và bàn phím
        </h3>
        <dl className="shortcut-list">
          {shortcuts.map(([action, keys]) => (
            <div key={action}>
              <dt>{action}</dt>
              <dd>{keys}</dd>
            </div>
          ))}
        </dl>
      </section>

      <button
        className="hud-wide-button"
        type="button"
        data-gesture-target
        onClick={onRecalibrate}
      >
        Hiệu chuẩn lại
      </button>
    </div>
  )
}
