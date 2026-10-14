import type { HandLandmark } from '../hand-tracking/handTrackingTypes'
import { detectGesture, smoothLandmarks } from './gestureMath'

const createHand = (extendedFingers: number[]): HandLandmark[] => {
  const hand = Array.from({ length: 21 }, () => ({ x: 0.5, y: 0.7, z: 0 }))
  hand[0] = { x: 0.5, y: 0.9, z: 0 }
  hand[4] = { x: 0.2, y: 0.5, z: 0 }

  const fingers = [
    { mcp: 5, pip: 6, tip: 8, x: 0.38 },
    { mcp: 9, pip: 10, tip: 12, x: 0.47 },
    { mcp: 13, pip: 14, tip: 16, x: 0.56 },
    { mcp: 17, pip: 18, tip: 20, x: 0.65 },
  ]

  fingers.forEach(({ mcp, pip, tip, x }, index) => {
    hand[mcp] = { x, y: 0.64, z: 0 }
    hand[pip] = { x, y: 0.5, z: 0 }
    hand[tip] = {
      x,
      y: extendedFingers.includes(index) ? 0.18 : 0.72,
      z: 0,
    }
  })

  return hand
}

describe('detectGesture', () => {
  it('detects an open palm', () => {
    expect(detectGesture(createHand([0, 1, 2, 3])).name).toBe('open-palm')
  })

  it('detects a pointing hand', () => {
    expect(detectGesture(createHand([0])).name).toBe('point')
  })

  it('detects a fist', () => {
    expect(detectGesture(createHand([])).name).toBe('fist')
  })

  it('gives pinch priority when thumb and index are close', () => {
    const hand = createHand([0])
    hand[4] = { ...hand[8], x: hand[8].x - 0.01 }

    expect(detectGesture(hand).name).toBe('pinch')
  })

  it('rejects incomplete landmark data', () => {
    expect(detectGesture([])).toEqual({ name: 'none', confidence: 0 })
  })
})

describe('smoothLandmarks', () => {
  it('uses a responsive default smoothing factor', () => {
    const previous = [{ x: 0, y: 0, z: 0 }]
    const current = [{ x: 1, y: 1, z: 1 }]

    expect(smoothLandmarks(previous, current)).toEqual([
      { x: 0.62, y: 0.62, z: 0.62 },
    ])
  })

  it('applies exponential smoothing between frames', () => {
    const previous = [{ x: 0, y: 0, z: 0 }]
    const current = [{ x: 1, y: 1, z: 1 }]

    expect(smoothLandmarks(previous, current, 0.25)).toEqual([
      { x: 0.25, y: 0.25, z: 0.25 },
    ])
  })
})

