#!/usr/bin/env python3
"""Reusable Python client for the local Mira Light bridge."""

from __future__ import annotations

from dataclasses import dataclass
import json
import os
from typing import Any
import urllib.error
import urllib.request


DEFAULT_BRIDGE_BASE_URL = os.environ.get("MIRA_LIGHT_BRIDGE_URL", "http://127.0.0.1:9783").rstrip("/")
DEFAULT_TIMEOUT_SECONDS = float(os.environ.get("MIRA_LIGHT_BRIDGE_TIMEOUT_SECONDS", "5.0"))


class MiraLightBridgeError(RuntimeError):
    """Raised when the bridge returns an error response."""

    def __init__(
        self,
        message: str,
        *,
        status_code: int | None = None,
        detail: Any | None = None,
        method: str | None = None,
        path: str | None = None,
    ):
        super().__init__(message)
        self.status_code = status_code
        self.detail = detail
        self.method = method
        self.path = path


@dataclass(frozen=True)
class MiraLightBridgeConfig:
    base_url: str = DEFAULT_BRIDGE_BASE_URL
    token: str = ""
    timeout_seconds: float = DEFAULT_TIMEOUT_SECONDS

    @classmethod
    def from_env(cls) -> "MiraLightBridgeConfig":
        return cls(
            base_url=os.environ.get("MIRA_LIGHT_BRIDGE_URL", DEFAULT_BRIDGE_BASE_URL).rstrip("/"),
            token=os.environ.get("MIRA_LIGHT_BRIDGE_TOKEN", ""),
            timeout_seconds=float(os.environ.get("MIRA_LIGHT_BRIDGE_TIMEOUT_SECONDS", str(DEFAULT_TIMEOUT_SECONDS))),
        )


def _drop_none(payload: dict[str, Any]) -> dict[str, Any]:
    return {key: value for key, value in payload.items() if value is not None}


