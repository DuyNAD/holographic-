import { PerspectiveCamera, Raycaster, Vector2, Vector3 } from 'three'
import {
  distanceBetweenLandmarks,
  handRotationAngle,
  intersectDragPlane,
  landmarkToNdc,
} from './gestureCoordinates'

const createSceneCamera = () => {
  const camera = new PerspectiveCamera(42, 16 / 9, 0.1, 100)
  camera.position.set(6.5, 4.3, 7.5)
  camera.lookAt(0, 0, 0)
  camera.updateMatrixWorld()
  return camera
}

const rayThrough = (camera: PerspectiveCamera, point: Vector3) => {
  const ndc = point.clone().project(camera)
  const raycaster = new Raycaster()
  raycaster.setFromCamera(new Vector2(ndc.x, ndc.y), camera)
  return raycaster.ray
}

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

  it('drags on a plane at the grabbed object depth without changing Z', () => {
    const camera = createSceneCamera()
    const object = new Vector3(0.8, 0.4, 1.6)
    const target = new Vector3(-1.5, 1.2, 1.6)

    const grabPoint = intersectDragPlane(rayThrough(camera, object), object.z)
    const dragPoint = intersectDragPlane(rayThrough(camera, target), object.z)

    expect(grabPoint?.x).toBeCloseTo(object.x)
    expect(grabPoint?.y).toBeCloseTo(object.y)
    expect(grabPoint?.z).toBeCloseTo(object.z)
    expect(dragPoint?.x).toBeCloseTo(target.x)
    expect(dragPoint?.y).toBeCloseTo(target.y)
    expect(dragPoint?.z).toBeCloseTo(object.z)
  })
})

