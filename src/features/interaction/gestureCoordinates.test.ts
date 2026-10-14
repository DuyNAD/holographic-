import {
  distanceBetweenLandmarks,
  handRotationAngle,
  landmarkToNdc,
} from './gestureCoordinates'

describe('gestureCoordinates', () => {
  it('maps mirrored camera coordinates into normalized device coordinates', () => {
    expect(landmarkToNdc({ x: 0.25, y: 0.75, z: 0 })).toEqual({
      x: 0.5,
      y: -0.5,
    })
  })

  it('measures two-hand scale distance in camera space', () => {
    expect(
      distanceBetweenLandmarks(
        { x: 0, y: 0, z: 0 },
        { x: 0.3, y: 0.4, z: 0 },
      ),
    ).toBeCloseTo(0.5)
  })

  it('calculates wrist rotation using mirrored coordinates', () => {
    const landmarks = Array.from({ length: 21 }, () => ({ x: 0, y: 0, z: 0 }))
    landmarks[0] = { x: 0.5, y: 0.5, z: 0 }
    landmarks[9] = { x: 0.5, y: 0.2, z: 0 }

    expect(handRotationAngle(landmarks)).toBeCloseTo(-Math.PI / 2)
  })
})

