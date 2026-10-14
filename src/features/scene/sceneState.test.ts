import {
  createInitialSceneState,
  createShapeObject,
  findSpawnPosition,
  sceneReducer,
} from './sceneState'

describe('sceneReducer', () => {
  it('adds and selects an imported model', () => {
    const initial = createInitialSceneState()
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

    const next = sceneReducer(initial, { type: 'add-object', object })

    expect(next.objects.at(-1)).toEqual(object)
    expect(next.selectedId).toBe(object.id)
  })

  it('does not add an object with a duplicate id', () => {
    const initial = createInitialSceneState()
    const duplicate = sceneReducer(initial, {
      type: 'add-object',
      object: { ...initial.objects[0] },
    })

    expect(duplicate).toBe(initial)
  })

  it('does not transform the scene before an object is selected', () => {
    const initial = createInitialSceneState()
    const next = sceneReducer(initial, {
      type: 'translate',
      axis: 0,
      delta: 1,
    })

    expect(next).toBe(initial)
  })

  it('selects and transforms only the selected object', () => {
    const selected = sceneReducer(createInitialSceneState(), {
      type: 'select',
      id: 'sphere-1',
    })
    const translated = sceneReducer(selected, {
      type: 'translate',
      axis: 0,
      delta: 0.5,
    })

    expect(translated.objects.find(({ id }) => id === 'sphere-1')?.position[0]).toBe(
      0.5,
    )
    expect(translated.objects.find(({ id }) => id === 'box-1')?.position[0]).toBe(
      -2.2,
    )
  })

  it('keeps scale within the safe interaction range', () => {
    const selected = sceneReducer(createInitialSceneState(), {
      type: 'select',
      id: 'box-1',
    })
    const tooSmall = sceneReducer(selected, { type: 'scale', delta: -100 })
    const tooLarge = sceneReducer(selected, { type: 'scale', delta: 100 })

    expect(tooSmall.objects[0].scale).toBe(0.4)
    expect(tooLarge.objects[0].scale).toBe(2.5)
  })

  it('applies absolute gesture transforms to the selected object', () => {
    const selected = sceneReducer(createInitialSceneState(), {
      type: 'select',
      id: 'sphere-1',
    })
    const moved = sceneReducer(selected, {
      type: 'set-position',
      position: [1, 2, 0],
    })
    const rotated = sceneReducer(moved, {
      type: 'set-rotation',
      rotation: [0, 0, 1.2],
    })
    const scaled = sceneReducer(rotated, { type: 'set-scale', scale: 8 })
    const sphere = scaled.objects.find(({ id }) => id === 'sphere-1')

    expect(sphere?.position).toEqual([1, 2, 0])
    expect(sphere?.rotation).toEqual([0, 0, 1.2])
    expect(sphere?.scale).toBe(2.5)
  })

  it('resets transforms and selection', () => {
    const selected = sceneReducer(createInitialSceneState(), {
      type: 'select',
      id: 'cylinder-1',
    })
    const transformed = sceneReducer(selected, {
      type: 'rotate',
      axis: 1,
      delta: 1,
    })

    expect(sceneReducer(transformed, { type: 'reset' })).toEqual(
      createInitialSceneState(),
    )
  })

  it('removes the selected object and clears the selection', () => {
    const selected = sceneReducer(createInitialSceneState(), {
      type: 'select',
      id: 'sphere-1',
    })
    const next = sceneReducer(selected, { type: 'remove-object' })

    expect(next.objects.map(({ id }) => id)).toEqual(['box-1', 'cylinder-1'])
    expect(next.selectedId).toBeNull()
  })

  it('removes an object by id and keeps a different selection', () => {
    const selected = sceneReducer(createInitialSceneState(), {
      type: 'select',
      id: 'box-1',
    })
    const next = sceneReducer(selected, {
      type: 'remove-object',
      id: 'cylinder-1',
    })

    expect(next.objects.map(({ id }) => id)).toEqual(['box-1', 'sphere-1'])
    expect(next.selectedId).toBe('box-1')
  })

  it('ignores removal without a selection or with an unknown id', () => {
    const initial = createInitialSceneState()

    expect(sceneReducer(initial, { type: 'remove-object' })).toBe(initial)
    expect(
      sceneReducer(initial, { type: 'remove-object', id: 'missing' }),
    ).toBe(initial)
  })

  it('spawns new objects in a free slot instead of on top of others', () => {
    const { objects } = createInitialSceneState()

    expect(findSpawnPosition([])).toEqual([0, 0, 0])
    expect(findSpawnPosition(objects)).toEqual([0, 1.9, 0])

    const crowded = [...objects, createShapeObject('box', [0, 1.9, 0])]
    expect(findSpawnPosition(crowded)).toEqual([-2.2, 1.9, 0])
  })
})
