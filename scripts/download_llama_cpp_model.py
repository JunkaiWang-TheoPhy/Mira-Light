#!/usr/bin/env python3
"""Download official Qwen GGUF files for llama.cpp with resume support."""

from __future__ import annotations

import argparse
import json
import os
from pathlib import Path
import sys
from typing import Any

from download_mlx_model import (
    DEFAULT_CHUNK_SIZE,
    DEFAULT_MAX_RETRIES,
    DEFAULT_TIMEOUT_SECONDS,
    DownloadError,
    HUGGING_FACE_API_BASE_URL,
    HUGGING_FACE_BASE_URL,
    SnapshotInfo,
    build_file_url,
    collect_remote_file_info,
    download_file,
    ensure_disk_headroom,
    fetch_snapshot_info,
    human_bytes,
    slugify_repo_id,
    verify_local_snapshot,
)


MANIFEST_FILENAME = "mira-light-llama-cpp-download-manifest.json"
MODEL_PRESETS: dict[str, dict[str, Any]] = {
    "qwen2.5-3b": {
        "repo": "Qwen/Qwen2.5-3B-Instruct-GGUF",
        "base_name": "qwen2.5-3b-instruct",
        "default_quant": "q4_k_m",
        "description": "Official Qwen GGUF preset for the fastest local llama.cpp path.",
    },
    "qwen2.5-7b": {
        "repo": "Qwen/Qwen2.5-7B-Instruct-GGUF",
        "base_name": "qwen2.5-7b-instruct",
        "default_quant": "q4_k_m",
        "description": "Official Qwen GGUF preset with better quality and larger memory use.",
    },
}
META_FILENAMES = ("README.md", "LICENSE")


def default_model_root() -> Path:
    override = os.environ.get("MIRA_LIGHT_LLAMA_CPP_MODEL_ROOT")
    if override:
        return Path(override).expanduser()
    if sys.platform == "darwin":
        return Path.home() / "Library" / "Caches" / "Mira-Light" / "llama-cpp-models"
    xdg_cache = os.environ.get("XDG_CACHE_HOME")
    if xdg_cache:
        return Path(xdg_cache) / "mira-light" / "llama-cpp-models"
    return Path.home() / ".cache" / "mira-light" / "llama-cpp-models"


def manifest_path_for(destination_dir: Path) -> Path:
    return destination_dir / MANIFEST_FILENAME


def resolve_output_dir(*, output_dir: str | None, dest_root: str | None, repo_id: str) -> Path:
    if output_dir:
        return Path(output_dir).expanduser()
    base = Path(dest_root).expanduser() if dest_root else default_model_root()
    return base / slugify_repo_id(repo_id)


def resolve_repo_id(args: argparse.Namespace) -> str:
    if args.repo:
        return args.repo
    preset = MODEL_PRESETS.get(args.model)
    if not preset:
        raise DownloadError(f"Unsupported model preset: {args.model}")
    return str(preset["repo"])


def print_presets() -> None:
    for name, config in sorted(MODEL_PRESETS.items()):
        print(f"{name}: {config['repo']}")
        print(f"  default quant: {config['default_quant']}")
        print(f"  {config['description']}")


def resolve_quant(args: argparse.Namespace) -> str:
    if args.quant:
        return args.quant.lower()
    preset = MODEL_PRESETS.get(args.model)
    if not preset:
        raise DownloadError(f"Unsupported model preset: {args.model}")
    return str(preset["default_quant"])


def select_model_filenames(snapshot: SnapshotInfo, *, base_name: str, quant: str) -> tuple[str, ...]:
    prefix = f"{base_name}-{quant}"
    matches = tuple(
        filename
        for filename in snapshot.files
        if filename.startswith(prefix) and filename.endswith(".gguf")
    )
    if not matches:
        available = sorted(
            filename for filename in snapshot.files if filename.startswith(base_name) and filename.endswith(".gguf")
        )
        raise DownloadError(
            f"No GGUF files found for quant '{quant}' in {snapshot.repo_id}. "
            f"Available files: {', '.join(available[:20])}"
        )
    return tuple(sorted(matches))


def build_target_snapshot(snapshot: SnapshotInfo, *, selected_files: tuple[str, ...]) -> SnapshotInfo:
    extra_meta = tuple(filename for filename in META_FILENAMES if filename in snapshot.files)
    combined_files = tuple(sorted(dict.fromkeys(selected_files + extra_meta)))
    return SnapshotInfo(
        repo_id=snapshot.repo_id,
        revision=snapshot.revision,
        used_storage=snapshot.used_storage,
        files=combined_files,
    )


def write_manifest(
    destination_dir: Path,
    *,
    snapshot: SnapshotInfo,
    files: list[dict[str, Any]],
    quant: str,
    entry_filename: str,
) -> Path:
    payload = {
        "repoId": snapshot.repo_id,
        "revision": snapshot.revision,
        "quant": quant,
        "entryFilename": entry_filename,
        "estimatedBytes": snapshot.used_storage,
        "files": files,
    }
    manifest_path = manifest_path_for(destination_dir)
    manifest_path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return manifest_path


