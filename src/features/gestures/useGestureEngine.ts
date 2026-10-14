import { useEffect, useRef, useState } from 'react'
import type { HandLandmark } from '../hand-tracking/handTrackingTypes'
import type { HandTrackingState } from '../hand-tracking/handTrackingTypes'
import { detectGesture, smoothLandmarks } from './gestureMath'
import {
  advanceGestureState,
  createGestureMachineState,
} from './gestureStateMachine'
import type { GestureMachineState, StableGesture } from './gestureTypes'

export function useGestureEngine(handTracking: HandTrackingState) {
  const [gestures, setGestures] = useState<StableGesture[]>([])
  const smoothedHandsRef = useRef<HandLandmark[][]>([])
  const machineStatesRef = useRef<GestureMachineState[]>([])

  useEffect(() => {
    let cancelled = false

    queueMicrotask(() => {
      if (cancelled) return

      if (handTracking.status !== 'tracking') {
        smoothedHandsRef.current = []
        machineStatesRef.current = []
        setGestures([])
        return
      }

      const nextGestures: StableGesture[] = []
      const nextSmoothedHands: HandLandmark[][] = []
      const nextMachineStates: GestureMachineState[] = []

      handTracking.landmarks.forEach((hand, handIndex) => {
        const smoothed = smoothLandmarks(
          smoothedHandsRef.current[handIndex],
          hand,
        )
        const observation = detectGesture(smoothed)
        const machine = advanceGestureState(
          machineStatesRef.current[handIndex] ?? createGestureMachineState(),
          observation,
        )

        nextSmoothedHands.push(smoothed)
        nextMachineStates.push(machine)

        if (machine.current !== 'none') {
          nextGestures.push({
            handIndex,
            handedness: handTracking.handedness[handIndex] ?? '',
            name: machine.current,
            confidence: machine.confidence,
            landmarks: smoothed,
          })
        }
      })

      smoothedHandsRef.current = nextSmoothedHands
      machineStatesRef.current = nextMachineStates
      setGestures(nextGestures)
    })

    return () => {
      cancelled = true
    }
  }, [handTracking])

  return gestures
}

