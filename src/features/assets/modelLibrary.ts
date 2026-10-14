import type { SceneHistoryState } from '../scene/sceneHistory'
import type { SceneObjectModel, Vector3Tuple } from '../scene/sceneState'
import { saveModelAsset, type ModelAssetRecord } from './modelAssetStore'
import { modelNameFromFile, validateGlbFile } from './modelAssetValidation'

export type ModelImportResult =
  | { ok: true; asset: ModelAssetRecord }
  | { ok: false; message: string }

export async function importModelFile(file: File): Promise<ModelImportResult> {
  const validationError = await validateGlbFile(file)
  if (validationError) return { ok: false, message: validationError }

  try {
    const { disposeModel, loadGlbModel } = await import('./modelAssetLoader')
    disposeModel(await loadGlbModel(file, 'validation'))
  } catch {
    return { ok: false, message: 'Không thể đọc nội dung file GLB.' }
  }

  const asset: ModelAssetRecord = {
    id: crypto.randomUUID(),
    name: modelNameFromFile(file.name),
    blob: file,
    size: file.size,
    createdAt: Date.now(),
  }

  try {
    await saveModelAsset(asset)
  } catch {
    return { ok: false, message: 'Không thể lưu vật thể trên thiết bị này.' }
  }

  return { ok: true, asset }
}

// Every placement gets its own object id, so one stored GLB can be placed
// in the scene many times without uploading it again.
export const createModelObject = (
  asset: Pick<ModelAssetRecord, 'id' | 'name'>,
  position: Vector3Tuple = [0, 0, 0],
): SceneObjectModel => ({
  id: `model-${crypto.randomUUID()}`,
  name: asset.name,
  kind: 'model',
  assetId: asset.id,
  color: '#ffffff',
  position,
  rotation: [0, 0, 0],
  scale: 1,
})

// An asset stays in the library while the scene or its Undo/Redo history can
// still bring back an object that renders it.
export function isAssetReferenced(
  history: SceneHistoryState,
  assetId: string,
) {
  return [history.present, ...history.past, ...history.future].some((scene) =>
    scene.objects.some((object) => object.assetId === assetId),
  )
}
