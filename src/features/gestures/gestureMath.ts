import type { HandLandmark } from '../hand-tracking/handTrackingTypes'
import type { GestureObservation } from './gestureTypes'

const FINGER_JOINTS = [
  { pip: 6, tip: 8 },
  { pip: 10, tip: 12 },
  { pip: 14, tip: 16 },
  { pip: 18, tip: 20 },
] as const

const clamp01 = (value: number) => Math.min(1, Math.max(0, value))

const distance = (a: HandLandmark, b: HandLandmark) =>
  Math.hypot(a.x - b.x, a.y - b.y, a.z - b.z)

const isFingerExtended = (
  landmarks: HandLandmark[],
  pipIndex: number,
  tipIndex: number,
) => {
  const wrist = landmarks[0]
  const pip = landmarks[pipIndex]
  const tip = landmarks[tipIndex]
  if (!wrist || !pip || !tip) return false

  return distance(wrist, tip) > distance(wrist, pip) * 1.12
}

export function detectGesture(landmarks: HandLandmark[]): GestureObservation {
  if (landmarks.length < 21) {
    return { name: 'none', confidence: 0 }
  }

  const palmSize = distance(landmarks[0], landmarks[9])
  if (palmSize <= Number.EPSILON) {
    return { name: 'none', confidence: 0 }
  }

  const pinchRatio = distance(landmarks[4], landmarks[8]) / palmSize
  if (pinchRatio < 0.38) {
    return {
      name: 'pinch',
      confidence: clamp01((0.45 - pinchRatio) / 0.3),
    }
  }

  const extended = FINGER_JOINTS.map(({ pip, tip }) =>
    isFingerExtended(landmarks, pip, tip),
  )
  const extendedCount = extended.filter(Boolean).length

  if (extendedCount === 4) {
    return { name: 'open-palm', confidence: 1 }
  }

  if (extended[0] && extended.slice(1).every((value) => !value)) {
    return { name: 'point', confidence: 1 }
  }

  if (extendedCount === 0) {
    return { name: 'fist', confidence: 1 }
  }

  return {
    name: 'none',
    confidence: clamp01(1 - extendedCount / 4),
  }
}

export function smoothLandmarks(
  previous: HandLandmark[] | undefined,
  current: HandLandmark[],
  alpha = 0.62,
) {
  if (!previous || previous.length !== current.length) {
    return current.map((point) => ({ ...point }))
  }

  return current.map((point, index) => ({
    x: previous[index].x + (point.x - previous[index].x) * alpha,
    y: previous[index].y + (point.y - previous[index].y) * alpha,
    z: previous[index].z + (point.z - previous[index].z) * alpha,
  }))
}

