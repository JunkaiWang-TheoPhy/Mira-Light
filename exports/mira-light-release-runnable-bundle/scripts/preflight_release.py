#!/usr/bin/env python3
"""Release preflight checks for Mira Light handoff and local bring-up."""

from __future__ import annotations

import argparse
import json
import os
from dataclasses import dataclass
from pathlib import Path
import shutil
import subprocess
import sys
from typing import Callable
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen


DEFAULT_BRIDGE_BASE_URL = "http://127.0.0.1:9783"
DEFAULT_RECEIVER_BASE_URL = "http://127.0.0.1:9784"
DEFAULT_TIMEOUT_SECONDS = 3.0
OPENCLAW_CONFIG_PATH = Path.home() / ".openclaw" / "openclaw.json"
OPENCLAW_PLUGIN_DIR = Path.home() / ".openclaw" / "extensions" / "mira-light-bridge"


@dataclass
class PreflightConfig:
    release_root: Path
    bridge_base_url: str
    receiver_base_url: str
    lamp_base_url: str
    bridge_token: str
    timeout_seconds: float
    strict_online: bool


@dataclass
class CheckResult:
    phase: str
    name: str
    status: str
    detail: str
    hint: str | None = None


def normalize_base_url(value: str) -> str:
    return value.strip().rstrip("/")


def resolve_default_bridge_base_url() -> str:
    explicit = os.environ.get("MIRA_LIGHT_BRIDGE_URL") or os.environ.get("MIRA_LIGHT_CONSOLE_BRIDGE_URL")
    if explicit:
        return explicit

    host = (os.environ.get("MIRA_LIGHT_BRIDGE_HOST") or "127.0.0.1").strip()
    if host in {"0.0.0.0", "::"}:
        host = "127.0.0.1"
    port = (os.environ.get("MIRA_LIGHT_BRIDGE_PORT") or "9783").strip()
    return f"http://{host}:{port}"


def resolve_default_receiver_base_url() -> str:
    host = (os.environ.get("MIRA_LIGHT_RECEIVER_HOST") or "127.0.0.1").strip()
    if host in {"0.0.0.0", "::"}:
        host = "127.0.0.1"
    port = (os.environ.get("MIRA_LIGHT_RECEIVER_PORT") or "9784").strip()
    return f"http://{host}:{port}"


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Run Mira Light release preflight checks.",
    )
    parser.add_argument(
        "mode",
        nargs="?",
        default="offline",
        choices=("offline", "online", "all"),
        help="Which group of checks to run",
    )
    parser.add_argument(
        "--strict-online",
        action="store_true",
        help="Turn online warnings into failures",
    )
    parser.add_argument(
        "--bridge-url",
        default=resolve_default_bridge_base_url(),
        help="Bridge base URL to probe",
    )
    parser.add_argument(
        "--receiver-url",
        default=resolve_default_receiver_base_url(),
        help="Receiver base URL to probe",
    )
    parser.add_argument(
        "--lamp-url",
        default=(os.environ.get("MIRA_LIGHT_LAMP_BASE_URL") or os.environ.get("MIRA_LIGHT_BASE_URL") or ""),
        help="Lamp base URL to probe",
    )
    parser.add_argument(
        "--bridge-token",
        default=os.environ.get("MIRA_LIGHT_BRIDGE_TOKEN", ""),
        help="Bridge token for authenticated API checks",
    )
    parser.add_argument(
        "--timeout",
        type=float,
        default=float(os.environ.get("MIRA_LIGHT_PREFLIGHT_TIMEOUT_SECONDS", DEFAULT_TIMEOUT_SECONDS)),
        help="HTTP timeout in seconds",
    )
    return parser


def pass_result(phase: str, name: str, detail: str, hint: str | None = None) -> CheckResult:
    return CheckResult(phase=phase, name=name, status="PASS", detail=detail, hint=hint)


def warn_result(phase: str, name: str, detail: str, hint: str | None = None) -> CheckResult:
    return CheckResult(phase=phase, name=name, status="WARN", detail=detail, hint=hint)


