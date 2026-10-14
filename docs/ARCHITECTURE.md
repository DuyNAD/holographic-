# Holographic Studio architecture

## Data flow

```text
Webcam
  → Camera controller
  → MediaPipe Hand Landmarker
  → Landmark smoothing
  → Gesture classifier
  → Debounced gesture state machine
  ├→ Hand pointer → dwell (1 s) → HUD buttons (menu, panels, calibration)
  └→ Three.js interaction controller
  → Scene history and persistence
```

Mouse, keyboard, and hand input all end in the same actions: HUD buttons call the same handlers whether they are clicked or pressed by dwell, and every scene change goes through `sceneHistoryReducer`.

Camera frames never enter React state. The video element is passed directly to MediaPipe, and only normalized landmark coordinates are stored for rendering and gesture recognition.

## Modules

- `features/camera`: starts and stops `MediaStream`, owns the video element, and maps browser errors into recoverable UI states.
- `features/hand-tracking`: initializes MediaPipe, performs video inference, and renders the landmark skeleton.
- `features/gestures`: smooths landmarks, classifies gestures, and debounces activation/release across frames.
- `features/interaction`: converts gesture coordinates into Three.js rays, groups continuous interaction frames, and drives the hand pointer. `dwell.ts` turns a pointer that rests on one `[data-gesture-target]` element for one second into a single click; pinches over `[data-hud]` elements never grab objects behind them.
- `features/hud`: the full-window HUD — status chips, the VR-style menu dock (add, delete, guide, collapse), its slide-out panels, and the undo toast.
- `features/scene`: owns object state (add, remove, transform), free-slot spawning, Undo/Redo history, persistence, and the full-window 3D viewport.
- `features/calibration`: enforces camera, hand-position, and pinch checks before first use.
- `features/assets`: the object library. Validates GLB uploads, stores model blobs in IndexedDB, lists and deletes stored models, creates a new scene object for every placement of a stored model, normalizes imported scenes, and tags child meshes for gesture raycasting. A model cannot be deleted from the library while the scene or its Undo/Redo history still references it.

## Safety boundaries

- Camera tracks are stopped when camera use ends or the component unmounts.
- Losing tracking ends the active interaction session before a hand can reconnect.
- Gesture transforms use bounded object scale values.
- Continuous gesture frames are grouped into one Undo entry; discrete edits made during a gesture (menu, keyboard, delete) still get their own entry.
- A dwell press fires once per hover; the cursor must leave a button before it can press it again.
- Invalid persisted scene data falls back to the initial scene.
- Imported files are limited to GLB 2.0 files of at most 25 MB and remain on the local device.
- A top-level error boundary provides a recoverable reload screen.

## Performance

The main application, MediaPipe bundle, and Three.js viewport are separate production chunks. MediaPipe is loaded only when hand tracking initializes. The scene is persisted with a short debounce to avoid writing every camera frame.

