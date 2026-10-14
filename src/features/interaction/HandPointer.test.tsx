import { render } from '@testing-library/react'
import type { StableGesture } from '../gestures/gestureTypes'
import HandPointer from './HandPointer'

const pointingAt = (x: number, y: number): StableGesture[] => {
  const landmarks = Array.from({ length: 21 }, () => ({ x: 0, y: 0, z: 0 }))
  landmarks[8] = { x: 1 - x, y, z: 0 }
  return [
    {
      handIndex: 0,
      handedness: 'Right',
      name: 'point',
      confidence: 1,
      landmarks,
    },
  ]
}

describe('HandPointer', () => {
  let now = 0
  let hovered: Element | null = null

  beforeEach(() => {
    now = 0
    vi.spyOn(performance, 'now').mockImplementation(() => now)
    document.elementFromPoint = vi.fn(() => hovered)
  })

  afterEach(() => {
    vi.restoreAllMocks()
    document.body.innerHTML = ''
  })

  it('presses a gesture target after the pointer dwells on it', () => {
    const button = document.createElement('button')
    button.dataset.gestureTarget = ''
    const onClick = vi.fn()
    button.addEventListener('click', onClick)
    document.body.append(button)
    hovered = button

    const { rerender } = render(<HandPointer gestures={pointingAt(0.5, 0.5)} />)
    expect(button).toHaveClass('is-gesture-hover')

    now = 600
    rerender(<HandPointer gestures={pointingAt(0.5, 0.5)} />)
    expect(onClick).not.toHaveBeenCalled()
    expect(button.style.getPropertyValue('--dwell-progress')).toBe('0.600')

    now = 1000
    rerender(<HandPointer gestures={pointingAt(0.5, 0.5)} />)
    now = 1400
    rerender(<HandPointer gestures={pointingAt(0.5, 0.5)} />)

    expect(onClick).toHaveBeenCalledOnce()
  })

  it('ignores disabled targets and clears hover when the pointer leaves', () => {
    const disabled = document.createElement('button')
    disabled.dataset.gestureTarget = ''
    disabled.disabled = true
    const enabled = document.createElement('button')
    enabled.dataset.gestureTarget = ''
    document.body.append(disabled, enabled)

    hovered = disabled
    const { rerender } = render(<HandPointer gestures={pointingAt(0.2, 0.2)} />)
    expect(disabled).not.toHaveClass('is-gesture-hover')

    hovered = enabled
    rerender(<HandPointer gestures={pointingAt(0.3, 0.3)} />)
    expect(enabled).toHaveClass('is-gesture-hover')

    rerender(<HandPointer gestures={[]} />)
    expect(enabled).not.toHaveClass('is-gesture-hover')
  })
})
