import {
  advanceGestureState,
  createGestureMachineState,
} from './gestureStateMachine'
import type { GestureMachineState } from './gestureTypes'

const gesture = (name: 'pinch' | 'none', confidence = 1) => ({
  name,
  confidence,
})

describe('advanceGestureState', () => {
  it('requires consecutive confident frames before activation', () => {
    const first = advanceGestureState(
      createGestureMachineState(),
      gesture('pinch'),
    )
    const second = advanceGestureState(first, gesture('pinch'))

    expect(first.current).toBe('none')
    expect(second.current).toBe('pinch')
  })

  it('ignores a single low-confidence jitter frame', () => {
    const active = {
      ...createGestureMachineState(),
      current: 'pinch' as const,
      confidence: 0.9,
    }

    const next = advanceGestureState(active, gesture('none', 0))

    expect(next.current).toBe('pinch')
    expect(next.missingFrames).toBe(1)
  })

  it('releases a gesture only after the configured missing frames', () => {
    let state: GestureMachineState = {
      ...createGestureMachineState(),
      current: 'pinch' as const,
      confidence: 0.9,
    }

    state = advanceGestureState(state, gesture('none', 0))
    expect(state.current).toBe('pinch')

    state = advanceGestureState(state, gesture('none', 0))
    expect(state.current).toBe('none')
  })
})

