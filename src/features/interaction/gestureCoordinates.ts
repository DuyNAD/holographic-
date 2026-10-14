import type { HandLandmark } from '../hand-tracking/handTrackingTypes'

export interface NormalizedDevicePoint {
  x: number
  y: number
}

export function landmarkToNdc(point: HandLandmark): NormalizedDevicePoint {
  return {
    x: (1 - point.x) * 2 - 1,
    y: 1 - point.y * 2,
  }
}

export function distanceBetweenLandmarks(
  first: HandLandmark,
  second: HandLandmark,
) {
  return Math.hypot(first.x - second.x, first.y - second.y)
}

export function handRotationAngle(landmarks: HandLandmark[]) {
  const wrist = landmarks[0]
  const middleBase = landmarks[9]
  if (!wrist || !middleBase) return 0

  return Math.atan2(
    middleBase.y - wrist.y,
    (1 - middleBase.x) - (1 - wrist.x),
  )
}

