import '@testing-library/jest-dom/vitest'

Object.defineProperty(HTMLMediaElement.prototype, 'srcObject', {
  configurable: true,
  writable: true,
  value: null,
})

