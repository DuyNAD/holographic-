import { createInitialSceneState } from './sceneState'
import { loadSceneState, saveSceneState } from './sceneStorage'

describe('sceneStorage', () => {
  beforeEach(() => localStorage.clear())

  it('round-trips a valid scene without restoring selection', () => {
    const scene = { ...createInitialSceneState(), selectedId: 'box-1' }
    scene.objects[0].position = [1, 2, 0]

    saveSceneState(scene)
    const restored = loadSceneState()

    expect(restored.objects[0].position).toEqual([1, 2, 0])
    expect(restored.selectedId).toBeNull()
  })

  it('falls back safely when stored data is corrupt', () => {
    localStorage.setItem('holographic-scene-v1', '{not-json')

    expect(loadSceneState()).toEqual(createInitialSceneState())
  })

  it('restores imported model metadata', () => {
    const scene = createInitialSceneState()
    scene.objects.push({
      id: 'model-asset-1',
      name: 'Robot',
      kind: 'model',
      assetId: 'asset-1',
      color: '#ffffff',
      position: [0, 0, 0],
      rotation: [0, 0, 0],
      scale: 1,
    })

    saveSceneState(scene)

    expect(loadSceneState().objects.at(-1)?.assetId).toBe('asset-1')
  })

  it('rejects imported model metadata without an asset id', () => {
    const scene = createInitialSceneState()
    localStorage.setItem(
      'holographic-scene-v1',
      JSON.stringify({
        objects: [
          ...scene.objects,
          {
            id: 'broken-model',
            name: 'Broken',
            kind: 'model',
            color: '#ffffff',
            position: [0, 0, 0],
            rotation: [0, 0, 0],
            scale: 1,
          },
        ],
      }),
    )

    expect(loadSceneState()).toEqual(createInitialSceneState())
  })
})