class MiraLightBridgeClient:
    """Thin bridge client usable from scripts, automation, and future adapters."""

    def __init__(
        self,
        base_url: str = DEFAULT_BRIDGE_BASE_URL,
        *,
        token: str = "",
        timeout_seconds: float = DEFAULT_TIMEOUT_SECONDS,
    ):
        self.base_url = base_url.rstrip("/")
        self.token = token
        self.timeout_seconds = timeout_seconds

    @classmethod
    def from_env(cls) -> "MiraLightBridgeClient":
        cfg = MiraLightBridgeConfig.from_env()
        return cls(base_url=cfg.base_url, token=cfg.token, timeout_seconds=cfg.timeout_seconds)

    def _headers(self) -> dict[str, str]:
        headers = {"Content-Type": "application/json"}
        if self.token:
            headers["Authorization"] = f"Bearer {self.token}"
        return headers

    def _request(self, method: str, path: str, payload: dict[str, Any] | None = None) -> Any:
        url = f"{self.base_url}{path}"
        body = None
        if payload is not None:
            body = json.dumps(payload, ensure_ascii=False).encode("utf-8")

        req = urllib.request.Request(url, data=body, headers=self._headers(), method=method)
        try:
            with urllib.request.urlopen(req, timeout=self.timeout_seconds) as response:
                raw = response.read().decode("utf-8").strip()
        except urllib.error.HTTPError as exc:
            raw = exc.read().decode("utf-8", errors="replace").strip()
            detail = raw
            try:
                detail = json.loads(raw) if raw else {}
            except json.JSONDecodeError:
                pass
            raise MiraLightBridgeError(
                f"Bridge returned HTTP {exc.code} for {method} {path}",
                status_code=exc.code,
                detail=detail,
                method=method,
                path=path,
            ) from exc
        except urllib.error.URLError as exc:
            raise MiraLightBridgeError(
                f"Failed to reach Mira Light bridge at {url}: {exc}",
                method=method,
                path=path,
            ) from exc

        if not raw:
            return {}
        try:
            return json.loads(raw)
        except json.JSONDecodeError:
            return raw

    def health(self) -> Any:
        return self._request("GET", "/health")

    def get_status(self) -> Any:
        return self._request("GET", "/v1/mira-light/status")

    def get_led(self) -> Any:
        return self._request("GET", "/v1/mira-light/led")

    def get_actions(self) -> Any:
        return self._request("GET", "/v1/mira-light/actions")

    def get_runtime(self) -> Any:
        return self._request("GET", "/v1/mira-light/runtime")

    def get_logs(self) -> Any:
        return self._request("GET", "/v1/mira-light/logs")

    def list_scenes(self) -> Any:
        return self._request("GET", "/v1/mira-light/scenes")

    def get_profile(self) -> Any:
        return self._request("GET", "/v1/mira-light/profile")

    def get_device_storage_info(self) -> Any:
        return self._request("GET", "/v1/mira-light/device/storage-info")

    def run_scene(
        self,
        scene: str,
        *,
        async_run: bool = True,
        context: dict[str, Any] | None = None,
        cue_mode: str | None = None,
        allow_unavailable: bool | None = None,
    ) -> Any:
        payload = _drop_none(
            {
                "scene": scene,
                "async": async_run,
                "context": context,
                "cueMode": cue_mode,
                "allowUnavailable": allow_unavailable,
            }
        )
        return self._request("POST", "/v1/mira-light/run-scene", payload)

    def trigger(self, event: str, payload: dict[str, Any] | None = None) -> Any:
        return self._request("POST", "/v1/mira-light/trigger", {"event": event, "payload": payload or {}})

    def speak(self, text: str, *, voice: str | None = None, wait: bool | None = None) -> Any:
        payload = _drop_none({"text": text, "voice": voice, "wait": wait})
        return self._request("POST", "/v1/mira-light/speak", payload)

    def stop(self) -> Any:
        return self._request("POST", "/v1/mira-light/stop", {})

    def reset(self) -> Any:
        return self._request("POST", "/v1/mira-light/reset", {})

    def apply_pose(self, pose: str) -> Any:
        return self._request("POST", "/v1/mira-light/apply-pose", {"pose": pose})

    def stop_to_neutral(self) -> Any:
        return self._request("POST", "/v1/mira-light/operator/stop-to-neutral", {})

    def stop_to_sleep(self) -> Any:
        return self._request("POST", "/v1/mira-light/operator/stop-to-sleep", {})

    def control_joints(
        self,
        *,
        mode: str,
        servo1: int | None = None,
        servo2: int | None = None,
        servo3: int | None = None,
        servo4: int | None = None,
    ) -> Any:
        payload = _drop_none(
            {
                "mode": mode,
                "servo1": servo1,
                "servo2": servo2,
                "servo3": servo3,
                "servo4": servo4,
            }
        )
        return self._request("POST", "/v1/mira-light/control", payload)

    def set_led(
        self,
        *,
        mode: str,
        brightness: int | None = None,
        color: dict[str, int] | None = None,
        pixels: list[dict[str, int]] | None = None,
    ) -> Any:
        payload = _drop_none(
            {
                "mode": mode,
                "brightness": brightness,
                "color": color,
                "pixels": pixels,
            }
        )
        return self._request("POST", "/v1/mira-light/led", payload)

    def run_action(self, name: str, *, loops: int = 1) -> Any:
        return self._request("POST", "/v1/mira-light/action", {"name": name, "loops": loops})

    def update_config(
        self,
        *,
        base_url: str | None = None,
        dry_run: bool | None = None,
        auto_recover_pose: str | None = None,
    ) -> Any:
        payload = _drop_none(
            {
                "baseUrl": base_url,
                "dryRun": dry_run,
                "autoRecoverPose": auto_recover_pose,
            }
        )
        return self._request("POST", "/v1/mira-light/config", payload)

    def capture_pose(
        self,
        name: str,
        *,
        notes: str | None = None,
        verified: bool | None = None,
    ) -> Any:
        payload = _drop_none({"name": name, "notes": notes, "verified": verified})
        return self._request("POST", "/v1/mira-light/profile/capture-pose", payload)

    def set_servo_meta(
        self,
        servo: str,
        *,
        label: str | None = None,
        neutral: int | None = None,
        hard_range: list[int] | None = None,
        rehearsal_range: list[int] | None = None,
        notes: str | None = None,
        verified: bool | None = None,
    ) -> Any:
        payload = _drop_none(
            {
                "servo": servo,
                "label": label,
                "neutral": neutral,
                "hardRange": hard_range,
                "rehearsalRange": rehearsal_range,
                "notes": notes,
                "verified": verified,
            }
        )
        return self._request("POST", "/v1/mira-light/profile/set-servo-meta", payload)

    def device_hello(self, body: dict[str, Any]) -> Any:
        return self._request("POST", "/v1/mira-light/device/hello", body)

    def device_heartbeat(self, body: dict[str, Any]) -> Any:
        return self._request("POST", "/v1/mira-light/device/heartbeat", body)

    def device_status(self, body: dict[str, Any]) -> Any:
        return self._request("POST", "/v1/mira-light/device/status", body)

    def device_event(self, body: dict[str, Any]) -> Any:
        return self._request("POST", "/v1/mira-light/device/event", body)
