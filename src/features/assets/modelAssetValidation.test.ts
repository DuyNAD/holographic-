import {
  modelNameFromFile,
  validateGlbFile,
} from './modelAssetValidation'

const createGlbFile = (name = 'robot.glb') => {
  const bytes = new Uint8Array(12)
  const view = new DataView(bytes.buffer)
  view.setUint32(0, 0x46546c67, true)
  view.setUint32(4, 2, true)
  view.setUint32(8, bytes.byteLength, true)
  return new File([bytes], name, { type: 'model/gltf-binary' })
}

describe('validateGlbFile', () => {
  it('accepts a GLB 2.0 header', async () => {
    await expect(validateGlbFile(createGlbFile())).resolves.toBeNull()
  })

  it('rejects another extension', async () => {
    await expect(validateGlbFile(createGlbFile('robot.gltf'))).resolves.toBe(
      'Chỉ hỗ trợ file GLB.',
    )
  })

  it('rejects an invalid GLB header', async () => {
    const file = new File([new Uint8Array(12)], 'broken.glb')
    await expect(validateGlbFile(file)).resolves.toBe(
      'File không phải GLB 2.0 hợp lệ.',
    )
  })
})

describe('modelNameFromFile', () => {
  it('creates a readable model name', () => {
    expect(modelNameFromFile('Iron-Man.glb')).toBe('Iron-Man')
  })
})
