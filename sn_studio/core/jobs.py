"""Background job queue with JSON persistence."""

from __future__ import annotations

import json
import logging
import re
import shutil
import time
import uuid
from concurrent.futures import Future, ThreadPoolExecutor
from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from enum import Enum
from pathlib import Path
from typing import Any, Callable

import gradio as gr

from sn_studio.core.config import sanitize_log
from sn_studio.core.paths import jobs_store_path, studio_output_dir

_log = logging.getLogger(__name__)

_executor = ThreadPoolExecutor(max_workers=2, thread_name_prefix="sn-studio")
_futures: dict[str, Future[Any]] = {}
_MAX_JOBS = 200
_IMAGE_EXTS = (".png", ".jpg", ".jpeg", ".webp", ".gif")
_SERIES_RUN_ID_RE = re.compile(r"^\d{8}_\d{6}$")
_SERIES_RUN_MARKERS = ("series-lines.txt", "manifest.json")

# ``image_*`` job kinds → ``outputs/studio/{subdir}/``
_JOB_KIND_STUDIO_SUBDIR: dict[str, str] = {
    "image_generate": "generate",
    "image_infographic": "infographic",
    "image_series": "series",
    "image_imitate": "imitate",
    "image_resume": "resume",
}


class JobStatus(str, Enum):
    PENDING = "pending"
    RUNNING = "running"
    DONE = "done"
    FAILED = "failed"


TERMINAL_STATUSES = frozenset({JobStatus.DONE.value, JobStatus.FAILED.value})


@dataclass
class Job:
    id: str
    kind: str
    status: str
    created_at: str
    params: dict[str, Any] = field(default_factory=dict)
    finished_at: str | None = None
    result: dict[str, Any] | None = None
    log: str = ""
    output_paths: list[str] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _series_root_dir() -> Path:
    return studio_output_dir() / "series"


def is_series_run_dir(path: Path) -> bool:
    """``outputs/studio/series/<YYYYMMDD_HHMMSS>/`` with expected series artifacts."""
    try:
        resolved = path.resolve()
    except OSError:
        return False
    if not resolved.is_dir():
        return False
    try:
        if resolved.parent.resolve() != _series_root_dir().resolve():
            return False
    except OSError:
        return False
    if not _SERIES_RUN_ID_RE.match(resolved.name):
        return False
    return any((resolved / name).is_file() for name in _SERIES_RUN_MARKERS)


def series_run_dir_for_job(job: Job) -> Path | None:
    """Resolve new-layout series run directory from a persisted job record."""
    if job.kind != "image_series":
        return None
    res = job.result or {}
    for key in ("series_dir", "work_dir"):
        raw = res.get(key)
        if raw:
            candidate = Path(str(raw))
            if is_series_run_dir(candidate):
                return candidate.resolve()
    for raw in raw_paths_from_job(job):
        p = Path(str(raw))
        candidate = p.parent if p.is_file() or p.suffix else p
        if is_series_run_dir(candidate):
            return candidate.resolve()
    return None


def is_valid_image_series_job(job: Job) -> bool:
    """Terminal ``image_series`` jobs must point at the new per-run folder layout."""
    if job.kind != "image_series":
        return True
    if not is_terminal(job):
        return True
    return series_run_dir_for_job(job) is not None


def _keep_job_in_store(job: Job) -> bool:
    if job.kind != "image_series":
        return True
    if not is_terminal(job):
        return True
    return is_valid_image_series_job(job)


def _prune_legacy_image_series_jobs(jobs: list[Job]) -> list[Job]:
    kept = [j for j in jobs if _keep_job_in_store(j)]
    if len(kept) != len(jobs):
        removed = len(jobs) - len(kept)
        _log.info("pruned %d legacy image_series job(s) from jobs.json", removed)
    return kept


