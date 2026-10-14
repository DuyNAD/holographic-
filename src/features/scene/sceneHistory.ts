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

const isGestureFrame = (action: SceneAction) =>
  action.type === 'set-position' ||
  action.type === 'set-rotation' ||
  action.type === 'set-scale'

const appendPast = (past: SceneState[], state: SceneState) =>
  [...past, state].slice(-HISTORY_LIMIT)

// Pushes the changes made since the interaction began as one history entry.
// The baseline itself is left for the caller to clear or rebase.
const commitInteraction = (state: SceneHistoryState): SceneHistoryState => {
  const baseline = state.interactionBaseline
  if (!baseline || sameObjects(baseline, state.present)) return state

  return {
    ...state,
    past: appendPast(state.past, {
      ...baseline,
      selectedId: state.present.selectedId,
    }),
    future: [],
  }
}

// While a gesture interaction stays open, later frames are grouped from the
// new present so the interaction layer and the history never fall out of sync.
const rebaseInteraction = (state: SceneHistoryState, present: SceneState) =>
  state.interactionBaseline ? present : null

export function sceneHistoryReducer(
  state: SceneHistoryState,
  action: SceneHistoryAction,
): SceneHistoryState {
  switch (action.type) {
    case 'undo': {
      const committed = commitInteraction(state)
      const previous = committed.past.at(-1)
      if (!previous) return state

      return {
        present: previous,
        past: committed.past.slice(0, -1),
        future: [committed.present, ...committed.future].slice(
          0,
          HISTORY_LIMIT,
        ),
        interactionBaseline: rebaseInteraction(state, previous),
      }
    }
    case 'redo': {
      const committed = commitInteraction(state)
      const next = committed.future[0]
      if (!next) return state

      return {
        present: next,
        past: appendPast(committed.past, committed.present),
        future: committed.future.slice(1),
        interactionBaseline: rebaseInteraction(state, next),
      }
    }
    case 'begin-interaction':
      return state.interactionBaseline
        ? state
        : { ...state, interactionBaseline: state.present }
    case 'end-interaction':
      if (!state.interactionBaseline) return state
      return { ...commitInteraction(state), interactionBaseline: null }
  }

  const nextPresent = sceneReducer(state.present, action)
  if (nextPresent === state.present) return state

  if (
    action.type === 'select' ||
    (state.interactionBaseline && isGestureFrame(action))
  ) {
    return { ...state, present: nextPresent }
  }

  // Discrete edits (keyboard, buttons, reset, uploads) always get their own
  // history entry, even while a gesture interaction is still open.
  const committed = commitInteraction(state)
  return {
    present: nextPresent,
    past: appendPast(committed.past, committed.present),
    future: [],
    interactionBaseline: rebaseInteraction(state, nextPresent),
  }
}

