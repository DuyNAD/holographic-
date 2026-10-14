import {
  HAND_TRACKING_FRAME_HEIGHT,
  HAND_TRACKING_FRAME_WIDTH,
  MAX_TRACKED_HANDS,
} from './handTrackingConfig'

describe('hand tracking configuration', () => {
  it('limits tracking to two hands', () => {
    expect(MAX_TRACKED_HANDS).toBe(2)
  })

  it('keeps the inference frame small and aligned with the camera ratio', () => {
    expect(HAND_TRACKING_FRAME_WIDTH).toBe(320)
    expect(HAND_TRACKING_FRAME_HEIGHT).toBe(180)
    expect(HAND_TRACKING_FRAME_WIDTH / HAND_TRACKING_FRAME_HEIGHT).toBe(16 / 9)
  })
})

