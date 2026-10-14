# Holographic Studio architecture

## Data flow

```text
Webcam
  → Camera controller
  → MediaPipe Hand Landmarker
  → Landmark smoothing
  → Gesture classifier
  → Debounced gesture state machine
  → Three.js interaction controller
  → Scene history and persistence
```

Camera frames never enter React state. The video element is passed directly to MediaPipe, and only normalized landmark coordinates are stored for rendering and gesture recognition.

## Modules

- `features/camera`: starts and stops `MediaStream`, owns the video element, and maps browser errors into recoverable UI states.
- `features/hand-tracking`: initializes MediaPipe, performs video inference, and renders the landmark skeleton.
- `features/gestures`: smooths landmarks, classifies gestures, and debounces activation/release across frames.
- `features/interaction`: converts gesture coordinates into Three.js rays and groups continuous interaction frames.
- `features/scene`: owns object state, Undo/Redo history, persistence, and the 3D viewport.
- `features/calibration`: enforces camera, hand-position, and pinch checks before first use.
- `features/assets`: validates GLB uploads, stores model blobs in IndexedDB, normalizes imported scenes, and tags child meshes for gesture raycasting.

## Safety boundaries

- Camera tracks are stopped when camera use ends or the component unmounts.
- Losing tracking ends the active interaction session before a hand can reconnect.
- Gesture transforms use bounded object scale values.
- Continuous gesture frames are grouped into one Undo entry.
- Invalid persisted scene data falls back to the initial scene.
- Imported files are limited to GLB 2.0 files of at most 25 MB and remain on the local device.
- A top-level error boundary provides a recoverable reload screen.

## Performance

The main application, MediaPipe bundle, and Three.js viewport are separate production chunks. MediaPipe is loaded only when hand tracking initializes. The scene is persisted with a short debounce to avoid writing every camera frame.

