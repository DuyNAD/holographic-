import { fireEvent, render, screen, waitFor } from '@testing-library/react'
import { Group } from 'three'
import ModelUploadPanel from './ModelUploadPanel'
import { loadGlbModel } from './modelAssetLoader'
import { saveModelAsset } from './modelAssetStore'

vi.mock('./modelAssetLoader', () => ({
  disposeModel: vi.fn(),
  loadGlbModel: vi.fn(),
}))

vi.mock('./modelAssetStore', () => ({
  saveModelAsset: vi.fn(),
}))

const createGlbFile = () => {
  const bytes = new Uint8Array(12)
  const view = new DataView(bytes.buffer)
  view.setUint32(0, 0x46546c67, true)
  view.setUint32(4, 2, true)
  view.setUint32(8, bytes.byteLength, true)
  return new File([bytes], 'robot.glb', { type: 'model/gltf-binary' })
}

describe('ModelUploadPanel', () => {
  beforeEach(() => {
    vi.clearAllMocks()
    vi.mocked(loadGlbModel).mockResolvedValue(new Group())
  })

  it('stores a valid GLB and adds it to the scene', async () => {
    const dispatch = vi.fn()
    vi.mocked(saveModelAsset).mockResolvedValue()

    render(<ModelUploadPanel dispatch={dispatch} />)
    fireEvent.change(screen.getByLabelText('Chọn file GLB'), {
      target: { files: [createGlbFile()] },
    })

    await waitFor(() => expect(saveModelAsset).toHaveBeenCalledOnce())
    expect(dispatch).toHaveBeenCalledWith(
      expect.objectContaining({
        type: 'add-object',
        object: expect.objectContaining({ name: 'robot', kind: 'model' }),
      }),
    )
    expect(screen.getByText('Đã thêm “robot” vào cảnh.')).toBeInTheDocument()
  })

  it('rejects a non-GLB file without storing it', async () => {
    const dispatch = vi.fn()
    render(<ModelUploadPanel dispatch={dispatch} />)

    fireEvent.change(screen.getByLabelText('Chọn file GLB'), {
      target: { files: [new File(['mesh'], 'mesh.obj')] },
    })

    expect(await screen.findByText('Chỉ hỗ trợ file GLB.')).toBeInTheDocument()
    expect(saveModelAsset).not.toHaveBeenCalled()
    expect(dispatch).not.toHaveBeenCalled()
  })

  it('reports a GLB that cannot be parsed', async () => {
    const dispatch = vi.fn()
    vi.mocked(loadGlbModel).mockRejectedValue(new Error('Invalid GLB'))
    render(<ModelUploadPanel dispatch={dispatch} />)

    fireEvent.change(screen.getByLabelText('Chọn file GLB'), {
      target: { files: [createGlbFile()] },
    })

    expect(
      await screen.findByText('Không thể đọc nội dung file GLB.'),
    ).toBeInTheDocument()
    expect(saveModelAsset).not.toHaveBeenCalled()
    expect(dispatch).not.toHaveBeenCalled()
  })
})
