import type { Dispatch } from 'react'
import type { SceneHistoryAction } from '../scene/sceneHistory'
import type {
  SceneObjectModel,
} from '../scene/sceneState'

interface ObjectControlsProps {
  selectedObject: SceneObjectModel | null
  dispatch: Dispatch<SceneHistoryAction>
  canUndo: boolean
  canRedo: boolean
}

interface ControlButtonProps {
  label: string
  disabled: boolean
  onClick: () => void
}

function ControlButton({ label, disabled, onClick }: ControlButtonProps) {
  return (
    <button type="button" disabled={disabled} onClick={onClick}>
      {label}
    </button>
  )
}

export default function ObjectControls({
  selectedObject,
  dispatch,
  canUndo,
  canRedo,
}: ObjectControlsProps) {
  const disabled = selectedObject === null

  return (
    <section className="control-panel" aria-label="Điều khiển vật thể">
      <div className="panel-heading">
        <p className="panel-kicker">Điều khiển dự phòng</p>
        <h2>Vật thể</h2>
      </div>

      <div className="selection-card" aria-live="polite">
        <span>Đang chọn</span>
        <strong>{selectedObject?.name ?? 'Chưa chọn vật thể'}</strong>
      </div>

      {!selectedObject && (
        <p className="empty-selection">
          Chọn một hình trong viewport để bật các điều khiển biến đổi.
        </p>
      )}

      <section className="control-group" aria-labelledby="translate-title">
        <h3 id="translate-title">Di chuyển</h3>
        <div className="control-grid">
          <ControlButton
            label="X −"
            disabled={disabled}
            onClick={() => dispatch({ type: 'translate', axis: 0, delta: -0.2 })}
          />
          <ControlButton
            label="X +"
            disabled={disabled}
            onClick={() => dispatch({ type: 'translate', axis: 0, delta: 0.2 })}
          />
          <ControlButton
            label="Y −"
            disabled={disabled}
            onClick={() => dispatch({ type: 'translate', axis: 1, delta: -0.2 })}
          />
          <ControlButton
            label="Y +"
            disabled={disabled}
            onClick={() => dispatch({ type: 'translate', axis: 1, delta: 0.2 })}
          />
          <ControlButton
            label="Z −"
            disabled={disabled}
            onClick={() => dispatch({ type: 'translate', axis: 2, delta: -0.2 })}
          />
          <ControlButton
            label="Z +"
            disabled={disabled}
            onClick={() => dispatch({ type: 'translate', axis: 2, delta: 0.2 })}
          />
        </div>
      </section>

      <section className="control-group" aria-labelledby="rotate-title">
        <h3 id="rotate-title">Xoay trục Y</h3>
        <div className="control-grid">
          <ControlButton
            label="↶ Trái"
            disabled={disabled}
            onClick={() => dispatch({ type: 'rotate', axis: 1, delta: -0.15 })}
          />
          <ControlButton
            label="Phải ↷"
            disabled={disabled}
            onClick={() => dispatch({ type: 'rotate', axis: 1, delta: 0.15 })}
          />
        </div>
      </section>

      <section className="control-group" aria-labelledby="scale-title">
        <h3 id="scale-title">Kích thước</h3>
        <div className="control-grid">
          <ControlButton
            label="Thu nhỏ"
            disabled={disabled}
            onClick={() => dispatch({ type: 'scale', delta: -0.1 })}
          />
          <ControlButton
            label="Phóng to"
            disabled={disabled}
            onClick={() => dispatch({ type: 'scale', delta: 0.1 })}
          />
        </div>
      </section>

      <button
        className="reset-button"
        type="button"
        onClick={() => dispatch({ type: 'reset' })}
      >
        Đặt lại cảnh
      </button>

      <div className="history-controls" aria-label="Lịch sử thao tác">
        <button
          type="button"
          disabled={!canUndo}
          onClick={() => dispatch({ type: 'undo' })}
        >
          ↶ Hoàn tác
        </button>
        <button
          type="button"
          disabled={!canRedo}
          onClick={() => dispatch({ type: 'redo' })}
        >
          Làm lại ↷
        </button>
      </div>
    </section>
  )
}

