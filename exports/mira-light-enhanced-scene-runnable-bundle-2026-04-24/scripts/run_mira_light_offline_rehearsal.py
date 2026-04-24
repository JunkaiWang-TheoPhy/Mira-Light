#!/usr/bin/env python3
"""One-click offline rehearsal entry for the Mira Light stack."""

from __future__ import annotations

import argparse
from dataclasses import dataclass
from datetime import datetime, timezone
import html
import json
import os
from pathlib import Path
import signal
import subprocess
import sys
import time
from typing import Any
from urllib.error import URLError
from urllib.request import urlopen


ROOT = Path(__file__).resolve().parents[1]


def now() -> datetime:
    return datetime.now(timezone.utc).astimezone()


def now_iso() -> str:
    return now().isoformat(timespec="seconds")


def timestamp_slug() -> str:
    return now().strftime("%Y-%m-%dT%H-%M-%S")


def resolve_path(value: str | Path, *, base: Path) -> Path:
    raw = Path(str(value)).expanduser()
    if raw.is_absolute():
        return raw
    return (base / raw).resolve()


def resolve_exec_path(value: str | Path, *, base: Path) -> Path:
    raw = Path(str(value)).expanduser()
    if raw.is_absolute():
        return raw
    return (base / raw).absolute()


@dataclass
class StepResult:
    name: str
    ok: bool
    command: list[str] | None
    started_at: str
    finished_at: str
    duration_ms: int
    log_path: str | None = None
    details: dict[str, Any] | None = None

    def as_dict(self) -> dict[str, Any]:
        payload = {
            "name": self.name,
            "ok": self.ok,
            "command": self.command,
            "startedAt": self.started_at,
            "finishedAt": self.finished_at,
            "durationMs": self.duration_ms,
            "logPath": self.log_path,
        }
        if self.details:
            payload["details"] = self.details
        return payload


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Run the Mira Light one-click offline rehearsal.")
    parser.add_argument("--mode", default="quick", help="Mode from config: quick, full, fault, interactive.")
    parser.add_argument(
        "--config",
        type=Path,
        default=Path("./config/mira_light_offline_rehearsal.json"),
        help="Offline rehearsal config JSON.",
    )
    parser.add_argument("--scene", help="Override the traced scene id.")
    parser.add_argument("--workspace", type=Path, help="Override the workspace path for memory/persona eval.")
    parser.add_argument("--fault-file", type=Path, help="Override the fault file used in fault mode.")
    parser.add_argument("--keep-mock-running", action="store_true", help="Do not stop the mock device on exit.")
    parser.add_argument("--skip-memory-persona", action="store_true", help="Skip the memory/persona evaluation step.")
    parser.add_argument("--skip-tests", action="store_true", help="Skip the unittest step.")
    parser.add_argument("--skip-scene-trace", action="store_true", help="Skip the scene trace step.")
    parser.add_argument("--skip-vision-replay", action="store_true", help="Skip the vision replay step.")
    return parser


def load_config(path: Path) -> dict[str, Any]:
    resolved = resolve_path(path, base=ROOT)
    return json.loads(resolved.read_text(encoding="utf-8"))


def wait_for_health(url: str, *, timeout_seconds: float, poll_seconds: float) -> None:
    deadline = time.monotonic() + timeout_seconds
    last_error = None
    while time.monotonic() < deadline:
        try:
            with urlopen(url, timeout=1.0) as response:  # noqa: S310 - local loopback
                if response.status == 200:
                    return
        except (OSError, URLError) as exc:
            last_error = exc
        time.sleep(poll_seconds)
    raise RuntimeError(f"Mock device did not become healthy at {url}: {last_error}")


