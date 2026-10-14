import { fireEvent, render, screen, waitFor } from '@testing-library/react'
import type { HandTrackingState } from '../hand-tracking/handTrackingTypes'
import CameraPanel from './CameraPanel'
import { useCamera } from './useCamera'

const idleTracking: HandTrackingState = {
  status: 'idle',
  message: 'Bật camera để bắt đầu nhận diện tay.',
  landmarks: [],
  handedness: [],
}

function CameraPanelHarness() {
  const camera = useCamera()
  return <CameraPanel camera={camera} handTracking={idleTracking} />
}

const setMediaDevices = (getUserMedia: ReturnType<typeof vi.fn>) => {
  Object.defineProperty(navigator, 'mediaDevices', {
    configurable: true,
    value: { getUserMedia },
  })
}

describe('CameraPanel', () => {
  it('starts and stops a local camera stream', async () => {
    const stop = vi.fn()
    const stream = {
      getTracks: () => [{ stop }],
    } as unknown as MediaStream
    const getUserMedia = vi.fn().mockResolvedValue(stream)
    setMediaDevices(getUserMedia)

    render(<CameraPanelHarness />)
    fireEvent.click(screen.getByRole('button', { name: 'Bật camera' }))

    expect(
      await screen.findByRole('button', { name: 'Tắt camera' }),
    ).toBeInTheDocument()
    expect(getUserMedia).toHaveBeenCalledWith(
      expect.objectContaining({
        audio: false,
        video: expect.objectContaining({
          width: { ideal: 640 },
          height: { ideal: 360 },
          aspectRatio: { ideal: 16 / 9 },
        }),
      }),
    )

    fireEvent.click(screen.getByRole('button', { name: 'Tắt camera' }))
    await waitFor(() => expect(stop).toHaveBeenCalledOnce())
    expect(screen.getByRole('button', { name: 'Bật camera' })).toBeInTheDocument()
  })

  it('reports a denied permission and remains retryable', async () => {
    setMediaDevices(
      vi.fn().mockRejectedValue(new DOMException('Denied', 'NotAllowedError')),
    )

    render(<CameraPanelHarness />)
    fireEvent.click(screen.getByRole('button', { name: 'Bật camera' }))

    expect(await screen.findByText('Thiếu quyền')).toBeInTheDocument()
    expect(
      screen.getByText('Quyền camera đã bị từ chối. Hãy cấp quyền rồi thử lại.'),
    ).toBeInTheDocument()
    expect(screen.getByRole('button', { name: 'Bật camera' })).toBeEnabled()
  })
})

