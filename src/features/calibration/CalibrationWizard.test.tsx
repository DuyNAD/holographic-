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
        onSkip={vi.fn()}
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
        onSkip={vi.fn()}
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
        onSkip={vi.fn()}
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
        onSkip={vi.fn()}
      />,
    )
    fireEvent.click(screen.getByRole('button', { name: 'Hoàn tất hiệu chuẩn' }))
    fireEvent.click(screen.getByRole('button', { name: 'Vào không gian thiết kế' }))

    expect(onComplete).toHaveBeenCalledOnce()
  })

  it('can be skipped from any step or with Escape', () => {
    const onSkip = vi.fn()
    render(
      <CalibrationWizard
        cameraStatus="denied"
        trackingStatus="idle"
        gestures={[]}
        onStartCamera={vi.fn()}
        onComplete={vi.fn()}
        onSkip={onSkip}
      />,
    )

    fireEvent.click(screen.getByRole('button', { name: 'Bắt đầu hiệu chuẩn' }))
    fireEvent.click(
      screen.getByRole('button', { name: 'Bỏ qua, dùng chuột và bàn phím' }),
    )
    fireEvent.keyDown(window, { key: 'Escape' })

    expect(onSkip).toHaveBeenCalledTimes(2)
  })

  it('lets the hand pointer press the buttons once tracking can run', () => {
    render(
      <CalibrationWizard
        cameraStatus="active"
        trackingStatus="tracking"
        gestures={[pinchGesture]}
        onStartCamera={vi.fn()}
        onComplete={vi.fn()}
        onSkip={vi.fn()}
      />,
    )

    fireEvent.click(screen.getByRole('button', { name: 'Bắt đầu hiệu chuẩn' }))
    for (const name of ['Tiếp tục', 'Bỏ qua, dùng chuột và bàn phím']) {
      expect(screen.getByRole('button', { name })).toHaveAttribute(
        'data-gesture-target',
      )
    }
  })
})
