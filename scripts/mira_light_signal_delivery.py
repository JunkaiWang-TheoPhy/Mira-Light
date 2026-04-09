"""Shared motion-script metadata aligned to the unified signal-delivery spec.

This keeps the per-scene launch manifests lightweight while making the
transport and payload contract explicit for the director console and any
downstream tooling that reads ``/api/motion-scripts``.
"""

from __future__ import annotations

from copy import deepcopy
import json
from pathlib import Path
from typing import Any


UNIFIED_SIGNAL_DELIVERY_DOC = "docs/Guide/09-Mira Light统一信号交付格式说明.md"
UNIFIED_SIGNAL_DELIVERY_SCHEMA = "config/mira_light_signal_delivery.schema.json"
LED_PIXEL_COUNT = 40

JOINT_CONTROL_CONTRACT = {
    "signalType": "jointControl",
    "transport": "bridge-http",
    "writePath": "/v1/mira-light/control",
    "statusPath": "/v1/mira-light/status",
    "rawTransport": "tcp://192.168.31.10:9527",
    "rawFrameFormat": "#IDPWWWWTTTT!",
    "payload": {
        "modeField": "mode",
        "supportedModes": ["absolute", "relative"],
        "servoFields": ["servo1", "servo2", "servo3", "servo4"],
    },
}

LED_CONTROL_CONTRACT = {
    "signalType": "led",
    "transport": "bridge-http",
    "writePath": "/v1/mira-light/led",
    "statusPaths": ["/v1/mira-light/led", "/v1/mira-light/status"],
    "payload": {
        "modeField": "mode",
        "writePixelsField": "pixels",
        "readPixelsField": "pixelSignals",
        "supportedModes": ["off", "solid", "breathing", "rainbow", "rainbow_cycle", "vector"],
        "vectorPixelCount": LED_PIXEL_COUNT,
        "vectorPixelShape": [0, 0, 0, 0],
    },
}

HEAD_CAPACITIVE_CONTRACT = {
    "signalType": "headCapacitive",
    "transport": "bridge-http",
    "writePath": "/v1/mira-light/sensors",
    "statusPaths": ["/v1/mira-light/sensors", "/v1/mira-light/status"],
    "payload": {
        "field": "headCapacitive",
        "allowedValues": [0, 1],
    },
}

_SIGNAL_CONTRACTS = {
    "jointControl": JOINT_CONTROL_CONTRACT,
    "led": LED_CONTROL_CONTRACT,
    "headCapacitive": HEAD_CAPACITIVE_CONTRACT,
}


def get_signal_contract(signal_type: str) -> dict[str, Any]:
    contract = _SIGNAL_CONTRACTS.get(signal_type)
    if contract is None:
        raise KeyError(f"Unsupported signal contract: {signal_type}")
    return deepcopy(contract)


def build_signal_delivery_contract(*, signal_domains: list[str] | None = None) -> dict[str, Any]:
    resolved_signal_domains = list(signal_domains or ["jointControl", "led", "headCapacitive"])
    contracts = [deepcopy(_SIGNAL_CONTRACTS[name]) for name in resolved_signal_domains if name in _SIGNAL_CONTRACTS]
    return {
        "docPath": UNIFIED_SIGNAL_DELIVERY_DOC,
        "schemaPath": UNIFIED_SIGNAL_DELIVERY_SCHEMA,
        "signalDomains": resolved_signal_domains,
        "contracts": contracts,
    }


def load_signal_delivery_schema(*, root: Path | None = None) -> dict[str, Any]:
    resolved_root = root or Path(__file__).resolve().parents[1]
    schema_path = resolved_root / UNIFIED_SIGNAL_DELIVERY_SCHEMA
    return json.loads(schema_path.read_text(encoding="utf-8"))


def build_scene_request_body(
    scene_id: str,
    *,
    cue_mode: str = "director",
    context: Any = None,
    async_run: bool = True,
    allow_unavailable: bool | None = None,
) -> dict[str, Any]:
    payload = {
        "scene": scene_id,
        "async": bool(async_run),
        "cueMode": cue_mode or "director",
    }
    if context:
        payload["context"] = context
    if allow_unavailable is not None:
        payload["allowUnavailable"] = bool(allow_unavailable)
    return payload


def build_scene_script_info(
    *,
    scene_id: str,
    title: str,
    folder_name: str,
    step_outline: list[str],
    source_scene_file: str = "scripts/scenes.py",
    source_scene_key: str | None = None,
    api_context_keys: list[str] | None = None,
    signal_domains: list[str] | None = None,
) -> dict[str, Any]:
    resolved_signal_domains = list(signal_domains or ["jointControl", "led"])
    info = {
        "sceneId": scene_id,
        "title": title,
        "folderName": folder_name,
        "sourceSceneFile": source_scene_file,
        "sourceSceneKey": source_scene_key or scene_id,
        "apiRunPath": f"/api/run-motion-script/{scene_id}",
        "stepOutline": list(step_outline),
        "signalDelivery": {
            **build_signal_delivery_contract(signal_domains=resolved_signal_domains),
            "launchTransport": "director-console -> bridge-http -> runtime",
            "launchPath": "/v1/mira-light/run-scene",
            "recommendedCallerPath": f"/api/run-motion-script/{scene_id}",
        },
    }
    if api_context_keys:
        info["apiContextKeys"] = list(api_context_keys)
    return info
