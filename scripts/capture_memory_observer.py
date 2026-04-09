#!/usr/bin/env python3
"""Select a representative booth capture, summarize it, and write memory.

Default pipeline:

captures/
-> choose one representative JPG from new frames
-> enrich with IP-based location + local observed time
-> ask a Volc multimodal model for a compact structured summary
-> update session-memory with the latest observation
-> optionally write a higher-salience episodic memory item
-> optionally drop a JSON handoff artifact to a cloud node over SSH

This script intentionally keeps the hot path simple:
- it does not attempt high-frequency visual tracking
- it does not send every frame to the model
- it does not require the cloud node to expose a direct OpenClaw CLI path
"""

from __future__ import annotations

import argparse
import base64
from dataclasses import asdict, dataclass
from datetime import datetime
import hashlib
import json
import logging
import math
import os
from pathlib import Path
import re
import subprocess
import sys
import time
from typing import Any
import urllib.error
import urllib.parse
import urllib.request

import cv2  # type: ignore
import numpy as np  # type: ignore


ROOT = Path(__file__).resolve().parents[1]
BRIDGE_DIR = ROOT / "tools" / "mira_light_bridge"
if str(BRIDGE_DIR) not in sys.path:
    sys.path.insert(0, str(BRIDGE_DIR))

from embodied_memory_client import EmbodiedMemoryClient


LOGGER = logging.getLogger("capture_memory_observer")

DEFAULT_CAPTURES_DIR = Path(os.environ.get("MIRA_LIGHT_CAPTURES_DIR", Path.home() / ".openclaw" / "workspace" / "runtime" / "captures"))
DEFAULT_RUNTIME_DIR = Path(
    os.environ.get(
        "MIRA_LIGHT_CAPTURE_MEMORY_RUNTIME_DIR",
        Path.home() / ".openclaw" / "workspace" / "runtime" / "capture-memory-observer",
    )
)
DEFAULT_INTERVAL_SECONDS = 300
DEFAULT_LOOKBACK_SECONDS = 900
DEFAULT_SAMPLE_LIMIT = 18
DEFAULT_MIN_IMAGE_DIMENSION = 64
DEFAULT_VOLC_BASE_URL = os.environ.get("MIRA_LIGHT_VOLC_BASE_URL", "https://ark.cn-beijing.volces.com/api/coding/v3")
DEFAULT_VOLC_MODEL = os.environ.get("MIRA_LIGHT_VOLC_MODEL", "doubao-seed-2-0-lite-260215")
DEFAULT_VOLC_API_KEY_ENV = "MIRA_LIGHT_VOLC_API_KEY"
DEFAULT_IPINFO_URL = os.environ.get("MIRA_LIGHT_IPINFO_URL", "https://ipinfo.io/json")
DEFAULT_MEMORY_SESSION_ID = os.environ.get("MIRA_LIGHT_CAPTURE_MEMORY_SESSION_ID", "mira-light-capture-observer")
DEFAULT_MEMORY_USER_ID = os.environ.get("MIRA_LIGHT_MEMORY_CONTEXT_USER_ID", "mira-light-bridge")
DEFAULT_CLOUD_DROP_DIR = os.environ.get(
    "MIRA_LIGHT_CLOUD_CLAW_DROP_DIR",
    "/home/ubuntu/mira_import/mira/.mira-runtime/mira-openclaw/var/capture-observations",
)


@dataclass
class CaptureScore:
    path: Path
    mtime: float
    width: int
    height: int
    file_size: int
    sharpness: float
    contrast: float
    brightness: float
    score: float


