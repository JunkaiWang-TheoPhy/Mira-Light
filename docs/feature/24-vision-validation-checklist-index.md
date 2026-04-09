# Vision Validation Checklist Index

## Purpose

This page is the one-stop operator entry for the current Mira Light vision validation flow.

Use it when you are on-site and need a single page that answers:

- what should be checked first
- which checklist to run next
- which checklist is browser-side vs CLI-side vs full integration
- what counts as a meaningful pass before moving on

This page does not replace the underlying checklists.
It exists to help an operator or engineer run them in the right order.

## Recommended Order

Run the following in sequence:

### Step 1. Browser-side sanity check

Use:

- [Director Console Vision UI 1-Minute Smoke Checklist](./21-director-console-vision-ui-smoke-checklist.md)

Goal:

- confirm the browser console loads
- confirm the `Vision State` panel is visible
- confirm operator lock / unlock is reflected in UI

Best for:

- operator-facing verification
- first visual confirmation that the page is wired correctly

### Step 2. CLI-side file and process sanity check

Use:

- [Vision Pipeline CLI 1-Minute Smoke Checklist](./22-vision-pipeline-cli-1-minute-smoke-checklist.md)

Goal:

- confirm the receiver is listening
- confirm JPEG frames are present
- confirm `vision.latest.json`, `vision.bridge.state.json`, and `vision.operator.json` exist and are valid

Best for:

- engineering-side verification
- quickly isolating “is this a UI issue or a pipeline issue?”

### Step 3. Full integration behavior check

Use:

- [Vision + Runtime + Scene 5-Minute Integration Checklist](./23-vision-runtime-scene-5-minute-integration-checklist.md)

Goal:

- confirm target appearance can trigger `wake_up`
- confirm stable target presence can maintain `track_target`
- confirm operator lock changes target preference
- confirm target disappearance produces a graceful exit

Best for:

- rehearsal validation
- pre-demo confidence checks
- confirming that the stack behaves like a coherent embodied system, not just a collection of scripts

## What Each Checklist Covers

| Checklist | Primary layer | Typical duration | Best used by |
| --- | --- | --- | --- |
| [UI 1-Minute](./21-director-console-vision-ui-smoke-checklist.md) | Browser / operator surface | 1 minute | Operator, demo lead |
| [CLI 1-Minute](./22-vision-pipeline-cli-1-minute-smoke-checklist.md) | Processes / files / local pipeline | 1 minute | Engineer, maintainer |
| [5-Minute Integration](./23-vision-runtime-scene-5-minute-integration-checklist.md) | Behavior / runtime / scene loop | 5 minutes | Engineer + operator together |

## Minimal Pass Bar For A Demo

If time is limited and you only need a practical “can we demo this?” answer, use this minimum pass bar:

1. UI 1-minute checklist passes
2. CLI 1-minute checklist passes
3. In the 5-minute integration checklist:
   - `wake_up` works
   - `track_target` works
   - lock / unlock works
   - target loss exits cleanly

If all four are true, the vision stack is usually good enough for a controlled demo.

## If Something Fails

Use this quick routing:

### Browser looks wrong, but CLI files exist

Likely issue:

- UI rendering
- browser polling
- console API wiring

Start with:

- [Director Console Vision UI 1-Minute Smoke Checklist](./21-director-console-vision-ui-smoke-checklist.md)

### Browser and CLI both show nothing

Likely issue:

- receiver not running
- no upstream frames
- wrong runtime directory

Start with:

- [Vision Pipeline CLI 1-Minute Smoke Checklist](./22-vision-pipeline-cli-1-minute-smoke-checklist.md)

### Files exist, but the lamp behaves strangely

Likely issue:

- bridge gating
- detector instability
- tracking / scene transition logic

Start with:

- [Vision + Runtime + Scene 5-Minute Integration Checklist](./23-vision-runtime-scene-5-minute-integration-checklist.md)

## Recommended On-Site Usage

For a real rehearsal or on-site setup:

1. One person opens the browser console and runs the UI checklist
2. One person watches terminal / files and runs the CLI checklist
3. Then both run the 5-minute integration checklist together

This splits operator-facing and engineering-facing confirmation while still converging on the same final behavior check.

## Related Feature Docs

If you need background beyond the checklists, read:

- [Camera CV and Runtime Bridge Progress](./20-camera-cv-runtime-bridge-progress.md)
- [../mira-light-vision-stream-and-gemini-summary.md](../mira-light-vision-stream-and-gemini-summary.md)
- [../mira-light-single-camera-fourdof-vision-development-guide.md](../mira-light-single-camera-fourdof-vision-development-guide.md)

## One-Line Summary

This page is the operator-friendly entrypoint for validating the full local Mira Light vision stack in the correct order:

```text
UI -> CLI -> behavior
```
