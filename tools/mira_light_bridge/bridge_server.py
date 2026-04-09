#!/usr/bin/env python3
"""Local HTTP bridge for Mira Light.

This follows the same architectural pattern already used elsewhere in the Mira /
Javis ecosystem:

- a local bridge stays close to the physical device
- a stable HTTP surface is exposed on loopback
- remote OpenClaw can reach that surface later through an SSH reverse tunnel

Why not let remote OpenClaw hit the ESP32 directly?

- the lamp is usually inside a private LAN
- the lamp API itself is intentionally simple and not release-hardened
- booth control needs a stable scene-first bridge surface, not raw device access
"""

from __future__ import annotations

import argparse
from datetime import datetime, timezone
import json
import os
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
import sys
from typing import Any
from urllib.parse import urlparse


ROOT = Path(__file__).resolve().parents[2]
SCRIPTS_DIR = ROOT / "scripts"
if str(SCRIPTS_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPTS_DIR))

from mira_light_runtime import DEFAULT_TIMEOUT_SECONDS, MiraLightRuntime  # noqa: E402
from scenes import POSES, PROFILE_INFO, SCENES, SERVO_CALIBRATION  # noqa: E402
from embodied_memory_client import EmbodiedMemoryClient  # noqa: E402


DEFAULT_CONFIG_PATH = Path(__file__).resolve().with_name("bridge_config.json")


def load_bridge_config(path: Path) -> dict[str, Any]:
    raw = path.read_text(encoding="utf-8")
    parsed = json.loads(raw)
    if not isinstance(parsed, dict):
        raise ValueError(f"Invalid bridge config: {path}")
    return parsed


def parse_truthy(value: Any) -> bool:
    if isinstance(value, bool):
        return value
    if isinstance(value, (int, float)):
        return bool(value)
    if isinstance(value, str):
        return value.strip().lower() in {"1", "true", "yes", "on"}
    return False


class BridgeHTTPServer(ThreadingHTTPServer):
    def __init__(
        self,
        server_address,
        handler_class,
        runtime: MiraLightRuntime,
        token: str,
        ingest_root: Path,
        memory_client: EmbodiedMemoryClient | None = None,
    ):
        super().__init__(server_address, handler_class)
        self.runtime = runtime
        self.token = token
        self.ingest_root = ingest_root
        self.memory_client = memory_client


class DeviceIngestStore:
    """Persist incoming device reports under a stable local runtime folder."""

    def __init__(self, root: Path):
        self.root = root
        self.inbox_dir = self.root / "inbox"
        self.snapshots_dir = self.root / "snapshots"
        self.events_dir = self.root / "events"
        self.errors_dir = self.root / "errors"

        for directory in [self.root, self.inbox_dir, self.snapshots_dir, self.events_dir, self.errors_dir]:
            directory.mkdir(parents=True, exist_ok=True)

    def now(self) -> datetime:
        return datetime.now(timezone.utc).astimezone()

    def storage_info(self) -> dict[str, Any]:
        return {
            "root": str(self.root),
            "inboxDir": str(self.inbox_dir),
            "snapshotsDir": str(self.snapshots_dir),
            "eventsDir": str(self.events_dir),
            "errorsDir": str(self.errors_dir),
        }

    def _safe_device_id(self, device_id: str | None) -> str:
        raw = (device_id or "unknown-device").strip()
        if not raw:
            raw = "unknown-device"
        return "".join(ch if ch.isalnum() or ch in ("-", "_", ".") else "-" for ch in raw)

    def _write_json(self, path: Path, payload: dict[str, Any]) -> None:
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

    def _append_jsonl(self, path: Path, payload: dict[str, Any]) -> None:
        path.parent.mkdir(parents=True, exist_ok=True)
        with path.open("a", encoding="utf-8") as handle:
            handle.write(json.dumps(payload, ensure_ascii=False) + "\n")

    def persist_report(self, report_type: str, body: dict[str, Any]) -> dict[str, Any]:
        now = self.now()
        date_part = now.strftime("%Y-%m-%d")
        ts_part = now.strftime("%Y-%m-%dT%H-%M-%S")
        device_id = self._safe_device_id(body.get("deviceId"))

        enriched = {
            "receivedAt": now.isoformat(timespec="seconds"),
            "reportType": report_type,
            "deviceId": device_id,
            "payload": body,
        }

        inbox_path = self.inbox_dir / date_part / f"{ts_part}_{device_id}_{report_type}.json"
        self._write_json(inbox_path, enriched)

        if report_type in {"hello", "heartbeat", "status"}:
            snapshot_path = self.snapshots_dir / f"{device_id}.{report_type}.latest.json"
            self._write_json(snapshot_path, enriched)

        event_record = {
            "ts": now.isoformat(timespec="seconds"),
            "type": report_type,
            "deviceId": device_id,
            "payload": body,
        }
        self._append_jsonl(self.events_dir / f"{date_part}.jsonl", event_record)

        event_type = str(body.get("eventType", "")).lower()
        if report_type == "event" and event_type in {"error", "warning"}:
            self._append_jsonl(self.errors_dir / f"{date_part}.jsonl", event_record)

        return {
            "stored": True,
            "deviceId": device_id,
            "reportType": report_type,
            "inboxPath": str(inbox_path),
        }