def configure_logging(level: str) -> None:
    logging.basicConfig(
        level=getattr(logging, level.upper(), logging.INFO),
        format="%(asctime)s %(levelname)s %(name)s: %(message)s",
    )


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Every few minutes pick a representative capture, summarize it with Volc, and write embodied memory."
    )
    parser.add_argument("--captures-dir", type=Path, default=DEFAULT_CAPTURES_DIR, help="Directory containing JPG captures.")
    parser.add_argument("--runtime-dir", type=Path, default=DEFAULT_RUNTIME_DIR, help="Directory for state and output artifacts.")
    parser.add_argument(
        "--interval-seconds",
        type=int,
        default=DEFAULT_INTERVAL_SECONDS,
        help="Loop interval in seconds. Default: 300.",
    )
    parser.add_argument(
        "--lookback-seconds",
        type=int,
        default=DEFAULT_LOOKBACK_SECONDS,
        help="If there is no prior state, only consider captures newer than this lookback window.",
    )
    parser.add_argument(
        "--sample-limit",
        type=int,
        default=DEFAULT_SAMPLE_LIMIT,
        help="Maximum number of candidate JPGs to score per batch.",
    )
    parser.add_argument(
        "--min-image-dimension",
        type=int,
        default=DEFAULT_MIN_IMAGE_DIMENSION,
        help="Minimum allowed width/height before a JPG is ignored.",
    )
    parser.add_argument("--state-file", type=Path, help="Optional explicit JSON state file path.")
    parser.add_argument("--once", action="store_true", help="Run one batch only.")
    parser.add_argument("--dry-run", action="store_true", help="Do not call Volc or memory-context; write local artifacts only.")
    parser.add_argument("--log-level", default="INFO", choices=["DEBUG", "INFO", "WARNING", "ERROR"], help="Logging level.")

    parser.add_argument("--volc-base-url", default=DEFAULT_VOLC_BASE_URL, help="Volc OpenAI-compatible base URL.")
    parser.add_argument("--volc-model", default=DEFAULT_VOLC_MODEL, help="Volc multimodal model id.")
    parser.add_argument(
        "--volc-api-key-env",
        default=DEFAULT_VOLC_API_KEY_ENV,
        help="Environment variable that holds the Volc API key.",
    )
    parser.add_argument(
        "--volc-max-tokens",
        type=int,
        default=768,
        help="Maximum response tokens for the Volc summary request.",
    )

    parser.add_argument("--ipinfo-url", default=DEFAULT_IPINFO_URL, help="Geolocation metadata URL. Default: ipinfo JSON endpoint.")
    parser.add_argument("--ipinfo-token-env", default="IPINFO_TOKEN", help="Optional env var for an ipinfo token.")
    parser.add_argument("--location-ip", default="", help="Optional explicit public IP to geolocate instead of auto-detect.")

    parser.add_argument(
        "--memory-base-url",
        default=os.environ.get("MIRA_LIGHT_MEMORY_CONTEXT_BASE_URL", ""),
        help="memory-context base URL. When omitted, memory writes are skipped unless provided later.",
    )
    parser.add_argument(
        "--memory-auth-token-env",
        default="MIRA_MEMORY_CONTEXT_AUTH_TOKEN",
        help="Environment variable that holds the memory-context bearer token.",
    )
    parser.add_argument("--memory-user-id", default=DEFAULT_MEMORY_USER_ID, help="Writer user id for memory-context.")
    parser.add_argument("--memory-session-id", default=DEFAULT_MEMORY_SESSION_ID, help="Session id for the latest observation note.")
    parser.add_argument(
        "--memory-session-title",
        default="Mira Light capture observer",
        help="Title used for session-memory updates.",
    )
    parser.add_argument(
        "--memory-working-ttl-seconds",
        type=int,
        default=1800,
        help="TTL for short-lived working-memory capture notes.",
    )
    parser.add_argument(
        "--memory-dedup-minutes",
        type=int,
        default=30,
        help="Do not write duplicate episodic observations within this many minutes.",
    )

    parser.add_argument(
        "--cloud-claw-ssh-target",
        default=os.environ.get("MIRA_LIGHT_CLOUD_CLAW_SSH_TARGET", ""),
        help="Optional SSH target like ubuntu@43.160.239.180 for remote handoff artifact upload.",
    )
    parser.add_argument(
        "--cloud-claw-drop-dir",
        default=DEFAULT_CLOUD_DROP_DIR,
        help="Remote directory that receives JSON handoff artifacts when SSH target is configured.",
    )
    parser.add_argument(
        "--cloud-claw-artifact-prefix",
        default="capture-observation",
        help="Filename prefix used for uploaded remote JSON artifacts.",
    )
    return parser


