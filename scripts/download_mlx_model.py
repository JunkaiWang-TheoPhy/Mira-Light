#!/usr/bin/env python3
"""Download MLX Hugging Face model snapshots with resume support."""

from __future__ import annotations

import argparse
import json
import os
import shutil
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
import sys
import time
from typing import Any
from urllib import error, parse, request


HUGGING_FACE_BASE_URL = "https://huggingface.co"
HUGGING_FACE_API_BASE_URL = "https://huggingface.co/api/models"
DEFAULT_TIMEOUT_SECONDS = 60.0
DEFAULT_CHUNK_SIZE = 1 << 20
DEFAULT_MAX_RETRIES = 8
DEFAULT_DISK_HEADROOM_BYTES = 1 << 30
MANIFEST_FILENAME = "mira-light-mlx-download-manifest.json"
SKIP_FILENAMES = {".gitattributes"}
MODEL_PRESETS: dict[str, dict[str, str]] = {
    "qwen2.5-3b": {
        "repo": "mlx-community/Qwen2.5-3B-Instruct-4bit",
        "description": "Fastest local Chinese-first default for Mira on this machine.",
    },
    "qwen2.5-7b": {
        "repo": "mlx-community/Qwen2.5-7B-Instruct-4bit",
        "description": "Stronger long-form and structured-output option once 3B is stable.",
    },
}


class DownloadError(RuntimeError):
    """Raised when a model or file download fails."""


@dataclass(frozen=True)
class SnapshotInfo:
    repo_id: str
    revision: str
    used_storage: int | None
    files: tuple[str, ...]


@dataclass(frozen=True)
class RemoteFileInfo:
    total_size: int | None
    etag: str | None


def utc_now_iso() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


def default_model_root() -> Path:
    override = os.environ.get("MIRA_LIGHT_MLX_MODEL_ROOT")
    if override:
        return Path(override).expanduser()
    if sys.platform == "darwin":
        return Path.home() / "Library" / "Caches" / "Mira-Light" / "mlx-models"
    xdg_cache = os.environ.get("XDG_CACHE_HOME")
    if xdg_cache:
        return Path(xdg_cache) / "mira-light" / "mlx-models"
    return Path.home() / ".cache" / "mira-light" / "mlx-models"


def human_bytes(value: int | None) -> str:
    if value is None:
        return "unknown"
    units = ("B", "KiB", "MiB", "GiB", "TiB")
    size = float(value)
    unit = 0
    while size >= 1024 and unit < len(units) - 1:
        size /= 1024
        unit += 1
    if unit == 0:
        return f"{int(size)} {units[unit]}"
    return f"{size:.1f} {units[unit]}"


def slugify_repo_id(repo_id: str) -> str:
    return repo_id.split("/")[-1]


def make_headers(*, token: str | None = None, range_start: int | None = None) -> dict[str, str]:
    headers = {
        "User-Agent": "Mira-Light-MLX-Downloader/1.0",
    }
    if token:
        headers["Authorization"] = f"Bearer {token}"
    if range_start is not None:
        headers["Range"] = f"bytes={range_start}-"
    return headers


def parse_total_size(response_headers: Any, *, existing_bytes: int) -> int | None:
    content_range = response_headers.get("Content-Range")
    if content_range and "/" in content_range:
        total = content_range.rsplit("/", 1)[-1].strip()
        if total.isdigit():
            return int(total)
    linked_size = response_headers.get("X-Linked-Size")
    if linked_size and linked_size.isdigit():
        return int(linked_size)
    content_length = response_headers.get("Content-Length")
    if content_length and content_length.isdigit():
        return int(content_length) + existing_bytes
    return None


def fetch_json(url: str, *, token: str | None = None, timeout_seconds: float = DEFAULT_TIMEOUT_SECONDS) -> dict[str, Any]:
    req = request.Request(url, headers=make_headers(token=token))
    with request.urlopen(req, timeout=timeout_seconds) as response:
        return json.load(response)


