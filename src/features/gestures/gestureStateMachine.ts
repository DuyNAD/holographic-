import type {
  GestureMachineState,
  GestureObservation,
} from './gestureTypes'

export interface GestureMachineConfig {
  activationFrames: number
  releaseFrames: number
  minimumConfidence: number
}

export const DEFAULT_GESTURE_MACHINE_CONFIG: GestureMachineConfig = {
  activationFrames: 2,
  releaseFrames: 2,
  minimumConfidence: 0.6,
}

export const createGestureMachineState = (): GestureMachineState => ({
  current: 'none',
  candidate: 'none',
  candidateFrames: 0,
  missingFrames: 0,
  confidence: 0,
})

export function advanceGestureState(
  state: GestureMachineState,
  observation: GestureObservation,
  config = DEFAULT_GESTURE_MACHINE_CONFIG,
): GestureMachineState {
  const qualified =
    observation.name !== 'none' &&
    observation.confidence >= config.minimumConfidence

  if (!qualified) {
    const missingFrames = state.missingFrames + 1
    if (state.current !== 'none' && missingFrames < config.releaseFrames) {
      return { ...state, missingFrames }
    }

    return {
      ...createGestureMachineState(),
      missingFrames: Math.min(missingFrames, config.releaseFrames),
    }
  }

  if (observation.name === state.current) {
    return {
      ...state,
      candidate: 'none',
      candidateFrames: 0,
      missingFrames: 0,
      confidence: observation.confidence,
    }
  }

  const sameCandidate = observation.name === state.candidate
  const candidateFrames = sameCandidate ? state.candidateFrames + 1 : 1

  if (candidateFrames >= config.activationFrames) {
    return {
      current: observation.name,
      candidate: 'none',
      candidateFrames: 0,
      missingFrames: 0,
      confidence: observation.confidence,
    }
  }

  return {
    ...state,
    candidate: observation.name,
    candidateFrames,
    missingFrames: 0,
  }
}

