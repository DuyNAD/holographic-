import { act, renderHook, waitFor } from '@testing-library/react'
import type { HandTrackingState } from '../hand-tracking/handTrackingTypes'
import { useGestureEngine } from './useGestureEngine'

const noHand: HandTrackingState = {
  status: 'no-hand',
  message: '',
  landmarks: [],
  handedness: [],
}

const createPinchTracking = (): HandTrackingState => {
  const hand = Array.from({ length: 21 }, () => ({ x: 0.5, y: 0.5, z: 0 }))
  hand[0] = { x: 0.5, y: 0.9, z: 0 }
  hand[4] = { x: 0.4, y: 0.4, z: 0 }
  hand[8] = { x: 0.41, y: 0.4, z: 0 }

  return {
    status: 'tracking',
    message: '',
    landmarks: [hand],
    handedness: ['Right'],
  }
}

describe('useGestureEngine', () => {
  it('processes new tracking data without waiting for an animation frame', async () => {
    const animationFrame = vi.spyOn(window, 'requestAnimationFrame')
    const { result, rerender } = renderHook(
      ({ tracking }) => useGestureEngine(tracking),
      { initialProps: { tracking: noHand } },
    )

    rerender({ tracking: createPinchTracking() })
    await act(async () => {})
    expect(result.current).toEqual([])

    rerender({ tracking: createPinchTracking() })
    await waitFor(() => expect(result.current[0]?.name).toBe('pinch'))
    expect(animationFrame).not.toHaveBeenCalled()

    animationFrame.mockRestore()
  })
})
