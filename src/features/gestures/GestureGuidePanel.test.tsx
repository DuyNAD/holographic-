import { render, screen } from '@testing-library/react'
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
  it('shows every supported interaction, including dwell to press', () => {
    render(<GestureGuidePanel gestures={[]} />)

    for (const name of ['Trỏ', 'Giữ để bấm', 'Chụm', 'Nắm tay', 'Mở tay', 'Hai tay chụm']) {
      expect(screen.getByText(name)).toBeInTheDocument()
    }
    expect(screen.getByText('Trỏ vào nút và giữ yên 1 giây')).toBeInTheDocument()
  })

  it('explains how to rotate the selected object with a fist', () => {
    render(<GestureGuidePanel gestures={[]} />)

    const fistRow = screen.getByText('Nắm tay').closest('article')
    expect(fistRow).toHaveTextContent(
      'Chọn vật thể trước, nắm tay rồi nghiêng cổ tay',
    )
    expect(fistRow).toHaveTextContent('Xoay vật thể theo hướng nghiêng tay')
  })

  it('marks a two-hand pinch as active', () => {
    render(
      <GestureGuidePanel
        gestures={[createGesture('pinch', 0), createGesture('pinch', 1)]}
      />,
    )

    expect(screen.getByText('Hai tay chụm').closest('article')).toHaveClass(
      'is-active',
    )
  })

  it('marks dwell as active while pointing', () => {
    render(<GestureGuidePanel gestures={[createGesture('point', 0)]} />)

    expect(screen.getByText('Giữ để bấm').closest('article')).toHaveClass(
      'is-active',
    )
  })
})
