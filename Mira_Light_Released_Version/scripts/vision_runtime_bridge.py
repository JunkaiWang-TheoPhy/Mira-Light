#!/usr/bin/env python3
"""Bridge Mira Light vision events into the current runtime.

This process intentionally stays thin:
- reads the latest vision event JSON
- applies small hysteresis / cooldown rules
- triggers existing scenes through MiraLightRuntime

It does not:
- compute vision events itself
- directly control raw servos
- replace the scene choreography layer
"""

from __future__ import annotations

import argparse
from dataclasses import dataclass, field
from datetime import datetime, timezone
import hashlib
import json
import os
from pathlib import Path
import time
from typing import Any

from mira_light_runtime import MiraLightRuntime


def now_iso() -> str:
    return datetime.now(timezone.utc).astimezone().isoformat(timespec="seconds")


@dataclass
class BridgeState:
    last_event_signature: str | None = None
    last_target_present: bool = False
    target_missing_since_monotonic: float | None = None
    last_scene_started: str | None = None
    last_scene_started_at_monotonic: float | None = None
    last_tracking_applied_at_monotonic: float | None = None
    last_seen_horizontal_zone: str | None = None
    last_seen_distance_band: str | None = None
    last_departure_direction: str | None = None
    scene_counts: dict[str, int] = field(default_factory=dict)


SCENE_PRIORITY: dict[str, int] = {
    "wake_up": 1,
    "curious_observe": 2,
    "track_target": 3,
    "sleep": 4,
}


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Consume vision.latest.json and trigger Mira Light runtime scenes.")
    parser.add_argument(
        "--event-file",
        type=Path,
        default=Path("./runtime/vision.latest.json"),
        help="Latest vision event JSON path.",
    )
    parser.add_argument(
        "--bridge-state-out",
        type=Path,
        default=Path("./runtime/vision.bridge.state.json"),
        help="Where to write bridge state for observability.",
    )
    parser.add_argument(
        "--poll-interval",
        type=float,
        default=0.5,
        help="Seconds between event file polls.",
    )
    parser.add_argument(
        "--base-url",
        default=os.environ.get("MIRA_LIGHT_BASE_URL", "http://172.20.10.3"),
        help="Lamp base URL passed to MiraLightRuntime.",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Do not call real hardware APIs.",
    )
    parser.add_argument(
        "--once",
        action="store_true",
        help="Read one event file, handle it once, then exit.",
    )
    parser.add_argument(
        "--allow-experimental",
        action="store_true",
        help="Enable tuning/prototype scenes in the runtime.",
    )
    parser.add_argument(
        "--scene-cooldown-ms",
        type=int,
        default=3500,
        help="Global cooldown between repeated scene starts.",
    )
    parser.add_argument(
        "--wake-up-cooldown-ms",
        type=int,
        default=6000,
        help="Cooldown before wake_up can be re-triggered.",
    )
    parser.add_argument(
        "--sleep-grace-ms",
        type=int,
        default=4000,
        help="How long target absence must persist before sleep is triggered.",
    )
    parser.add_argument(
        "--tracking-update-ms",
        type=int,
        default=220,
        help="Minimum interval between live tracking control updates.",
    )
    parser.add_argument(
        "--log-json",
        action="store_true",
        help="Print bridge decisions as JSON instead of plain text lines.",
    )
    return parser.parse_args()


def compute_signature(payload: dict[str, Any]) -> str:
    raw = json.dumps(payload, ensure_ascii=False, sort_keys=True).encode("utf-8")
    return hashlib.sha1(raw).hexdigest()


def load_json_file(path: Path) -> dict[str, Any] | None:
    if not path.exists():
        return None
    return json.loads(path.read_text(encoding="utf-8"))


def log(args: argparse.Namespace, message: str, **fields: Any) -> None:
    if args.log_json:
        payload = {"ts": now_iso(), "message": message, **fields}
        print(json.dumps(payload, ensure_ascii=False))
        return

    if fields:
        formatted = " ".join(f"{key}={value}" for key, value in fields.items())
        print(f"[vision-bridge] {message} {formatted}".rstrip())
    else:
        print(f"[vision-bridge] {message}")


