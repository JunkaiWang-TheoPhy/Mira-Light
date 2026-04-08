---
name: mira-light-orchestrator
description: Safely orchestrate Mira Light scenes, status checks, and low-level recovery through the local bridge.
metadata: {"openclaw":{"requires":{"config":["plugins.entries.mira-light-bridge.enabled"]}}}
---

# Mira Light Orchestrator

Use this skill when the task involves Mira's physical body, scene choice, lamp
state, or the boundary between vision events and motion.

## Default workflow

1. Read `mira_light_runtime_status` and `mira_light_status` if physical state matters.
2. Prefer `mira_light_list_scenes` or known scene names to reason about behavior.
3. Use `mira_light_run_scene` for embodied responses.
4. Use `mira_light_set_led` for light-only adjustments.
5. Use `mira_light_stop` or `mira_light_reset` for recovery.
6. Use `mira_light_control_joints` only when the human explicitly wants
   calibration, direct rehearsal, or recovery from a bad pose.

## Scene-first policy

The body should usually express intent through named scenes rather than raw
servo commands. Scene-first keeps the behavior legible and preserves Mira's
personality.

Good defaults:

- greet or first notice: `wake_up`
- gentle attention: `curious_observe`
- warmth or contact: `touch_affection`
- playful hesitation: `cute_probe`
- ambient aliveness: `daydream`
- positive payoff: `celebrate`
- departure: `farewell`
- rest: `sleep`

## Vision policy

When the task mentions seeing, target tracking, or camera input:

- treat vision outputs as event data
- look for `scene_hint` and `control_hint`
- prefer routing through the runtime bridge instead of inventing servo angles
- remember that `track_target` is still experimental

Reference files:

- `{baseDir}/../../TOOLS.md`
- `__REPO_ROOT__/config/mira_light_vision_event.schema.json`
- `__REPO_ROOT__/scripts/track_target_event_extractor.py`
- `__REPO_ROOT__/scripts/vision_runtime_bridge.py`

## Recovery rules

- If the bridge or lamp seems unhealthy, stop and inspect before sending more motion.
- If a user request conflicts with safety or scene readiness, explain the safer
  alternative and propose the closest scene.
- Preserve the feeling of intention: small safe actions are better than large unsafe ones.
