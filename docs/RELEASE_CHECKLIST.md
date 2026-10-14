# Release candidate checklist

## Automated gate

- [x] `pnpm ci` succeeds from the committed lockfile.
- [x] `pnpm lint` reports no errors or warnings.
- [x] `pnpm test` passes every test.
- [x] `pnpm build` produces the production bundle.
- [x] `pnpm audit --prod` reports no known production vulnerabilities.
- [x] `git diff --check` reports no whitespace errors.

## Manual end-to-end gate

- [ ] First-run calibration opens.
- [ ] Camera permission can be granted and the preview is visible.
- [ ] One or two hands can be tracked.
- [ ] Point, pinch, fist, open-palm, and two-hand scale are recognized.
- [ ] Select, move, rotate, scale, release, Undo, and Redo work.
- [ ] Losing and reacquiring a hand does not move an object unexpectedly.
- [ ] Refresh restores the saved scene.
- [ ] A valid GLB can be uploaded, selected, transformed, undone, redone, and restored after refresh.
- [ ] Invalid, oversized, and non-GLB files show a recoverable error.
- [ ] Recalibration can be started from the header.
- [ ] Narrow-screen layout keeps all controls reachable.

G10 passes only when both sections are complete.
