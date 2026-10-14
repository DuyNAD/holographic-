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

  it('keeps grouping gesture frames after an undo during an interaction', () => {
    let state = selectBox(createInitialSceneHistory())
    state = sceneHistoryReducer(state, { type: 'begin-interaction' })
    state = sceneHistoryReducer(state, {
      type: 'set-position',
      position: [1, 0, 0],
    })
    state = sceneHistoryReducer(state, { type: 'undo' })

    expect(state.present.objects[0].position).toEqual([-2.2, 0, 0])
    expect(state.past).toHaveLength(0)
    expect(state.future).toHaveLength(1)

    for (let frame = 1; frame <= 10; frame += 1) {
      state = sceneHistoryReducer(state, {
        type: 'set-position',
        position: [frame, 0, 0],
      })
    }

    expect(state.past).toHaveLength(0)

    state = sceneHistoryReducer(state, { type: 'end-interaction' })

    expect(state.past).toHaveLength(1)
    expect(state.future).toHaveLength(0)
    expect(state.interactionBaseline).toBeNull()
    expect(
      sceneHistoryReducer(state, { type: 'undo' }).present.objects[0].position,
    ).toEqual([-2.2, 0, 0])
  })

  it('keeps grouping gesture frames after a redo during an interaction', () => {
    let state = selectBox(createInitialSceneHistory())
    state = sceneHistoryReducer(state, { type: 'translate', axis: 0, delta: 1 })
    state = sceneHistoryReducer(state, { type: 'undo' })
    state = sceneHistoryReducer(state, { type: 'begin-interaction' })
    state = sceneHistoryReducer(state, { type: 'redo' })

    expect(state.present.objects[0].position[0]).toBeCloseTo(-1.2)
    expect(state.past).toHaveLength(1)

    state = sceneHistoryReducer(state, {
      type: 'set-position',
      position: [3, 0, 0],
    })
    state = sceneHistoryReducer(state, {
      type: 'set-position',
      position: [4, 0, 0],
    })
    state = sceneHistoryReducer(state, { type: 'end-interaction' })

    expect(state.past).toHaveLength(2)
    expect(
      sceneHistoryReducer(state, { type: 'undo' }).present.objects[0]
        .position[0],
    ).toBeCloseTo(-1.2)
  })

  it('records discrete edits separately while an interaction is open', () => {
    let state = selectBox(createInitialSceneHistory())
    state = sceneHistoryReducer(state, { type: 'begin-interaction' })
    state = sceneHistoryReducer(state, {
      type: 'set-position',
      position: [1, 0, 0],
    })
    state = sceneHistoryReducer(state, { type: 'translate', axis: 1, delta: 1 })
    state = sceneHistoryReducer(state, {
      type: 'set-position',
      position: [2, 1, 0],
    })
    state = sceneHistoryReducer(state, { type: 'end-interaction' })

    expect(state.past).toHaveLength(3)

    state = sceneHistoryReducer(state, { type: 'undo' })
    expect(state.present.objects[0].position).toEqual([1, 1, 0])
    state = sceneHistoryReducer(state, { type: 'undo' })
    expect(state.present.objects[0].position).toEqual([1, 0, 0])
    state = sceneHistoryReducer(state, { type: 'undo' })
    expect(state.present.objects[0].position).toEqual([-2.2, 0, 0])
  })

  it('lets a scene reset be undone while an interaction is open', () => {
    let state = selectBox(createInitialSceneHistory())
    state = sceneHistoryReducer(state, { type: 'translate', axis: 0, delta: 1 })
    state = sceneHistoryReducer(state, { type: 'begin-interaction' })
    state = sceneHistoryReducer(state, { type: 'reset' })
    state = sceneHistoryReducer(state, { type: 'end-interaction' })

    expect(state.past).toHaveLength(2)
    expect(
      sceneHistoryReducer(state, { type: 'undo' }).present.objects[0]
        .position[0],
    ).toBeCloseTo(-1.2)
  })

  it('does not create history for selection or an unchanged interaction', () => {
    let state = selectBox(createInitialSceneHistory())
    state = sceneHistoryReducer(state, { type: 'begin-interaction' })
    state = sceneHistoryReducer(state, { type: 'end-interaction' })

    expect(state.past).toHaveLength(0)
  })

  it('undoes and redoes removing an object', () => {
    const selected = selectBox(createInitialSceneHistory())
    const removed = sceneHistoryReducer(selected, { type: 'remove-object' })
    const undone = sceneHistoryReducer(removed, { type: 'undo' })
    const redone = sceneHistoryReducer(undone, { type: 'redo' })

    expect(removed.present.objects).toHaveLength(2)
    expect(removed.past).toHaveLength(1)
    expect(undone.present.objects[0].id).toBe('box-1')
    expect(redone.present.objects).toHaveLength(2)
  })
})
