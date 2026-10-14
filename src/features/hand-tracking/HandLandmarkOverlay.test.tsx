import { render, screen } from '@testing-library/react'
import HandLandmarkOverlay from './HandLandmarkOverlay'

describe('HandLandmarkOverlay', () => {
  it('renders the 21 landmarks of a detected hand', () => {
    const hand = Array.from({ length: 21 }, (_, index) => ({
      x: index / 21,
      y: index / 21,
      z: 0,
    }))

    const { container } = render(<HandLandmarkOverlay hands={[hand]} />)

    expect(screen.getByLabelText('1 bàn tay được nhận diện')).toBeInTheDocument()
    expect(container.querySelectorAll('circle')).toHaveLength(21)
    expect(container.querySelectorAll('line')).toHaveLength(21)
  })

  it('renders an empty overlay when no hand is present', () => {
    const { container } = render(<HandLandmarkOverlay hands={[]} />)

    expect(screen.getByLabelText('0 bàn tay được nhận diện')).toBeInTheDocument()
    expect(container.querySelectorAll('circle')).toHaveLength(0)
  })
})