def fail_result(phase: str, name: str, detail: str, hint: str | None = None) -> CheckResult:
    return CheckResult(phase=phase, name=name, status="FAIL", detail=detail, hint=hint)


def http_result(
    *,
    strict_online: bool,
    phase: str,
    name: str,
    detail: str,
    hint: str | None = None,
) -> CheckResult:
    if strict_online:
        return fail_result(phase, name, detail, hint)
    return warn_result(phase, name, detail, hint)


def request_json(
    url: str,
    *,
    timeout_seconds: float,
    headers: dict[str, str] | None = None,
) -> tuple[int, dict | list | None, str | None]:
    request = Request(url, headers=headers or {}, method="GET")
    try:
        with urlopen(request, timeout=timeout_seconds) as response:
            status = response.status
            raw = response.read().decode("utf-8")
    except HTTPError as exc:
        raw = exc.read().decode("utf-8", errors="replace")
        try:
            payload = json.loads(raw) if raw.strip() else None
        except json.JSONDecodeError:
            payload = None
        return exc.code, payload, raw
    except URLError as exc:
        raise ConnectionError(str(exc.reason)) from exc

    payload = json.loads(raw) if raw.strip() else None
    return status, payload, raw


def run_command(cmd: list[str]) -> tuple[int, str]:
    result = subprocess.run(
        cmd,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True,
        check=False,
    )
    return result.returncode, result.stdout.strip()


def run_offline_checks(config: PreflightConfig) -> list[CheckResult]:
    results: list[CheckResult] = []
    runtime_version = f"{sys.version_info.major}.{sys.version_info.minor}.{sys.version_info.micro}"
    if sys.version_info >= (3, 10):
        results.append(pass_result("offline", "python runtime", f"{sys.executable} ({runtime_version})"))
    else:
        results.append(
            fail_result(
                "offline",
                "python runtime",
                f"{sys.executable} ({runtime_version}) is below Python 3.10",
                "Re-run the release with Python 3.10+.",
            )
        )

    venv_python = config.release_root / ".venv" / "bin" / "python"
    if venv_python.is_file():
        code, output = run_command([str(venv_python), "--version"])
        version_detail = output or "Python version unavailable"
        if code == 0:
            results.append(pass_result("offline", "release venv", f"{venv_python} ({version_detail})"))
        else:
            results.append(
                warn_result(
                    "offline",
                    "release venv",
                    f"{venv_python} exists but did not report a version cleanly",
                    version_detail,
                )
            )
    else:
        results.append(
            fail_result(
                "offline",
                "release venv",
                f"missing {venv_python}",
                "Run `bash scripts/one_click_install.sh` first.",
            )
        )

    curl_path = shutil.which("curl")
    if curl_path:
        results.append(pass_result("offline", "curl", curl_path))
    else:
        results.append(
            fail_result(
                "offline",
                "curl",
                "curl was not found in PATH",
                "Install curl so smoke checks and network diagnostics can run.",
            )
        )

    lamp_url = normalize_base_url(config.lamp_base_url)
    if lamp_url:
        results.append(pass_result("offline", "lamp target", lamp_url))
    else:
        results.append(
            warn_result(
                "offline",
                "lamp target",
                "MIRA_LIGHT_LAMP_BASE_URL is empty",
                "Set a real lamp URL before online checks, or use `--dry-run` for rehearsals.",
            )
        )

    token = config.bridge_token.strip()
    if not token:
        results.append(
            warn_result(
                "offline",
                "bridge token",
                "MIRA_LIGHT_BRIDGE_TOKEN is empty",
                "Export a token before running authenticated bridge checks.",
            )
        )
    elif token == "test-token":
        results.append(
            warn_result(
                "offline",
                "bridge token",
                "using default development token `test-token`",
                "Set a non-default token before multi-user or long-running demos.",
            )
        )
    else:
        results.append(pass_result("offline", "bridge token", "non-default token configured"))

    openclaw_path = shutil.which("openclaw")
    if openclaw_path:
        results.append(pass_result("offline", "openclaw cli", openclaw_path))
    else:
        results.append(
            warn_result(
                "offline",
                "openclaw cli",
                "OpenClaw CLI not found in PATH",
                "Install OpenClaw if this handoff needs local plugin control.",
            )
        )

    if OPENCLAW_CONFIG_PATH.is_file():
        results.append(pass_result("offline", "openclaw config", str(OPENCLAW_CONFIG_PATH)))
        try:
            raw = json.loads(OPENCLAW_CONFIG_PATH.read_text(encoding="utf-8"))
        except json.JSONDecodeError as exc:
            results.append(
                warn_result(
                    "offline",
                    "openclaw plugin entry",
                    f"config JSON could not be parsed: {exc}",
                    "Repair ~/.openclaw/openclaw.json before plugin verification.",
                )
            )
        else:
            allow = raw.get("plugins", {}).get("allow", [])
            entries = raw.get("plugins", {}).get("entries", {})
            if "mira-light-bridge" in allow and "mira-light-bridge" in entries:
                results.append(pass_result("offline", "openclaw plugin entry", "mira-light-bridge is configured"))
            else:
                results.append(
                    warn_result(
                        "offline",
                        "openclaw plugin entry",
                        "mira-light-bridge is not fully configured in ~/.openclaw/openclaw.json",
                        "Run `bash scripts/install_openclaw_plugin.sh` if this machine needs plugin access.",
                    )
                )
    else:
        results.append(
            warn_result(
                "offline",
                "openclaw config",
                f"missing {OPENCLAW_CONFIG_PATH}",
                "OpenClaw plugin checks will be skipped until the config exists.",
            )
        )

    if OPENCLAW_PLUGIN_DIR.exists():
        results.append(pass_result("offline", "openclaw plugin dir", str(OPENCLAW_PLUGIN_DIR)))
    else:
        results.append(
            warn_result(
                "offline",
                "openclaw plugin dir",
                f"missing {OPENCLAW_PLUGIN_DIR}",
                "Run `bash scripts/install_openclaw_plugin.sh` if you want the local plugin installed here.",
            )
        )

    return results


