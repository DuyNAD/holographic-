import { Box3, BoxGeometry, Group, Mesh, MeshBasicMaterial, Vector3 } from 'three'
import {
  disposeModel,
  loadGlbModel,
  prepareModelScene,
} from './modelAssetLoader'

const createTriangleGlb = () => {
  const json = JSON.stringify({
    asset: { version: '2.0' },
    scene: 0,
    scenes: [{ nodes: [0] }],
    nodes: [{ mesh: 0 }],
    meshes: [{ primitives: [{ attributes: { POSITION: 0 }, indices: 1 }] }],
    buffers: [{ byteLength: 42 }],
    bufferViews: [
      { buffer: 0, byteOffset: 0, byteLength: 36, target: 34962 },
      { buffer: 0, byteOffset: 36, byteLength: 6, target: 34963 },
    ],
    accessors: [
      {
        bufferView: 0,
        componentType: 5126,
        count: 3,
        type: 'VEC3',
        min: [0, 0, 0],
        max: [1, 1, 0],
      },
      { bufferView: 1, componentType: 5123, count: 3, type: 'SCALAR' },
    ],
  })
  const encoder = new TextEncoder()
  const jsonBytes = encoder.encode(json)
  const paddedJsonLength = Math.ceil(jsonBytes.length / 4) * 4
  const binaryLength = 44
  const totalLength = 12 + 8 + paddedJsonLength + 8 + binaryLength
  const bytes = new Uint8Array(totalLength)
  const view = new DataView(bytes.buffer)

  view.setUint32(0, 0x46546c67, true)
  view.setUint32(4, 2, true)
  view.setUint32(8, totalLength, true)
  view.setUint32(12, paddedJsonLength, true)
  view.setUint32(16, 0x4e4f534a, true)
  bytes.fill(0x20, 20, 20 + paddedJsonLength)
  bytes.set(jsonBytes, 20)

  const binaryHeader = 20 + paddedJsonLength
  view.setUint32(binaryHeader, binaryLength, true)
  view.setUint32(binaryHeader + 4, 0x004e4942, true)
  const binaryStart = binaryHeader + 8
  const positions = new Float32Array([
    0, 0, 0,
    1, 0, 0,
    0, 1, 0,
  ])
  bytes.set(new Uint8Array(positions.buffer), binaryStart)
  const indices = new Uint16Array([0, 1, 2])
  bytes.set(new Uint8Array(indices.buffer), binaryStart + 36)

  return new Blob([bytes], { type: 'model/gltf-binary' })
}

describe('prepareModelScene', () => {
  it('centers, normalizes, and tags every model child for raycasting', () => {
    const source = new Group()
    const mesh = new Mesh(
      new BoxGeometry(4, 2, 1),
      new MeshBasicMaterial({ color: '#ffffff' }),
    )
    mesh.position.set(5, 3, -2)
    source.add(mesh)

    const prepared = prepareModelScene(source, 'model-1')
    const bounds = new Box3().setFromObject(prepared)
    const size = bounds.getSize(new Vector3())
    const center = bounds.getCenter(new Vector3())

    expect(Math.max(size.x, size.y, size.z)).toBeCloseTo(1.6)
    expect(center.length()).toBeCloseTo(0)
    expect(prepared.userData.objectId).toBe('model-1')
    expect(mesh.userData.objectId).toBe('model-1')
    expect(mesh.castShadow).toBe(true)
    expect(mesh.receiveShadow).toBe(true)

    disposeModel(prepared)
  })

  it('rejects a model without renderable geometry', () => {
    expect(() => prepareModelScene(new Group(), 'empty')).toThrow(
      'Model does not contain renderable geometry.',
    )
  })

  it('loads a binary GLB into a normalized scene', async () => {
    const model = await loadGlbModel(createTriangleGlb(), 'triangle-model')
    let meshCount = 0
    model.traverse((child) => {
      if (child.type === 'Mesh') meshCount += 1
    })

    expect(meshCount).toBe(1)
    expect(model.userData.objectId).toBe('triangle-model')
    disposeModel(model)
  })
})
