"""Unified prompt pipeline for all Studio image modules."""

from __future__ import annotations

import json
import random
import re
from dataclasses import asdict, dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Any, Callable

from sn_studio.core.paths import skill_path, studio_output_dir
from sn_studio.core.runner import RunError, run_agent_runner
from sn_studio.services import prompt_text
from sn_studio.services.prompt_text import (
    chinese_image_text_appendix,
    default_negative_prompt_chinese,
    inject_chinese_appendix,
)

ProgressFn = Callable[[str], None]

# Re-export for tests and callers
chinese_image_text_appendix = prompt_text.chinese_image_text_appendix
default_negative_prompt_chinese = prompt_text.default_negative_prompt_chinese
inject_chinese_appendix = prompt_text.inject_chinese_appendix
CHINESE_IMAGE_TEXT_APPENDIX = chinese_image_text_appendix()
DEFAULT_NEGATIVE_PROMPT_CHINESE = prompt_text.DEFAULT_NEGATIVE_PROMPT_CHINESE


@dataclass
class PipelineResult:
    expanded_prompt: str
    expanded_prompt_path: str
    pipeline_stages: list[dict[str, str]] = field(default_factory=list)
    prompts_expand_skipped: bool = False
    prompts_expand_mode: str = "auto"
    work_dir: str = ""
    layout: str | None = None
    style: str | None = None
    aspect_ratio: str = "16:9"
    module_kind: str = ""
    shared_style_block: str = ""
    output_paths: list[str] = field(default_factory=list)
    items: list[dict[str, Any]] = field(default_factory=list)
    log: str = ""

    def to_result_dict(self, extra: dict[str, Any] | None = None) -> dict[str, Any]:
        base: dict[str, Any] = {
            "expanded_prompt": self.expanded_prompt,
            "expanded_prompt_path": self.expanded_prompt_path,
            "pipeline_stages": self.pipeline_stages,
            "prompts_expand_skipped": self.prompts_expand_skipped,
            "prompts_expand_mode": self.prompts_expand_mode,
            "work_dir": self.work_dir,
            "layout": self.layout,
            "style": self.style,
            "aspect_ratio": self.aspect_ratio,
            "module_kind": self.module_kind,
            "shared_style_block": self.shared_style_block,
            "output_paths": self.output_paths,
            "log": self.log,
        }
        if extra:
            base.update(extra)
        return base


def _work_dir(module_kind: str) -> Path:
    ts = datetime.now().strftime("%Y%m%d_%H%M%S")
    d = studio_output_dir() / module_kind / ts
    d.mkdir(parents=True, exist_ok=True)
    return d


def _progress(on_progress: ProgressFn | None, label: str) -> None:
    if on_progress:
        on_progress(label)


def _record_stage(stages: list[dict[str, str]], stage_id: str, label: str) -> None:
    stages.append({"id": stage_id, "label": label})


def _normalize_mode(mode: str) -> str:
    m = (mode or "auto").strip().lower()
    if m not in ("auto", "force", "disable"):
        raise RunError(f"无效的扩写模式: {mode}")
    return m


def _save_expanded(work_dir: Path, text: str) -> Path:
    p = work_dir / "expanded-prompt.txt"
    p.write_text(text, encoding="utf-8")
    return p


_SERIES_LINE_PREFIX = re.compile(r"^\s*(?:\d+[\.\)、]|[-*•])\s*")


def parse_series_scene_lines(raw: str, count: int) -> list[str]:
    """Parse LLM output into exactly ``count`` non-empty scene lines."""
    n = max(3, min(8, int(count)))
    lines: list[str] = []
    for ln in (raw or "").splitlines():
        s = _SERIES_LINE_PREFIX.sub("", ln.strip())
        if s:
            lines.append(s)
    if len(lines) < n:
        pad_base = lines[0] if lines else "系列画面"
        while len(lines) < n:
            lines.append(f"{pad_base} — 第 {len(lines) + 1} 张")
    return lines[:n]