def _load_all() -> list[Job]:
    path = jobs_store_path()
    if not path.is_file():
        return []
    try:
        raw = json.loads(path.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, OSError):
        return []
    jobs: list[Job] = []
    for item in raw if isinstance(raw, list) else []:
        jobs.append(Job(**item))
    pruned = _prune_legacy_image_series_jobs(jobs)
    if len(pruned) != len(jobs):
        _save_all(pruned)
    return pruned


def _save_all(jobs: list[Job]) -> None:
    path = jobs_store_path()
    trimmed = jobs[-_MAX_JOBS:]
    path.write_text(
        json.dumps([j.to_dict() for j in trimmed], ensure_ascii=False, indent=2),
        encoding="utf-8",
    )


def list_jobs(limit: int = 50) -> list[Job]:
    return list(reversed(_load_all()[-limit:]))


def get_job(job_id: str) -> Job | None:
    for j in _load_all():
        if j.id == job_id:
            return j
    return None


def set_job_progress(job_id: str, message: str) -> None:
    """Update in-flight job log for UI polling (e.g. infographic stages)."""
    job = get_job(job_id)
    if job is None or is_terminal(job):
        return
    job.log = sanitize_log(message)[:8000]
    _update(job)


def is_terminal(job: Job | None) -> bool:
    return job is not None and job.status in TERMINAL_STATUSES


def preview_cache_dir() -> Path:
    d = studio_output_dir() / "preview_cache"
    d.mkdir(parents=True, exist_ok=True)
    return d


def _is_image_path(path: str) -> bool:
    return path.lower().endswith(_IMAGE_EXTS)


def raw_paths_from_job(job: Job) -> list[str]:
    """Collect candidate output paths from job fields and result payload."""
    seen: set[str] = set()
    ordered: list[str] = []

    def _add(raw: Any) -> None:
        if not raw:
            return
        s = str(raw).strip()
        if not s or s in seen:
            return
        seen.add(s)
        ordered.append(s)

    for p in job.output_paths or []:
        _add(p)
    res = job.result or {}
    for key in ("save_path", "path", "html", "expanded_prompt_path", "series_dir", "work_dir"):
        _add(res.get(key))
    for item in res.get("items") or []:
        if isinstance(item, dict):
            _add(item.get("path"))
    return ordered


def studio_module_dir_for_job_kind(kind: str) -> Path:
    """Default ``outputs/studio/{module}/`` directory for a job kind (created if missing)."""
    sub = _JOB_KIND_STUDIO_SUBDIR.get(kind or "", "")
    d = studio_output_dir() / sub if sub else studio_output_dir()
    d.mkdir(parents=True, exist_ok=True)
    return d.resolve()


def primary_output_path_for_job(job: Job) -> str | None:
    """Best-effort absolute path string for UI display (prefers image outputs)."""
    raw = raw_paths_from_job(job)
    if not raw:
        return None
    for p in raw:
        if _is_image_path(p):
            try:
                return str(Path(p).expanduser().resolve())
            except OSError:
                return p
    try:
        return str(Path(raw[0]).expanduser().resolve())
    except OSError:
        return raw[0]


def output_path_display(job_id: str, *, fallback_kind: str | None = None) -> str:
    """Path shown in Studio UI: last job file, or default kind directory."""
    jid = (job_id or "").strip()
    if jid:
        job = get_job(jid)
        if job:
            primary = primary_output_path_for_job(job)
            if primary:
                return primary
            return str(studio_module_dir_for_job_kind(job.kind))
    if fallback_kind:
        return str(studio_module_dir_for_job_kind(fallback_kind))
    return str(studio_output_dir().resolve())


def output_folder_for_open(job_id: str, *, fallback_kind: str | None = None) -> Path | None:
    """Directory to open in the local file manager (parent of file outputs)."""
    display = output_path_display(job_id, fallback_kind=fallback_kind)
    if not display:
        return None
    p = Path(display)
    if p.is_file():
        return p.parent.resolve()
    if p.is_dir():
        return p.resolve()
    if p.exists():
        return (p if p.is_dir() else p.parent).resolve()
    parent = p.parent
    if parent.is_dir():
        return parent.resolve()
    jid = (job_id or "").strip()
    kind = fallback_kind
    if jid:
        job = get_job(jid)
        if job:
            kind = job.kind
    if kind:
        return studio_module_dir_for_job_kind(kind)
    return studio_output_dir().resolve()