def fetch_snapshot_info(
    repo_id: str,
    *,
    api_base_url: str = HUGGING_FACE_API_BASE_URL,
    token: str | None = None,
    timeout_seconds: float = DEFAULT_TIMEOUT_SECONDS,
) -> SnapshotInfo:
    encoded_repo = parse.quote(repo_id, safe="/")
    payload = fetch_json(
        f"{api_base_url}/{encoded_repo}",
        token=token,
        timeout_seconds=timeout_seconds,
    )
    siblings = payload.get("siblings")
    if not isinstance(siblings, list):
        raise DownloadError(f"Unexpected Hugging Face payload for {repo_id}: missing siblings")
    files = tuple(
        item["rfilename"]
        for item in siblings
        if isinstance(item, dict)
        and isinstance(item.get("rfilename"), str)
        and item["rfilename"] not in SKIP_FILENAMES
    )
    if not files:
        raise DownloadError(f"No downloadable files found for {repo_id}")
    revision = str(payload.get("sha") or "main")
    used_storage = payload.get("usedStorage")
    return SnapshotInfo(
        repo_id=repo_id,
        revision=revision,
        used_storage=int(used_storage) if isinstance(used_storage, int) else None,
        files=tuple(sorted(files, key=file_priority_key)),
    )


def file_priority_key(filename: str) -> tuple[int, str]:
    if filename == "model.safetensors":
        return (0, filename)
    if filename.endswith(".index.json"):
        return (1, filename)
    if filename.endswith(".json"):
        return (2, filename)
    if filename.endswith(".txt"):
        return (3, filename)
    return (4, filename)


def build_file_url(repo_id: str, filename: str, *, base_url: str = HUGGING_FACE_BASE_URL, revision: str = "main") -> str:
    encoded_repo = parse.quote(repo_id, safe="/")
    encoded_filename = parse.quote(filename, safe="/")
    return f"{base_url}/{encoded_repo}/resolve/{revision}/{encoded_filename}"


def part_path_for(destination: Path) -> Path:
    return destination.parent / f"{destination.name}.part"


def ensure_parent_directory(path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)


def emit_progress(filename: str, downloaded: int, total: int | None, *, started_at: float, finished: bool = False) -> None:
    elapsed = max(time.monotonic() - started_at, 0.001)
    speed = downloaded / elapsed
    if total:
        percent = min(100.0, (downloaded / total) * 100)
        print(
            f"[download] {filename} {percent:5.1f}% "
            f"({human_bytes(downloaded)} / {human_bytes(total)}) at {human_bytes(int(speed))}/s"
            + (" [done]" if finished else ""),
            flush=True,
        )
        return
    print(
        f"[download] {filename} {human_bytes(downloaded)} at {human_bytes(int(speed))}/s"
        + (" [done]" if finished else ""),
        flush=True,
    )


