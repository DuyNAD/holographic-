import {
  lazy,
  Suspense,
  useCallback,
  useEffect,
  useMemo,
  useReducer,
  useState,
} from 'react'
import AddObjectPanel from './features/assets/AddObjectPanel'
import { useModelLibrary } from './features/assets/useModelLibrary'
import CalibrationWizard from './features/calibration/CalibrationWizard'
import CameraWindow from './features/camera/CameraWindow'
import { useCamera } from './features/camera/useCamera'
import { useGestureEngine } from './features/gestures/useGestureEngine'
import { useHandTracking } from './features/hand-tracking/useHandTracking'
import GuidePanel from './features/hud/GuidePanel'
import HudMenu from './features/hud/HudMenu'
import HudStatus from './features/hud/HudStatus'
import UndoToast from './features/hud/UndoToast'
import HandPointer from './features/interaction/HandPointer'
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
  const closeCalibration = useCallback(() => setCalibrationOpen(false), [])
  const camera = useCamera()
  const handTracking = useHandTracking(camera.videoRef, camera.status)
  const gestures = useGestureEngine(handTracking)
  const library = useModelLibrary()
  const [sceneHistory, dispatch] = useReducer(
    sceneHistoryReducer,
    loadSceneState(),
    createInitialSceneHistory,
  )
  const scene = sceneHistory.present
  const [undoMessage, setUndoMessage] = useState<string | null>(null)
  const dismissUndo = useCallback(() => setUndoMessage(null), [])

  const selectedObject = useMemo(
    () => scene.objects.find((object) => object.id === scene.selectedId) ?? null,
    [scene.objects, scene.selectedId],
  )

  const deleteSelected = useCallback(() => {
    if (!selectedObject) return
    dispatch({ type: 'remove-object', id: selectedObject.id })
    setUndoMessage(`Đã xóa “${selectedObject.name}”`)
  }, [selectedObject])

  useEffect(() => {
    const timeout = window.setTimeout(() => saveSceneState(scene), 250)
    return () => window.clearTimeout(timeout)
  }, [scene])

  useEffect(() => {
    if (calibrationOpen) return

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
        Delete: deleteSelected,
      }

      const action = keyActions[event.key]
      if (action && selectedObject) {
        event.preventDefault()
        action()
      }
    }

    window.addEventListener('keydown', handleKeyDown)
    return () => window.removeEventListener('keydown', handleKeyDown)
  }, [calibrationOpen, deleteSelected, selectedObject])

  return (
    <main className="studio">
      <Suspense
        fallback={
          <div className="scene-loading" role="status">
            Đang khởi tạo không gian 3D…
          </div>
        }
      >
        <SceneViewport scene={scene} dispatch={dispatch} gestures={gestures} />
      </Suspense>

      <div className="hud">
        <HudStatus
          gestures={gestures}
          trackingStatus={handTracking.status}
          selectedName={selectedObject?.name ?? null}
        />
        <CameraWindow camera={camera} handTracking={handTracking} />
        <HudMenu
          selectedName={selectedObject?.name ?? null}
          onDelete={deleteSelected}
          addPanel={
            <AddObjectPanel
              dispatch={dispatch}
              history={sceneHistory}
              library={library}
            />
          }
          guidePanel={
            <GuidePanel
              gestures={gestures}
              onRecalibrate={() => setCalibrationOpen(true)}
            />
          }
        />
        {undoMessage && (
          <UndoToast
            message={undoMessage}
            onUndo={() => dispatch({ type: 'undo' })}
            onDismiss={dismissUndo}
          />
        )}
      </div>

      <HandPointer gestures={gestures} />

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
          onSkip={closeCalibration}
        />
      )}
    </main>
  )
}

export default App
