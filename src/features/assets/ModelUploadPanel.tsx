import { useId, useState, type ChangeEvent, type Dispatch } from 'react'
import type { SceneHistoryAction } from '../scene/sceneHistory'
import type { SceneObjectModel } from '../scene/sceneState'
import { saveModelAsset } from './modelAssetStore'
import {
  modelNameFromFile,
  validateGlbFile,
} from './modelAssetValidation'

interface ModelUploadPanelProps {
  dispatch: Dispatch<SceneHistoryAction>
}

export default function ModelUploadPanel({ dispatch }: ModelUploadPanelProps) {
  const inputId = useId()
  const [busy, setBusy] = useState(false)
  const [message, setMessage] = useState(
    'GLB tối đa 25 MB · xử lý cục bộ trên thiết bị.',
  )
  const [hasError, setHasError] = useState(false)

  const handleFile = async (event: ChangeEvent<HTMLInputElement>) => {
    const file = event.target.files?.[0]
    event.target.value = ''
    if (!file) return

    setBusy(true)
    setHasError(false)
    setMessage('Đang kiểm tra và lưu vật thể…')

    try {
      const validationError = await validateGlbFile(file)
      if (validationError) {
        setHasError(true)
        setMessage(validationError)
        return
      }

      const assetId = crypto.randomUUID()
      const name = modelNameFromFile(file.name)
      const objectId = `model-${assetId}`

      try {
        const { disposeModel, loadGlbModel } = await import('./modelAssetLoader')
        const parsedModel = await loadGlbModel(file, objectId)
        disposeModel(parsedModel)
      } catch {
        setHasError(true)
        setMessage('Không thể đọc nội dung file GLB.')
        return
      }

      await saveModelAsset({
        id: assetId,
        name,
        blob: file,
        size: file.size,
        createdAt: Date.now(),
      })

      const object: SceneObjectModel = {
        id: objectId,
        name,
        kind: 'model',
        assetId,
        color: '#ffffff',
        position: [0, 0, 0],
        rotation: [0, 0, 0],
        scale: 1,
      }

      dispatch({ type: 'add-object', object })
      setMessage(`Đã thêm “${name}” vào cảnh.`)
    } catch {
      setHasError(true)
      setMessage('Không thể lưu vật thể trên thiết bị này.')
    } finally {
      setBusy(false)
    }
  }

  return (
    <section className="model-upload-panel" aria-labelledby="model-upload-title">
      <div className="panel-heading">
        <p className="panel-kicker">Thư viện cá nhân</p>
        <h2 id="model-upload-title">Tải vật thể</h2>
      </div>

      <label className="model-upload-button" htmlFor={inputId}>
        {busy ? 'Đang xử lý…' : 'Chọn file GLB'}
      </label>
      <input
        id={inputId}
        className="model-upload-input"
        type="file"
        accept=".glb,model/gltf-binary"
        disabled={busy}
        onChange={(event) => void handleFile(event)}
      />
      <p
        className={`model-upload-message ${hasError ? 'is-error' : ''}`}
        role="status"
      >
        {message}
      </p>
    </section>
  )
}
