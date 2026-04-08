#!/usr/bin/env python3
"""Optional memory-context writer for embodied Mira Light events."""

from __future__ import annotations

from datetime import datetime, timedelta, timezone
import json
from typing import Any
import urllib.error
import urllib.request


def _now_iso() -> str:
    return datetime.now(timezone.utc).astimezone().isoformat(timespec="seconds")


def _expires_after(seconds: int) -> str:
    return (datetime.now(timezone.utc) + timedelta(seconds=max(1, seconds))).astimezone().isoformat(timespec="seconds")


def _trim_text(value: Any, max_chars: int = 280) -> str:
    if not isinstance(value, str):
        return ""
    return " ".join(value.strip().split())[:max_chars]


class EmbodiedMemoryClient:
    """Write selected scene/device outcomes into Mira's typed memory-context."""

    def __init__(
        self,
        *,
        base_url: str = "",
        auth_token: str = "",
        user_id: str = "mira-light-bridge",
        request_timeout_seconds: float = 2.0,
        device_status_ttl_seconds: int = 900,
        failure_ttl_seconds: int = 3600,
        enabled: bool = False,
        emit: callable | None = None,
    ) -> None:
        self.base_url = base_url.rstrip("/")
        self.auth_token = auth_token
        self.user_id = user_id
        self.request_timeout_seconds = max(0.2, float(request_timeout_seconds))
        self.device_status_ttl_seconds = max(30, int(device_status_ttl_seconds))
        self.failure_ttl_seconds = max(60, int(failure_ttl_seconds))
        self.enabled = bool(enabled and self.base_url)
        self.emit = emit

    def _log(self, message: str) -> None:
        if self.emit:
            self.emit(message)

    def _post_write(self, source: str, items: list[dict[str, Any]]) -> dict[str, Any]:
        if not self.enabled or not items:
            return {"ok": True, "skipped": True}

        body = json.dumps({"source": source, "items": items}, ensure_ascii=False).encode("utf-8")
        req = urllib.request.Request(
            f"{self.base_url}/v1/memory/write",
            data=body,
            method="POST",
            headers={
                "Content-Type": "application/json; charset=utf-8",
                **({"Authorization": f"Bearer {self.auth_token}"} if self.auth_token else {}),
            },
        )
        try:
            with urllib.request.urlopen(req, timeout=self.request_timeout_seconds) as response:
                raw = response.read().decode("utf-8").strip()
                return json.loads(raw) if raw else {"ok": True}
        except urllib.error.HTTPError as exc:
            detail = exc.read().decode("utf-8", errors="replace").strip()
            raise RuntimeError(f"memory-context HTTP {exc.code}: {detail}") from exc
        except urllib.error.URLError as exc:
            raise RuntimeError(f"memory-context unavailable: {exc}") from exc

    def record_scene_outcome(
        self,
        *,
        scene_name: str,
        status: str,
        runtime_state: dict[str, Any],
        error: str | None = None,
    ) -> dict[str, Any]:
        scene_label = _trim_text(scene_name, 80) or "unknown-scene"
        status_label = _trim_text(status, 40) or "unknown"
        message = f"Mira Light scene '{scene_label}' finished with status '{status_label}'."
        if error:
            message = f"{message} Error: {_trim_text(error, 180)}"

        items: list[dict[str, Any]] = [
            {
                "user_id": self.user_id,
                "namespace": "home",
                "layer": "episodic",
                "kind": "execution_outcome",
                "content": message,
                "structured_value": {
                    "system": "mira-light",
                    "sceneName": scene_name,
                    "status": status,
                    "error": error,
                    "runtimeState": runtime_state,
                    "observedAt": _now_iso(),
                },
                "confidence": 0.96,
                "salience": 0.88 if status == "completed" else 0.95,
                "sensitivity": "normal",
                "tags": ["mira-light", f"scene:{scene_name}", f"status:{status}"],
                "evidence_refs": [f"mira-light:scene:{scene_name}:{status}"],
            }
        ]

        if status != "completed":
            items.append(
                {
                    "user_id": self.user_id,
                    "namespace": "home",
                    "layer": "working",
                    "kind": "scene_state",
                    "content": (
                        f"Mira Light scene '{scene_label}' most recently ended with status '{status_label}'. "
                        "Check bridge/device state before retrying."
                    ),
                    "structured_value": {
                        "system": "mira-light",
                        "sceneName": scene_name,
                        "status": status,
                        "error": error,
                    },
                    "confidence": 1,
                    "salience": 0.95,
                    "sensitivity": "normal",
                    "tags": ["mira-light", "working", f"scene:{scene_name}", f"status:{status}"],
                    "evidence_refs": [f"mira-light:scene:{scene_name}:{status}"],
                    "expires_at": _expires_after(self.failure_ttl_seconds),
                }
            )

        return self._post_write("scene_execution", items)

    def record_device_report(
        self,
        *,
        report_type: str,
        payload: dict[str, Any],
        stored: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        if report_type in {"hello", "heartbeat"}:
            return {"ok": True, "skipped": True, "reason": "low_signal_report"}

        device_id = _trim_text(str(payload.get("deviceId", "unknown-device")), 120) or "unknown-device"
        scene = _trim_text(str(payload.get("scene", payload.get("scene_hint", ""))), 120)
        event_type = _trim_text(str(payload.get("eventType", "")), 80).lower()
        led_mode = _trim_text(str(payload.get("ledMode", "")), 80)
        playing = payload.get("playing")

        if report_type == "status":
            content_bits = [f"Mira Light device '{device_id}' reported status"]
            if scene:
                content_bits.append(f"scene={scene}")
            if isinstance(playing, bool):
                content_bits.append(f"playing={playing}")
            if led_mode:
                content_bits.append(f"ledMode={led_mode}")

            item = {
                "user_id": self.user_id,
                "namespace": "home",
                "layer": "working",
                "kind": "scene_state",
                "content": ", ".join(content_bits) + ".",
                "structured_value": {
                    "system": "mira-light",
                    "reportType": report_type,
                    "deviceId": device_id,
                    "payload": payload,
                    "stored": stored,
                },
                "confidence": 0.86,
                "salience": 0.72,
                "sensitivity": "normal",
                "tags": ["mira-light", "device-status", f"device:{device_id}"],
                "evidence_refs": [f"mira-light:device:{device_id}:status"],
                "expires_at": _expires_after(self.device_status_ttl_seconds),
            }
            return self._post_write("device_observation", [item])

        if report_type == "event":
            severity = "normal"
            if event_type in {"error", "warning", "fault", "blocked", "offline"}:
                severity = event_type
            elif not event_type:
                return {"ok": True, "skipped": True, "reason": "event_missing_type"}

            content = f"Mira Light device '{device_id}' emitted event '{event_type}'."
            if scene:
                content = f"{content} scene={scene}."

            items: list[dict[str, Any]] = [
                {
                    "user_id": self.user_id,
                    "namespace": "home",
                    "layer": "episodic",
                    "kind": "execution_outcome",
                    "content": content,
                    "structured_value": {
                        "system": "mira-light",
                        "reportType": report_type,
                        "eventType": event_type,
                        "deviceId": device_id,
                        "payload": payload,
                        "stored": stored,
                    },
                    "confidence": 0.9,
                    "salience": 0.9 if severity != "normal" else 0.7,
                    "sensitivity": "normal",
                    "tags": ["mira-light", "device-event", f"device:{device_id}", f"event:{event_type}"],
                    "evidence_refs": [f"mira-light:device:{device_id}:event:{event_type}"],
                }
            ]

            if severity != "normal":
                items.append(
                    {
                        "user_id": self.user_id,
                        "namespace": "home",
                        "layer": "working",
                        "kind": "scene_state",
                        "content": (
                            f"Mira Light device '{device_id}' recently reported event '{event_type}'. "
                            "Treat device or bridge state as potentially degraded until re-checked."
                        ),
                        "structured_value": {
                            "system": "mira-light",
                            "eventType": event_type,
                            "deviceId": device_id,
                        },
                        "confidence": 0.96,
                        "salience": 0.92,
                        "sensitivity": "normal",
                        "tags": ["mira-light", "working", f"device:{device_id}", f"event:{event_type}"],
                        "evidence_refs": [f"mira-light:device:{device_id}:event:{event_type}"],
                        "expires_at": _expires_after(self.failure_ttl_seconds),
                    }
                )
            return self._post_write("device_observation", items)

        return {"ok": True, "skipped": True, "reason": "unsupported_report_type"}
