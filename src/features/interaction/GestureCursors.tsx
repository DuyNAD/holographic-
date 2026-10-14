import type { StableGesture } from '../gestures/gestureTypes'

interface GestureCursorsProps {
  gestures: StableGesture[]
}

const cursorLabels: Record<StableGesture['name'], string> = {
  point: 'Trỏ',
  pinch: 'Nắm',
  fist: 'Xoay',
  'open-palm': 'Thả',
}

export default function GestureCursors({ gestures }: GestureCursorsProps) {
  return (
    <div className="gesture-cursors" aria-hidden="true">
      {gestures.map((gesture) => {
        const tip = gesture.landmarks[8]
        if (!tip) return null

        return (
          <div
            className={`gesture-cursor gesture-cursor--${gesture.name}`}
            key={`${gesture.handedness}-${gesture.handIndex}`}
            style={{ left: `${(1 - tip.x) * 100}%`, top: `${tip.y * 100}%` }}
          >
            <span />
            <small>{cursorLabels[gesture.name]}</small>
          </div>
        )
      })}
    </div>
  )
}

