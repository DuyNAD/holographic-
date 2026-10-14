import {
  createInitialSceneState,
  type SceneObjectKind,
  type SceneObjectModel,
  type SceneState,
  type Vector3Tuple,
} from './sceneState'

const SCENE_STORAGE_KEY = 'holographic-scene-v1'
const objectKinds: SceneObjectKind[] = ['box', 'sphere', 'cylinder', 'model']

const isVector = (value: unknown): value is Vector3Tuple =>
  Array.isArray(value) &&
  value.length === 3 &&
  value.every((item) => typeof item === 'number' && Number.isFinite(item))

const isSceneObject = (value: unknown): value is SceneObjectModel => {
  if (!value || typeof value !== 'object') return false
  const object = value as Partial<SceneObjectModel>

  const commonFieldsAreValid =
    typeof object.id === 'string' &&
    typeof object.name === 'string' &&
    typeof object.kind === 'string' &&
    objectKinds.includes(object.kind as SceneObjectKind) &&
    typeof object.color === 'string' &&
    isVector(object.position) &&
    isVector(object.rotation) &&
    typeof object.scale === 'number' &&
    Number.isFinite(object.scale)

  return (
    commonFieldsAreValid &&
    (object.kind !== 'model' || typeof object.assetId === 'string')
  )
}

export function loadSceneState(storage: Storage = localStorage): SceneState {
  try {
    const serialized = storage.getItem(SCENE_STORAGE_KEY)
    if (!serialized) return createInitialSceneState()

    const parsed = JSON.parse(serialized) as Partial<SceneState>
    if (!Array.isArray(parsed.objects) || !parsed.objects.every(isSceneObject)) {
      return createInitialSceneState()
    }

    return {
      objects: parsed.objects.map((object) => ({
        ...object,
        scale: Math.min(2.5, Math.max(0.4, object.scale)),
      })),
      selectedId: null,
    }
  } catch {
    return createInitialSceneState()
  }
}

export function saveSceneState(
  scene: SceneState,
  storage: Storage = localStorage,
) {
  storage.setItem(
    SCENE_STORAGE_KEY,
    JSON.stringify({ objects: scene.objects, selectedId: null }),
  )
}