def expand_series_prompts(
    theme: str,
    count: int,
    *,
    style_hint: str = "",
    on_progress: ProgressFn | None = None,
) -> list[str]:
    """Expand a one-line theme into N short scene descriptions for series generation."""
    from sn_studio.services.infographic_pipeline import _result_text, _text_optimize

    subject = (theme or "").strip()
    if not subject:
        raise RunError("请输入系列主题")
    n = max(3, min(8, int(count)))
    _progress(on_progress, "拆解系列场景")
    anchor = (style_hint or "").strip()
    anchor_line = f"\n风格锚点：{anchor}" if anchor else ""
    sys = inject_chinese_appendix(
        f"用户给出一句话系列主题，请拆解为恰好 {n} 张图的短描述（每张 20–60 字）。"
        "要求：同一系列、角色与视觉风格一致，画面有清晰递进或并列关系。"
        f"只输出 {n} 行，每行一张，不要编号、不要空行、不要 JSON。"
    )
    user = f"主题：{subject}{anchor_line}\n张数：{n}"
    data = _text_optimize(system_prompt=sys, user_prompt=user, timeout=240)
    return parse_series_scene_lines(_result_text(data), n)


def _generate_image(
    prompt: str,
    *,
    aspect_ratio: str,
    save_path: Path,
    negative_prompt: str = "",
    seed: int | None = None,
) -> dict[str, Any]:
    args = [
        "sn-image-generate",
        "--prompt",
        prompt,
        "--aspect-ratio",
        aspect_ratio,
        "--image-size",
        "2k",
        "--save-path",
        str(save_path),
        "-o",
        "json",
    ]
    neg = negative_prompt.strip()
    if neg:
        args.extend(["--negative-prompt", neg])
    if seed is not None and seed >= 0:
        args.extend(["--seed", str(seed)])
    return run_agent_runner(args, timeout=600)


def run_pipeline(
    user_prompt: str,
    *,
    module_kind: str,
    prompts_expand_mode: str = "auto",
    style_hint: str = "",
    aspect_ratio: str = "16:9",
    negative_prompt: str = "",
    reference_image: str = "",
    max_rounds: int = 1,
    series_lines: list[str] | None = None,
    seed: int | None = None,
    on_progress: ProgressFn | None = None,
) -> dict[str, Any]:
    """Route to module-specific pipeline; return job result dict."""
    kind = (module_kind or "generate").strip().lower()
    mode = _normalize_mode(prompts_expand_mode)

    if kind == "infographic":
        from sn_studio.services.infographic_pipeline import run_infographic_pipeline

        return run_infographic_pipeline(
            user_prompt,
            style_hint=style_hint,
            prompts_expand_mode=mode,
            max_rounds=max_rounds,
            on_progress=on_progress,
        )

    if kind == "generate":
        return _run_generate(
            user_prompt,
            mode=mode,
            style_hint=style_hint,
            aspect_ratio=aspect_ratio,
            negative_prompt=negative_prompt,
            seed=seed,
            on_progress=on_progress,
        ).to_result_dict()

    if kind == "series":
        lines = series_lines or [ln.strip() for ln in user_prompt.splitlines() if ln.strip()]
        series_result = _run_series(
            lines,
            mode=mode,
            aspect_ratio=aspect_ratio,
            negative_prompt=negative_prompt,
            on_progress=on_progress,
        )
        out = series_result.to_result_dict()
        out["items"] = series_result.items
        out["series_dir"] = series_result.work_dir
        out["count"] = len(lines)
        return out

    if kind == "imitate":
        return _run_imitate(
            reference_image,
            user_prompt,
            mode=mode,
            aspect_ratio=aspect_ratio,
            negative_prompt=negative_prompt,
            on_progress=on_progress,
        ).to_result_dict()

    if kind == "resume":
        return _run_resume(
            user_prompt,
            style_hint=style_hint,
            mode=mode,
            aspect_ratio=aspect_ratio or "9:16",
            negative_prompt=negative_prompt,
            on_progress=on_progress,
        ).to_result_dict()

    raise RunError(f"未知流水线模块: {module_kind}")


