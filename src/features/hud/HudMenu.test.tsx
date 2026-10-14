import { fireEvent, render, screen } from '@testing-library/react'
import HudMenu from './HudMenu'

const renderMenu = (selectedName: string | null = null, onDelete = vi.fn()) =>
  render(
    <HudMenu
      selectedName={selectedName}
      onDelete={onDelete}
      addPanel={<p>Nội dung thêm vật thể</p>}
      guidePanel={<p>Nội dung hướng dẫn</p>}
    />,
  )

describe('HudMenu', () => {
  it('offers add, delete, guide, and collapse as gesture targets', () => {
    renderMenu()

    for (const name of ['Thu gọn menu', 'Thêm vật thể', 'Xóa vật thể', 'Hướng dẫn']) {
      expect(screen.getByRole('button', { name })).toHaveAttribute(
        'data-gesture-target',
      )
    }
  })

  it('opens one panel at a time and closes it again', () => {
    renderMenu()

    fireEvent.click(screen.getByRole('button', { name: 'Thêm vật thể' }))
    expect(screen.getByText('Nội dung thêm vật thể')).toBeInTheDocument()

    fireEvent.click(screen.getByRole('button', { name: 'Hướng dẫn' }))
    expect(screen.queryByText('Nội dung thêm vật thể')).not.toBeInTheDocument()
    expect(screen.getByText('Nội dung hướng dẫn')).toBeInTheDocument()

    fireEvent.click(screen.getByRole('button', { name: 'Đóng bảng' }))
    expect(screen.queryByText('Nội dung hướng dẫn')).not.toBeInTheDocument()
  })

  it('deletes only when an object is selected', () => {
    const onDelete = vi.fn()
    const { rerender } = renderMenu(null, onDelete)
    expect(screen.getByRole('button', { name: 'Xóa vật thể' })).toBeDisabled()

    rerender(
      <HudMenu
        selectedName="Khối cầu"
        onDelete={onDelete}
        addPanel={null}
        guidePanel={null}
      />,
    )
    fireEvent.click(screen.getByRole('button', { name: 'Xóa vật thể' }))
    expect(onDelete).toHaveBeenCalledOnce()
  })

  it('collapses to a single button and expands again', () => {
    renderMenu()
    fireEvent.click(screen.getByRole('button', { name: 'Thêm vật thể' }))

    fireEvent.click(screen.getByRole('button', { name: 'Thu gọn menu' }))
    expect(screen.getAllByRole('button')).toHaveLength(1)
    expect(screen.queryByText('Nội dung thêm vật thể')).not.toBeInTheDocument()

    fireEvent.click(screen.getByRole('button', { name: 'Mở menu' }))
    expect(screen.getByRole('button', { name: 'Thêm vật thể' })).toBeInTheDocument()
  })
})
