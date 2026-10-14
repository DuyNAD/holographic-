import { Component, type ErrorInfo, type ReactNode } from 'react'

interface AppErrorBoundaryProps {
  children: ReactNode
}

interface AppErrorBoundaryState {
  failed: boolean
}

export default class AppErrorBoundary extends Component<
  AppErrorBoundaryProps,
  AppErrorBoundaryState
> {
  state: AppErrorBoundaryState = { failed: false }

  static getDerivedStateFromError(): AppErrorBoundaryState {
    return { failed: true }
  }

  componentDidCatch(error: Error, info: ErrorInfo) {
    console.error('Holographic Studio render failure', error, info)
  }

  render() {
    if (this.state.failed) {
      return (
        <main className="fatal-error" role="alert">
          <p className="eyebrow">Không thể tiếp tục</p>
          <h1>Ứng dụng gặp lỗi hiển thị</h1>
          <p>
            Camera đã được giải phóng khi trang dừng. Hãy tải lại để khởi tạo một
            phiên làm việc mới.
          </p>
          <button type="button" onClick={() => window.location.reload()}>
            Tải lại ứng dụng
          </button>
        </main>
      )
    }

    return this.props.children
  }
}

