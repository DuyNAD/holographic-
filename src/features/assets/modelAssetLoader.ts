import {
  Box3,
  Group,
  Mesh,
  Texture,
  Vector3,
  type Material,
  type Object3D,
} from 'three'
import { GLTFLoader } from 'three/addons/loaders/GLTFLoader.js'

const NORMALIZED_MODEL_SIZE = 1.6

const readBlob = (blob: Blob) =>
  new Promise<ArrayBuffer>((resolve, reject) => {
    const reader = new FileReader()
    reader.onload = () => resolve(reader.result as ArrayBuffer)
    reader.onerror = () => reject(reader.error)
    reader.readAsArrayBuffer(blob)
  })

const disposeMaterial = (material: Material) => {
  Object.values(material).forEach((value) => {
    if (value instanceof Texture) value.dispose()
  })
  material.dispose()
}

export function disposeModel(root: Object3D) {
  root.traverse((child) => {
    if (!(child instanceof Mesh)) return
    child.geometry.dispose()
    const materials = Array.isArray(child.material)
      ? child.material
      : [child.material]
    materials.forEach(disposeMaterial)
  })
}

export function prepareModelScene(scene: Object3D, objectId: string) {
  scene.updateMatrixWorld(true)
  const bounds = new Box3().setFromObject(scene)
  const size = bounds.getSize(new Vector3())
  const center = bounds.getCenter(new Vector3())
  const largestDimension = Math.max(size.x, size.y, size.z)

  if (!Number.isFinite(largestDimension) || largestDimension <= 0) {
    throw new Error('Model does not contain renderable geometry.')
  }

  scene.position.sub(center)

  const normalized = new Group()
  normalized.scale.setScalar(NORMALIZED_MODEL_SIZE / largestDimension)
  normalized.userData.objectId = objectId
  normalized.add(scene)
  normalized.traverse((child) => {
    child.userData.objectId = objectId
    if (child instanceof Mesh) {
      child.castShadow = true
      child.receiveShadow = true
    }
  })
  normalized.updateMatrixWorld(true)

  return normalized
}

export async function loadGlbModel(
  blob: Blob,
  objectId: string,
): Promise<Group> {
  const data = await readBlob(blob)
  const loader = new GLTFLoader()

  const gltf = await new Promise<{ scene: Group }>((resolve, reject) => {
    loader.parse(data, '', resolve, reject)
  })

  return prepareModelScene(gltf.scene, objectId)
}
