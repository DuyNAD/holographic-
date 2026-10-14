import type { HandLandmark } from './handTrackingTypes'

export interface HandTrackingFrameMessage {
  type: 'frame'
  frame: ImageBitmap
  timestamp: number
}

export type HandTrackingWorkerRequest = HandTrackingFrameMessage

export type HandTrackingWorkerResponse =
  | { type: 'ready' }
  | {
      type: 'result'
      landmarks: HandLandmark[][]
      handedness: string[]
    }
  | { type: 'error'; message: string }
