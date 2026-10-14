export const DWELL_DURATION_MS = 1000

export interface DwellState<T> {
  target: T | null
  startedAt: number
  fired: boolean
}

export interface DwellStep<T> {
  state: DwellState<T>
  progress: number
  fire: boolean
}

export const createDwellState = <T>(): DwellState<T> => ({
  target: null,
  startedAt: 0,
  fired: false,
})

// Holding the hand cursor on one target for the full duration presses it once.
// The same target only fires again after the cursor leaves it.
export function advanceDwell<T>(
  state: DwellState<T>,
  target: T | null,
  now: number,
  duration = DWELL_DURATION_MS,
): DwellStep<T> {
  if (target === null) {
    return { state: createDwellState(), progress: 0, fire: false }
  }

  if (target !== state.target) {
    return {
      state: { target, startedAt: now, fired: false },
      progress: 0,
      fire: false,
    }
  }

  if (state.fired) return { state, progress: 1, fire: false }

  const progress = Math.min(1, (now - state.startedAt) / duration)
  if (progress < 1) return { state, progress, fire: false }

  return { state: { ...state, fired: true }, progress: 1, fire: true }
}
