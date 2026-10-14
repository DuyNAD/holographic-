import { fireEvent, render, screen, waitFor } from '@testing-library/react'
import { vi } from 'vitest'
import App from './App'

vi.mock('./features/scene/SceneViewport', () => ({
  default: () => <div data-testid="scene-viewport" />,
}))

vi.mock('./features/assets/modelAssetStore', () => ({
  deleteModelAsset: vi.fn(),
  listModelAssets: vi.fn().mockResolvedValue([]),
  saveModelAsset: vi.fn(),
}))

describe('App', () => {
  beforeEach(() => {
    localStorage.clear()
    localStorage.setItem('holographic-calibration', 'complete')
  })

  it('renders the full-window space with camera window and menu', async () => {
    render(<App />)

    expect(
      screen.getByRole('heading', { name: 'Holographic Studio' }),
    ).toBeInTheDocument()
    expect(await screen.findByTestId('scene-viewport')).toBeInTheDocument()
    expect(screen.getByRole('region', { name: 'Camera' })).toBeInTheDocument()
    expect(screen.getByRole('navigation', { name: 'Menu chính' })).toBeInTheDocument()
    expect(screen.getByRole('button', { name: 'Xóa vật thể' })).toBeDisabled()
  })

  it('adds a shape from the menu, deletes it, and undoes the delete', async () => {
    render(<App />)

    fireEvent.click(screen.getByRole('button', { name: 'Thêm vật thể' }))
    fireEvent.click(screen.getByRole('button', { name: /Khối trụ/ }))
    expect(screen.getAllByText('Khối trụ').length).toBeGreaterThan(0)

    fireEvent.click(screen.getByRole('button', { name: 'Xóa vật thể' }))
    expect(screen.getByText('Đã xóa “Khối trụ”')).toBeInTheDocument()
    expect(screen.getByText('Chưa chọn vật thể')).toBeInTheDocument()

    fireEvent.click(screen.getByRole('button', { name: 'Hoàn tác' }))
    await waitFor(() =>
      expect(screen.queryByText('Đã xóa “Khối trụ”')).not.toBeInTheDocument(),
    )
    expect(screen.getByRole('button', { name: 'Xóa vật thể' })).toBeEnabled()
  })

  it('lets first-time users without a camera skip calibration', async () => {
    localStorage.removeItem('holographic-calibration')
    render(<App />)

    expect(screen.getByRole('dialog')).toBeInTheDocument()
    fireEvent.click(
      screen.getByRole('button', { name: 'Bỏ qua, dùng chuột và bàn phím' }),
    )

    expect(screen.queryByRole('dialog')).not.toBeInTheDocument()
    expect(await screen.findByTestId('scene-viewport')).toBeInTheDocument()
    expect(localStorage.getItem('holographic-calibration')).toBeNull()
  })
})
