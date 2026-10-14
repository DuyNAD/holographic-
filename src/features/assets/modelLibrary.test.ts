import { createInitialSceneHistory, sceneHistoryReducer } from '../scene/sceneHistory'
import { createShapeObject } from '../scene/sceneState'
import { createModelObject, isAssetReferenced } from './modelLibrary'

describe('modelLibrary', () => {
  it('creates a new scene object for every placement of one asset', () => {
    const asset = { id: 'asset-1', name: 'Robot' }
    const first = createModelObject(asset)
    const second = createModelObject(asset)

    expect(first).toMatchObject({ kind: 'model', assetId: 'asset-1', name: 'Robot' })
    expect(second.assetId).toBe('asset-1')
    expect(first.id).not.toBe(second.id)
  })

  it('creates built-in shapes with unique ids', () => {
    const first = createShapeObject('sphere')
    const second = createShapeObject('sphere')

    expect(first).toMatchObject({ kind: 'sphere', name: 'Khối cầu' })
    expect(first.id).not.toBe(second.id)
  })

  it('treats an asset as referenced while undo history can restore it', () => {
    const object = createModelObject({ id: 'asset-1', name: 'Robot' })
    let history = createInitialSceneHistory()

    expect(isAssetReferenced(history, 'asset-1')).toBe(false)

    history = sceneHistoryReducer(history, { type: 'add-object', object })
    expect(isAssetReferenced(history, 'asset-1')).toBe(true)

    history = sceneHistoryReducer(history, { type: 'remove-object' })
    expect(history.present.objects).not.toContainEqual(object)
    expect(isAssetReferenced(history, 'asset-1')).toBe(true)
  })
})