def read_manifest(destination_dir: Path) -> dict[str, Any] | None:
    manifest_path = destination_dir / MANIFEST_FILENAME
    if not manifest_path.is_file():
        return None
    try:
        return json.loads(manifest_path.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        return None


def extract_remote_file_info(response_headers: Any, *, existing_bytes: int) -> RemoteFileInfo:
    return RemoteFileInfo(
        total_size=parse_total_size(response_headers, existing_bytes=existing_bytes),
        etag=response_headers.get("ETag") or response_headers.get("X-Linked-Etag") or response_headers.get("X-Linked-ETag"),
    )


def fetch_remote_file_info(
    url: str,
    *,
    token: str | None = None,
    timeout_seconds: float = DEFAULT_TIMEOUT_SECONDS,
) -> RemoteFileInfo:
    head_request = request.Request(url, headers=make_headers(token=token), method="HEAD")
    try:
        with request.urlopen(head_request, timeout=timeout_seconds) as response:
            return extract_remote_file_info(response.headers, existing_bytes=0)
    except error.HTTPError as exc:
        if exc.code not in {405, 501}:
            raise DownloadError(f"Unable to inspect remote file metadata: HTTP {exc.code}") from exc

    range_request = request.Request(url, headers=make_headers(token=token, range_start=0))
    with request.urlopen(range_request, timeout=timeout_seconds) as response:
        response.read(1)
        return extract_remote_file_info(response.headers, existing_bytes=0)


def collect_remote_file_info(
    snapshot: SnapshotInfo,
    *,
    base_url: str = HUGGING_FACE_BASE_URL,
    token: str | None = None,
    timeout_seconds: float = DEFAULT_TIMEOUT_SECONDS,
) -> dict[str, RemoteFileInfo]:
    remote_info: dict[str, RemoteFileInfo] = {}
    for filename in snapshot.files:
        remote_info[filename] = fetch_remote_file_info(
            build_file_url(snapshot.repo_id, filename, base_url=base_url, revision=snapshot.revision),
            token=token,
            timeout_seconds=timeout_seconds,
        )
    return remote_info


def existing_snapshot_bytes(destination_dir: Path, snapshot: SnapshotInfo) -> int:
    total = 0
    for filename in snapshot.files:
        destination = destination_dir / filename
        partial = part_path_for(destination)
        if destination.is_file():
            total += destination.stat().st_size
        elif partial.is_file():
            total += partial.stat().st_size
    return total


def ensure_disk_headroom(
    destination_dir: Path,
    snapshot: SnapshotInfo,
    *,
    reserve_bytes: int = DEFAULT_DISK_HEADROOM_BYTES,
) -> None:
    if snapshot.used_storage is None:
        return
    existing_bytes = existing_snapshot_bytes(destination_dir, snapshot)
    remaining_bytes = max(0, snapshot.used_storage - existing_bytes)
    if remaining_bytes == 0:
        return
    probe_root = destination_dir if destination_dir.exists() else destination_dir.parent
    probe_root.mkdir(parents=True, exist_ok=True)
    usage = shutil.disk_usage(probe_root)
    required_free_bytes = remaining_bytes + reserve_bytes
    if usage.free < required_free_bytes:
        raise DownloadError(
            "Not enough free disk space for this snapshot: "
            f"need at least {human_bytes(required_free_bytes)}, have {human_bytes(usage.free)} free."
        )


def verify_local_snapshot(
    destination_dir: Path,
    snapshot: SnapshotInfo,
    *,
    base_url: str = HUGGING_FACE_BASE_URL,
    token: str | None = None,
    timeout_seconds: float = DEFAULT_TIMEOUT_SECONDS,
    remote_info_by_file: dict[str, RemoteFileInfo] | None = None,
) -> list[str]:
    issues: list[str] = []
    manifest = read_manifest(destination_dir)
    if manifest and manifest.get("revision") != snapshot.revision:
        issues.append(
            f"manifest revision mismatch: local={manifest.get('revision')} remote={snapshot.revision}"
        )

    if remote_info_by_file is None:
        remote_info_by_file = collect_remote_file_info(
            snapshot,
            base_url=base_url,
            token=token,
            timeout_seconds=timeout_seconds,
        )

    for filename in snapshot.files:
        destination = destination_dir / filename
        partial = part_path_for(destination)
        remote = remote_info_by_file.get(filename)
        if destination.is_file():
            local_size = destination.stat().st_size
            if remote and remote.total_size is not None and local_size != remote.total_size:
                issues.append(
                    f"{filename}: local size {human_bytes(local_size)} does not match remote {human_bytes(remote.total_size)}"
                )
            continue
        if partial.is_file():
            issues.append(f"{filename}: partial download still present at {partial}")
            continue
        issues.append(f"{filename}: missing from {destination_dir}")
    return issues


def finalize_existing_partial(part_path: Path, destination: Path, *, total_size: int | None) -> bool:
    if not part_path.exists():
        return False
    if total_size is None:
        return False
    if part_path.stat().st_size != total_size:
        return False
    ensure_parent_directory(destination)
    part_path.replace(destination)
    return True


def download_file(
    *,
    url: str,
    destination: Path,
    token: str | None = None,
    timeout_seconds: float = DEFAULT_TIMEOUT_SECONDS,
    chunk_size: int = DEFAULT_CHUNK_SIZE,
    max_retries: int = DEFAULT_MAX_RETRIES,
    force: bool = False,
    expected_size: int | None = None,
) -> dict[str, Any]:
    ensure_parent_directory(destination)
    temp_path = part_path_for(destination)

    if temp_path.exists() and expected_size is not None and temp_path.stat().st_size > expected_size:
        print(f"[stale] removing oversize partial file for {destination.name}", flush=True)
        temp_path.unlink()

    if destination.exists() and not force:
        size = destination.stat().st_size
        if expected_size is None or size == expected_size:
            print(f"[skip] {destination.name} already exists ({human_bytes(size)})", flush=True)
            return {"path": str(destination), "bytes": size, "status": "existing"}
        print(
            f"[stale] {destination.name} has local size {human_bytes(size)} but remote is {human_bytes(expected_size)}; "
            "re-downloading",
            flush=True,
        )
        destination.unlink()

    if force:
        destination.unlink(missing_ok=True)
        temp_path.unlink(missing_ok=True)

    attempt = 0
    while True:
        existing_bytes = temp_path.stat().st_size if temp_path.exists() else 0
        started_at = time.monotonic()
        last_report_at = started_at
        try:
            req = request.Request(
                url,
                headers=make_headers(
                    token=token,
                    range_start=existing_bytes if existing_bytes else None,
                ),
            )
            with request.urlopen(req, timeout=timeout_seconds) as response:
                status = getattr(response, "status", 200)
                total_size = parse_total_size(response.headers, existing_bytes=existing_bytes)
                if expected_size is not None:
                    total_size = expected_size

                if status == 200 and existing_bytes:
                    temp_path.unlink(missing_ok=True)
                    existing_bytes = 0
                    file_mode = "wb"
                else:
                    file_mode = "ab" if existing_bytes else "wb"

                downloaded = existing_bytes
                with temp_path.open(file_mode) as handle:
                    while True:
                        chunk = response.read(chunk_size)
                        if not chunk:
                            break
                        handle.write(chunk)
                        downloaded += len(chunk)
                        now = time.monotonic()
                        if now - last_report_at >= 2:
                            emit_progress(destination.name, downloaded, total_size, started_at=started_at)
                            last_report_at = now

                final_size = temp_path.stat().st_size
                if total_size is not None and final_size < total_size:
                    raise DownloadError(
                        f"Incomplete download for {destination.name}: expected {human_bytes(total_size)}, "
                        f"got {human_bytes(final_size)}"
                    )
                temp_path.replace(destination)
                emit_progress(destination.name, destination.stat().st_size, total_size, started_at=started_at, finished=True)
                return {"path": str(destination), "bytes": destination.stat().st_size, "status": "downloaded"}
        except error.HTTPError as exc:
            total_size = parse_total_size(exc.headers, existing_bytes=0)
            if exc.code == 416 and finalize_existing_partial(temp_path, destination, total_size=expected_size or total_size):
                size = destination.stat().st_size
                print(f"[resume] {destination.name} already complete via partial file ({human_bytes(size)})", flush=True)
                return {"path": str(destination), "bytes": size, "status": "resumed"}
            retryable = exc.code in {408, 409, 423, 425, 429, 500, 502, 503, 504}
            message = f"HTTP {exc.code} for {destination.name}"
            if not retryable or attempt >= max_retries:
                raise DownloadError(message) from exc
            attempt += 1
            wait_seconds = min(30.0, 2 ** (attempt - 1))
            print(f"[retry] {message}; waiting {wait_seconds:.1f}s before retry {attempt}/{max_retries}", flush=True)
            time.sleep(wait_seconds)
        except (DownloadError, OSError, TimeoutError, error.URLError) as exc:
            if attempt >= max_retries:
                raise DownloadError(f"Failed downloading {destination.name}: {exc}") from exc
            attempt += 1
            wait_seconds = min(30.0, 2 ** (attempt - 1))
            print(
                f"[retry] {destination.name} interrupted ({exc}); waiting {wait_seconds:.1f}s before retry "
                f"{attempt}/{max_retries}",
                flush=True,
            )
            time.sleep(wait_seconds)


def write_manifest(
    destination_dir: Path,
    *,
    snapshot: SnapshotInfo,
    files: list[dict[str, Any]],
    remote_info_by_file: dict[str, RemoteFileInfo],
) -> Path:
    payload = {
        "repoId": snapshot.repo_id,
        "revision": snapshot.revision,
        "estimatedBytes": snapshot.used_storage,
        "writtenAt": utc_now_iso(),
        "files": [
            {
                **item,
                "etag": remote_info_by_file.get(item["filename"]).etag if remote_info_by_file.get(item["filename"]) else None,
                "expectedBytes": (
                    remote_info_by_file.get(item["filename"]).total_size if remote_info_by_file.get(item["filename"]) else None
                ),
            }
            for item in files
        ],
    }
    manifest_path = destination_dir / MANIFEST_FILENAME
    manifest_path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return manifest_path


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
    return preset["repo"]


def print_presets() -> None:
    for name, config in sorted(MODEL_PRESETS.items()):
        print(f"{name}: {config['repo']}")
        print(f"  {config['description']}")


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Download a Qwen2.5 MLX model snapshot with resume and retry support.",
    )
    parser.add_argument(
        "--model",
        default="qwen2.5-3b",
        choices=sorted(MODEL_PRESETS),
        help="Named preset for the MLX Qwen2.5 model to fetch.",
    )
    parser.add_argument("--repo", help="Override the Hugging Face repo id, for example mlx-community/Qwen2.5-3B-Instruct-4bit.")
    parser.add_argument("--dest-root", help="Root directory for downloaded models. Defaults to a Mira-Light cache path.")
    parser.add_argument("--output-dir", help="Exact output directory for this snapshot. Overrides --dest-root.")
    parser.add_argument("--token", default=os.environ.get("HF_TOKEN"), help="Optional Hugging Face token.")
    parser.add_argument("--timeout-seconds", type=float, default=DEFAULT_TIMEOUT_SECONDS, help="Per-request timeout.")
    parser.add_argument("--chunk-size-mb", type=int, default=1, help="Streaming chunk size in MiB.")
    parser.add_argument("--max-retries", type=int, default=DEFAULT_MAX_RETRIES, help="Retries for interrupted downloads.")
    parser.add_argument("--force", action="store_true", help="Delete any existing local copy and download again.")
    parser.add_argument("--dry-run", action="store_true", help="Resolve repo and output directory without downloading.")
    parser.add_argument("--verify", action="store_true", help="Verify local files against the remote snapshot and exit.")
    parser.add_argument("--list-presets", action="store_true", help="Print built-in model presets and exit.")
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
    destination_dir = resolve_output_dir(output_dir=args.output_dir, dest_root=args.dest_root, repo_id=repo_id)
    snapshot = fetch_snapshot_info(
        repo_id,
        api_base_url=args.api_base_url,
        token=args.token,
        timeout_seconds=args.timeout_seconds,
    )

    print(f"[model] repo: {snapshot.repo_id}")
    print(f"[model] revision: {snapshot.revision}")
    print(f"[model] estimated size: {human_bytes(snapshot.used_storage)}")
    print(f"[model] output dir: {destination_dir}")
    print(f"[model] files: {len(snapshot.files)}")

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
        url = build_file_url(snapshot.repo_id, filename, base_url=args.base_url, revision=snapshot.revision)
        result = download_file(
            url=url,
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
        remote_info_by_file=remote_info_by_file,
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

    print(f"[done] MLX model available at {destination_dir}")
    print(f"[done] manifest written to {manifest_path}")
    print(f"[next] python3 scripts/smoke_test_mlx_model.py --model-dir {destination_dir}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