def resolve_preview_path(raw: str) -> str | None:
    """Absolute path suitable for Gradio Gallery (forward slashes)."""
    try:
        src = Path(raw).expanduser()
        if not src.is_absolute():
            src = src.resolve()
        else:
            src = src.resolve()
    except OSError:
        return None
    if not src.is_file():
        return None
    return src.as_posix()


def _ensure_gradio_preview_path(resolved_posix: str) -> str:
    """Copy into studio preview_cache if needed so Gradio can serve the file."""
    src = Path(resolved_posix)
    cache = preview_cache_dir()
    try:
        if src.is_relative_to(cache.resolve()):
            return resolved_posix
    except ValueError:
        pass
    dest = cache / f"{src.stem}_{src.stat().st_mtime_ns}{src.suffix.lower()}"
    if not dest.is_file() or dest.stat().st_size != src.stat().st_size:
        shutil.copy2(src, dest)
    return dest.resolve().as_posix()


def _series_image_paths_from_run_dir(run_dir: Path) -> list[str]:
    """Ordered PNG paths for a series run (``01.png`` … or manifest order)."""
    manifest = run_dir / "manifest.json"
    ordered: list[Path] = []
    if manifest.is_file():
        try:
            data = json.loads(manifest.read_text(encoding="utf-8"))
        except (json.JSONDecodeError, OSError):
            data = None
        if isinstance(data, list):
            for item in data:
                if isinstance(item, dict) and item.get("path"):
                    p = Path(str(item["path"]))
                    if p.is_file() and _is_image_path(str(p)):
                        ordered.append(p)
    if not ordered:
        ordered = sorted(
            p for p in run_dir.glob("*.png") if _is_image_path(p.name)
        )
    out: list[str] = []
    seen: set[str] = set()
    for p in ordered:
        resolved = resolve_preview_path(str(p))
        if not resolved:
            continue
        try:
            display = _ensure_gradio_preview_path(resolved)
        except OSError as exc:
            _log.debug("preview cache copy failed for %s: %s", p, exc)
            display = resolved
        if display in seen:
            continue
        seen.add(display)
        out.append(display)
    return out


def series_session_thumbnail(job: Job) -> str | None:
    """First series image for session history thumb strip."""
    run_dir = series_run_dir_for_job(job)
    if run_dir is None:
        return None
    paths = _series_image_paths_from_run_dir(run_dir)
    return paths[0] if paths else None


def image_paths_from_job(job: Job) -> list[str]:
    """Resolved image paths for Gallery (existing files only)."""
    if job.kind == "image_series":
        run_dir = series_run_dir_for_job(job)
        if run_dir is None:
            return []
        return _series_image_paths_from_run_dir(run_dir)
    out: list[str] = []
    seen: set[str] = set()
    for raw in raw_paths_from_job(job):
        if not _is_image_path(raw):
            continue
        resolved = resolve_preview_path(raw)
        if not resolved:
            continue
        try:
            display = _ensure_gradio_preview_path(resolved)
        except OSError as exc:
            _log.debug("preview cache copy failed for %s: %s", raw, exc)
            display = resolved
        if display in seen:
            continue
        seen.add(display)
        out.append(display)
    return out


def gallery_update_for_job(job: Job) -> dict[str, Any]:
    imgs = image_paths_from_job(job)
    return gr.update(value=imgs)


def preview_status_line(job: Job | None) -> str:
    """Status text for poll handlers; adds path fallback when Gallery has no images."""
    base = status_line(job)
    if job is None or not is_terminal(job) or job.status != JobStatus.DONE.value:
        return base
    if image_paths_from_job(job):
        return base
    paths = raw_paths_from_job(job)
    if not paths:
        return base
    lines = [base, "", "（预览区未识别到图片，但任务已有输出文件）"]
    for p in paths[:10]:
        lines.append(f"  · {p}")
    if len(paths) > 10:
        lines.append(f"  … 另有 {len(paths) - 10} 个文件")
    lines.append(
        "提示：请复制输出路径，或在本地运行 Studio 时点击「打开输出文件夹」。"
    )
    return "\n".join(lines)