class BridgeHandler(BaseHTTPRequestHandler):
    server: BridgeHTTPServer

    def log_message(self, format: str, *args) -> None:  # noqa: A003
        self.server.runtime.log(f"[bridge-http] {self.address_string()} - {format % args}")

    def _send_json(self, status_code: int, payload: dict) -> None:
        body = json.dumps(payload, ensure_ascii=False, indent=2).encode("utf-8")
        self.send_response(status_code)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def _read_json_body(self) -> dict:
        length = int(self.headers.get("Content-Length", "0") or 0)
        if length <= 0:
            return {}
        raw = self.rfile.read(length).decode("utf-8")
        if not raw.strip():
            return {}
        return json.loads(raw)

    @property
    def ingest_store(self) -> DeviceIngestStore:
        return DeviceIngestStore(self.server.ingest_root)

    def _authorize(self) -> bool:
        if not self.server.token:
            return True
        header = self.headers.get("Authorization", "")
        return header == f"Bearer {self.server.token}"

    def _guard(self) -> bool:
        if self.path == "/health":
            return True
        if self._authorize():
            return True
        self._send_json(401, {"ok": False, "error": "Unauthorized"})
        return False

    def _record_device_outcome(self, report_type: str, body: dict[str, Any], stored: dict[str, Any]) -> None:
        client = self.server.memory_client
        if client is None:
            return
        try:
            client.record_device_report(report_type=report_type, payload=body, stored=stored)
        except Exception as exc:  # noqa: BLE001
            self.server.runtime.log(f"[memory-warning] device outcome write failed: {exc}")

    def do_HEAD(self) -> None:  # noqa: N802
        parsed = urlparse(self.path)
        if parsed.path == "/health":
            self.send_response(200)
            self.end_headers()
            return
        if not self._authorize():
            self.send_response(401)
            self.end_headers()
            return
        self.send_response(200)
        self.end_headers()

    def do_GET(self) -> None:  # noqa: N802
        if not self._guard():
            return

        parsed = urlparse(self.path)
        path = parsed.path

        try:
            if path == "/health":
                self._send_json(
                    200,
                    {
                        "ok": True,
                        "service": "mira-light-bridge",
                        "runtime": self.server.runtime.get_runtime_state(),
                        "profile": PROFILE_INFO,
                    },
                )
                return

            if path == "/v1/mira-light/status":
                self._send_json(200, {"ok": True, "data": self.server.runtime.get_status()})
                return

            if path == "/v1/mira-light/led":
                self._send_json(200, {"ok": True, "data": self.server.runtime.get_led()})
                return

            if path == "/v1/mira-light/sensors":
                self._send_json(200, {"ok": True, "data": self.server.runtime.get_sensors()})
                return

            if path == "/v1/mira-light/actions":
                self._send_json(200, {"ok": True, "data": self.server.runtime.get_actions()})
                return

            if path == "/v1/mira-light/runtime":
                self._send_json(200, {"ok": True, "runtime": self.server.runtime.get_runtime_state()})
                return

            if path == "/v1/mira-light/logs":
                self._send_json(200, {"ok": True, "items": self.server.runtime.get_logs()})
                return

            if path == "/v1/mira-light/scenes":
                self._send_json(200, {"ok": True, "items": self.server.runtime.list_scenes()})
                return

            if path == "/v1/mira-light/profile":
                self._send_json(
                    200,
                    {
                        "ok": True,
                        "profile": {
                            "info": PROFILE_INFO,
                            "servoCalibration": SERVO_CALIBRATION,
                            "poses": POSES,
                        },
                    },
                )
                return

            if path == "/v1/mira-light/device/storage-info":
                self._send_json(200, {"ok": True, "storage": self.ingest_store.storage_info()})
                return

            self._send_json(404, {"ok": False, "error": "Unknown endpoint"})
        except Exception as exc:  # noqa: BLE001
            self._send_json(500, {"ok": False, "error": str(exc)})

    def do_POST(self) -> None:  # noqa: N802
        if not self._guard():
            return

        parsed = urlparse(self.path)
        path = parsed.path

        try:
            if path == "/v1/mira-light/run-scene":
                body = self._read_json_body()
                scene_name = body.get("scene") or body.get("name")
                if not isinstance(scene_name, str) or not scene_name:
                    self._send_json(400, {"ok": False, "error": "scene is required"})
                    return

                async_run = bool(body.get("async", True))
                scene_context = body.get("context") if isinstance(body.get("context"), dict) else None
                cue_mode = str(body.get("cueMode") or "scene")
                allow_unavailable = bool(body.get("allowUnavailable", False))
                if async_run:
                    runtime_state = self.server.runtime.start_scene(
                        scene_name,
                        scene_context=scene_context,
                        cue_mode=cue_mode,
                        allow_unavailable=allow_unavailable,
                    )
                else:
                    runtime_state = self.server.runtime.run_scene_blocking(
                        scene_name,
                        scene_context=scene_context,
                        cue_mode=cue_mode,
                        allow_unavailable=allow_unavailable,
                    )
                self._send_json(200, {"ok": True, "runtime": runtime_state})
                return

            if path == "/v1/mira-light/trigger":
                body = self._read_json_body()
                event_name = body.get("event") or body.get("name")
                if not isinstance(event_name, str) or not event_name:
                    self._send_json(400, {"ok": False, "error": "event is required"})
                    return
                payload = body.get("payload") if isinstance(body.get("payload"), dict) else {}
                runtime_state = self.server.runtime.trigger_event(event_name, payload)
                self._send_json(200, {"ok": True, "runtime": runtime_state})
                return

            if path == "/v1/mira-light/speak":
                body = self._read_json_body()
                self._send_json(200, {"ok": True, "data": self.server.runtime.speak_text(body)})
                return

            if path == "/v1/mira-light/stop":
                self._send_json(200, {"ok": True, "runtime": self.server.runtime.stop_scene()})
                return

            if path == "/v1/mira-light/reset":
                self._send_json(200, {"ok": True, "data": self.server.runtime.reset_lamp()})
                return

            if path == "/v1/mira-light/apply-pose":
                body = self._read_json_body()
                pose_name = body.get("pose")
                if not isinstance(pose_name, str) or not pose_name:
                    self._send_json(400, {"ok": False, "error": "pose is required"})
                    return
                self._send_json(200, {"ok": True, "data": self.server.runtime.apply_pose(pose_name)})
                return

            if path == "/v1/mira-light/operator/stop-to-neutral":
                self._send_json(200, {"ok": True, "runtime": self.server.runtime.stop_to_pose("neutral")})
                return

            if path == "/v1/mira-light/operator/stop-to-sleep":
                self._send_json(200, {"ok": True, "runtime": self.server.runtime.stop_to_pose("sleep")})
                return

            if path == "/v1/mira-light/control":
                body = self._read_json_body()
                self._send_json(200, {"ok": True, "data": self.server.runtime.control_joints(body)})
                return

            if path == "/v1/mira-light/led":
                body = self._read_json_body()
                self._send_json(200, {"ok": True, "data": self.server.runtime.set_led_state(body)})
                return

            if path == "/v1/mira-light/sensors":
                body = self._read_json_body()
                self._send_json(200, {"ok": True, "data": self.server.runtime.set_sensors_state(body)})
                return

            if path == "/v1/mira-light/action":
                body = self._read_json_body()
                self._send_json(200, {"ok": True, "data": self.server.runtime.get_client().run_action(body)})
                return

            if path == "/v1/mira-light/config":
                body = self._read_json_body()
                runtime_state = self.server.runtime.update_config(
                    base_url=body.get("baseUrl"),
                    dry_run=body.get("dryRun"),
                    auto_recover_pose=body.get("autoRecoverPose"),
                )
                self._send_json(200, {"ok": True, "runtime": runtime_state})
                return

            if path == "/v1/mira-light/profile/capture-pose":
                body = self._read_json_body()
                pose_name = body.get("name") or body.get("pose")
                if not isinstance(pose_name, str) or not pose_name:
                    self._send_json(400, {"ok": False, "error": "pose name is required"})
                    return
                data = self.server.runtime.capture_pose_to_profile(
                    pose_name,
                    notes=str(body.get("notes") or ""),
                    verified=bool(body.get("verified", False)),
                )
                self._send_json(200, {"ok": True, "data": data})
                return

            if path == "/v1/mira-light/profile/set-servo-meta":
                body = self._read_json_body()
                servo_name = body.get("servo")
                if not isinstance(servo_name, str) or not servo_name:
                    self._send_json(400, {"ok": False, "error": "servo is required"})
                    return
                updates = {
                    "label": body.get("label"),
                    "neutral": body.get("neutral"),
                    "hard_range": body.get("hardRange"),
                    "rehearsal_range": body.get("rehearsalRange"),
                    "notes": body.get("notes"),
                    "verified": body.get("verified"),
                }
                data = self.server.runtime.update_servo_meta_in_profile(servo_name, updates)
                self._send_json(200, {"ok": True, "data": data})
                return

            if path == "/v1/mira-light/device/hello":
                body = self._read_json_body()
                stored = self.ingest_store.persist_report("hello", body)
                self._record_device_outcome("hello", body, stored)
                self._send_json(
                    200,
                    {
                        "ok": True,
                        "stored": stored,
                        "serverTime": datetime.now(timezone.utc).astimezone().isoformat(timespec="seconds"),
                    },
                )
                return

            if path == "/v1/mira-light/device/heartbeat":
                body = self._read_json_body()
                stored = self.ingest_store.persist_report("heartbeat", body)
                self._record_device_outcome("heartbeat", body, stored)
                self._send_json(200, {"ok": True, "stored": stored})
                return

            if path == "/v1/mira-light/device/status":
                body = self._read_json_body()
                stored = self.ingest_store.persist_report("status", body)
                self._record_device_outcome("status", body, stored)
                self._send_json(200, {"ok": True, "stored": stored})
                return

            if path == "/v1/mira-light/device/event":
                body = self._read_json_body()
                stored = self.ingest_store.persist_report("event", body)
                self._record_device_outcome("event", body, stored)
                self._send_json(200, {"ok": True, "stored": stored})
                return

            self._send_json(404, {"ok": False, "error": "Unknown endpoint"})
        except KeyError as exc:
            self._send_json(404, {"ok": False, "error": str(exc)})
        except RuntimeError as exc:
            message = str(exc)
            status_code = 409 if "already running" in message or "while a scene is running" in message else 400
            self._send_json(status_code, {"ok": False, "error": message})
        except Exception as exc:  # noqa: BLE001
            self._send_json(500, {"ok": False, "error": str(exc)})


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Run the local Mira Light bridge service.")
    parser.add_argument("--config", default=str(DEFAULT_CONFIG_PATH), help="Path to bridge_config.json")
    parser.add_argument("--host", help="Override listen host")
    parser.add_argument("--port", type=int, help="Override listen port")
    parser.add_argument("--base-url", help="Override lamp base URL")
    parser.add_argument("--dry-run", action="store_true", help="Do not send real lamp requests")
    return parser


