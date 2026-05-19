"""Image generation and related pipelines."""

from __future__ import annotations

from typing import Any

from sn_studio.core import jobs
from sn_studio.core.runner import RunError
from sn_studio.services.prompt_pipeline import expand_series_prompts, run_pipeline


def generate_image(
    prompt: str,
    aspect_ratio: str = "16:9",
    seed: int | None = None,
    negative_prompt: str = "",
    *,
    prompts_expand_mode: str = "auto",
    style_hint: str = "",
    on_progress: Any = None,
) -> dict[str, Any]:
    return run_pipeline(
        prompt,
        module_kind="generate",
        prompts_expand_mode=prompts_expand_mode,
        style_hint=style_hint,
        aspect_ratio=aspect_ratio,
        negative_prompt=negative_prompt,
        seed=seed,
        on_progress=on_progress,
    )


def generate_infographic(
    content: str,
    style_hint: str = "",
    *,
    prompts_expand_mode: str = "auto",
    max_rounds: int = 1,
    on_progress: Any = None,
) -> dict[str, Any]:
    return run_pipeline(
        content,
        module_kind="infographic",
        style_hint=style_hint,
        prompts_expand_mode=prompts_expand_mode,
        max_rounds=max_rounds,
        on_progress=on_progress,
    )


def generate_series(
    prompts_text: str = "",
    aspect_ratio: str = "16:9",
    *,
    theme: str = "",
    count: int = 6,
    style_hint: str = "",
    prompts_expand_mode: str = "auto",
    negative_prompt: str = "",
    on_progress: Any = None,
) -> dict[str, Any]:
    theme_s = (theme or "").strip()
    if theme_s:
        lines = expand_series_prompts(
            theme_s,
            count,
            style_hint=style_hint,
            on_progress=on_progress,
        )
        prompts_text = "\n".join(lines)
    else:
        lines = [ln.strip() for ln in (prompts_text or "").splitlines() if ln.strip()]
    return run_pipeline(
        prompts_text,
        module_kind="series",
        prompts_expand_mode=prompts_expand_mode,
        aspect_ratio=aspect_ratio,
        negative_prompt=negative_prompt,
        series_lines=lines,
        on_progress=on_progress,
    )


def imitate_style(
    reference_image: str,
    new_content: str,
    *,
    prompts_expand_mode: str = "auto",
    aspect_ratio: str = "16:9",
    negative_prompt: str = "",
    on_progress: Any = None,
) -> dict[str, Any]:
    return run_pipeline(
        new_content,
        module_kind="imitate",
        prompts_expand_mode=prompts_expand_mode,
        aspect_ratio=aspect_ratio,
        negative_prompt=negative_prompt,
        reference_image=reference_image,
        on_progress=on_progress,
    )


def resume_image(
    resume_text: str,
    style_notes: str = "",
    *,
    prompts_expand_mode: str = "auto",
    aspect_ratio: str = "9:16",
    negative_prompt: str = "",
    on_progress: Any = None,
) -> dict[str, Any]:
    return run_pipeline(
        resume_text,
        module_kind="resume",
        style_hint=style_notes,
        prompts_expand_mode=prompts_expand_mode,
        aspect_ratio=aspect_ratio,
        negative_prompt=negative_prompt,
        on_progress=on_progress,
    )


def submit_image_job(kind: str, **params: Any) -> jobs.Job:
    progress_job_id: dict[str, str] = {}

    def _progress(stage: str) -> None:
        jid = progress_job_id.get("id")
        if jid:
            jobs.set_job_progress(jid, stage)

    def _run() -> dict[str, Any]:
        mode = params.get("prompts_expand_mode", "auto")
        if kind == "generate":
            seed_v = params.get("seed")
            return generate_image(
                params["prompt"],
                params.get("aspect_ratio", "16:9"),
                seed_v,
                params.get("negative_prompt", ""),
                prompts_expand_mode=mode,
                style_hint=params.get("style_hint", ""),
                on_progress=_progress,
            )
        if kind == "infographic":
            return generate_infographic(
                params["content"],
                params.get("style_hint", ""),
                prompts_expand_mode=mode,
                max_rounds=params.get("max_rounds", 1),
                on_progress=_progress,
            )
        if kind == "series":
            return generate_series(
                params.get("prompts", ""),
                params.get("aspect_ratio", "16:9"),
                theme=params.get("theme", ""),
                count=params.get("count", 6),
                style_hint=params.get("style_hint", ""),
                prompts_expand_mode=mode,
                negative_prompt=params.get("negative_prompt", ""),
                on_progress=_progress,
            )
        if kind == "imitate":
            return imitate_style(
                params["reference_image"],
                params["new_content"],
                prompts_expand_mode=mode,
                aspect_ratio=params.get("aspect_ratio", "16:9"),
                negative_prompt=params.get("negative_prompt", ""),
                on_progress=_progress,
            )
        if kind == "resume":
            return resume_image(
                params["resume_text"],
                params.get("style_notes", ""),
                prompts_expand_mode=mode,
                aspect_ratio=params.get("aspect_ratio", "9:16"),
                negative_prompt=params.get("negative_prompt", ""),
                on_progress=_progress,
            )
        raise RunError(f"未知任务类型: {kind}")

    job = jobs.submit(f"image_{kind}", params, _run)
    progress_job_id["id"] = job.id
    return job