def wait_for_job(job_id: str, timeout: float = 600.0, poll_interval: float = 1.0) -> Job:
    """Block until job reaches a terminal state or timeout."""
    deadline = time.monotonic() + timeout
    while time.monotonic() < deadline:
        job = get_job(job_id)
        if job is None:
            raise ValueError(f"任务不存在: {job_id}")
        if is_terminal(job):
            return job
        time.sleep(poll_interval)
    raise TimeoutError(f"任务 {job_id} 在 {timeout}s 内未完成")


def status_line(job: Job | None) -> str:
    if job is None:
        return "无任务"
    if job.status in (JobStatus.PENDING.value, JobStatus.RUNNING.value):
        label = "排队中" if job.status == JobStatus.PENDING.value else "处理中"
        stage = (job.log or "").strip()
        if stage:
            return f"⏳ {stage}… ({job.kind})"
        return f"⏳ {label}… ({job.kind})"
    if job.status == JobStatus.FAILED.value:
        err = job.log or (job.result or {}).get("error", "未知错误")
        text = str(err)
        if "Traceback (most recent call last)" in text:
            text = text.split("Traceback (most recent call last)", 1)[0].strip()
        if text.startswith("脚本失败 (code="):
            return text[:4000]
        return f"❌ 失败: {text[:4000]}"
    log_bit = (job.log or "")[:4000]
    paths = ", ".join(job.output_paths[:3]) if job.output_paths else ""
    extra = f"\n输出: {paths}" if paths else ""
    if log_bit:
        failed_check = "存在失败项" in log_bit or "Environment check failed" in log_bit
        if failed_check:
            return f"⚠️ 诊断完成（存在失败项） · {job.kind}\n{log_bit}{extra}"
        return f"✅ 完成 · {job.kind}\n{log_bit}{extra}"
    return f"✅ 完成 · {job.kind}{extra}"


def _update(job: Job) -> None:
    jobs = _load_all()
    for i, j in enumerate(jobs):
        if j.id == job.id:
            jobs[i] = job
            _save_all(jobs)
            return
    jobs.append(job)
    _save_all(jobs)


def submit(kind: str, params: dict[str, Any], fn: Callable[[], dict[str, Any]]) -> Job:
    job = Job(
        id=uuid.uuid4().hex[:12],
        kind=kind,
        status=JobStatus.PENDING.value,
        created_at=_now(),
        params=params,
    )
    _update(job)

    def _wrap() -> dict[str, Any]:
        job.status = JobStatus.RUNNING.value
        _update(job)
        try:
            result = fn()
            job.status = JobStatus.DONE.value
            job.result = result
            job.output_paths = result.get("output_paths", []) or []
            if "log" in result:
                job.log = sanitize_log(str(result["log"]))[:8000]
            job.finished_at = _now()
            _update(job)
            return result
        except Exception as exc:
            job.status = JobStatus.FAILED.value
            job.log = sanitize_log(str(exc))[:8000]
            job.finished_at = _now()
            job.result = {"error": str(exc)}
            _update(job)
            raise

    future = _executor.submit(_wrap)
    _futures[job.id] = future
    return job


_IMAGE_JOB_KIND_PREFIX = "image_"


def is_image_job(job: Job) -> bool:
    return job.kind.startswith(_IMAGE_JOB_KIND_PREFIX)


