import { fireEvent, render, screen, waitFor } from '@testing-library/react'
import {
  createInitialSceneHistory,
  sceneHistoryReducer,
} from '../scene/sceneHistory'
import AddObjectPanel from './AddObjectPanel'
import { createModelObject } from './modelLibrary'
import type { ModelLibrary } from './useModelLibrary'

const robot = { id: 'asset-1', name: 'Robot', size: 2048, createdAt: 1 }

const createLibrary = (overrides: Partial<ModelLibrary> = {}): ModelLibrary => ({
  items: [robot],
  busy: false,
  message: 'GLB tối đa 25 MB · lưu trên thiết bị.',
  hasError: false,
  importFile: vi.fn().mockResolvedValue(null),
  removeItem: vi.fn().mockResolvedValue(undefined),
  report: vi.fn(),
  ...overrides,
})

describe('AddObjectPanel', () => {
  it('adds a built-in shape to the scene', () => {
    const dispatch = vi.fn()
    render(
      <AddObjectPanel
        dispatch={dispatch}
        history={createInitialSceneHistory()}
        library={createLibrary()}
      />,
    )

    fireEvent.click(screen.getByRole('button', { name: /Khối cầu/ }))

    expect(dispatch).toHaveBeenCalledWith({
      type: 'add-object',
      object: expect.objectContaining({ kind: 'sphere', name: 'Khối cầu' }),
    })
  })

  it('places a stored model again and again without uploading it', () => {
    const dispatch = vi.fn()
    render(
      <AddObjectPanel
        dispatch={dispatch}
        history={createInitialSceneHistory()}
        library={createLibrary()}
      />,
    )

    const robotButton = screen.getByRole('button', { name: /^Robot/ })
    expect(robotButton).toHaveAttribute('data-gesture-target')
    fireEvent.click(robotButton)
    fireEvent.click(robotButton)

    expect(dispatch).toHaveBeenCalledTimes(2)
    const [first, second] = dispatch.mock.calls.map(([action]) => action.object)
    expect(first).toMatchObject({ kind: 'model', assetId: 'asset-1' })
    expect(second.assetId).toBe('asset-1')
    expect(first.id).not.toBe(second.id)
  })

  it('removes an unused model from the library', () => {
    const library = createLibrary()
    render(
      <AddObjectPanel
        dispatch={vi.fn()}
        history={createInitialSceneHistory()}
        library={library}
      />,
    )

    fireEvent.click(screen.getByRole('button', { name: 'Xóa “Robot” khỏi kho' }))

    expect(library.removeItem).toHaveBeenCalledWith(robot)
  })

  it('keeps a model in the library while the scene still uses it', () => {
    const library = createLibrary()
    const history = sceneHistoryReducer(createInitialSceneHistory(), {
      type: 'add-object',
      object: createModelObject(robot),
    })
    render(
      <AddObjectPanel dispatch={vi.fn()} history={history} library={library} />,
    )

    fireEvent.click(screen.getByRole('button', { name: 'Xóa “Robot” khỏi kho' }))

    expect(library.removeItem).not.toHaveBeenCalled()
    expect(library.report).toHaveBeenCalledWith(
      expect.stringContaining('chưa thể xóa'),
      true,
    )
  })

  it('stores an uploaded GLB and places it in the scene', async () => {
    const dispatch = vi.fn()
    const library = createLibrary({
      items: [],
      importFile: vi.fn().mockResolvedValue(robot),
    })
    render(
      <AddObjectPanel
        dispatch={dispatch}
        history={createInitialSceneHistory()}
        library={library}
      />,
    )

    expect(screen.getByText(/Kho đang trống/)).toBeInTheDocument()
    const file = new File(['glb'], 'robot.glb')
    fireEvent.change(screen.getByLabelText('Tải file GLB vào kho'), {
      target: { files: [file] },
    })

    await waitFor(() => expect(dispatch).toHaveBeenCalledOnce())
    expect(library.importFile).toHaveBeenCalledWith(file)
    expect(dispatch.mock.calls[0][0].object).toMatchObject({ assetId: 'asset-1' })
  })
})
