import type { HandLandmark } from '../hand-tracking/handTrackingTypes'

export const GESTURE_TARGET_SELECTOR = '[data-gesture-target]'
export const HUD_SELECTOR = '[data-hud]'

// Landmarks are in camera space; the preview is mirrored, so x is flipped to
// match what the user sees across the full window.
export const landmarkToViewport = (point: HandLandmark) => ({
  x: (1 - point.x) * window.innerWidth,
  y: point.y * window.innerHeight,
})

const elementAt = (point: HandLandmark) => {
  const { x, y } = landmarkToViewport(point)
  return document.elementFromPoint(x, y)
}

export const gestureTargetAt = (point: HandLandmark) =>
  elementAt(point)?.closest<HTMLElement>(GESTURE_TARGET_SELECTOR) ?? null

export const isOverHud = (point: HandLandmark) =>
  Boolean(elementAt(point)?.closest(HUD_SELECTOR))
