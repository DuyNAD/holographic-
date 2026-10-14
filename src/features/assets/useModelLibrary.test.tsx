import { act, renderHook, waitFor } from '@testing-library/react'
import { Group } from 'three'
import { loadGlbModel } from './modelAssetLoader'
import {
  deleteModelAsset,
  listModelAssets,
  saveModelAsset,
  type ModelAssetRecord,
} from './modelAssetStore'
import { useModelLibrary } from './useModelLibrary'

vi.mock('./modelAssetLoader', () => ({
  disposeModel: vi.fn(),
  loadGlbModel: vi.fn(),
}))

vi.mock('./modelAssetStore', () => ({
  deleteModelAsset: vi.fn(),
  listModelAssets: vi.fn(),
  saveModelAsset: vi.fn(),
}))

const storedAsset: ModelAssetRecord = {
  id: 'asset-1',
  name: 'Ghế',
  blob: new Blob(),
  size: 128,
  createdAt: 1,
}

const createGlbFile = () => {
  const bytes = new Uint8Array(12)
  const view = new DataView(bytes.buffer)
  view.setUint32(0, 0x46546c67, true)
  view.setUint32(4, 2, true)
  view.setUint32(8, bytes.byteLength, true)
  return new File([bytes], 'robot.glb', { type: 'model/gltf-binary' })
}

describe('useModelLibrary', () => {
  beforeEach(() => {
    vi.clearAllMocks()
    vi.mocked(listModelAssets).mockResolvedValue([storedAsset])
    vi.mocked(saveModelAsset).mockResolvedValue()
    vi.mocked(deleteModelAsset).mockResolvedValue()
    vi.mocked(loadGlbModel).mockResolvedValue(new Group())
  })

  it('loads stored assets from the device', async () => {
    const { result } = renderHook(() => useModelLibrary())

    await waitFor(() => expect(result.current.items).toHaveLength(1))
    expect(result.current.items[0]).toEqual({
      id: 'asset-1',
      name: 'Ghế',
      size: 128,
      createdAt: 1,
    })
  })

  it('stores an imported GLB at the top of the library', async () => {
    const { result } = renderHook(() => useModelLibrary())
    await waitFor(() => expect(result.current.items).toHaveLength(1))

    let imported: Awaited<ReturnType<typeof result.current.importFile>> = null
    await act(async () => {
      imported = await result.current.importFile(createGlbFile())
    })

    expect(saveModelAsset).toHaveBeenCalledOnce()
    expect(imported).toMatchObject({ name: 'robot' })
    expect(result.current.items.map(({ name }) => name)).toEqual(['robot', 'Ghế'])
    expect(result.current.message).toBe('Đã lưu “robot” vào kho.')
  })

  it('reports an invalid file without storing it', async () => {
    const { result } = renderHook(() => useModelLibrary())

    await act(async () => {
      await result.current.importFile(new File(['mesh'], 'mesh.obj'))
    })

    expect(saveModelAsset).not.toHaveBeenCalled()
    expect(result.current.hasError).toBe(true)
    expect(result.current.message).toBe('Chỉ hỗ trợ file GLB.')
  })

  it('removes an asset from the device library', async () => {
    const { result } = renderHook(() => useModelLibrary())
    await waitFor(() => expect(result.current.items).toHaveLength(1))

    await act(async () => {
      await result.current.removeItem(result.current.items[0])
    })

    expect(deleteModelAsset).toHaveBeenCalledWith('asset-1')
    expect(result.current.items).toHaveLength(0)
  })
})
