import {
  createInitialSceneState,
  sceneReducer,
  type SceneAction,
  type SceneState,
} from './sceneState'

export type SceneHistoryAction =
  | SceneAction
  | { type: 'undo' }
  | { type: 'redo' }
  | { type: 'begin-interaction' }
  | { type: 'end-interaction' }

export interface SceneHistoryState {
  present: SceneState
  past: SceneState[]
  future: SceneState[]
  interactionBaseline: SceneState | null
}

const HISTORY_LIMIT = 50

export const createInitialSceneHistory = (
  present = createInitialSceneState(),
): SceneHistoryState => ({
  present,
  past: [],
  future: [],
  interactionBaseline: null,
})

const sameObjects = (first: SceneState, second: SceneState) =>
  JSON.stringify(first.objects) === JSON.stringify(second.objects)

const appendPast = (past: SceneState[], state: SceneState) =>
  [...past, state].slice(-HISTORY_LIMIT)

export function sceneHistoryReducer(
  state: SceneHistoryState,
  action: SceneHistoryAction,
): SceneHistoryState {
  switch (action.type) {
    case 'undo': {
      const previous = state.past.at(-1)
      if (!previous) return state

      return {
        present: previous,
        past: state.past.slice(0, -1),
        future: [state.present, ...state.future].slice(0, HISTORY_LIMIT),
        interactionBaseline: null,
      }
    }
    case 'redo': {
      const next = state.future[0]
      if (!next) return state

      return {
        present: next,
        past: appendPast(state.past, state.present),
        future: state.future.slice(1),
        interactionBaseline: null,
      }
    }
    case 'begin-interaction':
      return state.interactionBaseline
        ? state
        : { ...state, interactionBaseline: state.present }
    case 'end-interaction': {
      const baseline = state.interactionBaseline
      if (!baseline) return state

      if (sameObjects(baseline, state.present)) {
        return { ...state, interactionBaseline: null }
      }

      return {
        ...state,
        past: appendPast(state.past, {
          ...baseline,
          selectedId: state.present.selectedId,
        }),
        future: [],
        interactionBaseline: null,
      }
    }
  }

  const nextPresent = sceneReducer(state.present, action)
  if (nextPresent === state.present) return state

  if (action.type === 'select' || state.interactionBaseline) {
    return { ...state, present: nextPresent }
  }

  return {
    present: nextPresent,
    past: appendPast(state.past, state.present),
    future: [],
    interactionBaseline: null,
  }
}

