import { useEffect, useRef, useState } from 'react'
import type { StableGesture } from '../gestures/gestureTypes'
import { advanceDwell, createDwellState, type DwellState } from './dwell'
import { gestureTargetAt } from './hudHitTest'

interface HandPointerProps {
  gestures: StableGesture[]
}

const cursorLabels: Record<StableGesture['name'], string> = {
  point: 'Trỏ',
  pinch: 'Nắm',
  fist: 'Xoay',
  'open-palm': 'Thả',
}

const HOVER_CLASS = 'is-gesture-hover'

const clearHover = (element: HTMLElement | null) => {
  element?.classList.remove(HOVER_CLASS)
  element?.style.removeProperty('--dwell-progress')
}

export default function HandPointer({ gestures }: HandPointerProps) {
  const dwellRef = useRef<DwellState<HTMLElement>>(createDwellState())
  const [progress, setProgress] = useState(0)
  const pointer = gestures.find(({ name }) => name === 'point')
  const tip = pointer?.landmarks[8]

  useEffect(() => {
    const previous = dwellRef.current.target
    const target = tip ? gestureTargetAt(tip) : null
    const usable =
      target && !(target as HTMLButtonElement).disabled ? target : null
    const step = advanceDwell(dwellRef.current, usable, performance.now())

    if (previous !== step.state.target) clearHover(previous)
    if (step.state.target) {
      step.state.target.classList.add(HOVER_CLASS)
      step.state.target.style.setProperty(
        '--dwell-progress',
        step.progress.toFixed(3),
      )
    }

    dwellRef.current = step.state
    setProgress(step.progress)
    if (step.fire) step.state.target?.click()
  }, [tip])

  useEffect(() => () => clearHover(dwellRef.current.target), [])

  return (
    <div className="hand-pointer-layer" aria-hidden="true">
      {gestures.map((gesture) => {
        const point = gesture.landmarks[8]
        if (!point) return null
        const isPointer = gesture === pointer

        return (
          <div
            className={`hand-pointer hand-pointer--${gesture.name}`}
            key={`${gesture.handedness}-${gesture.handIndex}`}
            style={{ left: `${(1 - point.x) * 100}%`, top: `${point.y * 100}%` }}
          >
            {isPointer && progress > 0 && (
              <svg className="hand-pointer-dwell" viewBox="0 0 36 36">
                <circle
                  cx="18"
                  cy="18"
                  r="16"
                  pathLength={1}
                  strokeDasharray={`${progress} 1`}
                />
              </svg>
            )}
            <span />
            <small>{cursorLabels[gesture.name]}</small>
          </div>
        )
      })}
    </div>
  )
}
