import { advanceDwell, createDwellState, DWELL_DURATION_MS } from './dwell'

describe('advanceDwell', () => {
  it('fires once after the cursor stays on a target for one second', () => {
    let state = createDwellState<string>()

    let step = advanceDwell(state, 'add', 0)
    expect(step).toMatchObject({ progress: 0, fire: false })
    state = step.state

    step = advanceDwell(state, 'add', DWELL_DURATION_MS / 2)
    expect(step.progress).toBeCloseTo(0.5)
    expect(step.fire).toBe(false)
    state = step.state

    step = advanceDwell(state, 'add', DWELL_DURATION_MS)
    expect(step).toMatchObject({ progress: 1, fire: true })
    state = step.state

    step = advanceDwell(state, 'add', DWELL_DURATION_MS * 3)
    expect(step).toMatchObject({ progress: 1, fire: false })
  })

  it('restarts the timer when the cursor moves to another target', () => {
    let state = advanceDwell(createDwellState<string>(), 'add', 0).state
    state = advanceDwell(state, 'add', 900).state

    const step = advanceDwell(state, 'delete', 950)
    expect(step).toMatchObject({ progress: 0, fire: false })
    expect(advanceDwell(step.state, 'delete', 1500).fire).toBe(false)
    expect(advanceDwell(step.state, 'delete', 1950).fire).toBe(true)
  })

  it('can press the same target again after leaving it', () => {
    let state = advanceDwell(createDwellState<string>(), 'add', 0).state
    state = advanceDwell(state, 'add', 1000).state
    state = advanceDwell(state, null, 1100).state
    state = advanceDwell(state, 'add', 1200).state

    expect(advanceDwell(state, 'add', 2200).fire).toBe(true)
  })
})
