import { useId, type ChangeEvent, type Dispatch } from 'react'
import type {
  SceneHistoryAction,
  SceneHistoryState,
} from '../scene/sceneHistory'
import {
  createShapeObject,
  findSpawnPosition,
  SHAPE_PRESETS,
  type ShapeKind,
} from '../scene/sceneState'
import { createModelObject, isAssetReferenced } from './modelLibrary'
import type { ModelLibrary, ModelLibraryItem } from './useModelLibrary'

interface AddObjectPanelProps {
  dispatch: Dispatch<SceneHistoryAction>
  history: SceneHistoryState
  library: ModelLibrary
}

const shapeIcons: Record<ShapeKind, string> = {
  box: '▣',
  sphere: '◉',
  cylinder: '▥',
}

const formatSize = (bytes: number) =>
  bytes >= 1024 * 1024
    ? `${(bytes / 1024 / 1024).toFixed(1)} MB`
    : `${Math.max(1, Math.round(bytes / 1024))} KB`

export default function AddObjectPanel({
  dispatch,
  history,
  library,
}: AddObjectPanelProps) {
  const inputId = useId()
  const { items, busy, message, hasError, importFile, removeItem, report } =
    library

  const spawnPosition = () => findSpawnPosition(history.present.objects)

  const placeShape = (kind: ShapeKind) => {
    const object = createShapeObject(kind, spawnPosition())
    dispatch({ type: 'add-object', object })
    report(`Đã thêm “${object.name}” vào cảnh.`)
  }

  const placeModel = (item: ModelLibraryItem) => {
    dispatch({
      type: 'add-object',
      object: createModelObject(item, spawnPosition()),
    })
    report(`Đã lấy “${item.name}” từ kho.`)
  }

  const deleteFromLibrary = (item: ModelLibraryItem) => {
    if (isAssetReferenced(history, item.id)) {
      report(
        `“${item.name}” đang có trong cảnh hoặc lịch sử Hoàn tác nên chưa thể xóa khỏi kho.`,
        true,
      )
      return
    }

    void removeItem(item)
  }

  const handleFile = async (event: ChangeEvent<HTMLInputElement>) => {
    const file = event.target.files?.[0]
    event.target.value = ''
    if (!file) return

    const item = await importFile(file)
    if (item) {
      dispatch({
        type: 'add-object',
        object: createModelObject(item, spawnPosition()),
      })
    }
  }

  return (
    <div className="add-panel">
      <section aria-labelledby="shape-title">
        <h3 id="shape-title" className="hud-section-title">
          Hình cơ bản
        </h3>
        <div className="shape-grid">
          {(Object.keys(SHAPE_PRESETS) as ShapeKind[]).map((kind) => (
            <button
              className="hud-tile"
              type="button"
              key={kind}
              data-gesture-target
              onClick={() => placeShape(kind)}
            >
              <span aria-hidden="true">{shapeIcons[kind]}</span>
              {SHAPE_PRESETS[kind].name}
            </button>
          ))}
        </div>
      </section>

      <section aria-labelledby="library-title">
        <h3 id="library-title" className="hud-section-title">
          Kho vật thể <span>{items.length}</span>
        </h3>
        {items.length === 0 ? (
          <p className="library-empty">
            Kho đang trống. Tải file GLB lên một lần, sau đó có thể lấy ra bằng
            cử chỉ tay bao nhiêu lần tùy ý.
          </p>
        ) : (
          <ul className="library-list">
            {items.map((item) => (
              <li key={item.id}>
                <button
                  className="library-item"
                  type="button"
                  data-gesture-target
                  onClick={() => placeModel(item)}
                >
                  <span className="library-item-icon" aria-hidden="true">
                    ◈
                  </span>
                  <span className="library-item-name">{item.name}</span>
                  <small>{formatSize(item.size)}</small>
                </button>
                <button
                  className="library-remove"
                  type="button"
                  aria-label={`Xóa “${item.name}” khỏi kho`}
                  data-gesture-target
                  onClick={() => deleteFromLibrary(item)}
                >
                  ✕
                </button>
              </li>
            ))}
          </ul>
        )}
      </section>

      <label className={`upload-button ${busy ? 'is-busy' : ''}`} htmlFor={inputId}>
        {busy ? 'Đang xử lý…' : 'Tải file GLB vào kho'}
      </label>
      <input
        id={inputId}
        className="visually-hidden"
        type="file"
        accept=".glb,model/gltf-binary"
        disabled={busy}
        onChange={(event) => void handleFile(event)}
      />
      <p className="upload-hint">Chọn file cần dùng chuột · GLB tối đa 25 MB</p>
      <p className={`hud-message ${hasError ? 'is-error' : ''}`} role="status">
        {message}
      </p>
    </div>
  )
}