def run_http_check(
    *,
    phase: str,
    name: str,
    url: str,
    timeout_seconds: float,
    strict_online: bool,
    headers: dict[str, str] | None = None,
    validator: Callable[[int, object | None], tuple[bool, str]],
    failure_hint: str | None = None,
) -> CheckResult:
    try:
        status, payload, _raw = request_json(url, timeout_seconds=timeout_seconds, headers=headers)
    except ConnectionError as exc:
        return http_result(
            strict_online=strict_online,
            phase=phase,
            name=name,
            detail=f"{url} unreachable: {exc}",
            hint=failure_hint,
        )
    except json.JSONDecodeError as exc:
        return http_result(
            strict_online=strict_online,
            phase=phase,
            name=name,
            detail=f"{url} returned invalid JSON: {exc}",
            hint=failure_hint,
        )

    ok, detail = validator(status, payload)
    if ok:
        return pass_result(phase, name, detail)
    return http_result(
        strict_online=strict_online,
        phase=phase,
        name=name,
        detail=detail,
        hint=failure_hint,
    )


def validate_health_json(status: int, payload: object | None) -> tuple[bool, str]:
    if status != 200:
        return False, f"expected HTTP 200, got {status}"
    if not isinstance(payload, dict):
        return False, "expected a JSON object"
    if not payload.get("ok"):
        return False, "health payload did not contain ok=true"
    return True, "ok=true"


def validate_status_payload(status: int, payload: object | None) -> tuple[bool, str]:
    if status != 200:
        return False, f"expected HTTP 200, got {status}"
    if not isinstance(payload, dict):
        return False, "expected a JSON object"
    return True, "device /status returned JSON"


def validate_bridge_scenes(status: int, payload: object | None) -> tuple[bool, str]:
    if status != 200:
        return False, f"expected HTTP 200, got {status}"
    if not isinstance(payload, dict):
        return False, "expected a JSON object"
    if not isinstance(payload.get("items"), list):
        return False, "bridge scenes payload did not contain an items list"
    return True, f"authenticated bridge scenes returned {len(payload['items'])} items"