def run_command(command: list[str], *, cwd: Path, log_path: Path, env: dict[str, str] | None = None) -> StepResult:
    started = time.monotonic()
    started_at = now_iso()
    result = subprocess.run(
        command,
        cwd=cwd,
        capture_output=True,
        text=True,
        env=env,
        check=False,
    )
    finished_at = now_iso()
    duration_ms = int(round((time.monotonic() - started) * 1000))
    combined = []
    if result.stdout:
        combined.append(result.stdout.rstrip())
    if result.stderr:
        combined.append(result.stderr.rstrip())
    log_path.parent.mkdir(parents=True, exist_ok=True)
    log_path.write_text("\n\n".join(combined).strip() + ("\n" if combined else ""), encoding="utf-8")
    if result.returncode != 0:
        raise RuntimeError(
            f"Command failed with exit code {result.returncode}: {' '.join(command)}\n"
            f"See log: {log_path}"
        )
    return StepResult(
        name=log_path.stem,
        ok=True,
        command=command,
        started_at=started_at,
        finished_at=finished_at,
        duration_ms=duration_ms,
        log_path=str(log_path),
    )


def parse_json_file(path: Path) -> dict[str, Any] | None:
    if not path.exists():
        return None
    return json.loads(path.read_text(encoding="utf-8"))


def render_index_html(summary: dict[str, Any]) -> str:
    rows = []
    for step in summary["steps"]:
        details = html.escape(json.dumps(step.get("details", {}), ensure_ascii=False, indent=2))
        command = html.escape(" ".join(step.get("command") or []))
        log_path = step.get("logPath")
        log_html = f'<a href="{html.escape(Path(log_path).name)}">{html.escape(Path(log_path).name)}</a>' if log_path else "n/a"
        rows.append(
            "<tr>"
            f"<td>{html.escape(step['name'])}</td>"
            f"<td>{'ok' if step['ok'] else 'failed'}</td>"
            f"<td>{step['durationMs']} ms</td>"
            f"<td><code>{command}</code></td>"
            f"<td>{log_html}</td>"
            f"<td><pre>{details}</pre></td>"
            "</tr>"
        )

    artifact_rows = []
    for label, path in sorted(summary.get("artifacts", {}).items()):
        artifact_rows.append(
            f"<li><a href=\"{html.escape(path)}\">{html.escape(label)}</a></li>"
        )

    return f"""<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <title>Mira Light Offline Rehearsal</title>
  <style>
    :root {{
      color-scheme: light;
      --bg: #f4efe7;
      --panel: rgba(255, 251, 246, 0.92);
      --ink: #2b241c;
      --line: #ddd0c1;
      --accent: #8b4b23;
      --ok: #1f7a4c;
      --bad: #a53434;
    }}
    body {{
      margin: 0;
      padding: 28px;
      background: linear-gradient(180deg, #efe5d6 0%, var(--bg) 100%);
      color: var(--ink);
      font-family: "Iowan Old Style", "Palatino Linotype", serif;
    }}
    main {{
      max-width: 1180px;
      margin: 0 auto;
      display: grid;
      gap: 18px;
    }}
    section {{
      background: var(--panel);
      border: 1px solid var(--line);
      border-radius: 18px;
      padding: 20px 24px;
      box-shadow: 0 14px 34px rgba(90, 54, 24, 0.08);
    }}
    h1, h2 {{
      margin: 0 0 12px;
    }}
    h1 {{
      color: var(--accent);
      font-size: 32px;
    }}
    .meta {{
      display: grid;
      grid-template-columns: repeat(auto-fit, minmax(180px, 1fr));
      gap: 12px;
    }}
    .card {{
      background: rgba(255,255,255,0.7);
      border: 1px solid var(--line);
      border-radius: 14px;
      padding: 12px 14px;
    }}
    table {{
      width: 100%;
      border-collapse: collapse;
      font-size: 13px;
    }}
    th, td {{
      text-align: left;
      vertical-align: top;
      padding: 10px;
      border-top: 1px solid var(--line);
    }}
    code, pre {{
      font-family: ui-monospace, SFMono-Regular, Menlo, monospace;
      white-space: pre-wrap;
      word-break: break-word;
      margin: 0;
    }}
  </style>
</head>
<body>
  <main>
    <section>
      <h1>Mira Light Offline Rehearsal</h1>
      <div class="meta">
        <div class="card"><strong>Mode</strong><div>{html.escape(summary['mode'])}</div></div>
        <div class="card"><strong>Started</strong><div>{html.escape(summary['startedAt'])}</div></div>
        <div class="card"><strong>Finished</strong><div>{html.escape(summary['finishedAt'])}</div></div>
        <div class="card"><strong>Run Dir</strong><div>{html.escape(summary['runDir'])}</div></div>
      </div>
    </section>
    <section>
      <h2>Artifacts</h2>
      <ul>
        {''.join(artifact_rows)}
      </ul>
    </section>
    <section>
      <h2>Steps</h2>
      <table>
        <thead>
          <tr><th>step</th><th>status</th><th>duration</th><th>command</th><th>log</th><th>details</th></tr>
        </thead>
        <tbody>
          {''.join(rows)}
        </tbody>
      </table>
    </section>
  </main>
</body>
</html>
"""


