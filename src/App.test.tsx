import { render, screen } from '@testing-library/react'
import { vi } from 'vitest'
import App from './App'

vi.mock('./features/scene/SceneViewport', () => ({
  default: () => <div data-testid="scene-viewport" />,
}))

describe('App', () => {
  beforeEach(() => {
    localStorage.setItem('holographic-calibration', 'complete')
  })

  it('renders the 3D workspace and disabled fallback controls', async () => {
    render(<App />)

    expect(
      screen.getByRole('heading', { name: 'Holographic Studio' }),
    ).toBeInTheDocument()
    expect(await screen.findByTestId('scene-viewport')).toBeInTheDocument()
    expect(screen.getByText('Chưa chọn vật thể')).toBeInTheDocument()
    expect(screen.getByRole('button', { name: 'X +' })).toBeDisabled()
  })
})