def run_online_checks(config: PreflightConfig) -> list[CheckResult]:
    results: list[CheckResult] = []
    bridge_url = normalize_base_url(config.bridge_base_url)
    receiver_url = normalize_base_url(config.receiver_base_url)
    lamp_url = normalize_base_url(config.lamp_base_url)

    results.append(
        run_http_check(
            phase="online",
            name="bridge health",
            url=f"{bridge_url}/health",
            timeout_seconds=config.timeout_seconds,
            strict_online=config.strict_online,
            validator=validate_health_json,
            failure_hint="Start the bridge first or check the bridge port in deploy/repo.env.example.",
        )
    )
    results.append(
        run_http_check(
            phase="online",
            name="receiver health",
            url=f"{receiver_url}/health",
            timeout_seconds=config.timeout_seconds,
            strict_online=config.strict_online,
            validator=validate_health_json,
            failure_hint="Start the simple receiver or update MIRA_LIGHT_RECEIVER_PORT.",
        )
    )

    if lamp_url:
        results.append(
            run_http_check(
                phase="online",
                name="lamp status",
                url=f"{lamp_url}/status",
                timeout_seconds=config.timeout_seconds,
                strict_online=config.strict_online,
                validator=validate_status_payload,
                failure_hint="Confirm the lamp IP on the current network, then retry the preflight.",
            )
        )
    else:
        results.append(
            http_result(
                strict_online=config.strict_online,
                phase="online",
                name="lamp status",
                detail="lamp base URL is empty; skipping /status probe",
                hint="Set MIRA_LIGHT_LAMP_BASE_URL or pass --lamp-url.",
            )
        )

    token = config.bridge_token.strip()
    if token:
        results.append(
            run_http_check(
                phase="online",
                name="bridge auth scenes",
                url=f"{bridge_url}/v1/mira-light/scenes",
                timeout_seconds=config.timeout_seconds,
                strict_online=config.strict_online,
                headers={"Authorization": f"Bearer {token}"},
                validator=validate_bridge_scenes,
                failure_hint="Check MIRA_LIGHT_BRIDGE_TOKEN and make sure the bridge accepts the same token.",
            )
        )
    else:
        results.append(
            http_result(
                strict_online=config.strict_online,
                phase="online",
                name="bridge auth scenes",
                detail="bridge token is empty; skipping authenticated bridge probe",
                hint="Export MIRA_LIGHT_BRIDGE_TOKEN or pass --bridge-token.",
            )
        )

    return results


def print_results(results: list[CheckResult]) -> None:
    for result in results:
        print(f"[{result.phase}] {result.status:<4} {result.name}: {result.detail}")
        if result.hint:
            print(f"  hint: {result.hint}")


def summarize(results: list[CheckResult]) -> None:
    pass_count = sum(result.status == "PASS" for result in results)
    warn_count = sum(result.status == "WARN" for result in results)
    fail_count = sum(result.status == "FAIL" for result in results)
    print(f"[preflight] summary pass={pass_count} warn={warn_count} fail={fail_count}")


def build_config(args: argparse.Namespace) -> PreflightConfig:
    return PreflightConfig(
        release_root=Path(__file__).resolve().parents[1],
        bridge_base_url=normalize_base_url(args.bridge_url),
        receiver_base_url=normalize_base_url(args.receiver_url or DEFAULT_RECEIVER_BASE_URL),
        lamp_base_url=normalize_base_url(args.lamp_url),
        bridge_token=args.bridge_token,
        timeout_seconds=args.timeout,
        strict_online=args.strict_online,
    )


def main() -> int:
    parser = build_parser()
    args = parser.parse_args()
    config = build_config(args)
    print(f"[preflight] mode={args.mode} strict_online={config.strict_online}")
    print(f"[preflight] release root={config.release_root}")

    results: list[CheckResult] = []
    if args.mode in {"offline", "all"}:
        results.extend(run_offline_checks(config))
    if args.mode in {"online", "all"}:
        results.extend(run_online_checks(config))

    print_results(results)
    summarize(results)
    return 1 if any(result.status == "FAIL" for result in results) else 0


if __name__ == "__main__":
    raise SystemExit(main())