def ensure_runtime_layout(runtime_dir: Path, state_file: Path | None) -> tuple[Path, Path, Path]:
    runtime_dir.mkdir(parents=True, exist_ok=True)
    observations_dir = runtime_dir / "observations"
    observations_dir.mkdir(parents=True, exist_ok=True)
    prompts_dir = runtime_dir / "prompts"
    prompts_dir.mkdir(parents=True, exist_ok=True)
    final_state = state_file.expanduser().resolve() if state_file else runtime_dir / "state.json"
    final_state.parent.mkdir(parents=True, exist_ok=True)
    return observations_dir, prompts_dir, final_state


def load_state(path: Path) -> dict[str, Any]:
    if not path.is_file():
        return {}
    try:
        raw = path.read_text(encoding="utf-8").strip()
        if not raw:
            return {}
        parsed = json.loads(raw)
        return parsed if isinstance(parsed, dict) else {}
    except Exception:
        return {}


def save_state(path: Path, payload: dict[str, Any]) -> None:
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def list_new_capture_paths(captures_dir: Path, state: dict[str, Any], *, lookback_seconds: int) -> list[Path]:
    captures_dir = captures_dir.expanduser().resolve()
    if not captures_dir.is_dir():
        return []

    last_processed_mtime = 0.0
    try:
        last_processed_mtime = float(state.get("lastProcessedMtime") or 0.0)
    except (TypeError, ValueError):
        last_processed_mtime = 0.0

    if last_processed_mtime <= 0:
        cutoff = time.time() - max(60, lookback_seconds)
    else:
        cutoff = last_processed_mtime

    frames = [
        path
        for path in captures_dir.rglob("*.jpg")
        if path.is_file() and path.stat().st_mtime > cutoff
    ]
    return sorted(frames, key=lambda item: item.stat().st_mtime)


def evenly_sample_paths(paths: list[Path], limit: int) -> list[Path]:
    if limit <= 0 or len(paths) <= limit:
        return paths
    picked: list[Path] = []
    for slot in range(limit):
        index = round((slot * (len(paths) - 1)) / max(1, limit - 1))
        path = paths[index]
        if path not in picked:
            picked.append(path)
    return picked


def read_jpg(path: Path) -> np.ndarray | None:
    data = path.read_bytes()
    arr = np.frombuffer(data, dtype=np.uint8)
    return cv2.imdecode(arr, cv2.IMREAD_COLOR)


def score_capture(path: Path, *, min_dimension: int) -> CaptureScore | None:
    image = read_jpg(path)
    if image is None:
        return None

    height, width = image.shape[:2]
    if width < min_dimension or height < min_dimension:
        return None

    gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
    sharpness = float(cv2.Laplacian(gray, cv2.CV_64F).var())
    contrast = float(np.std(gray))
    brightness = float(np.mean(gray))
    brightness_score = max(0.0, 1.0 - min(abs(brightness - 138.0) / 138.0, 1.0))
    resolution_score = min((width * height) / float(1280 * 720), 1.8)
    file_size = path.stat().st_size
    log_size = math.log(max(file_size, 1), 2)

    score = (
        min(sharpness, 950.0) * 0.6
        + min(contrast, 72.0) * 2.2
        + brightness_score * 140.0
        + resolution_score * 45.0
        + min(log_size, 20.0) * 4.0
    )

    return CaptureScore(
        path=path,
        mtime=path.stat().st_mtime,
        width=width,
        height=height,
        file_size=file_size,
        sharpness=round(sharpness, 4),
        contrast=round(contrast, 4),
        brightness=round(brightness, 4),
        score=round(score, 4),
    )


def choose_capture(paths: list[Path], *, limit: int, min_dimension: int) -> CaptureScore | None:
    sampled = evenly_sample_paths(paths, limit)
    best: CaptureScore | None = None
    for path in sampled:
        score = score_capture(path, min_dimension=min_dimension)
        if score is None:
            continue
        if best is None or score.score > best.score:
            best = score
    return best