def write_state_file(path: Path, runtime: MiraLightRuntime, bridge: BridgeState, last_event: dict[str, Any] | None) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    payload = {
        "updatedAt": now_iso(),
        "runtime": runtime.get_runtime_state(),
        "bridge": {
            "lastEventSignature": bridge.last_event_signature,
            "lastTargetPresent": bridge.last_target_present,
            "targetMissingSinceMonotonic": bridge.target_missing_since_monotonic,
            "lastSceneStarted": bridge.last_scene_started,
            "lastTrackingAppliedAtMonotonic": bridge.last_tracking_applied_at_monotonic,
            "lastSeenHorizontalZone": bridge.last_seen_horizontal_zone,
            "lastSeenDistanceBand": bridge.last_seen_distance_band,
            "lastDepartureDirection": bridge.last_departure_direction,
            "sceneCounts": bridge.scene_counts,
        },
        "lastVisionEvent": last_event,
    }
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def should_start_scene(
    scene_name: str,
    *,
    runtime_state: dict[str, Any],
    bridge_state: BridgeState,
    now_mono: float,
    args: argparse.Namespace,
) -> tuple[bool, str]:
    if scene_name == "none":
        return False, "scene_hint is none"

    if runtime_state["running"]:
        running_scene = runtime_state["runningScene"]
        return False, f"runtime already running {running_scene}"

    last_started = bridge_state.last_scene_started_at_monotonic
    if last_started is not None:
        age_ms = (now_mono - last_started) * 1000.0
        if age_ms < args.scene_cooldown_ms:
            return False, f"global cooldown active ({age_ms:.0f}ms)"

    if scene_name == "wake_up" and bridge_state.last_scene_started == "wake_up":
        if last_started is not None:
            age_ms = (now_mono - last_started) * 1000.0
            if age_ms < args.wake_up_cooldown_ms:
                return False, f"wake_up cooldown active ({age_ms:.0f}ms)"

    if bridge_state.last_scene_started == scene_name and last_started is not None:
        age_ms = (now_mono - last_started) * 1000.0
        if age_ms < args.scene_cooldown_ms * 1.4:
            return False, f"same scene cooldown active ({age_ms:.0f}ms)"

    return True, "ok"


def resolve_candidate_scene(event: dict[str, Any], bridge_state: BridgeState, now_mono: float, args: argparse.Namespace) -> tuple[str, str]:
    tracking = event.get("tracking", {})
    control_hint = event.get("control_hint", {}) if isinstance(event.get("control_hint"), dict) else {}
    target_present = bool(tracking.get("target_present"))
    scene_hint = (event.get("scene_hint") or {}).get("name", "none")
    event_type = event.get("event_type", "no_target")
    horizontal_zone = tracking.get("horizontal_zone")
    approach_state = tracking.get("approach_state")
    yaw_error = abs(_hint_float(control_hint, "yaw_error_norm"))
    pitch_error = abs(_hint_float(control_hint, "pitch_error_norm"))

    if target_present:
        bridge_state.target_missing_since_monotonic = None
        bridge_state.last_departure_direction = None
        if event_type == "target_seen":
            return "wake_up", "target_seen transition"
        if bridge_state.last_scene_started == "track_target" and event_type in {"target_updated", "target_moved"}:
            return "track_target", "continue live tracking"
        if scene_hint in {"curious_observe", "track_target"}:
            return scene_hint, f"scene_hint={scene_hint}"
        if scene_hint == "wake_up":
            return "wake_up", "scene_hint=wake_up"
        if horizontal_zone in {"left", "right"} or approach_state in {"approaching", "receding"}:
            return "track_target", "tracking heuristics from target movement"
        if yaw_error >= 0.18 or pitch_error >= 0.22:
            return "track_target", "tracking heuristics from control_hint"
        return "curious_observe", "target present fallback"

    if bridge_state.last_target_present and bridge_state.target_missing_since_monotonic is None:
        bridge_state.target_missing_since_monotonic = now_mono
        if bridge_state.last_departure_direction:
            return "none", f"target just disappeared toward {bridge_state.last_departure_direction}, waiting grace period"
        return "none", "target just disappeared, waiting grace period"

    if bridge_state.target_missing_since_monotonic is not None:
        missing_ms = (now_mono - bridge_state.target_missing_since_monotonic) * 1000.0
        if missing_ms >= args.sleep_grace_ms:
            return "sleep", f"target missing for {missing_ms:.0f}ms"
        return "none", f"target missing grace active ({missing_ms:.0f}ms)"

    return "none", "no target and no prior target state"


def apply_scene(scene_name: str, runtime: MiraLightRuntime, bridge_state: BridgeState, now_mono: float, args: argparse.Namespace) -> None:
    runtime.start_scene(scene_name)
    bridge_state.last_scene_started = scene_name
    bridge_state.last_scene_started_at_monotonic = now_mono
    bridge_state.scene_counts[scene_name] = bridge_state.scene_counts.get(scene_name, 0) + 1
    log(args, "scene started", scene=scene_name, dry_run=runtime.dry_run)


def _hint_float(payload: dict[str, Any], key: str, default: float = 0.0) -> float:
    try:
        return float(payload.get(key, default) or default)
    except (TypeError, ValueError):
        return default


def observe_tracking(event: dict[str, Any], bridge_state: BridgeState) -> None:
    tracking = event.get("tracking", {}) if isinstance(event.get("tracking"), dict) else {}
    target_present = bool(tracking.get("target_present"))
    horizontal_zone = tracking.get("horizontal_zone")
    distance_band = tracking.get("distance_band")

    if target_present:
        if horizontal_zone in {"left", "center", "right"}:
            bridge_state.last_seen_horizontal_zone = horizontal_zone
        if isinstance(distance_band, str) and distance_band:
            bridge_state.last_seen_distance_band = distance_band
        bridge_state.last_departure_direction = None
        return

    approach_state = tracking.get("approach_state")
    if approach_state != "receding" and event.get("event_type") != "target_lost":
        return

    if horizontal_zone in {"left", "right", "center"}:
        bridge_state.last_departure_direction = horizontal_zone
        return

    if bridge_state.last_seen_horizontal_zone in {"left", "right", "center"}:
        bridge_state.last_departure_direction = bridge_state.last_seen_horizontal_zone


