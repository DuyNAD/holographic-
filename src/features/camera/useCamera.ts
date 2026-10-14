import { useCallback, useEffect, useRef, useState } from 'react'
import { mapCameraError, type CameraFailureStatus } from './cameraErrors'

export type CameraStatus =
  | 'idle'
  | 'requesting'
  | 'active'
  | CameraFailureStatus

interface CameraState {
  status: CameraStatus
  message: string
}

const idleState: CameraState = {
  status: 'idle',
  message: 'Camera đang tắt.',
}

export function useCamera() {
  const videoRef = useRef<HTMLVideoElement>(null)
  const streamRef = useRef<MediaStream | null>(null)
  const [state, setState] = useState<CameraState>(idleState)

  const stop = useCallback(() => {
    streamRef.current?.getTracks().forEach((track) => track.stop())
    streamRef.current = null

    if (videoRef.current) {
      videoRef.current.srcObject = null
    }

    setState(idleState)
  }, [])

  const start = useCallback(async () => {
    if (!navigator.mediaDevices?.getUserMedia) {
      setState({
        status: 'unavailable',
        message: 'Trình duyệt này không hỗ trợ truy cập camera.',
      })
      return
    }

    setState({ status: 'requesting', message: 'Đang kết nối camera…' })

    try {
      const stream = await navigator.mediaDevices.getUserMedia({
        audio: false,
        video: {
          facingMode: 'user',
          width: { ideal: 640 },
          height: { ideal: 360 },
          aspectRatio: { ideal: 16 / 9 },
          frameRate: { ideal: 30, max: 30 },
        },
      })

      streamRef.current?.getTracks().forEach((track) => track.stop())
      streamRef.current = stream

      if (videoRef.current) {
        videoRef.current.srcObject = stream
      }

      setState({
        status: 'active',
        message: 'Camera đang hoạt động trên thiết bị.',
      })
    } catch (error) {
      streamRef.current = null
      setState(mapCameraError(error))
    }
  }, [])

  useEffect(
    () => () => {
      streamRef.current?.getTracks().forEach((track) => track.stop())
    },
    [],
  )

  return {
    ...state,
    videoRef,
    start,
    stop,
  }
}

export type CameraController = ReturnType<typeof useCamera>