def load_json_response(url: str, *, headers: dict[str, str] | None = None, method: str = "GET", body: dict[str, Any] | None = None) -> dict[str, Any]:
    data = None if body is None else json.dumps(body, ensure_ascii=False).encode("utf-8")
    request_obj = urllib.request.Request(
        url,
        data=data,
        method=method,
        headers={
            "Content-Type": "application/json; charset=utf-8",
            **(headers or {}),
        },
    )
    with urllib.request.urlopen(request_obj, timeout=30) as response:
        raw = response.read().decode("utf-8")
        return json.loads(raw) if raw.strip() else {}


def get_ip_location(*, ipinfo_url: str, ipinfo_token: str = "", explicit_ip: str = "") -> dict[str, Any]:
    if explicit_ip.strip():
        if ipinfo_url.endswith("/json"):
            url = ipinfo_url[: -len("/json")] + f"/{explicit_ip.strip()}/json"
        else:
            url = ipinfo_url.rstrip("/") + f"/{explicit_ip.strip()}/json"
    else:
        url = ipinfo_url

    if ipinfo_token.strip():
        joiner = "&" if "?" in url else "?"
        url = f"{url}{joiner}token={urllib.parse.quote(ipinfo_token.strip())}"

    try:
        payload = load_json_response(url)
    except Exception as exc:  # noqa: BLE001
        LOGGER.warning("IP location lookup failed: %s", exc)
        return {
            "ip": explicit_ip or "unknown",
            "locationSummary": "unknown",
            "city": "",
            "region": "",
            "country": "",
            "timezone": "",
            "source": "lookup_failed",
        }

    city = str(payload.get("city") or "").strip()
    region = str(payload.get("region") or "").strip()
    country = str(payload.get("country") or "").strip()
    location_summary = ", ".join(part for part in (city, region, country) if part) or "unknown"
    return {
        "ip": str(payload.get("ip") or explicit_ip or "unknown").strip() or "unknown",
        "locationSummary": location_summary,
        "city": city,
        "region": region,
        "country": country,
        "timezone": str(payload.get("timezone") or "").strip(),
        "org": str(payload.get("org") or "").strip(),
        "loc": str(payload.get("loc") or "").strip(),
        "source": ipinfo_url,
    }


def build_volc_request_payload(
    *,
    model: str,
    image_path: Path,
    observed_at_local: str,
    location_summary: str,
    ip_address: str,
    max_tokens: int,
) -> dict[str, Any]:
    image_b64 = base64.b64encode(image_path.read_bytes()).decode("ascii")
    prompt = (
        "你在为 Mira Light 生成一条适合写入记忆系统的图像摘要。"
        "请严格只输出一个 JSON 对象，不要输出任何额外解释。"
        "根据图片与提供的元数据，总结这张图里最值得保留的观察结果。"
        "字段必须包含："
        "peopleCount(number), peopleSummary(string), objects(array of short strings), "
        "activity(string), sceneSummary(string), time(string), location(string), "
        "memoryWorthy(boolean), memoryReason(string)."
        "规则："
        "1. peopleSummary 必须概括图中人相关信息；没人时写“未见明显人物”。"
        "2. objects 只列最主要的 1-6 个物体。"
        "3. time 直接使用提供的 observed_at_local。"
        "4. location 直接使用提供的 location_summary 与 ip_address，不要自行猜城市。"
        "5. 不确定时用“未知”或保守表述，不要编造。"
        f" 元数据：observed_at_local={observed_at_local}; location_summary={location_summary}; ip_address={ip_address}."
    )
    return {
        "model": model,
        "messages": [
            {
                "role": "user",
                "content": [
                    {"type": "text", "text": prompt},
                    {"type": "image_url", "image_url": {"url": f"data:image/jpeg;base64,{image_b64}"}},
                ],
            }
        ],
        "max_tokens": max_tokens,
    }