def main() -> int:
    parser = build_parser()
    args = parser.parse_args()

    config = load_bridge_config(Path(args.config))
    host = args.host or config.get("listenHost", "127.0.0.1")
    port = int(args.port or config.get("listenPort", 9783))
    base_url = args.base_url or config.get("lampBaseUrl", "http://172.20.10.3")
    timeout_seconds = float(config.get("requestTimeoutSeconds", DEFAULT_TIMEOUT_SECONDS))
    dry_run = bool(args.dry_run or config.get("dryRun", False))
    ingest_root = Path(os.path.expanduser(config.get("deviceIngestRoot", "~/Documents/Mira-Light-Runtime"))).resolve()

    token_env_name = config.get("bridgeTokenEnv", "MIRA_LIGHT_BRIDGE_TOKEN")
    token = os.environ.get(token_env_name, "")

    memory_cfg = config.get("memoryContext", {}) if isinstance(config.get("memoryContext"), dict) else {}
    memory_enabled = parse_truthy(
        os.environ.get("MIRA_LIGHT_MEMORY_CONTEXT_ENABLED", memory_cfg.get("enabled", False))
    )
    memory_base_url = str(
        os.environ.get("MIRA_LIGHT_MEMORY_CONTEXT_URL", "")
        or memory_cfg.get("baseUrl", "")
    ).rstrip("/")
    memory_auth_token_env = str(memory_cfg.get("authTokenEnv", "MIRA_MEMORY_CONTEXT_AUTH_TOKEN"))
    memory_auth_token = os.environ.get(memory_auth_token_env, "")
    memory_user_id = str(memory_cfg.get("userId", "mira-light-bridge"))
    memory_timeout_seconds = float(memory_cfg.get("requestTimeoutSeconds", 2.0))
    memory_device_status_ttl_seconds = int(memory_cfg.get("deviceStatusTtlSeconds", 900))
    memory_failure_ttl_seconds = int(memory_cfg.get("failureTtlSeconds", 3600))

    memory_client = EmbodiedMemoryClient(
        base_url=memory_base_url,
        auth_token=memory_auth_token,
        user_id=memory_user_id,
        request_timeout_seconds=memory_timeout_seconds,
        device_status_ttl_seconds=memory_device_status_ttl_seconds,
        failure_ttl_seconds=memory_failure_ttl_seconds,
        enabled=memory_enabled,
        emit=None,
    ) if memory_base_url else None

    runtime = MiraLightRuntime(
        base_url=base_url,
        timeout_seconds=timeout_seconds,
        dry_run=dry_run,
        embodied_memory_client=memory_client,
    )
    if memory_client is not None:
        memory_client.emit = lambda message: runtime.log(f"[memory] {message}")
    runtime.log(f"[bridge] starting at http://{host}:{port}")
    runtime.log(f"[bridge] lamp base url {base_url}")
    runtime.log(f"[bridge] auth env {token_env_name} present={bool(token)}")
    runtime.log(f"[bridge] device ingest root {ingest_root}")
    runtime.log(f"[bridge] memory context enabled={bool(memory_client and memory_client.enabled)} base={memory_base_url or '-'}")

    server = BridgeHTTPServer(
        (host, port),
        BridgeHandler,
        runtime=runtime,
        token=token,
        ingest_root=ingest_root,
        memory_client=memory_client,
    )
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        runtime.log("[bridge] shutdown requested")
    finally:
        server.server_close()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
