export type Vector3Tuple = [number, number, number]

export type SceneObjectKind = 'box' | 'sphere' | 'cylinder' | 'model'

export interface SceneObjectModel {
  id: string
  name: string
  kind: SceneObjectKind
  assetId?: string
  color: string
  position: Vector3Tuple
  rotation: Vector3Tuple
  scale: number
}

export interface SceneState {
  objects: SceneObjectModel[]
  selectedId: string | null
}

export type SceneAction =
  | { type: 'add-object'; object: SceneObjectModel }
  | { type: 'select'; id: string | null }
  | { type: 'translate'; axis: 0 | 1 | 2; delta: number }
  | { type: 'rotate'; axis: 0 | 1 | 2; delta: number }
  | { type: 'scale'; delta: number }
  | { type: 'set-position'; position: Vector3Tuple }
  | { type: 'set-rotation'; rotation: Vector3Tuple }
  | { type: 'set-scale'; scale: number }
  | { type: 'reset' }

const createObjects = (): SceneObjectModel[] => [
  {
    id: 'box-1',
    name: 'Khối lập phương',
    kind: 'box',
    color: '#43c7ff',
    position: [-2.2, 0, 0],
    rotation: [0, 0.35, 0],
    scale: 1,
  },
  {
    id: 'sphere-1',
    name: 'Khối cầu',
    kind: 'sphere',
    color: '#7d67ff',
    position: [0, 0, 0],
    rotation: [0, 0, 0],
    scale: 1,
  },
  {
    id: 'cylinder-1',
    name: 'Khối trụ',
    kind: 'cylinder',
    color: '#43e0aa',
    position: [2.2, 0, 0],
    rotation: [0, 0, 0.18],
    scale: 1,
  },
]

export const createInitialSceneState = (): SceneState => ({
  objects: createObjects(),
  selectedId: null,
})

const updateSelected = (
  state: SceneState,
  update: (object: SceneObjectModel) => SceneObjectModel,
): SceneState => {
  if (!state.selectedId) {
    return state
  }

  return {
    ...state,
    objects: state.objects.map((object) =>
      object.id === state.selectedId ? update(object) : object,
    ),
  }
}

const updateTuple = (
  tuple: Vector3Tuple,
  axis: 0 | 1 | 2,
  delta: number,
): Vector3Tuple => {
  const next: Vector3Tuple = [...tuple]
  next[axis] += delta
  return next
}

export function sceneReducer(state: SceneState, action: SceneAction): SceneState {
  switch (action.type) {
    case 'add-object':
      if (state.objects.some(({ id }) => id === action.object.id)) return state
      return {
        objects: [...state.objects, action.object],
        selectedId: action.object.id,
      }
    case 'select':
      return { ...state, selectedId: action.id }
    case 'translate':
      return updateSelected(state, (object) => ({
        ...object,
        position: updateTuple(object.position, action.axis, action.delta),
      }))
    case 'rotate':
      return updateSelected(state, (object) => ({
        ...object,
        rotation: updateTuple(object.rotation, action.axis, action.delta),
      }))
    case 'scale':
      return updateSelected(state, (object) => ({
        ...object,
        scale: Math.min(2.5, Math.max(0.4, object.scale + action.delta)),
      }))
    case 'set-position':
      return updateSelected(state, (object) => ({
        ...object,
        position: action.position,
      }))
    case 'set-rotation':
      return updateSelected(state, (object) => ({
        ...object,
        rotation: action.rotation,
      }))
    case 'set-scale':
      return updateSelected(state, (object) => ({
        ...object,
        scale: Math.min(2.5, Math.max(0.4, action.scale)),
      }))
    case 'reset':
      return createInitialSceneState()
  }
}