def extract_first_json_object(text: str) -> dict[str, Any]:
    text = text.strip()
    if not text:
        raise ValueError("empty model response")

    try:
        parsed = json.loads(text)
        if isinstance(parsed, dict):
            return parsed
    except json.JSONDecodeError:
        pass

    match = re.search(r"\{.*\}", text, re.S)
    if not match:
        raise ValueError("no JSON object found in model response")
    parsed = json.loads(match.group(0))
    if not isinstance(parsed, dict):
        raise ValueError("model response JSON was not an object")
    return parsed


def summarize_capture_with_volc(
    *,
    base_url: str,
    api_key: str,
    model: str,
    image_path: Path,
    observed_at_local: str,
    location_summary: str,
    ip_address: str,
    max_tokens: int,
) -> dict[str, Any]:
    url = base_url.rstrip("/") + "/chat/completions"
    payload = build_volc_request_payload(
        model=model,
        image_path=image_path,
        observed_at_local=observed_at_local,
        location_summary=location_summary,
        ip_address=ip_address,
        max_tokens=max_tokens,
    )
    raw = load_json_response(
        url,
        headers={"Authorization": f"Bearer {api_key}"},
        method="POST",
        body=payload,
    )
    choices = raw.get("choices")
    if not isinstance(choices, list) or not choices:
        raise RuntimeError(f"Volc response missing choices: {raw}")
    message = choices[0].get("message", {})
    if not isinstance(message, dict):
        raise RuntimeError(f"Volc response missing message: {raw}")
    content = str(message.get("content") or "").strip()
    summary = extract_first_json_object(content)
    summary["_providerResponse"] = raw
    return summary


def normalize_summary(summary: dict[str, Any], *, observed_at_local: str, location_summary: str, ip_address: str) -> dict[str, Any]:
    objects = summary.get("objects")
    if not isinstance(objects, list):
        if isinstance(objects, str) and objects.strip():
            objects = [objects.strip()]
        else:
            objects = []

    normalized = {
        "peopleCount": max(0, int(summary.get("peopleCount") or 0)),
        "peopleSummary": str(summary.get("peopleSummary") or "未见明显人物").strip() or "未见明显人物",
        "objects": [str(item).strip() for item in objects if str(item).strip()][:6],
        "activity": str(summary.get("activity") or "未知").strip() or "未知",
        "sceneSummary": str(summary.get("sceneSummary") or "未知").strip() or "未知",
        "time": str(summary.get("time") or observed_at_local).strip() or observed_at_local,
        "location": str(summary.get("location") or f"{location_summary} (IP: {ip_address})").strip()
        or f"{location_summary} (IP: {ip_address})",
        "memoryWorthy": bool(summary.get("memoryWorthy")),
        "memoryReason": str(summary.get("memoryReason") or "未提供").strip() or "未提供",
    }
    return normalized


def build_observation_signature(summary: dict[str, Any]) -> str:
    signature_payload = {
        "peopleCount": summary.get("peopleCount"),
        "peopleSummary": summary.get("peopleSummary"),
        "objects": summary.get("objects"),
        "activity": summary.get("activity"),
        "sceneSummary": summary.get("sceneSummary"),
        "location": summary.get("location"),
    }
    blob = json.dumps(signature_payload, ensure_ascii=False, sort_keys=True)
    return hashlib.sha256(blob.encode("utf-8")).hexdigest()


def should_write_episodic_memory(
    *,
    summary: dict[str, Any],
    state: dict[str, Any],
    dedup_minutes: int,
) -> tuple[bool, str]:
    signature = build_observation_signature(summary)
    if signature == str(state.get("lastMemorySignature") or ""):
        try:
            last_at = float(state.get("lastMemorySignatureAt") or 0.0)
        except (TypeError, ValueError):
            last_at = 0.0
        age_minutes = (time.time() - last_at) / 60.0 if last_at > 0 else 9999
        if age_minutes < max(1, dedup_minutes):
            return False, f"duplicate signature within {dedup_minutes} minutes"

    if bool(summary.get("memoryWorthy")):
        return True, "model marked observation as memory-worthy"

    if int(summary.get("peopleCount") or 0) > 0:
        return True, "visible people present in booth frame"

    if len(summary.get("objects") or []) >= 3:
        return True, "multiple salient booth objects present"

    return False, "summary not salient enough for episodic write"