def write_summary(run_dir: Path, summary: dict[str, Any]) -> None:
    summary_path = run_dir / "summary.json"
    summary_path.write_text(json.dumps(summary, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    index_path = run_dir / "index.html"
    index_path.write_text(render_index_html(summary), encoding="utf-8")


def relative_artifact(path: Path, *, run_dir: Path) -> str:
    try:
        return str(path.resolve().relative_to(run_dir.resolve()))
    except ValueError:
        return str(path.resolve())


def build_run_dir(config: dict[str, Any], *, mode: str) -> Path:
    runtime_root = resolve_path(config["runtimeRoot"], base=ROOT)
    run_dir = runtime_root / f"{timestamp_slug()}-{mode}"
    run_dir.mkdir(parents=True, exist_ok=True)
    return run_dir


def build_python_path(config: dict[str, Any]) -> Path:
    return resolve_exec_path(config["pythonPath"], base=ROOT)


def start_mock_device(
    *,
    python_path: Path,
    config: dict[str, Any],
    run_dir: Path,
    fault_file: Path | None,
) -> tuple[subprocess.Popen[str], Any, dict[str, Any]]:
    mock_cfg = config["mockDevice"]
    host = str(mock_cfg["host"])
    port = int(mock_cfg["port"])
    base_url = f"http://{host}:{port}"

    request_log_path = run_dir / "mock-device.requests.jsonl"
    state_out_path = run_dir / "mock-device.state.json"
    log_path = run_dir / "mock-device.log"
    log_handle = log_path.open("w", encoding="utf-8")

    command = [
        str(python_path),
        str(ROOT / "scripts" / "mock_mira_light_device.py"),
        "--host",
        host,
        "--port",
        str(port),
        "--request-log-out",
        str(request_log_path),
        "--state-out",
        str(state_out_path),
    ]
    if fault_file is not None:
        command.extend(["--fault-file", str(fault_file)])

    process = subprocess.Popen(
        command,
        cwd=ROOT,
        stdout=log_handle,
        stderr=subprocess.STDOUT,
        text=True,
    )
    try:
        wait_for_health(
            f"{base_url}/health",
            timeout_seconds=float(mock_cfg["startupTimeoutSeconds"]),
            poll_seconds=float(mock_cfg["healthPollSeconds"]),
        )
    except Exception:
        log_handle.flush()
        raise

    details = {
        "baseUrl": base_url,
        "requestLogPath": str(request_log_path),
        "statePath": str(state_out_path),
        "logPath": str(log_path),
        "faultFile": str(fault_file) if fault_file else None,
    }
    return process, log_handle, details


def stop_mock_device(process: subprocess.Popen[str] | None, log_handle: Any) -> None:
    if process is None:
        return
    if process.poll() is None:
        process.terminate()
        try:
            process.wait(timeout=5)
        except subprocess.TimeoutExpired:
            process.kill()
            process.wait(timeout=5)
    if log_handle is not None:
        log_handle.close()


def main() -> int:
    args = build_parser().parse_args()
    config = load_config(args.config)
    mode_config = (config.get("modes") or {}).get(args.mode)
    if not mode_config:
        raise SystemExit(f"Unknown mode: {args.mode}")

    python_path = build_python_path(config)
    if not python_path.exists():
        raise SystemExit(f"Python path not found: {python_path}")

    run_dir = build_run_dir(config, mode=args.mode)
    started_at = now_iso()
    steps: list[dict[str, Any]] = []
    artifacts: dict[str, str] = {}

    fault_value = args.fault_file
    if fault_value is None and mode_config.get("faultFile"):
        fault_value = Path(str(mode_config["faultFile"]))
    fault_file = resolve_path(fault_value, base=ROOT) if fault_value else None

    mock_process = None
    mock_handle = None
    mock_details = None

    try:
        mock_process, mock_handle, mock_details = start_mock_device(
            python_path=python_path,
            config=config,
            run_dir=run_dir,
            fault_file=fault_file,
        )
        artifacts["mock-device-log"] = relative_artifact(Path(mock_details["logPath"]), run_dir=run_dir)
        artifacts["mock-device-state"] = relative_artifact(Path(mock_details["statePath"]), run_dir=run_dir)
        artifacts["mock-device-requests"] = relative_artifact(Path(mock_details["requestLogPath"]), run_dir=run_dir)
        steps.append(
            StepResult(
                name="mock-device",
                ok=True,
                command=None,
                started_at=started_at,
                finished_at=now_iso(),
                duration_ms=0,
                log_path=mock_details["logPath"],
                details=mock_details,
            ).as_dict()
        )

        if mode_config.get("interactive"):
            instructions_path = run_dir / "interactive-instructions.txt"
            instructions_path.write_text(
                "\n".join(
                    [
                        f"Mock base URL: {mock_details['baseUrl']}",
                        f"Mock log: {mock_details['logPath']}",
                        f"Mock state: {mock_details['statePath']}",
                        "Press Ctrl-C to stop the interactive rehearsal.",
                    ]
                )
                + "\n",
                encoding="utf-8",
            )
            artifacts["interactive-instructions"] = relative_artifact(instructions_path, run_dir=run_dir)
            summary = {
                "mode": args.mode,
                "startedAt": started_at,
                "finishedAt": now_iso(),
                "runDir": str(run_dir),
                "artifacts": artifacts,
                "steps": steps,
            }
            write_summary(run_dir, summary)
            print(json.dumps(summary, ensure_ascii=False, indent=2))
            print("Interactive mock device is running. Press Ctrl-C to stop.")
            while True:
                time.sleep(1.0)

        if mode_config.get("tests") and not args.skip_tests:
            test_log = run_dir / "tests.log"
            step = run_command(
                [str(python_path), "-m", "unittest", *mode_config["tests"]],
                cwd=ROOT,
                log_path=test_log,
            )
            step.name = "tests"
            steps.append(step.as_dict())
            artifacts["tests-log"] = relative_artifact(test_log, run_dir=run_dir)

        if mode_config.get("sceneTrace") and not args.skip_scene_trace:
            scene_name = args.scene or config["sceneTrace"]["scene"]
            trace_dir = run_dir / "scene-traces"
            trace_log = run_dir / "scene-trace.log"
            command = [
                str(python_path),
                str(ROOT / "scripts" / "scene_trace_recorder.py"),
                scene_name,
                "--base-url",
                mock_details["baseUrl"],
                "--out-dir",
                str(trace_dir),
            ]
            if config["sceneTrace"].get("skipDelays", False):
                command.append("--skip-delays")
            step = run_command(command, cwd=ROOT, log_path=trace_log)
            step.name = "scene-trace"
            step.details = {
                "scene": scene_name,
                "traceJson": str(trace_dir / f"{scene_name}.trace.json"),
                "traceHtml": str(trace_dir / f"{scene_name}.trace.html"),
            }
            steps.append(step.as_dict())
            artifacts["scene-trace-log"] = relative_artifact(trace_log, run_dir=run_dir)
            artifacts["scene-trace-json"] = relative_artifact(trace_dir / f"{scene_name}.trace.json", run_dir=run_dir)
            artifacts["scene-trace-html"] = relative_artifact(trace_dir / f"{scene_name}.trace.html", run_dir=run_dir)

        if mode_config.get("visionReplay") and not args.skip_vision_replay:
            replay_cfg = config["visionReplay"]
            replay_log = run_dir / "vision-replay.log"
            captures_dir = run_dir / "vision-demo-captures"
            replay_dir = run_dir / "vision-replay"
            command = [
                str(python_path),
                str(ROOT / "scripts" / "vision_replay_bench.py"),
                "--captures-dir",
                str(captures_dir),
                "--out-dir",
                str(replay_dir),
                "--base-url",
                mock_details["baseUrl"],
                "--frame-spacing-ms",
                str(replay_cfg["frameSpacingMs"]),
                "--scene-cooldown-ms",
                str(replay_cfg["sceneCooldownMs"]),
                "--wake-up-cooldown-ms",
                str(replay_cfg["wakeUpCooldownMs"]),
                "--sleep-grace-ms",
                str(replay_cfg["sleepGraceMs"]),
                "--warmup-frames",
                str(replay_cfg["warmupFrames"]),
            ]
            if replay_cfg.get("allowExperimental", False):
                command.append("--allow-experimental")
            if replay_cfg.get("generateSyntheticDemo", False):
                command.append("--generate-synthetic-demo")
            if replay_cfg.get("dryRun", False):
                command.append("--dry-run")
            step = run_command(command, cwd=ROOT, log_path=replay_log)
            step.name = "vision-replay"
            step.details = {
                "reportPath": str(replay_dir / "vision.replay.report.json"),
                "latestEventPath": str(replay_dir / "vision.latest.json"),
                "bridgeStatePath": str(replay_dir / "vision.bridge.state.json"),
            }
            steps.append(step.as_dict())
            artifacts["vision-replay-log"] = relative_artifact(replay_log, run_dir=run_dir)
            artifacts["vision-replay-report"] = relative_artifact(replay_dir / "vision.replay.report.json", run_dir=run_dir)
            artifacts["vision-latest"] = relative_artifact(replay_dir / "vision.latest.json", run_dir=run_dir)
            artifacts["vision-bridge-state"] = relative_artifact(replay_dir / "vision.bridge.state.json", run_dir=run_dir)

        if mode_config.get("memoryPersonaEval") and not args.skip_memory_persona:
            eval_cfg = config["memoryPersonaEval"]
            eval_log = run_dir / "memory-persona-eval.log"
            eval_output = run_dir / "mira-memory-persona-eval.json"
            workspace = resolve_path(args.workspace or eval_cfg["workspace"], base=ROOT)
            command = [
                str(python_path),
                str(ROOT / "scripts" / "mira_memory_persona_eval.py"),
                "--workspace",
                str(workspace),
                "--config",
                str(resolve_path(eval_cfg["config"], base=ROOT)),
                "--out",
                str(eval_output),
            ]
            skip_agent_prompts = bool(mode_config.get("memoryPersonaEvalSkipAgentPrompts", eval_cfg.get("skipAgentPrompts", False)))
            if skip_agent_prompts:
                command.append("--skip-agent-prompts")
            step = run_command(command, cwd=ROOT, log_path=eval_log, env={**os.environ})
            step.name = "memory-persona-eval"
            parsed = parse_json_file(eval_output) or {}
            step.details = {
                "workspace": str(workspace),
                "reportPath": str(eval_output),
                "passed": (parsed.get("counts") or {}).get("passed"),
                "failed": (parsed.get("counts") or {}).get("failed"),
                "skipAgentPrompts": skip_agent_prompts,
            }
            steps.append(step.as_dict())
            artifacts["memory-persona-log"] = relative_artifact(eval_log, run_dir=run_dir)
            artifacts["memory-persona-report"] = relative_artifact(eval_output, run_dir=run_dir)

        finished_at = now_iso()
        summary = {
            "mode": args.mode,
            "startedAt": started_at,
            "finishedAt": finished_at,
            "runDir": str(run_dir),
            "artifacts": artifacts,
            "steps": steps,
            "description": mode_config.get("description"),
        }
        write_summary(run_dir, summary)
        print(json.dumps(summary, ensure_ascii=False, indent=2))
        return 0
    except KeyboardInterrupt:
        print("\nOffline rehearsal interrupted.", file=sys.stderr)
        return 130
    finally:
        if not args.keep_mock_running:
            stop_mock_device(mock_process, mock_handle)


if __name__ == "__main__":
    raise SystemExit(main())
