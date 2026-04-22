#!/usr/bin/env python3
"""Record an offline timeline for one Mira Light scene."""

from __future__ import annotations

import argparse
from dataclasses import dataclass, field
import html
import json
from pathlib import Path
import time
from typing import Any

from mira_light_runtime import BoothController, MiraLightClient
from scenes import SCENE_META, SCENES


def now_ms(start_mono: float) -> float:
    return round((time.perf_counter() - start_mono) * 1000.0, 2)


@dataclass
class TraceBundle:
    scene_name: str
    scene_title: str
    started_at_monotonic: float
    timeline: list[dict[str, Any]] = field(default_factory=list)
    logs: list[dict[str, Any]] = field(default_factory=list)

    def push(self, kind: str, **fields: Any) -> None:
        self.timeline.append({"tMs": now_ms(self.started_at_monotonic), "kind": kind, **fields})

    def log(self, message: str) -> None:
        entry = {"tMs": now_ms(self.started_at_monotonic), "text": message}
        self.logs.append(entry)
        self.push("log", text=message)


class TracingMiraLightClient(MiraLightClient):
    def __init__(self, *, trace: TraceBundle, **kwargs: Any) -> None:
        super().__init__(**kwargs)
        self.trace = trace

    def _request(self, method: str, path: str, payload: dict[str, Any] | None = None) -> Any:
        started = time.perf_counter()
        try:
            response = super()._request(method, path, payload)
        except Exception as exc:  # noqa: BLE001
            self.trace.push(
                "request",
                method=method,
                path=path,
                payload=payload,
                durationMs=round((time.perf_counter() - started) * 1000.0, 2),
                outcome="error",
                error=str(exc),
            )
            raise

        self.trace.push(
            "request",
            method=method,
            path=path,
            payload=payload,
            durationMs=round((time.perf_counter() - started) * 1000.0, 2),
            outcome="ok",
            response=response,
        )
        return response


class FastBoothController(BoothController):
    def _sleep_ms(self, ms: int) -> None:
        self._log(f"[trace-skip-delay] {ms}ms")


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Record a timeline trace for one scene.")
    parser.add_argument("scene", help="Scene id from scripts/scenes.py")
    parser.add_argument("--out-dir", type=Path, default=Path("./runtime/scene-traces"), help="Output directory.")
    parser.add_argument("--base-url", default="http://127.0.0.1:9799", help="Lamp or mock device base URL.")
    parser.add_argument("--timeout-seconds", type=float, default=3.0, help="HTTP timeout for device requests.")
    parser.add_argument("--dry-run", action="store_true", help="Use runtime dry-run HTTP responses.")
    parser.add_argument("--skip-delays", action="store_true", help="Do not sleep on delay steps.")
    return parser


def render_trace_html(report: dict[str, Any]) -> str:
    scene = report["scene"]
    summary = report["summary"]
    rows = []
    for item in report["timeline"]:
        payload = html.escape(json.dumps(item, ensure_ascii=False, indent=2))
        rows.append(
            "<tr>"
            f"<td>{item['tMs']:.2f}</td>"
            f"<td>{html.escape(str(item['kind']))}</td>"
            f"<td><pre>{payload}</pre></td>"
            "</tr>"
        )

    return f"""<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <title>Scene Trace: {html.escape(scene['name'])}</title>
  <style>
    :root {{
      color-scheme: light;
      --bg: #f7f1e8;
      --panel: #fffaf4;
      --ink: #2c241c;
      --muted: #7e6f61;
      --line: #dfd1c1;
      --accent: #b5653b;
    }}
    body {{
      font-family: "Iowan Old Style", "Palatino Linotype", serif;
      background: linear-gradient(180deg, #f8efe1 0%, var(--bg) 100%);
      color: var(--ink);
      margin: 0;
      padding: 32px;
    }}
    main {{
      max-width: 1100px;
      margin: 0 auto;
      display: grid;
      gap: 20px;
    }}
    section {{
      background: rgba(255, 250, 244, 0.92);
      border: 1px solid var(--line);
      border-radius: 18px;
      padding: 20px 24px;
      box-shadow: 0 18px 40px rgba(130, 93, 61, 0.08);
    }}
    h1, h2 {{
      margin: 0 0 12px;
    }}
    h1 {{
      font-size: 32px;
      color: var(--accent);
    }}
    p {{
      margin: 8px 0;
      line-height: 1.55;
    }}
    .meta {{
      display: grid;
      grid-template-columns: repeat(auto-fit, minmax(180px, 1fr));
      gap: 12px;
    }}
    .card {{
      background: rgba(255,255,255,0.68);
      border: 1px solid var(--line);
      border-radius: 14px;
      padding: 14px;
    }}
    table {{
      width: 100%;
      border-collapse: collapse;
      font-family: ui-monospace, SFMono-Regular, Menlo, monospace;
      font-size: 12px;
    }}
    th, td {{
      vertical-align: top;
      text-align: left;
      padding: 10px;
      border-top: 1px solid var(--line);
    }}
    pre {{
      margin: 0;
      white-space: pre-wrap;
      word-break: break-word;
    }}
    .tag {{
      display: inline-block;
      padding: 3px 8px;
      border-radius: 999px;
      background: #f0dfcf;
      margin-right: 6px;
      margin-bottom: 6px;
      color: #7e4c28;
      font-size: 12px;
    }}
  </style>
</head>
<body>
  <main>
    <section>
      <h1>{html.escape(scene['title'])}</h1>
      <p>{html.escape(scene['hostLine'])}</p>
      <p><strong>Operator cue:</strong> {html.escape(scene['operatorCue'])}</p>
      <div>{"".join(f'<span class="tag">{html.escape(tag)}</span>' for tag in scene['emotionTags'])}</div>
    </section>
    <section>
      <h2>Summary</h2>
      <div class="meta">
        <div class="card"><strong>Duration</strong><p>{summary['durationMs']} ms</p></div>
        <div class="card"><strong>Steps</strong><p>{summary['stepCount']}</p></div>
        <div class="card"><strong>Requests</strong><p>{summary['requestCount']}</p></div>
        <div class="card"><strong>Dry Run</strong><p>{summary['dryRun']}</p></div>
      </div>
    </section>
    <section>
      <h2>Timeline</h2>
      <table>
        <thead>
          <tr><th>t (ms)</th><th>kind</th><th>payload</th></tr>
        </thead>
        <tbody>
          {"".join(rows)}
        </tbody>
      </table>
    </section>
  </main>
</body>
</html>
"""


