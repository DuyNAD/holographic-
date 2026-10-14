import {
  createInitialSceneHistory,
  sceneHistoryReducer,
  type SceneHistoryState,
} from './sceneHistory'

const selectBox = (state: SceneHistoryState) =>
  sceneHistoryReducer(state, { type: 'select', id: 'box-1' })

describe('sceneHistoryReducer', () => {
  it('undoes and redoes adding an imported model', () => {
    const initial = createInitialSceneHistory()
    const object = {
      id: 'model-asset-1',
      name: 'Robot',
      kind: 'model' as const,
      assetId: 'asset-1',
      color: '#ffffff',
      position: [0, 0, 0] as [number, number, number],
      rotation: [0, 0, 0] as [number, number, number],
      scale: 1,
    }

    const added = sceneHistoryReducer(initial, { type: 'add-object', object })
    const undone = sceneHistoryReducer(added, { type: 'undo' })
    const redone = sceneHistoryReducer(undone, { type: 'redo' })

    expect(added.present.objects).toContainEqual(object)
    expect(undone.present.objects).not.toContainEqual(object)
    expect(redone.present.objects).toContainEqual(object)
  })

  it('undoes and redoes a discrete transform', () => {
    const selected = selectBox(createInitialSceneHistory())
    const moved = sceneHistoryReducer(selected, {
      type: 'translate',
      axis: 0,
      delta: 1,
    })
    const undone = sceneHistoryReducer(moved, { type: 'undo' })
    const redone = sceneHistoryReducer(undone, { type: 'redo' })

    expect(moved.present.objects[0].position[0]).toBeCloseTo(-1.2)
    expect(undone.present.objects[0].position[0]).toBe(-2.2)
    expect(redone.present.objects[0].position[0]).toBeCloseTo(-1.2)
  })

  it('groups many gesture frames into one undo entry', () => {
    let state = selectBox(createInitialSceneHistory())
    state = sceneHistoryReducer(state, { type: 'begin-interaction' })
    state = sceneHistoryReducer(state, {
      type: 'set-position',
      position: [1, 0, 0],
    })
    state = sceneHistoryReducer(state, {
      type: 'set-position',
      position: [2, 0, 0],
    })
    state = sceneHistoryReducer(state, { type: 'end-interaction' })

    expect(state.past).toHaveLength(1)
    expect(sceneHistoryReducer(state, { type: 'undo' }).present.objects[0].position).toEqual(
      [-2.2, 0, 0],
    )
  })

  it('does not create history for selection or an unchanged interaction', () => {
    let state = selectBox(createInitialSceneHistory())
    state = sceneHistoryReducer(state, { type: 'begin-interaction' })
    state = sceneHistoryReducer(state, { type: 'end-interaction' })

    expect(state.past).toHaveLength(0)
  })
})