def write_local_artifact(path: Path, payload: dict[str, Any]) -> None:
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def update_capture_session_note(
    client: EmbodiedMemoryClient,
    *,
    session_id: str,
    title: str,
    observation: dict[str, Any],
) -> dict[str, Any]:
    if not client.enabled:
        return {"ok": True, "skipped": True}

    observed_at = str(observation.get("observedAtLocal") or "")
    summary = observation.get("summary", {}) if isinstance(observation.get("summary"), dict) else {}
    people_summary = str(summary.get("peopleSummary") or "未见明显人物")
    scene_summary = str(summary.get("sceneSummary") or "未知")
    location = str(summary.get("location") or "unknown")
    objects = summary.get("objects") if isinstance(summary.get("objects"), list) else []
    key_result = f"{observed_at} capture={Path(str(observation.get('capturePath') or '')).name} people={summary.get('peopleCount', 0)}"

    try:
        existing = client.get_current_session_note(session_id=session_id).get("note")
    except Exception as exc:  # noqa: BLE001
        LOGGER.warning("session-memory current note read failed: %s", exc)
        existing = None

    note = client._merged_session_note(  # type: ignore[attr-defined]
        existing_note=existing,
        title=title,
        current_state=(
            f"Latest booth capture at {observed_at} in {location}. "
            f"people={summary.get('peopleCount', 0)}; peopleSummary={people_summary}; sceneSummary={scene_summary}."
        ),
        next_step="Keep sampling captures every 5 minutes and promote only salient visual observations into episodic memory.",
        task_spec="Summarize representative booth captures into structured visual memory for Mira Light and cloud Claw prompt-pack retrieval.",
        relevant_files=[
            "scripts/capture_memory_observer.py",
            "docs/cam_receiver_new.py",
            str(observation.get("capturePath") or ""),
        ],
        key_results=[key_result],
        worklog=[f"{observed_at} objects={', '.join(objects) if objects else 'none'}"],
    )
    return client.update_session_note(session_id=session_id, note=note)


def write_capture_memory(
    client: EmbodiedMemoryClient,
    *,
    observation: dict[str, Any],
    working_ttl_seconds: int,
) -> dict[str, Any]:
    if not client.enabled:
        return {"ok": True, "skipped": True}

    summary = observation["summary"]
    observed_at = observation["observedAtLocal"]
    capture_path = str(observation["capturePath"])
    signature = str(observation["signature"])
    selection = observation["selection"]

    content = (
        f"At {observed_at}, Mira Light observed: {summary['sceneSummary']}. "
        f"People: {summary['peopleSummary']}. Objects: {', '.join(summary['objects']) if summary['objects'] else 'none'}."
    )

    episodic_item = {
        "user_id": client.user_id,
        "namespace": "home",
        "layer": "episodic",
        "kind": "environment_observation",
        "content": content,
        "structured_value": {
            "system": "mira-light",
            "observer": "capture-memory-observer",
            "capturePath": capture_path,
            "observedAtLocal": observed_at,
            "summary": summary,
            "selection": selection,
            "signature": signature,
        },
        "confidence": 0.9,
        "salience": 0.88 if summary["memoryWorthy"] else 0.76,
        "sensitivity": "normal",
        "tags": [
            "mira-light",
            "visual-observation",
            f"location:{summary['location']}",
            f"people:{summary['peopleCount']}",
        ],
        "evidence_refs": [f"mira-light:capture:{signature}", capture_path],
    }

    working_item = {
        "user_id": client.user_id,
        "namespace": "home",
        "layer": "working",
        "kind": "scene_state",
        "content": (
            f"Recent booth capture summary: {summary['sceneSummary']} "
            f"(people={summary['peopleCount']}, location={summary['location']})."
        ),
        "structured_value": {
            "system": "mira-light",
            "observer": "capture-memory-observer",
            "signature": signature,
            "capturePath": capture_path,
            "summary": summary,
        },
        "confidence": 0.93,
        "salience": 0.8,
        "sensitivity": "normal",
        "tags": ["mira-light", "working", "visual-observation"],
        "evidence_refs": [f"mira-light:capture:{signature}"],
        "expires_at": datetime.fromtimestamp(time.time() + max(60, working_ttl_seconds)).astimezone().isoformat(timespec="seconds"),
    }

    return client._post_write("capture_observation", [episodic_item, working_item])  # type: ignore[attr-defined]