def should_apply_tracking(
    *,
    runtime_state: dict[str, Any],
    bridge_state: BridgeState,
    now_mono: float,
    args: argparse.Namespace,
) -> tuple[bool, str]:
    if runtime_state.get("running") and runtime_state.get("runningScene") not in {None, "track_target"}:
        return False, f"runtime already running {runtime_state.get('runningScene')}"

    last_applied = bridge_state.last_tracking_applied_at_monotonic
    if last_applied is not None:
        age_ms = (now_mono - last_applied) * 1000.0
        if age_ms < args.tracking_update_ms:
            return False, f"tracking update interval active ({age_ms:.0f}ms)"

    return True, "ok"


def apply_tracking(runtime: MiraLightRuntime, bridge_state: BridgeState, event: dict[str, Any], now_mono: float, args: argparse.Namespace) -> None:
    runtime.apply_tracking_event(event, source="vision")
    bridge_state.last_scene_started = "track_target"
    bridge_state.last_scene_started_at_monotonic = now_mono
    bridge_state.last_tracking_applied_at_monotonic = now_mono
    bridge_state.scene_counts["track_target"] = bridge_state.scene_counts.get("track_target", 0) + 1
    log(args, "tracking updated", dry_run=runtime.dry_run)


def handle_event(event: dict[str, Any], runtime: MiraLightRuntime, bridge_state: BridgeState, args: argparse.Namespace) -> None:
    now_mono = time.monotonic()
    tracking = event.get("tracking", {})
    target_present = bool(tracking.get("target_present"))
    observe_tracking(event, bridge_state)

    candidate_scene, candidate_reason = resolve_candidate_scene(event, bridge_state, now_mono, args)
    runtime_state = runtime.get_runtime_state()
    allowed, allowed_reason = should_start_scene(
        candidate_scene,
        runtime_state=runtime_state,
        bridge_state=bridge_state,
        now_mono=now_mono,
        args=args,
    )

    log(
        args,
        "vision event handled",
        event_type=event.get("event_type"),
        scene_hint=(event.get("scene_hint") or {}).get("name"),
        candidate_scene=candidate_scene,
        candidate_reason=candidate_reason,
        allowed=allowed,
        allowed_reason=allowed_reason,
        target_present=target_present,
        distance_band=tracking.get("distance_band"),
        horizontal_zone=tracking.get("horizontal_zone"),
        departure_direction=bridge_state.last_departure_direction or "unknown",
    )

    if not target_present and runtime_state.get("trackingActive") and hasattr(runtime, "apply_tracking_event"):
        runtime.apply_tracking_event(event, source="vision-clear")

    if candidate_scene == "track_target" and target_present and hasattr(runtime, "apply_tracking_event"):
        allowed, allowed_reason = should_apply_tracking(
            runtime_state=runtime_state,
            bridge_state=bridge_state,
            now_mono=now_mono,
            args=args,
        )
        log(
            args,
            "tracking candidate evaluated",
            allowed=allowed,
            allowed_reason=allowed_reason,
            horizontal_zone=tracking.get("horizontal_zone"),
            distance_band=tracking.get("distance_band"),
        )
        if allowed:
            apply_tracking(runtime, bridge_state, event, now_mono, args)
    elif allowed:
        apply_scene(candidate_scene, runtime, bridge_state, now_mono, args)

    bridge_state.last_target_present = target_present


def main() -> int:
    args = parse_args()
    event_file = args.event_file.expanduser().resolve()
    bridge_state_out = args.bridge_state_out.expanduser().resolve()

    runtime = MiraLightRuntime(base_url=args.base_url, dry_run=args.dry_run)
    runtime.show_experimental = args.allow_experimental or runtime.show_experimental
    bridge_state = BridgeState()

    log(
        args,
        "starting",
        event_file=event_file,
        base_url=runtime.base_url,
        dry_run=runtime.dry_run,
        show_experimental=runtime.show_experimental,
        tracking_update_ms=args.tracking_update_ms,
    )

    while True:
        event = load_json_file(event_file)
        if event is not None:
            signature = compute_signature(event)
            if signature != bridge_state.last_event_signature:
                bridge_state.last_event_signature = signature
                handle_event(event, runtime, bridge_state, args)
                write_state_file(bridge_state_out, runtime, bridge_state, event)
                if args.once:
                    return 0
        else:
            write_state_file(bridge_state_out, runtime, bridge_state, None)
            if args.once:
                log(args, "event file not found", event_file=event_file)
                return 1

        time.sleep(args.poll_interval)


if __name__ == "__main__":
    raise SystemExit(main())
