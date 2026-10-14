import { Canvas, type ThreeEvent } from '@react-three/fiber'
import type { Dispatch } from 'react'
import ImportedModel from '../assets/ImportedModel'
import type { StableGesture } from '../gestures/gestureTypes'
import GestureCursors from '../interaction/GestureCursors'
import GestureInteractionLayer from '../interaction/GestureInteractionLayer'
import type { SceneHistoryAction } from './sceneHistory'
import type {
  SceneObjectKind,
  SceneObjectModel,
  SceneState,
} from './sceneState'

interface SceneViewportProps {
  scene: SceneState
  dispatch: Dispatch<SceneHistoryAction>
  gestures: StableGesture[]
}

interface SceneMeshProps {
  object: SceneObjectModel
  selected: boolean
  onSelect: (event: ThreeEvent<PointerEvent>) => void
}

function ObjectGeometry({ kind }: { kind: SceneObjectKind }) {
  switch (kind) {
    case 'sphere':
      return <sphereGeometry args={[0.82, 40, 40]} />
    case 'cylinder':
      return <cylinderGeometry args={[0.7, 0.88, 1.65, 36]} />
    case 'box':
      return <boxGeometry args={[1.45, 1.45, 1.45]} />
  }
}

function SceneMesh({ object, selected, onSelect }: SceneMeshProps) {
  return (
    <mesh
      position={object.position}
      rotation={object.rotation}
      scale={object.scale}
      onPointerDown={onSelect}
      userData={{ objectId: object.id }}
      castShadow
      receiveShadow
    >
      <ObjectGeometry kind={object.kind} />
      <meshStandardMaterial
        color={object.color}
        emissive={selected ? '#164e68' : '#000000'}
        emissiveIntensity={selected ? 1.5 : 0}
        metalness={0.42}
        roughness={0.28}
      />
    </mesh>
  )
}

function SceneObject({ object, selected, onSelect }: SceneMeshProps) {
  if (object.kind === 'model') {
    return (
      <ImportedModel
        object={object}
        selected={selected}
        onSelect={onSelect}
      />
    )
  }

  return <SceneMesh object={object} selected={selected} onSelect={onSelect} />
}

function SceneContent({ scene, dispatch, gestures }: SceneViewportProps) {
  return (
    <>
      <color attach="background" args={['#030a13']} />
      <ambientLight intensity={0.8} />
      <directionalLight
        position={[4, 7, 5]}
        intensity={2.4}
        color="#dff7ff"
        castShadow
      />
      <pointLight position={[-5, 2, 2]} intensity={16} color="#1d9dff" />
      <pointLight position={[5, 1, -2]} intensity={12} color="#6a46ff" />

      {scene.objects.map((object) => (
        <SceneObject
          key={object.id}
          object={object}
          selected={scene.selectedId === object.id}
          onSelect={(event) => {
            event.stopPropagation()
            dispatch({ type: 'select', id: object.id })
          }}
        />
      ))}

      <GestureInteractionLayer
        gestures={gestures}
        sceneState={scene}
        dispatch={dispatch}
      />

      <gridHelper
        args={[18, 18, '#1b7599', '#113148']}
        position={[0, -1.15, 0]}
      />
    </>
  )
}

export default function SceneViewport({
  scene,
  dispatch,
  gestures,
}: SceneViewportProps) {
  return (
    <div className="scene-viewport" aria-label="Khung nhìn ba chiều">
      <p className="viewport-label">3D viewport · chọn một vật thể</p>
      <Canvas
        camera={{ position: [6.5, 4.3, 7.5], fov: 42 }}
        dpr={[1, 1.75]}
        gl={{ antialias: true, alpha: false }}
        onPointerMissed={() => dispatch({ type: 'select', id: null })}
        shadows
      >
        <SceneContent scene={scene} dispatch={dispatch} gestures={gestures} />
      </Canvas>
      <GestureCursors gestures={gestures} />
    </div>
  )
}

