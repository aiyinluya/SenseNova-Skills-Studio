"""Studio job preview path mapping (no Gradio UI)."""
from __future__ import annotations

from sn_studio.core import jobs
from sn_studio.ui.components import job_status


def test_image_paths_from_completed_series_job():
    """Prefer a new-layout series job when present; legacy flat dirs are ignored."""
    for job in jobs.list_jobs(80):
        if job.kind != "image_series" or job.status != jobs.JobStatus.DONE.value:
            continue
        if not jobs.is_valid_image_series_job(job):
            continue
        paths = jobs.image_paths_from_job(job)
        if paths:
            assert all(p.endswith(".png") for p in paths)
            return
    # No new-layout series job in store — skip (CI / fresh checkout).


def test_poll_gallery_tick_skips_when_no_job_id():
    gal, log, timer = job_status.poll_gallery_tick("")
    assert gal is job_status._SKIP
    assert log is job_status._SKIP
    assert timer is job_status._SKIP


def test_poll_gallery_tick_fills_gallery_when_done():
    job = None
    for j in jobs.list_jobs(80):
        if j.kind == "image_series" and j.status == jobs.JobStatus.DONE.value:
            if jobs.is_valid_image_series_job(j) and jobs.image_paths_from_job(j):
                job = j
                break
    if job is None:
        return
    gal, log, timer = job_status.poll_gallery_tick(job.id)
    assert isinstance(gal, dict)
    assert gal.get("value")
    assert "完成" in log or "✅" in log
    assert timer.get("active") is False


def test_build_app_import():
    from sn_studio.ui.app import build_app

    app = build_app()
    assert app is not None
