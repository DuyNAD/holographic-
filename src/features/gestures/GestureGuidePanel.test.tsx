import { fireEvent, render, screen } from '@testing-library/react'
import type { StableGesture } from './gestureTypes'
import GestureGuidePanel from './GestureGuidePanel'

const createGesture = (
  name: StableGesture['name'],
  handIndex: number,
): StableGesture => ({
  handIndex,
  handedness: handIndex === 0 ? 'Left' : 'Right',
  name,
  confidence: 0.92,
  landmarks: [],
})

describe('GestureGuidePanel', () => {
  it('shows every supported interaction', () => {
    render(<GestureGuidePanel gestures={[]} trackingStatus="no-hand" />)

    expect(screen.getByText('Trỏ')).toBeInTheDocument()
    expect(screen.getByText('Chụm')).toBeInTheDocument()
    expect(screen.getByText('Nắm tay')).toBeInTheDocument()
    expect(screen.getByText('Mở tay')).toBeInTheDocument()
    expect(screen.getByText('Hai tay chụm')).toBeInTheDocument()
  })

  it('marks a two-hand pinch as active', () => {
    render(
      <GestureGuidePanel
        gestures={[createGesture('pinch', 0), createGesture('pinch', 1)]}
        trackingStatus="tracking"
      />,
    )

    const twoHandRow = screen.getByText('Hai tay chụm').closest('article')
    expect(twoHandRow).toHaveClass('is-active')
    expect(screen.getByText('92%')).toBeInTheDocument()
  })

  it('collapses the guide without removing its summary', () => {
    render(<GestureGuidePanel gestures={[]} trackingStatus="no-hand" />)

    fireEvent.click(screen.getByRole('button', { name: 'Thu gọn' }))

    expect(screen.queryByText('Hai tay chụm')).not.toBeInTheDocument()
    expect(screen.getByText('Cử chỉ hiện tại')).toBeInTheDocument()
    expect(screen.getByRole('button', { name: 'Mở rộng' })).toHaveAttribute(
      'aria-expanded',
      'false',
    )
  })
})

