import { fireEvent, render, screen } from '@testing-library/react'
import type { StableGesture } from '../gestures/gestureTypes'
import CalibrationWizard from './CalibrationWizard'

const pinchGesture: StableGesture = {
  handIndex: 0,
  handedness: 'Right',
  name: 'pinch',
  confidence: 0.9,
  landmarks: [],
}

describe('CalibrationWizard', () => {
  it('requires camera, hand tracking, and pinch before completion', () => {
    const onStartCamera = vi.fn()
    const onComplete = vi.fn()
    const { rerender } = render(
      <CalibrationWizard
        cameraStatus="idle"
        trackingStatus="idle"
        gestures={[]}
        onStartCamera={onStartCamera}
        onComplete={onComplete}
      />,
    )

    fireEvent.click(screen.getByRole('button', { name: 'Bắt đầu hiệu chuẩn' }))
    fireEvent.click(screen.getByRole('button', { name: 'Bật camera' }))
    expect(onStartCamera).toHaveBeenCalledOnce()

    rerender(
      <CalibrationWizard
        cameraStatus="active"
        trackingStatus="no-hand"
        gestures={[]}
        onStartCamera={onStartCamera}
        onComplete={onComplete}
      />,
    )
    fireEvent.click(screen.getByRole('button', { name: 'Tiếp tục' }))
    expect(screen.getByRole('button', { name: 'Đưa tay vào camera' })).toBeDisabled()

    rerender(
      <CalibrationWizard
        cameraStatus="active"
        trackingStatus="tracking"
        gestures={[]}
        onStartCamera={onStartCamera}
        onComplete={onComplete}
      />,
    )
    fireEvent.click(screen.getByRole('button', { name: 'Tay đã ở đúng vị trí' }))
    expect(screen.getByRole('button', { name: 'Hãy thử chụm hai ngón' })).toBeDisabled()

    rerender(
      <CalibrationWizard
        cameraStatus="active"
        trackingStatus="tracking"
        gestures={[pinchGesture]}
        onStartCamera={onStartCamera}
        onComplete={onComplete}
      />,
    )
    fireEvent.click(screen.getByRole('button', { name: 'Hoàn tất hiệu chuẩn' }))
    fireEvent.click(screen.getByRole('button', { name: 'Vào không gian thiết kế' }))

    expect(onComplete).toHaveBeenCalledOnce()
  })
})