def maybe_upload_remote_artifact(
    *,
    ssh_target: str,
    remote_dir: str,
    artifact_prefix: str,
    payload: dict[str, Any],
) -> dict[str, Any]:
    if not ssh_target.strip():
        return {"ok": True, "skipped": True, "reason": "cloud_claw_ssh_target_not_configured"}

    timestamp = datetime.now().strftime("%Y%m%d-%H%M%S")
    remote_name = f"{artifact_prefix}-{timestamp}.json"
    remote_path = remote_dir.rstrip("/") + "/" + remote_name
    command = [
        "ssh",
        ssh_target.strip(),
        f"mkdir -p {shlex_quote(remote_dir)} && cat > {shlex_quote(remote_path)}",
    ]
    completed = subprocess.run(
        command,
        input=(json.dumps(payload, ensure_ascii=False, indent=2) + "\n"),
        text=True,
        capture_output=True,
        check=False,
    )
    if completed.returncode != 0:
        raise RuntimeError(completed.stderr.strip() or completed.stdout.strip() or "remote artifact upload failed")
    return {"ok": True, "remotePath": remote_path}


def shlex_quote(value: str) -> str:
    return "'" + value.replace("'", "'\"'\"'") + "'"


def process_once(args: argparse.Namespace, *, observations_dir: Path, prompts_dir: Path, state_path: Path) -> int:
    state = load_state(state_path)
    new_paths = list_new_capture_paths(args.captures_dir, state, lookback_seconds=args.lookback_seconds)
    if not new_paths:
        LOGGER.info("No new captures found under %s", args.captures_dir)
        return 0

    chosen = choose_capture(
        new_paths,
        limit=args.sample_limit,
        min_dimension=args.min_image_dimension,
    )
    if chosen is None:
        LOGGER.warning("No suitable JPG could be selected from %s new captures", len(new_paths))
        return 1

    observed_at_local = datetime.fromtimestamp(chosen.mtime).astimezone().strftime("%Y-%m-%d %H:%M:%S %Z")
    ipinfo_token = os.environ.get(args.ipinfo_token_env, "").strip()
    location = get_ip_location(
        ipinfo_url=args.ipinfo_url,
        ipinfo_token=ipinfo_token,
        explicit_ip=args.location_ip,
    )

    prompt_artifact = prompts_dir / f"{datetime.now().strftime('%Y%m%d-%H%M%S')}-request.json"
    prompt_payload = build_volc_request_payload(
        model=args.volc_model,
        image_path=chosen.path,
        observed_at_local=observed_at_local,
        location_summary=location["locationSummary"],
        ip_address=location["ip"],
        max_tokens=args.volc_max_tokens,
    )
    write_local_artifact(prompt_artifact, prompt_payload)

    if args.dry_run:
        summary = {
            "peopleCount": 0,
            "peopleSummary": "dry-run 未调用模型",
            "objects": [],
            "activity": "未知",
            "sceneSummary": f"dry-run selected {chosen.path.name}",
            "time": observed_at_local,
            "location": f"{location['locationSummary']} (IP: {location['ip']})",
            "memoryWorthy": False,
            "memoryReason": "dry-run",
        }
        provider_payload = {"ok": True, "dryRun": True}
    else:
        api_key = os.environ.get(args.volc_api_key_env, "").strip()
        if not api_key:
            raise SystemExit(f"Missing Volc API key env: {args.volc_api_key_env}")
        raw_summary = summarize_capture_with_volc(
            base_url=args.volc_base_url,
            api_key=api_key,
            model=args.volc_model,
            image_path=chosen.path,
            observed_at_local=observed_at_local,
            location_summary=location["locationSummary"],
            ip_address=location["ip"],
            max_tokens=args.volc_max_tokens,
        )
        provider_payload = raw_summary.pop("_providerResponse", {})
        summary = normalize_summary(
            raw_summary,
            observed_at_local=observed_at_local,
            location_summary=location["locationSummary"],
            ip_address=location["ip"],
        )

    signature = build_observation_signature(summary)
    should_write, write_reason = should_write_episodic_memory(
        summary=summary,
        state=state,
        dedup_minutes=args.memory_dedup_minutes,
    )

    observation = {
        "capturePath": str(chosen.path),
        "observedAtLocal": observed_at_local,
        "selection": asdict(chosen),
        "summary": summary,
        "signature": signature,
        "location": location,
        "volcModel": args.volc_model,
        "providerPayload": provider_payload,
        "memoryWriteSuggested": should_write,
        "memoryWriteReason": write_reason,
    }

    artifact_path = observations_dir / f"{datetime.now().strftime('%Y%m%d-%H%M%S')}-{signature[:12]}.json"
    write_local_artifact(artifact_path, observation)

    memory_client = EmbodiedMemoryClient(
        base_url=args.memory_base_url.strip(),
        auth_token=os.environ.get(args.memory_auth_token_env, "").strip(),
        user_id=args.memory_user_id.strip() or DEFAULT_MEMORY_USER_ID,
        enabled=bool(args.memory_base_url.strip() and not args.dry_run),
    )

    session_result = update_capture_session_note(
        memory_client,
        session_id=args.memory_session_id,
        title=args.memory_session_title,
        observation=observation,
    )
    memory_result = {"ok": True, "skipped": True, "reason": write_reason}
    if should_write:
        memory_result = write_capture_memory(
            memory_client,
            observation=observation,
            working_ttl_seconds=args.memory_working_ttl_seconds,
        )

    remote_result = {"ok": True, "skipped": True, "reason": "cloud hook disabled"}
    if not args.dry_run:
        remote_result = maybe_upload_remote_artifact(
            ssh_target=args.cloud_claw_ssh_target,
            remote_dir=args.cloud_claw_drop_dir,
            artifact_prefix=args.cloud_claw_artifact_prefix,
            payload=observation,
        )

    next_state = {
        "lastProcessedPath": str(chosen.path),
        "lastProcessedMtime": chosen.mtime,
        "lastObservationArtifact": str(artifact_path),
        "lastObservationSignature": signature,
        "lastObservationAt": time.time(),
        "lastMemorySignature": signature if should_write else state.get("lastMemorySignature"),
        "lastMemorySignatureAt": time.time() if should_write else state.get("lastMemorySignatureAt"),
        "lastSessionResult": session_result,
        "lastMemoryResult": memory_result,
        "lastRemoteResult": remote_result,
    }
    save_state(state_path, next_state)

    LOGGER.info(
        "selected=%s people=%s objects=%s memory_write=%s remote=%s",
        chosen.path.name,
        summary["peopleCount"],
        len(summary["objects"]),
        should_write,
        remote_result.get("ok", False),
    )
    return 0


def main() -> int:
    args = build_parser().parse_args()
    configure_logging(args.log_level)
    observations_dir, prompts_dir, state_path = ensure_runtime_layout(
        args.runtime_dir.expanduser().resolve(),
        args.state_file,
    )

    while True:
        try:
            code = process_once(args, observations_dir=observations_dir, prompts_dir=prompts_dir, state_path=state_path)
        except KeyboardInterrupt:
            LOGGER.info("Stopped by user")
            return 0
        except Exception as exc:  # noqa: BLE001
            LOGGER.exception("capture memory observer failed: %s", exc)
            code = 1

        if args.once:
            return code

        time.sleep(max(30, args.interval_seconds))


if __name__ == "__main__":
    raise SystemExit(main())