def _run_generate(
    user_prompt: str,
    *,
    mode: str,
    style_hint: str,
    aspect_ratio: str,
    negative_prompt: str,
    seed: int | None,
    on_progress: ProgressFn | None,
) -> PipelineResult:
    from sn_studio.services.infographic_pipeline import (
        _infer_aspect_ratio,
        _result_text,
        _select_layout_style,
        _should_expand_auto,
        _text_optimize,
    )

    text = (user_prompt or "").strip()
    if not text:
        raise RunError("请输入画面描述")

    work_dir = _work_dir("generate")
    stages: list[dict[str, str]] = []
    ratio = aspect_ratio or _infer_aspect_ratio(text)
    neg = default_negative_prompt_chinese(negative_prompt)
    skipped = False
    layout: str | None = None
    style: str | None = None

    if mode == "disable":
        expanded = text
        skipped = True
        _record_stage(stages, "generate", "生成图像")
        _progress(on_progress, "生成图像")
    else:
        should_expand = True
        if mode == "auto":
            _record_stage(stages, "evaluate", "评估中")
            _progress(on_progress, "评估中")
            should_expand = _should_expand_auto(text)

        if not should_expand and mode == "auto":
            expanded = text
            skipped = True
            _record_stage(stages, "generate", "生成图像")
            _progress(on_progress, "生成图像")
        else:
            _record_stage(stages, "analyze", "分析内容")
            _progress(on_progress, "分析内容")
            analysis_sys = inject_chinese_appendix(
                "分析用户画面需求：主体、场景、数据类型、情绪与受众。"
                "输出简洁要点列表（中文），不要编造用户未提供的事实。"
            )
            analysis_data = _text_optimize(system_prompt=analysis_sys, user_prompt=text, timeout=180)
            analysis_text = _result_text(analysis_data)
            (work_dir / "analysis.txt").write_text(analysis_text, encoding="utf-8")

            _record_stage(stages, "layout", "分析版式")
            _progress(on_progress, "分析版式")
            layout, style = _select_layout_style(text, None, style_hint)
            (work_dir / "layout-style.json").write_text(
                json.dumps({"layout": layout, "style": style}, ensure_ascii=False),
                encoding="utf-8",
            )

            _record_stage(stages, "expand", "扩写 Prompt")
            _progress(on_progress, "扩写 Prompt")
            expand_sys = inject_chinese_appendix(
                "将用户描述扩写为一条完整的中文文生图 prompt（400–800 字）。"
                f"建议版式气质: layout={layout}, style={style}。"
                "包含主体、构图、光影、配色；图中文字用引号列出。"
                "只输出最终 prompt，不要解释。"
            )
            user_block = text
            if style_hint.strip():
                user_block += f"\n\n风格偏好: {style_hint.strip()}"
            if analysis_text:
                user_block = f"## 分析\n{analysis_text}\n\n## 用户\n{user_block}"
            expand_data = _text_optimize(system_prompt=expand_sys, user_prompt=user_block, timeout=300)
            expanded = _result_text(expand_data) or text
            (work_dir / "expand-system-prompt.md").write_text(expand_sys, encoding="utf-8")

            _record_stage(stages, "generate", "生成图像")
            _progress(on_progress, "生成图像")

    expanded_path = _save_expanded(work_dir, expanded)
    save = work_dir / "round_1.png"
    gen_data = _generate_image(
        expanded,
        aspect_ratio=ratio,
        save_path=save,
        negative_prompt=neg,
        seed=seed,
    )
    image_path = str(gen_data.get("save_path") or gen_data.get("path") or save)
    log = "\n".join(
        [
            f"扩写: {'跳过' if skipped else '已执行'}",
            f"版式: {layout or '-'} · 风格: {style or '-'}",
            f"宽高比: {ratio}",
            f"扩写后 Prompt 长度: {len(expanded)} 字",
        ]
    )
    return PipelineResult(
        expanded_prompt=expanded,
        expanded_prompt_path=str(expanded_path),
        pipeline_stages=stages,
        prompts_expand_skipped=skipped,
        prompts_expand_mode=mode,
        work_dir=str(work_dir),
        layout=layout,
        style=style,
        aspect_ratio=ratio,
        module_kind="generate",
        output_paths=[image_path, str(expanded_path)],
        log=log,
    )


