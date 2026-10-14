import { useEffect } from 'react'

export const UNDO_TOAST_MS = 6000

interface UndoToastProps {
  message: string
  onUndo: () => void
  onDismiss: () => void
}

export default function UndoToast({ message, onUndo, onDismiss }: UndoToastProps) {
  useEffect(() => {
    const timeout = window.setTimeout(onDismiss, UNDO_TOAST_MS)
    return () => window.clearTimeout(timeout)
  }, [message, onDismiss])

  return (
    <div className="undo-toast hud-glass" role="status" data-hud>
      <span>{message}</span>
      <button
        type="button"
        data-gesture-target
        onClick={() => {
          onUndo()
          onDismiss()
        }}
      >
        Hoàn tác
      </button>
    </div>
  )
}
