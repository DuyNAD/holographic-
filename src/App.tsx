import {
  lazy,
  Suspense,
  useEffect,
  useMemo,
  useReducer,
  useState,
} from 'react'
import ModelUploadPanel from './features/assets/ModelUploadPanel'
import CalibrationWizard from './features/calibration/CalibrationWizard'
import CameraPanel from './features/camera/CameraPanel'
import { useCamera } from './features/camera/useCamera'
import ObjectControls from './features/controls/ObjectControls'
import GestureGuidePanel from './features/gestures/GestureGuidePanel'
import { useGestureEngine } from './features/gestures/useGestureEngine'
import { useHandTracking } from './features/hand-tracking/useHandTracking'
import {
  createInitialSceneHistory,
  sceneHistoryReducer,
} from './features/scene/sceneHistory'
import { loadSceneState, saveSceneState } from './features/scene/sceneStorage'
import './App.css'

const SceneViewport = lazy(() => import('./features/scene/SceneViewport'))

function App() {
  const [calibrationOpen, setCalibrationOpen] = useState(
    () => localStorage.getItem('holographic-calibration') !== 'complete',
  )
  const camera = useCamera()
  const handTracking = useHandTracking(camera.videoRef, camera.status)
  const gestures = useGestureEngine(handTracking)
  const [sceneHistory, dispatch] = useReducer(
    sceneHistoryReducer,
    loadSceneState(),
    createInitialSceneHistory,
  )
  const scene = sceneHistory.present

  const selectedObject = useMemo(
    () => scene.objects.find((object) => object.id === scene.selectedId) ?? null,
    [scene.objects, scene.selectedId],
  )

  useEffect(() => {
    const timeout = window.setTimeout(() => saveSceneState(scene), 250)
    return () => window.clearTimeout(timeout)
  }, [scene])

  useEffect(() => {
    const handleKeyDown = (event: KeyboardEvent) => {
      if (event.ctrlKey && event.key.toLowerCase() === 'z') {
        event.preventDefault()
        dispatch({ type: event.shiftKey ? 'redo' : 'undo' })
        return
      }

      if (event.ctrlKey && event.key.toLowerCase() === 'y') {
        event.preventDefault()
        dispatch({ type: 'redo' })
        return
      }

      const keyActions: Record<string, () => void> = {
        ArrowLeft: () =>
          dispatch({ type: 'translate', axis: 0, delta: -0.2 }),
        ArrowRight: () =>
          dispatch({ type: 'translate', axis: 0, delta: 0.2 }),
        ArrowUp: () => dispatch({ type: 'translate', axis: 1, delta: 0.2 }),
        ArrowDown: () =>
          dispatch({ type: 'translate', axis: 1, delta: -0.2 }),
        q: () => dispatch({ type: 'rotate', axis: 1, delta: -0.15 }),
        e: () => dispatch({ type: 'rotate', axis: 1, delta: 0.15 }),
        '-': () => dispatch({ type: 'scale', delta: -0.1 }),
        '=': () => dispatch({ type: 'scale', delta: 0.1 }),
      }

      const action = keyActions[event.key]
      if (action && scene.selectedId) {
        event.preventDefault()
        action()
      }
    }

    window.addEventListener('keydown', handleKeyDown)
    return () => window.removeEventListener('keydown', handleKeyDown)
  }, [scene.selectedId])

  return (
    <main className="studio-shell">
      <header className="studio-header">
        <div>
          <p className="eyebrow">Không gian thử nghiệm</p>
          <h1>Holographic Studio</h1>
        </div>
        <div className="header-actions">
          <button
            className="recalibrate-button"
            type="button"
            onClick={() => setCalibrationOpen(true)}
          >
            Hiệu chuẩn lại
          </button>
          <div className="system-status" role="status">
            <span className="status-dot" aria-hidden="true" />
            3D engine sẵn sàng
          </div>
        </div>
      </header>

      <section className="workspace" aria-label="Không gian thiết kế 3D">
        <Suspense
          fallback={
            <div className="scene-loading" role="status">
              Đang khởi tạo không gian 3D…
            </div>
          }
        >
          <SceneViewport scene={scene} dispatch={dispatch} gestures={gestures} />
        </Suspense>
        <aside className="side-rail" aria-label="Bảng điều khiển">
          <CameraPanel
            camera={camera}
            handTracking={handTracking}
          />
          <GestureGuidePanel
            gestures={gestures}
            trackingStatus={handTracking.status}
          />
          <ModelUploadPanel dispatch={dispatch} />
          <ObjectControls
            selectedObject={selectedObject}
            dispatch={dispatch}
            canUndo={sceneHistory.past.length > 0}
            canRedo={sceneHistory.future.length > 0}
          />
        </aside>
      </section>

      <footer className="shortcut-bar">
        <span>Chọn vật thể bằng chuột</span>
        <span>Di chuyển: phím mũi tên</span>
        <span>Xoay: Q / E</span>
        <span>Thu phóng: − / +</span>
        <span>Hoàn tác: Ctrl + Z</span>
      </footer>

      {calibrationOpen && (
        <CalibrationWizard
          cameraStatus={camera.status}
          trackingStatus={handTracking.status}
          gestures={gestures}
          onStartCamera={() => void camera.start()}
          onComplete={() => {
            localStorage.setItem('holographic-calibration', 'complete')
            setCalibrationOpen(false)
          }}
        />
      )}
    </main>
  )
}

export default App

