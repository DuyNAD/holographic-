export type CameraFailureStatus =
  | 'denied'
  | 'unavailable'
  | 'busy'
  | 'error'

export interface CameraFailure {
  status: CameraFailureStatus
  message: string
}

export function mapCameraError(error: unknown): CameraFailure {
  if (error instanceof DOMException) {
    switch (error.name) {
      case 'NotAllowedError':
      case 'SecurityError':
        return {
          status: 'denied',
          message: 'Quyền camera đã bị từ chối. Hãy cấp quyền rồi thử lại.',
        }
      case 'NotFoundError':
      case 'OverconstrainedError':
        return {
          status: 'unavailable',
          message: 'Không tìm thấy camera phù hợp trên thiết bị này.',
        }
      case 'NotReadableError':
      case 'AbortError':
        return {
          status: 'busy',
          message: 'Camera đang được ứng dụng khác sử dụng hoặc chưa sẵn sàng.',
        }
    }
  }

  return {
    status: 'error',
    message: 'Không thể khởi động camera. Vui lòng thử lại.',
  }
}

