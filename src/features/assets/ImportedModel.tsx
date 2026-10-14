import { useEffect, useState } from 'react'
import type { ThreeEvent } from '@react-three/fiber'
import type { Group } from 'three'
import type { SceneObjectModel } from '../scene/sceneState'
import { loadModelAsset } from './modelAssetStore'

interface ImportedModelProps {
  object: SceneObjectModel
  selected: boolean
  onSelect: (event: ThreeEvent<PointerEvent>) => void
}

export default function ImportedModel({
  object,
  selected,
  onSelect,
}: ImportedModelProps) {
  const [model, setModel] = useState<Group | null>(null)
  const [failed, setFailed] = useState(false)

  useEffect(() => {
    let cancelled = false
    let loadedModel: Group | null = null
    let disposeLoadedModel: ((model: Group) => void) | null = null

    const load = async () => {
      if (!object.assetId) throw new Error('Missing model asset id.')
      const asset = await loadModelAsset(object.assetId)
      if (!asset) throw new Error('Model asset was not found.')

      const { disposeModel, loadGlbModel } = await import('./modelAssetLoader')
      disposeLoadedModel = disposeModel
      loadedModel = await loadGlbModel(asset.blob, object.id)
      if (cancelled) {
        disposeLoadedModel(loadedModel)
        return
      }

      setModel(loadedModel)
    }

    void load().catch(() => {
      if (!cancelled) setFailed(true)
    })

    return () => {
      cancelled = true
      if (loadedModel) disposeLoadedModel?.(loadedModel)
    }
  }, [object.assetId, object.id])

  return (
    <group
      position={object.position}
      rotation={object.rotation}
      scale={object.scale}
      onPointerDown={onSelect}
      userData={{ objectId: object.id }}
    >
      {model && <primitive object={model} />}
      {!model && (
        <mesh userData={{ objectId: object.id }}>
          <boxGeometry args={[1.4, 1.4, 1.4]} />
          <meshBasicMaterial
            color={failed ? '#ff6f7d' : '#47d9ff'}
            opacity={0.32}
            transparent
            wireframe
          />
        </mesh>
      )}
      {selected && (
        <mesh scale={1.12} raycast={() => null}>
          <boxGeometry args={[1.6, 1.6, 1.6]} />
          <meshBasicMaterial
            color="#79ebff"
            opacity={0.5}
            transparent
            wireframe
          />
        </mesh>
      )}
    </group>
  )
}