def _run_series(
    lines: list[str],
    *,
    mode: str,
    aspect_ratio: str,
    negative_prompt: str,
    on_progress: ProgressFn | None,
) -> PipelineResult:
    from sn_studio.services.infographic_pipeline import (
        _result_text,
        _should_expand_auto,
        _text_optimize,
    )

    if not lines:
        raise RunError("请至少输入一行描述")

    work_dir = _work_dir("series")
    stages: list[dict[str, str]] = []
    neg = default_negative_prompt_chinese(negative_prompt)
    ratio = aspect_ratio or "16:9"
    shared_style = ""
    skipped = mode == "disable"

    if mode == "disable":
        shared_style = ""
    elif mode == "auto":
        _record_stage(stages, "evaluate", "评估中")
        _progress(on_progress, "评估中")
        brief = "\n".join(lines[:3])
        if not _should_expand_auto(brief):
            skipped = True

    if not skipped and mode != "disable":
        _record_stage(stages, "series_style", "系列风格统一")
        _progress(on_progress, "系列风格统一")
        brief = "系列主题（多图统一视觉）:\n" + "\n".join(f"- {ln}" for ln in lines)
        style_sys = inject_chinese_appendix(
            "为以下多图系列输出一段「共享视觉风格块」（150–250 字）："
            "配色、插画类型、字体气质、边框与留白。只输出风格块，不要逐张描述。"
        )
        style_data = _text_optimize(system_prompt=style_sys, user_prompt=brief, timeout=240)
        shared_style = _result_text(style_data)
        (work_dir / "shared-style-block.txt").write_text(shared_style, encoding="utf-8")

    (work_dir / "series-lines.txt").write_text("\n".join(lines), encoding="utf-8")
    series_seed = random.randint(0, 2**31 - 1)
    results: list[dict[str, Any]] = []
    paths: list[str] = []
    last_expanded = ""

    for i, line in enumerate(lines, 1):
        _record_stage(stages, "expand", f"扩写 Prompt ({i}/{len(lines)})")
        _progress(on_progress, f"扩写 Prompt ({i}/{len(lines)})")

        if skipped or mode == "disable":
            expanded = line
        else:
            expand_sys = inject_chinese_appendix(
                "在共享风格块约束下，将本张画面扩写为一条中文文生图 prompt（200–400 字）。"
                "只输出 prompt。"
            )
            user = line
            if shared_style:
                user = f"## 共享风格\n{shared_style}\n\n## 本张内容\n{line}"
            expand_data = _text_optimize(system_prompt=expand_sys, user_prompt=user, timeout=240)
            expanded = _result_text(expand_data) or line

        last_expanded = expanded
        (work_dir / f"expanded-prompt-{i:02d}.txt").write_text(expanded, encoding="utf-8")

        _record_stage(stages, "generate", f"生成图像 ({i}/{len(lines)})")
        _progress(on_progress, f"生成图像 ({i}/{len(lines)})")
        save = work_dir / f"{i:02d}.png"
        gen_data = _generate_image(
            expanded,
            aspect_ratio=ratio,
            save_path=save,
            negative_prompt=neg,
            seed=series_seed,
        )
        p = str(gen_data.get("save_path") or save)
        paths.append(p)
        results.append({"index": i, "path": p, "prompt": expanded[:200]})

    expanded_path = _save_expanded(work_dir, last_expanded)
    manifest = work_dir / "manifest.json"
    manifest.write_text(json.dumps(results, ensure_ascii=False, indent=2), encoding="utf-8")
    paths.append(str(manifest))
    paths.append(str(expanded_path))

    log = f"系列 {len(lines)} 张 · 扩写: {'跳过' if skipped else '已执行'} · 共享风格块: {len(shared_style)} 字"
    pr = PipelineResult(
        expanded_prompt=last_expanded,
        expanded_prompt_path=str(expanded_path),
        pipeline_stages=stages,
        prompts_expand_skipped=skipped,
        prompts_expand_mode=mode,
        work_dir=str(work_dir),
        aspect_ratio=ratio,
        module_kind="series",
        shared_style_block=shared_style,
        output_paths=paths,
        log=log,
        items=results,
    )
    return pr


