import { StrictMode } from 'react'
import { createRoot } from 'react-dom/client'
import App from './App'
import AppErrorBoundary from './AppErrorBoundary'
import './index.css'

const rootElement = document.getElementById('root')

if (!rootElement) {
  throw new Error('Không tìm thấy phần tử gốc của ứng dụng.')
}

createRoot(rootElement).render(
  <StrictMode>
    <AppErrorBoundary>
      <App />
    </AppErrorBoundary>
  </StrictMode>,
)