def resolve_entry_filename(model_files: tuple[str, ...]) -> str:
    gguf_files = tuple(filename for filename in model_files if filename.endswith(".gguf"))
    if not gguf_files:
        raise DownloadError("No GGUF files were selected.")
    return sorted(gguf_files)[0]


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Download official Qwen GGUF files for llama.cpp with resume and verify support.",
    )
    parser.add_argument(
        "--model",
        default="qwen2.5-3b",
        choices=sorted(MODEL_PRESETS),
        help="Named official Qwen GGUF preset to fetch.",
    )
    parser.add_argument("--quant", help="GGUF quantization name, for example q4_k_m or q8_0.")
    parser.add_argument("--repo", help="Override the Hugging Face repo id, for example Qwen/Qwen2.5-3B-Instruct-GGUF.")
    parser.add_argument("--base-name", help="Override the GGUF filename base, for example qwen2.5-3b-instruct.")
    parser.add_argument("--dest-root", help="Root directory for downloaded models. Defaults to a Mira-Light cache path.")
    parser.add_argument("--output-dir", help="Exact output directory for this snapshot. Overrides --dest-root.")
    parser.add_argument("--token", default=os.environ.get("HF_TOKEN"), help="Optional Hugging Face token.")
    parser.add_argument("--timeout-seconds", type=float, default=DEFAULT_TIMEOUT_SECONDS, help="Per-request timeout.")
    parser.add_argument("--chunk-size-mb", type=int, default=1, help="Streaming chunk size in MiB.")
    parser.add_argument("--max-retries", type=int, default=DEFAULT_MAX_RETRIES, help="Retries for interrupted downloads.")
    parser.add_argument("--force", action="store_true", help="Delete any existing local copy and download again.")
    parser.add_argument("--dry-run", action="store_true", help="Resolve repo and selected files without downloading.")
    parser.add_argument("--verify", action="store_true", help="Verify local files against the remote selection and exit.")
    parser.add_argument("--list-presets", action="store_true", help="Print built-in Qwen GGUF presets and exit.")
    parser.add_argument("--skip-space-check", action="store_true", help="Skip the free-disk-space guard.")
    parser.add_argument("--base-url", default=HUGGING_FACE_BASE_URL, help=argparse.SUPPRESS)
    parser.add_argument("--api-base-url", default=HUGGING_FACE_API_BASE_URL, help=argparse.SUPPRESS)
    return parser


def main() -> int:
    parser = build_parser()
    args = parser.parse_args()

    if args.list_presets:
        print_presets()
        return 0

    repo_id = resolve_repo_id(args)
    base_name = args.base_name or str(MODEL_PRESETS.get(args.model, {}).get("base_name") or "")
    if not base_name:
        raise DownloadError("A base model filename is required.")
    quant = resolve_quant(args)

    raw_snapshot = fetch_snapshot_info(
        repo_id,
        api_base_url=args.api_base_url,
        token=args.token,
        timeout_seconds=args.timeout_seconds,
    )
    model_files = select_model_filenames(raw_snapshot, base_name=base_name, quant=quant)
    snapshot = build_target_snapshot(raw_snapshot, selected_files=model_files)
    destination_dir = resolve_output_dir(output_dir=args.output_dir, dest_root=args.dest_root, repo_id=repo_id)
    entry_filename = resolve_entry_filename(model_files)

    print(f"[model] repo: {snapshot.repo_id}")
    print(f"[model] revision: {snapshot.revision}")
    print(f"[model] quant: {quant}")
    print(f"[model] output dir: {destination_dir}")
    print(f"[model] entry file: {entry_filename}")
    print(f"[model] selected files: {len(snapshot.files)}")

    if args.dry_run:
        for filename in snapshot.files:
            print(f"  - {filename}")
        return 0

    remote_info_by_file = collect_remote_file_info(
        snapshot,
        base_url=args.base_url,
        token=args.token,
        timeout_seconds=args.timeout_seconds,
    )

    if args.verify:
        issues = verify_local_snapshot(
            destination_dir,
            snapshot,
            base_url=args.base_url,
            token=args.token,
            timeout_seconds=args.timeout_seconds,
            remote_info_by_file=remote_info_by_file,
        )
        if issues:
            print("[verify] snapshot is incomplete:", flush=True)
            for issue in issues:
                print(f"  - {issue}", flush=True)
            return 1
        print(f"[verify] snapshot is complete at {destination_dir}", flush=True)
        return 0

    if not args.skip_space_check:
        ensure_disk_headroom(destination_dir, snapshot)

    destination_dir.mkdir(parents=True, exist_ok=True)
    file_results: list[dict[str, Any]] = []
    chunk_size = max(1, args.chunk_size_mb) * (1 << 20)

    for filename in snapshot.files:
        remote = remote_info_by_file.get(filename)
        result = download_file(
            url=build_file_url(snapshot.repo_id, filename, base_url=args.base_url, revision=snapshot.revision),
            destination=destination_dir / filename,
            token=args.token,
            timeout_seconds=args.timeout_seconds,
            chunk_size=chunk_size,
            max_retries=max(0, args.max_retries),
            force=args.force,
            expected_size=remote.total_size if remote else None,
        )
        result["filename"] = filename
        file_results.append(result)

    manifest_path = write_manifest(
        destination_dir,
        snapshot=snapshot,
        files=file_results,
        quant=quant,
        entry_filename=entry_filename,
    )

    issues = verify_local_snapshot(
        destination_dir,
        snapshot,
        base_url=args.base_url,
        token=args.token,
        timeout_seconds=args.timeout_seconds,
        remote_info_by_file=remote_info_by_file,
    )
    if issues:
        print("[verify] downloaded files still have issues:", flush=True)
        for issue in issues:
            print(f"  - {issue}", flush=True)
        return 1

    total_bytes = sum(item.get("bytes", 0) for item in file_results if isinstance(item.get("bytes"), int))
    print(f"[done] llama.cpp model available at {destination_dir}")
    print(f"[done] downloaded size: {human_bytes(total_bytes)}")
    print(f"[done] manifest written to {manifest_path}")
    print(f"[next] python3 scripts/smoke_test_llama_cpp.py --model-dir {destination_dir} --model-file {entry_filename}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
