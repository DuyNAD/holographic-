import { mapCameraError } from './cameraErrors'

describe('mapCameraError', () => {
  it('maps a rejected permission without throwing', () => {
    expect(mapCameraError(new DOMException('Denied', 'NotAllowedError'))).toEqual({
      status: 'denied',
      message: 'Quyền camera đã bị từ chối. Hãy cấp quyền rồi thử lại.',
    })
  })

  it('maps a missing device', () => {
    expect(mapCameraError(new DOMException('Missing', 'NotFoundError')).status).toBe(
      'unavailable',
    )
  })

  it('provides a safe fallback for unknown errors', () => {
    expect(mapCameraError(new Error('Unknown')).status).toBe('error')
  })
})

