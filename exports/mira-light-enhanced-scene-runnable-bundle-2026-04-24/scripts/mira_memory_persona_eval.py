#!/usr/bin/env python3
"""Evaluate Mira memory retrieval and persona behavior."""

from __future__ import annotations

import argparse
from dataclasses import dataclass
import json
from pathlib import Path
import subprocess
import sys
from typing import Any


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Run memory and persona checks for Mira.")
    parser.add_argument(
        "--config",
        type=Path,
        default=Path("./config/mira_memory_persona_eval.json"),
        help="Evaluation config JSON.",
    )
    parser.add_argument(
        "--workspace",
        type=Path,
        default=Path("~/.openclaw/workspace"),
        help="Workspace root for AGENTS/SOUL/IDENTITY/TOOLS checks.",
    )
    parser.add_argument("--agent-id", default="main", help="OpenClaw agent id for local persona prompts.")
    parser.add_argument("--max-results", type=int, default=5, help="Max results per memory search.")
    parser.add_argument("--skip-agent-prompts", action="store_true", help="Only run retrieval/file checks.")
    parser.add_argument("--strict", action="store_true", help="Exit non-zero if any check fails.")
    parser.add_argument("--out", type=Path, help="Optional JSON report output path.")
    return parser


@dataclass
class EvalOutcome:
    check_id: str
    passed: bool
    details: dict[str, Any]

    def as_dict(self) -> dict[str, Any]:
        return {
            "id": self.check_id,
            "passed": self.passed,
            **self.details,
        }


def run_json_command(command: list[str], *, timeout_seconds: int = 120) -> dict[str, Any]:
    result = subprocess.run(
        command,
        capture_output=True,
        text=True,
        timeout=timeout_seconds,
        check=False,
    )
    if result.returncode != 0:
        raise RuntimeError(
            f"Command failed ({result.returncode}): {' '.join(command)}\n"
            f"stdout:\n{result.stdout}\n\nstderr:\n{result.stderr}"
        )

    candidates = [result.stdout.strip(), result.stderr.strip()]
    for candidate in candidates:
        if not candidate:
            continue
        try:
            return json.loads(candidate)
        except json.JSONDecodeError:
            continue

    raise RuntimeError(
        f"Command did not return valid JSON: {' '.join(command)}\n"
        f"stdout:\n{result.stdout}\n\nstderr:\n{result.stderr}"
    )


def contains_any(text: str, fragments: list[str]) -> bool:
    lowered = text.lower()
    return any(fragment.lower() in lowered for fragment in fragments)


def contains_all(text: str, fragments: list[str]) -> bool:
    lowered = text.lower()
    return all(fragment.lower() in lowered for fragment in fragments)


def evaluate_memory_query(item: dict[str, Any], *, max_results: int) -> EvalOutcome:
    payload = run_json_command(
        [
            "openclaw",
            "memory",
            "search",
            "--query",
            item["query"],
            "--max-results",
            str(max_results),
            "--json",
        ],
        timeout_seconds=120,
    )
    results = payload.get("results", [])
    combined_paths = "\n".join(str(result.get("path", "")) for result in results)
    combined_snippets = "\n".join(str(result.get("snippet", "")) for result in results)

    path_any = item.get("expectPathAny", [])
    snippet_any = item.get("expectSnippetAny", [])
    path_ok = True if not path_any else contains_any(combined_paths, path_any)
    snippet_ok = True if not snippet_any else contains_any(combined_snippets, snippet_any)

    return EvalOutcome(
        check_id=item["id"],
        passed=bool(path_ok and snippet_ok and results),
        details={
            "type": "memoryQuery",
            "query": item["query"],
            "resultCount": len(results),
            "matchedPathExpectation": path_ok,
            "matchedSnippetExpectation": snippet_ok,
            "topPaths": [result.get("path") for result in results[:3]],
        },
    )


def evaluate_persona_file(item: dict[str, Any], *, workspace: Path) -> EvalOutcome:
    file_path = (workspace / item["path"]).expanduser().resolve()
    text = file_path.read_text(encoding="utf-8")
    expect_any = item.get("expectAny", [])
    expect_all = item.get("expectAll", [])
    any_ok = True if not expect_any else contains_any(text, expect_any)
    all_ok = True if not expect_all else contains_all(text, expect_all)

    return EvalOutcome(
        check_id=item["id"],
        passed=bool(any_ok and all_ok),
        details={
            "type": "personaFile",
            "path": str(file_path),
            "matchedAnyExpectation": any_ok,
            "matchedAllExpectation": all_ok,
        },
    )


def extract_agent_text(payload: dict[str, Any]) -> str:
    texts = [str(item.get("text", "")) for item in payload.get("payloads", []) if item.get("text")]
    return "\n".join(texts).strip()


def evaluate_agent_prompt(item: dict[str, Any], *, agent_id: str) -> EvalOutcome:
    payload = run_json_command(
        [
            "openclaw",
            "agent",
            "--agent",
            agent_id,
            "--message",
            item["message"],
            "--local",
            "--json",
        ],
        timeout_seconds=180,
    )
    text = extract_agent_text(payload)
    expect_any = item.get("expectAny", [])
    expect_all = item.get("expectAll", [])
    any_ok = True if not expect_any else contains_any(text, expect_any)
    all_ok = True if not expect_all else contains_all(text, expect_all)
    agent_meta = ((payload.get("meta") or {}).get("agentMeta") or {})

    return EvalOutcome(
        check_id=item["id"],
        passed=bool(text and any_ok and all_ok),
        details={
            "type": "agentPrompt",
            "message": item["message"],
            "response": text,
            "matchedAnyExpectation": any_ok,
            "matchedAllExpectation": all_ok,
            "provider": agent_meta.get("provider"),
            "model": agent_meta.get("model"),
        },
    )


def run_eval(args: argparse.Namespace) -> dict[str, Any]:
    config = json.loads(args.config.expanduser().resolve().read_text(encoding="utf-8"))
    workspace = args.workspace.expanduser().resolve()

    outcomes: list[EvalOutcome] = []
    for item in config.get("memoryQueries", []):
        outcomes.append(evaluate_memory_query(item, max_results=args.max_results))

    for item in config.get("personaFileChecks", []):
        outcomes.append(evaluate_persona_file(item, workspace=workspace))

    if not args.skip_agent_prompts:
        for item in config.get("agentPrompts", []):
            outcomes.append(evaluate_agent_prompt(item, agent_id=args.agent_id))

    report = {
        "workspace": str(workspace),
        "config": str(args.config.expanduser().resolve()),
        "counts": {
            "total": len(outcomes),
            "passed": sum(1 for outcome in outcomes if outcome.passed),
            "failed": sum(1 for outcome in outcomes if not outcome.passed),
        },
        "results": [outcome.as_dict() for outcome in outcomes],
    }
    return report


def main() -> int:
    args = build_parser().parse_args()
    try:
        report = run_eval(args)
    except Exception as exc:  # noqa: BLE001
        print(json.dumps({"ok": False, "error": str(exc)}, ensure_ascii=False, indent=2), file=sys.stderr)
        return 1

    if args.out:
        out_path = args.out.expanduser().resolve()
        out_path.parent.mkdir(parents=True, exist_ok=True)
        out_path.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

    print(json.dumps(report, ensure_ascii=False, indent=2))
    if args.strict and report["counts"]["failed"]:
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
