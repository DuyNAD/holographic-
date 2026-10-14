import { Plane, Vector3, type Ray } from 'three'
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

const DRAG_PLANE_NORMAL = new Vector3(0, 0, 1)

// Drags happen on a camera-facing XY plane at the grabbed object's depth, so
// moving an object by hand never changes its Z position.
export function intersectDragPlane(ray: Ray, depth: number) {
  const plane = new Plane(DRAG_PLANE_NORMAL, -depth)
  return ray.intersectPlane(plane, new Vector3())
}
