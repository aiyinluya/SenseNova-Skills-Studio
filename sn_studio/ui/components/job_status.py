"""Gradio helpers: immediate ack + Timer polling for background jobs."""



from __future__ import annotations



from typing import Any



import gradio as gr



from sn_studio.core import jobs
from sn_studio.ui.components.prompt_preview import (
    expanded_prompt_from_job_result,
    stages_line_from_job_result,
)



POLL_INTERVAL_SEC = 1.5



MSG_SUBMITTED = "⏳ 已提交，正在处理…"

MSG_PROCESSING = "⏳ 处理中…"



# Inactive image tabs share one Timer; skip their outputs instead of deactivating it.

_SKIP = gr.skip()





def toast(msg: str) -> dict[str, Any]:
    return gr.update(value=msg, elem_classes=["sn-toast"])


_STATUS_PREFIXES: tuple[str, ...] = (
    "✅ ",
    "❌ ",
    "⏳ ",
    "⚠️ ",
    "⌛ ",
    "✅",
    "❌",
    "⏳",
    "⚠️",
    "⌛",
)


def strip_status_prefix(line: str) -> str:
    """Remove leading status emoji(s) so UI wrappers add at most one icon."""
    text = (line or "").strip()
    while text:
        stripped = False
        for prefix in _STATUS_PREFIXES:
            if text.startswith(prefix):
                text = text[len(prefix) :].lstrip()
                stripped = True
                break
        if not stripped:
            break
    return text


def format_stage_message(line: str, *, failed: bool = False, done: bool = False) -> str:
    """Single leading status icon for the right-pane stage bar."""
    body = strip_status_prefix(line or "")
    if failed:
        return f"❌ **{body or '生成失败'}**"
    if done:
        return f"✅ **{body or '已完成'}**"
    if body:
        return f"⏳ {body}"
    return "*处理中…*"


def toast_for_terminal_job(job: jobs.Job) -> dict[str, Any]:
    """Compact completion toast with a single leading status icon."""
    if job.status == jobs.JobStatus.FAILED.value:
        line = jobs.preview_status_line(job)
        body = strip_status_prefix(line.split("\n", 1)[0])
        return toast(f"❌ {body}" if body else "❌ 任务失败")
    paths = ", ".join(job.output_paths[:2]) if job.output_paths else ""
    body = f"完成 · {job.kind}"
    if paths:
        body += f" · 输出: {paths}"
    return toast(f"✅ {body}")





def activate_timer() -> dict[str, Any]:

    return gr.Timer(active=True)





def deactivate_timer() -> dict[str, Any]:

    return gr.Timer(active=False)





def on_submit(job: jobs.Job, toast_detail: str = "") -> tuple[str, str, dict[str, Any]]:

    """Return (job_id, tab_status, timer_active) after submit."""

    detail = f" · {toast_detail}" if toast_detail else ""

    return job.id, f"{MSG_SUBMITTED}{detail}", activate_timer()





def poll_infographic_tick(job_id: str) -> tuple[Any, Any, Any, Any]:
    """Backward-compatible: gallery + status + timer + expanded only."""
    gal, log, timer, exp, _st = poll_pipeline_tick(job_id)
    return gal, log, timer, exp


def poll_pipeline_tick(job_id: str) -> tuple[Any, Any, Any, Any, Any]:
    """Gallery + status + timer + expanded prompt + pipeline stages line."""
    if not job_id:
        return _SKIP, _SKIP, _SKIP, _SKIP, _SKIP
    job = jobs.get_job(job_id)
    if job is None:
        return _SKIP, "❌ 任务不存在", deactivate_timer(), gr.update(), gr.update()

    res = job.result if isinstance(job.result, dict) else {}
    expanded = expanded_prompt_from_job_result(res)
    stages_line = stages_line_from_job_result(res)

    if not jobs.is_terminal(job):
        return (
            _SKIP,
            jobs.preview_status_line(job),
            activate_timer(),
            gr.update(value=expanded) if expanded else _SKIP,
            gr.update(value=stages_line) if stages_line else _SKIP,
        )
    if job.status == jobs.JobStatus.FAILED.value:
        return (
            _SKIP,
            jobs.preview_status_line(job),
            deactivate_timer(),
            gr.update(value=expanded),
            gr.update(value=stages_line),
        )

    return (
        jobs.gallery_update_for_job(job),
        jobs.preview_status_line(job),
        deactivate_timer(),
        gr.update(value=expanded),
        gr.update(value=stages_line),
    )


def poll_gallery_tick(job_id: str) -> tuple[Any, Any, Any]:

    """Timer tick: update gallery, status line, timer active flag."""

    if not job_id:

        return _SKIP, _SKIP, _SKIP

    job = jobs.get_job(job_id)

    if job is None:

        return _SKIP, "❌ 任务不存在", deactivate_timer()

    if not jobs.is_terminal(job):

        return _SKIP, jobs.preview_status_line(job), activate_timer()

    if job.status == jobs.JobStatus.FAILED.value:

        return _SKIP, jobs.preview_status_line(job), deactivate_timer()

    return jobs.gallery_update_for_job(job), jobs.preview_status_line(job), deactivate_timer()





def poll_text_tick(job_id: str) -> tuple[Any, Any]:

    if not job_id:

        return _SKIP, _SKIP

    job = jobs.get_job(job_id)

    if job is None:

        return "❌ 任务不存在", deactivate_timer()

    if not jobs.is_terminal(job):

        return jobs.preview_status_line(job), activate_timer()

    return jobs.preview_status_line(job), deactivate_timer()





def poll_toast_and_text(job_id: str) -> tuple[dict[str, Any], str, dict[str, Any]]:

    """For doctor jobs: update global toast + result textbox."""

    if not job_id:

        return toast(""), "无任务", deactivate_timer()

    job = jobs.get_job(job_id)

    if job is None:

        return toast("❌ 任务不存在"), "❌ 任务不存在", deactivate_timer()

    if not jobs.is_terminal(job):
        line = jobs.preview_status_line(job)
        return toast(line), line, activate_timer()

    line = jobs.preview_status_line(job)

    log = (job.log or "").strip()

    has_failures = "存在失败项" in log or "Environment check failed" in log

    if job.status == jobs.JobStatus.DONE.value and has_failures:
        return (
            toast("诊断完成（存在失败项，请查看下方详情）"),
            line,
            deactivate_timer(),
        )
    if job.status == jobs.JobStatus.DONE.value:
        return toast_for_terminal_job(job), line, deactivate_timer()

    return toast("❌ 诊断失败"), line, deactivate_timer()

