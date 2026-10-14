export interface HandLandmark {
  x: number
  y: number
  z: number
}

export type HandTrackingStatus =
  | 'idle'
  | 'loading'
  | 'no-hand'
  | 'tracking'
  | 'error'

export interface HandTrackingState {
  status: HandTrackingStatus
  message: string
  landmarks: HandLandmark[][]
  handedness: string[]
}

