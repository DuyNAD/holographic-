import { useThree } from '@react-three/fiber'
import { useEffect, useRef, type Dispatch } from 'react'
import { Plane, Raycaster, Vector2, Vector3 } from 'three'
import type { StableGesture } from '../gestures/gestureTypes'
import type { SceneHistoryAction } from '../scene/sceneHistory'
import type { SceneState } from '../scene/sceneState'
import {
  distanceBetweenLandmarks,
  handRotationAngle,
  landmarkToNdc,
} from './gestureCoordinates'

interface GestureInteractionLayerProps {
  gestures: StableGesture[]
  sceneState: SceneState
  dispatch: Dispatch<SceneHistoryAction>
}

const createDragPlane = () => new Plane(new Vector3(0, 0, 1), 0)

export default function GestureInteractionLayer({
  gestures,
  sceneState,
  dispatch,
}: GestureInteractionLayerProps) {
  const { camera, scene } = useThree()
  const sceneStateRef = useRef(sceneState)
  const raycasterRef = useRef(new Raycaster())
  const dragPlaneRef = useRef(createDragPlane())
  const grabbedIdRef = useRef<string | null>(null)
  const dragOffsetRef = useRef(new Vector3())
  const scaleStartRef = useRef<{ distance: number; scale: number } | null>(null)
  const rotationStartRef = useRef<{ angle: number; rotation: number } | null>(null)
  const interactionActiveRef = useRef(false)

  useEffect(() => {
    sceneStateRef.current = sceneState
  }, [sceneState])

  useEffect(() => {
    const resetSession = () => {
      if (interactionActiveRef.current) {
        dispatch({ type: 'end-interaction' })
        interactionActiveRef.current = false
      }
      grabbedIdRef.current = null
      scaleStartRef.current = null
      rotationStartRef.current = null
    }

    if (gestures.length === 0 || gestures.some(({ name }) => name === 'open-palm')) {
      resetSession()
      return
    }

    const pinches = gestures.filter(({ name }) => name === 'pinch')
    const selected = sceneStateRef.current.objects.find(
      ({ id }) => id === sceneStateRef.current.selectedId,
    )

    if (pinches.length >= 2 && selected) {
      grabbedIdRef.current = null
      rotationStartRef.current = null
      const firstTip = pinches[0].landmarks[8]
      const secondTip = pinches[1].landmarks[8]
      if (!firstTip || !secondTip) return

      const distance = distanceBetweenLandmarks(firstTip, secondTip)
      if (!scaleStartRef.current) {
        if (!interactionActiveRef.current) {
          dispatch({ type: 'begin-interaction' })
          interactionActiveRef.current = true
        }
        scaleStartRef.current = { distance: Math.max(distance, 0.01), scale: selected.scale }
        return
      }

      dispatch({
        type: 'set-scale',
        scale:
          scaleStartRef.current.scale *
          (distance / scaleStartRef.current.distance),
      })
      return
    }

    scaleStartRef.current = null
    const primary = gestures[0]
    const indexTip = primary?.landmarks[8]
    if (!primary || !indexTip) return

    if (primary.name === 'pinch') {
      rotationStartRef.current = null
      const ndc = landmarkToNdc(indexTip)
      raycasterRef.current.setFromCamera(new Vector2(ndc.x, ndc.y), camera)

      if (!grabbedIdRef.current) {
        const hit = raycasterRef.current
          .intersectObjects(scene.children, true)
          .find(({ object }) => typeof object.userData.objectId === 'string')

        if (!hit) return

        const objectId = hit.object.userData.objectId as string
        const objectModel = sceneStateRef.current.objects.find(
          ({ id }) => id === objectId,
        )
        if (!objectModel) return

        grabbedIdRef.current = objectId
        dispatch({ type: 'select', id: objectId })
        if (!interactionActiveRef.current) {
          dispatch({ type: 'begin-interaction' })
          interactionActiveRef.current = true
        }

        const planePoint = new Vector3()
        if (raycasterRef.current.ray.intersectPlane(dragPlaneRef.current, planePoint)) {
          dragOffsetRef.current.set(
            objectModel.position[0] - planePoint.x,
            objectModel.position[1] - planePoint.y,
            0,
          )
        }
        return
      }

      const planePoint = new Vector3()
      if (raycasterRef.current.ray.intersectPlane(dragPlaneRef.current, planePoint)) {
        dispatch({
          type: 'set-position',
          position: [
            planePoint.x + dragOffsetRef.current.x,
            planePoint.y + dragOffsetRef.current.y,
            0,
          ],
        })
      }
      return
    }

    grabbedIdRef.current = null

    if (primary.name === 'fist' && selected) {
      const angle = handRotationAngle(primary.landmarks)
      if (!rotationStartRef.current) {
        if (!interactionActiveRef.current) {
          dispatch({ type: 'begin-interaction' })
          interactionActiveRef.current = true
        }
        rotationStartRef.current = {
          angle,
          rotation: selected.rotation[2],
        }
        return
      }

      dispatch({
        type: 'set-rotation',
        rotation: [
          selected.rotation[0],
          selected.rotation[1],
          rotationStartRef.current.rotation +
            (angle - rotationStartRef.current.angle),
        ],
      })
      return
    }

    rotationStartRef.current = null
  }, [camera, dispatch, gestures, scene])

  return null
}