def record_scene_trace(
    *,
    scene_name: str,
    out_dir: Path,
    base_url: str,
    timeout_seconds: float,
    dry_run: bool,
    skip_delays: bool,
) -> dict[str, Any]:
    if scene_name not in SCENES:
        raise KeyError(f"Unknown scene: {scene_name}")

    scene = SCENES[scene_name]
    meta = SCENE_META.get(scene_name, {})
    out_dir.mkdir(parents=True, exist_ok=True)

    trace = TraceBundle(scene_name=scene_name, scene_title=scene["title"], started_at_monotonic=time.perf_counter())
    trace.push("scene-start", scene=scene_name, title=scene["title"])

    client = TracingMiraLightClient(
        base_url=base_url,
        timeout_seconds=timeout_seconds,
        dry_run=dry_run,
        trace=trace,
    )

    controller_cls = FastBoothController if skip_delays else BoothController
    controller = controller_cls(
        client=client,
        emit=trace.log,
        on_step=lambda payload: trace.push("step", **payload),
    )

    error = None
    try:
        controller.run_scene(scene_name)
    except Exception as exc:  # noqa: BLE001
        error = str(exc)
        trace.push("scene-error", error=error)
        raise
    finally:
        trace.push("scene-finished", scene=scene_name, error=error)

    duration_ms = round(now_ms(trace.started_at_monotonic), 2)
    request_count = sum(1 for item in trace.timeline if item["kind"] == "request")
    report = {
        "scene": {
            "name": scene_name,
            "title": scene["title"],
            "hostLine": scene.get("host_line", ""),
            "emotionTags": meta.get("emotionTags", []),
            "operatorCue": meta.get("operatorCue", ""),
            "readiness": meta.get("readiness", "prototype"),
            "notes": scene.get("notes", []),
            "tuningNotes": scene.get("tuning_notes", []),
        },
        "summary": {
            "durationMs": duration_ms,
            "stepCount": len(scene.get("steps", [])),
            "requestCount": request_count,
            "dryRun": dry_run,
            "skipDelays": skip_delays,
            "baseUrl": base_url,
        },
        "timeline": trace.timeline,
        "logs": trace.logs,
    }

    json_path = out_dir / f"{scene_name}.trace.json"
    html_path = out_dir / f"{scene_name}.trace.html"
    json_path.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    html_path.write_text(render_trace_html(report), encoding="utf-8")
    return {"jsonPath": str(json_path), "htmlPath": str(html_path), "report": report}


def main() -> int:
    args = build_parser().parse_args()
    result = record_scene_trace(
        scene_name=args.scene,
        out_dir=args.out_dir.expanduser().resolve(),
        base_url=args.base_url,
        timeout_seconds=args.timeout_seconds,
        dry_run=args.dry_run,
        skip_delays=args.skip_delays,
    )
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
