import { useEffect, useState, type RefObject } from 'react'
import type { CameraStatus } from '../camera/useCamera'
import {
  HAND_TRACKING_FRAME_HEIGHT,
  HAND_TRACKING_FRAME_WIDTH,
  MAX_TRACKED_HANDS,
} from './handTrackingConfig'
import type { HandTrackingState } from './handTrackingTypes'
import type {
  HandTrackingWorkerRequest,
  HandTrackingWorkerResponse,
} from './handTrackingWorkerProtocol'

const idleState: HandTrackingState = {
  status: 'idle',
  message: 'Bật camera để bắt đầu nhận diện tay.',
  landmarks: [],
  handedness: [],
}

export function useHandTracking(
  videoRef: RefObject<HTMLVideoElement | null>,
  cameraStatus: CameraStatus,
) {
  const [state, setState] = useState<HandTrackingState>(idleState)

  useEffect(() => {
    if (cameraStatus !== 'active') return

    let cancelled = false
    let workerReady = false
    let animationFrame = 0
    let videoFrameCallback = 0
    let scheduledVideo: HTMLVideoElement | null = null
    let lastVideoTime = -1

    const worker = new Worker(
      new URL('./handTracking.worker.ts', import.meta.url),
      { type: 'module' },
    )

    const scheduleFrame = () => {
      if (cancelled || !workerReady) return

      const video = videoRef.current
      if (
        video &&
        typeof video.requestVideoFrameCallback === 'function'
      ) {
        scheduledVideo = video
        videoFrameCallback = video.requestVideoFrameCallback((timestamp) => {
          void captureFrame(timestamp, true)
        })
        return
      }

      animationFrame = requestAnimationFrame((timestamp) => {
        void captureFrame(timestamp, false)
      })
    }

    const captureFrame = async (
      timestamp: number,
      isVideoFrame: boolean,
    ) => {
      if (cancelled) return

      const video = videoRef.current
      if (
        !video ||
        video.readyState < HTMLMediaElement.HAVE_CURRENT_DATA ||
        (!isVideoFrame && video.currentTime === lastVideoTime)
      ) {
        scheduleFrame()
        return
      }

      lastVideoTime = video.currentTime

      try {
        const frame = await createImageBitmap(
          video,
          0,
          0,
          video.videoWidth,
          video.videoHeight,
          {
            resizeWidth: HAND_TRACKING_FRAME_WIDTH,
            resizeHeight: HAND_TRACKING_FRAME_HEIGHT,
            resizeQuality: 'low',
          },
        )
        if (cancelled) {
          frame.close()
          return
        }

        const message: HandTrackingWorkerRequest = {
          type: 'frame',
          frame,
          timestamp,
        }
        worker.postMessage(message, [frame])
      } catch {
        if (!cancelled) {
          setState({
            status: 'error',
            message: 'Không thể đọc khung hình camera.',
            landmarks: [],
            handedness: [],
          })
        }
      }
    }

    const handleMessage = ({
      data,
    }: MessageEvent<HandTrackingWorkerResponse>) => {
      if (cancelled) return

      if (data.type === 'ready') {
        workerReady = true
        setState({
          status: 'no-hand',
          message: 'Đưa bàn tay vào giữa khung hình.',
          landmarks: [],
          handedness: [],
        })
        scheduleFrame()
        return
      }

      if (data.type === 'error') {
        setState({
          status: 'error',
          message: data.message,
          landmarks: [],
          handedness: [],
        })
        return
      }

      setState({
        status: data.landmarks.length > 0 ? 'tracking' : 'no-hand',
        message:
          data.landmarks.length > 0
            ? `Đã nhận diện ${data.landmarks.length}/${MAX_TRACKED_HANDS} bàn tay.`
            : 'Đưa bàn tay vào giữa khung hình.',
        landmarks: data.landmarks,
        handedness: data.handedness,
      })
      scheduleFrame()
    }

    const handleWorkerError = () => {
      if (!cancelled) {
        setState({
          status: 'error',
          message: 'Luồng nhận diện tay đã dừng.',
          landmarks: [],
          handedness: [],
        })
      }
    }

    worker.addEventListener('message', handleMessage)
    worker.addEventListener('error', handleWorkerError)

    queueMicrotask(() => {
      if (cancelled) return
      setState({
        status: 'loading',
        message: 'Đang tải mô hình nhận diện tay…',
        landmarks: [],
        handedness: [],
      })
    })

    return () => {
      cancelled = true
      cancelAnimationFrame(animationFrame)
      if (scheduledVideo && videoFrameCallback) {
        scheduledVideo.cancelVideoFrameCallback(videoFrameCallback)
      }
      worker.removeEventListener('message', handleMessage)
      worker.removeEventListener('error', handleWorkerError)
      worker.terminate()
    }
  }, [cameraStatus, videoRef])

  return cameraStatus === 'active' ? state : idleState
}
