import type { HandLandmark } from '../hand-tracking/handTrackingTypes'

export type GestureName = 'none' | 'point' | 'pinch' | 'fist' | 'open-palm'

export interface GestureObservation {
  name: GestureName
  confidence: number
}

export interface StableGesture {
  handIndex: number
  handedness: string
  name: Exclude<GestureName, 'none'>
  confidence: number
  landmarks: HandLandmark[]
}

export interface GestureMachineState {
  current: GestureName
  candidate: GestureName
  candidateFrames: number
  missingFrames: number
  confidence: number
}

