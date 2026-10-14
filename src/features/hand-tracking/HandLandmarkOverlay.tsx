import type { HandLandmark } from './handTrackingTypes'
import { HAND_CONNECTIONS } from './handConnections'

interface HandLandmarkOverlayProps {
  hands: HandLandmark[][]
}

const mirroredX = (x: number) => 1 - x

export default function HandLandmarkOverlay({ hands }: HandLandmarkOverlayProps) {
  return (
    <svg
      className="hand-overlay"
      viewBox="0 0 1 1"
      preserveAspectRatio="none"
      aria-label={`${hands.length} bàn tay được nhận diện`}
    >
      {hands.map((hand, handIndex) => (
        <g key={`hand-${handIndex}`}>
          {HAND_CONNECTIONS.map(([startIndex, endIndex]) => {
            const start = hand[startIndex]
            const end = hand[endIndex]
            if (!start || !end) return null

            return (
              <line
                key={`${handIndex}-${startIndex}-${endIndex}`}
                x1={mirroredX(start.x)}
                y1={start.y}
                x2={mirroredX(end.x)}
                y2={end.y}
              />
            )
          })}
          {hand.map((point, pointIndex) => (
            <circle
              key={`${handIndex}-${pointIndex}`}
              cx={mirroredX(point.x)}
              cy={point.y}
              r={pointIndex === 0 ? 0.014 : 0.009}
            />
          ))}
        </g>
      ))}
    </svg>
  )
}

