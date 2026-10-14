import {
  FilesetResolver,
  HandLandmarker,
  type HandLandmarkerOptions,
} from '@mediapipe/tasks-vision'
import {
  HAND_LANDMARKER_MODEL_PATH,
  HAND_TRACKING_FRAME_HEIGHT,
  HAND_TRACKING_FRAME_WIDTH,
  MAX_TRACKED_HANDS,
  MEDIAPIPE_WASM_PATH,
} from './handTrackingConfig'
import type {
  HandTrackingWorkerRequest,
  HandTrackingWorkerResponse,
} from './handTrackingWorkerProtocol'

interface WorkerScope {
  onmessage: ((event: MessageEvent<HandTrackingWorkerRequest>) => void) | null
  postMessage(message: HandTrackingWorkerResponse): void
}

const workerScope = globalThis as unknown as WorkerScope
let landmarker: HandLandmarker | null = null
let processing = false

const createOptions = (
  delegate: 'GPU' | 'CPU',
): HandLandmarkerOptions => ({
  baseOptions: {
    modelAssetPath: HAND_LANDMARKER_MODEL_PATH,
    delegate,
  },
  runningMode: 'VIDEO',
  numHands: MAX_TRACKED_HANDS,
  minHandDetectionConfidence: 0.55,
  minHandPresenceConfidence: 0.55,
  minTrackingConfidence: 0.55,
  ...(delegate === 'GPU'
    ? {
        canvas: new OffscreenCanvas(
          HAND_TRACKING_FRAME_WIDTH,
          HAND_TRACKING_FRAME_HEIGHT,
        ),
      }
    : {}),
})

async function initialize() {
  const vision = await FilesetResolver.forVisionTasks(MEDIAPIPE_WASM_PATH, true)

  try {
    landmarker = await HandLandmarker.createFromOptions(
      vision,
      createOptions('GPU'),
    )
  } catch {
    landmarker = await HandLandmarker.createFromOptions(
      vision,
      createOptions('CPU'),
    )
  }

  workerScope.postMessage({ type: 'ready' })
}

workerScope.onmessage = ({ data }) => {
  if (data.type !== 'frame') return

  if (!landmarker || processing) {
    data.frame.close()
    return
  }

  processing = true

  try {
    const result = landmarker.detectForVideo(data.frame, data.timestamp)
    workerScope.postMessage({
      type: 'result',
      landmarks: result.landmarks.map((hand) =>
        hand.map(({ x, y, z }) => ({ x, y, z })),
      ),
      handedness: result.handedness.map(
        (categories) =>
          categories[0]?.displayName ?? categories[0]?.categoryName ?? '',
      ),
    })
  } catch {
    workerScope.postMessage({
      type: 'error',
      message: 'Không thể xử lý khung hình camera.',
    })
  } finally {
    data.frame.close()
    processing = false
  }
}

void initialize().catch(() => {
  workerScope.postMessage({
    type: 'error',
    message: 'Không thể tải mô hình nhận diện tay.',
  })
})