def _image_job_gallery_items(
    limit: int,
    *,
    kind: str | None = None,
    done_only: bool = False,
) -> tuple[list[str | tuple[str, str]], list[str]]:
    """Build gallery thumbs + job ids from persisted ``outputs/.studio_jobs/jobs.json``."""
    items: list[str | tuple[str, str]] = []
    ids: list[str] = []
    scan_limit = max(limit * 4, 40)
    for j in list_jobs(scan_limit):
        if not is_image_job(j):
            continue
        if kind is not None and j.kind != kind:
            continue
        if done_only and (not is_terminal(j) or j.status != JobStatus.DONE.value):
            continue
        if j.kind == "image_series" and not is_valid_image_series_job(j):
            continue
        imgs = image_paths_from_job(j)
        if not imgs:
            continue
        short_kind = j.kind.replace("image_", "")
        label = f"{short_kind} · {j.id[:8]}"
        items.append((imgs[0], label))
        ids.append(j.id)
        if len(ids) >= limit:
            break
    return items, ids


def session_history_gallery(
    limit: int = 16,
    *,
    kind: str | None = None,
) -> tuple[list[str | tuple[str, str]], list[str]]:
    """Session thumb strip: completed image jobs from disk-backed job store."""
    items, ids = _image_job_gallery_items(limit, kind=kind, done_only=True)
    if items:
        return items, ids
    return _disk_fallback_session_history(limit, kind=kind)


def _disk_fallback_series_session_history(
    limit: int,
) -> tuple[list[str | tuple[str, str]], list[str]]:
    """Scan ``outputs/studio/series/<timestamp>/`` runs when jobs.json has no thumbs."""
    series_root = _series_root_dir()
    if not series_root.is_dir():
        return [], []
    candidates: list[tuple[float, Path, str]] = []
    for entry in series_root.iterdir():
        if not entry.is_dir() or not _SERIES_RUN_ID_RE.match(entry.name):
            continue
        if not is_series_run_dir(entry):
            continue
        paths = _series_image_paths_from_run_dir(entry)
        if not paths:
            continue
        try:
            mtime = max(
                (p.stat().st_mtime for p in entry.glob("*.png") if p.is_file()),
                default=entry.stat().st_mtime,
            )
        except OSError:
            mtime = 0.0
        candidates.append((mtime, entry, paths[0]))
    candidates.sort(key=lambda x: x[0], reverse=True)
    items: list[str | tuple[str, str]] = []
    ids: list[str] = []
    for _, entry, thumb in candidates[:limit]:
        label = f"series · {entry.name}"
        items.append((thumb, label))
        ids.append("")
    return items, ids


def _disk_fallback_session_history(
    limit: int,
    *,
    kind: str | None = None,
) -> tuple[list[str | tuple[str, str]], list[str]]:
    """When jobs.json has no thumbs, scan ``outputs/studio`` image files by mtime."""
    if kind == "image_series":
        return _disk_fallback_series_session_history(limit)
    kind_dirs: dict[str, tuple[str, ...]] = {
        "image_generate": ("generate",),
        "image_infographic": ("infographic",),
        "image_imitate": ("imitate",),
        "image_resume": ("resume",),
    }
    prefixes = kind_dirs.get(kind or "", ())
    root = studio_output_dir()
    if not root.is_dir():
        return [], []
    candidates: list[tuple[float, Path]] = []
    for entry in root.iterdir():
        if not entry.is_dir():
            continue
        name = entry.name
        if prefixes:
            if not any(name.startswith(p) or name == p.rstrip("_") for p in prefixes):
                continue
        for path in entry.rglob("*"):
            if path.is_file() and path.suffix.lower() in _IMAGE_EXTS:
                try:
                    candidates.append((path.stat().st_mtime, path))
                except OSError:
                    continue
    candidates.sort(key=lambda x: x[0], reverse=True)
    items: list[str | tuple[str, str]] = []
    ids: list[str] = []
    seen: set[str] = set()
    for _, path in candidates:
        resolved = resolve_preview_path(str(path))
        if not resolved or resolved in seen:
            continue
        try:
            display = _ensure_gradio_preview_path(resolved)
        except OSError:
            display = resolved
        seen.add(display)
        label = f"{path.parent.name} · {path.name}"
        items.append((display, label))
        ids.append("")
        if len(items) >= limit:
            break
    return items, ids