def _run_imitate(
    reference_image: str,
    new_content: str,
    *,
    mode: str,
    aspect_ratio: str,
    negative_prompt: str,
    on_progress: ProgressFn | None,
) -> PipelineResult:
    from sn_studio.services.infographic_pipeline import _result_text, _text_optimize

    if not reference_image or not Path(reference_image).is_file():
        raise RunError("请上传有效的参考图")
    content = (new_content or "").strip()
    if not content:
        raise RunError("请输入新内容")

    work_dir = _work_dir("imitate")
    stages: list[dict[str, str]] = []
    ratio = aspect_ratio or "16:9"
    neg = default_negative_prompt_chinese(negative_prompt)
    skipped = mode == "disable"

    _record_stage(stages, "caption", "解析参考图")
    _progress(on_progress, "解析参考图")
    rec = run_agent_runner(
        [
            "sn-image-recognize",
            "--images",
            reference_image,
            "--user-prompt",
            "详细描述这张图的视觉风格、配色、构图、插画类型与版式结构，用于风格迁移。",
            "-o",
            "json",
        ],
        timeout=180,
    )
    style_desc = rec.get("text") or rec.get("content") or ""
    (work_dir / "reference-caption.txt").write_text(style_desc, encoding="utf-8")

    if skipped:
        expanded = f"{style_desc}\n\n新内容: {content}"
    else:
        _record_stage(stages, "rewrite", "改写 Prompt")
        _progress(on_progress, "改写 Prompt")
        rewrite_sys = inject_chinese_appendix(
            "根据参考图风格描述和用户新内容，生成一条完整的中文文生图 prompt。"
            "保持参考图的版式结构与风格，更新文字与主体内容；布局锁定，不随意改变分区。"
            "只输出 prompt。"
        )
        user = f"风格:\n{style_desc}\n\n新内容:\n{content}"
        expand_data = _text_optimize(system_prompt=rewrite_sys, user_prompt=user, timeout=240)
        expanded = _result_text(expand_data) or user
        (work_dir / "rewrite-system.md").write_text(rewrite_sys, encoding="utf-8")

    expanded_path = _save_expanded(work_dir, expanded)
    _record_stage(stages, "generate", "生成图像")
    _progress(on_progress, "生成图像")
    save = work_dir / "round_1.png"
    gen_data = _generate_image(expanded, aspect_ratio=ratio, save_path=save, negative_prompt=neg)
    image_path = str(gen_data.get("save_path") or save)

    log = f"风格模仿 · 扩写: {'跳过' if skipped else '已执行'} · 参考图 caption {len(style_desc)} 字"
    return PipelineResult(
        expanded_prompt=expanded,
        expanded_prompt_path=str(expanded_path),
        pipeline_stages=stages,
        prompts_expand_skipped=skipped,
        prompts_expand_mode=mode,
        work_dir=str(work_dir),
        aspect_ratio=ratio,
        module_kind="imitate",
        output_paths=[image_path, str(expanded_path)],
        log=log,
    )


def _run_resume(
    resume_text: str,
    *,
    style_hint: str,
    mode: str,
    aspect_ratio: str,
    negative_prompt: str,
    on_progress: ProgressFn | None,
) -> PipelineResult:
    from sn_studio.services.infographic_pipeline import _result_text, _text_optimize

    text = (resume_text or "").strip()
    if not text:
        raise RunError("请输入简历文本")

    work_dir = _work_dir("resume")
    stages: list[dict[str, str]] = []
    ratio = aspect_ratio or "9:16"
    neg = default_negative_prompt_chinese(negative_prompt)
    skipped = mode == "disable"

    resume_sys_path = skill_path("sn-image-resume") / "prompts" / "resume.md"
    if resume_sys_path.is_file():
        base_sys = resume_sys_path.read_text(encoding="utf-8")
    else:
        base_sys = (
            "将简历文本转为「个人简历海报」竖版视觉设计的中文文生图 prompt，"
            "强调排版、分区、图标，不要编造未提供的经历。"
        )
    sys_prompt = inject_chinese_appendix(base_sys)
    if style_hint.strip():
        sys_prompt += f"\n\n额外风格: {style_hint.strip()}"

    if skipped:
        expanded = text
    else:
        _record_stage(stages, "resume_expand", "简历排版扩写")
        _progress(on_progress, "简历排版扩写")
        expand_data = _text_optimize(system_prompt=sys_prompt, user_prompt=text, timeout=300)
        expanded = _result_text(expand_data) or text
        (work_dir / "resume-expand-system.md").write_text(sys_prompt, encoding="utf-8")

    expanded_path = _save_expanded(work_dir, expanded)
    _record_stage(stages, "generate", "生成图像")
    _progress(on_progress, "生成图像")
    save = work_dir / "round_1.png"
    gen_data = _generate_image(expanded, aspect_ratio=ratio, save_path=save, negative_prompt=neg)
    image_path = str(gen_data.get("save_path") or save)

    log = f"简历图 · 扩写: {'跳过' if skipped else '已执行'} · 宽高比 {ratio}"
    return PipelineResult(
        expanded_prompt=expanded,
        expanded_prompt_path=str(expanded_path),
        pipeline_stages=stages,
        prompts_expand_skipped=skipped,
        prompts_expand_mode=mode,
        work_dir=str(work_dir),
        aspect_ratio=ratio,
        module_kind="resume",
        output_paths=[image_path, str(expanded_path)],
        log=log,
    )


def pipeline_stages_summary(stages: list[dict[str, str]] | None) -> str:
    if not stages:
        return ""
    return " → ".join(s.get("label", s.get("id", "")) for s in stages)
