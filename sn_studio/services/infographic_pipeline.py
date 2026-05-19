"""sn-infographic workflow for Studio (parity with SKILL.md via sn_agent_runner)."""

from __future__ import annotations

import json
import random
import re
from datetime import datetime
from pathlib import Path
from typing import Any, Callable

from sn_studio.core.paths import skill_path, studio_output_dir
from sn_studio.core.runner import RunError, run_agent_runner
from sn_studio.services.prompt_text import inject_chinese_appendix

ProgressFn = Callable[[str], None]

INFOG_SKILL = "sn-infographic"
LAYOUT_FALLBACK = "hub-spoke"
STYLE_FALLBACK = "corporate-memphis"

# data_type -> (primary_layout, alternative_layouts)
_LAYOUT_BY_DATA_TYPE: dict[str, tuple[str, list[str]]] = {
    "timeline": ("linear-progression", ["winding-roadmap", "step-staircase", "one-way-flow"]),
    "history": ("linear-progression", ["winding-roadmap", "step-staircase"]),
    "process": ("linear-progression", ["winding-roadmap", "step-staircase", "swimlane"]),
    "tutorial": ("linear-progression", ["winding-roadmap", "step-staircase"]),
    "comparison": ("binary-comparison", ["four-quadrant-grid", "conflict-contrast"]),
    "hierarchy": ("hierarchical-layers", ["axial-expansion", "deconstruction"]),
    "relationships": ("hub-spoke", ["jigsaw", "multi-focal", "venn-diagram"]),
    "data": ("dashboard", ["periodic-table", "data-landscape"]),
    "metrics": ("dashboard", ["periodic-table", "data-landscape"]),
    "cycle": ("circular-flow", ["s-curve", "wave-path"]),
    "loop": ("circular-flow", ["s-curve", "wave-path"]),
    "system": ("structural-breakdown", ["multi-scale", "containerization"]),
    "structure": ("structural-breakdown", ["multi-scale", "containerization"]),
    "journey": ("winding-roadmap", ["story-mountain", "comic-strip"]),
    "narrative": ("winding-roadmap", ["story-mountain", "full-illustration"]),
    "overview": ("bento-grid", ["periodic-table", "containerization"]),
    "summary": ("bento-grid", ["periodic-table", "containerization"]),
    "problem": ("iceberg", ["conflict-contrast", "funnel"]),
    "solution": ("iceberg", ["conflict-contrast", "funnel"]),
    "categories": ("periodic-table", ["bento-grid", "tile-layout"]),
    "collection": ("periodic-table", ["bento-grid", "tile-layout"]),
    "spatial": ("multi-scale", ["strong-perspective", "panorama"]),
    "geographic": ("multi-scale", ["isometric-map", "panorama"]),
    "workflow": ("swimlane", ["linear-progression", "modular-repetition"]),
    "feature": ("modular-repetition", ["bento-grid", "containerization"]),
    "catalog": ("modular-repetition", ["bento-grid", "containerization"]),
    "single": ("single-focal-point", ["big-typography", "header-body"]),
    "dialogue": ("speech-bubbles", ["character-guide", "comic-strip"]),
    "discovery": ("nonlinear-path", ["scene-unfolding", "hidden-details"]),
    "network": ("multi-focal", ["hub-spoke", "multi-directional"]),
    "report": ("header-body", ["swiss-grid", "chapter-layout"]),
    "marketing": ("z-pattern", ["tile-layout", "full-bleed-image"]),
}

_STYLE_BY_CONTEXT: dict[str, tuple[str, list[str]]] = {
    "technical": ("technical-schematic", ["ikea-manual", "ui-wireframe", "technical-diagram"]),
    "engineering": ("technical-schematic", ["technical-diagram", "parametric-design"]),
    "software": ("tech-brand", ["material-design", "corporate-memphis"]),
    "product": ("tech-brand", ["material-design", "corporate-memphis"]),
    "sci-fi": ("neon-futurism", ["cyberpunk", "sci-fi-ui", "synthwave"]),
    "futuristic": ("neon-futurism", ["cyberpunk", "holographic"]),
    "professional": ("corporate-memphis", ["swiss-style", "minimalism", "flat-design"]),
    "business": ("corporate-memphis", ["swiss-style", "flat-design"]),
    "data": ("data-visualization", ["technical-diagram", "swiss-style"]),
    "analytics": ("data-visualization", ["technical-diagram", "minimalism"]),
    "educational": ("chalkboard", ["instructional-visual", "ikea-manual"]),
    "instructional": ("chalkboard", ["instructional-visual", "paper-collage"]),
    "playful": ("paper-collage", ["cartoon-flat", "kawaii", "crayon-hand-drawn"]),
    "casual": ("paper-collage", ["cartoon-flat", "kawaii"]),
    "kids": ("paper-collage", ["cartoon-flat", "kawaii"]),
    "luxury": ("luxury-minimal", ["fashion-editorial", "art-deco"]),
    "premium": ("luxury-minimal", ["fashion-editorial"]),
    "chinese": ("chinese-guochao", ["modern-ink-wash"]),
    "japanese": ("ukiyo-e", ["kawaii"]),
    "vintage": ("aged-academia", ["vintage-poster", "newspaper-collage"]),
    "retro": ("aged-academia", ["vintage-poster", "screen-print"]),
    "artistic": ("impressionism", ["expressionism", "cubism"]),
    "handmade": ("paper-collage", ["storybook-watercolor", "claymation"]),
    "craft": ("paper-collage", ["storybook-watercolor", "screen-print"]),
    "illustration": ("pen-sketch", ["line-drawing", "marker-style"]),
    "experimental": ("deconstructivism", ["glitch-art", "op-art"]),
    "scandinavian": ("scandinavian", ["minimalism", "swiss-style"]),
    "minimal": ("minimalism", ["scandinavian", "swiss-style"]),
    "marketing": ("high-contrast-ad", ["screen-print", "flat-design"]),
    "medical": ("instructional-visual", ["flat-design", "corporate-memphis"]),
    "health": ("instructional-visual", ["flat-design", "scandinavian"]),
}

_DATA_TYPE_KEYWORDS: list[tuple[str, str]] = [
    (r"时间线|历史|演变|年代|历程|退化|阶段", "timeline"),
    (r"步骤|流程|教程|如何|四步|五步", "process"),
    (r"对比|vs|相比|优劣|前后", "comparison"),
    (r"层次|架构|分级|金字塔", "hierarchy"),
    (r"关系|关联|网络|生态", "relationships"),
    (r"数据|指标|KPI|统计|占比", "data"),
    (r"循环|闭环|反馈", "cycle"),
    (r"系统|结构|组成|解剖", "system"),
    (r"旅程|故事|叙事", "journey"),
    (r"概览|总结|要点", "overview"),
    (r"问题|解决|方案", "problem"),
    (r"分类|集合|目录", "categories"),
    (r"地图|地理|空间", "spatial"),
    (r"泳道|跨部门|工作流", "workflow"),
    (r"功能|特性|清单", "feature"),
    (r"问答|FAQ|对话", "dialogue"),
    (r"报告|长文|白皮书", "report"),
]

_STYLE_KEYWORDS: list[tuple[str, str]] = [
    (r"技术|工程|原理|解剖|医学|颈椎|脊柱", "technical"),
    (r"软件|产品|科技|互联网", "software"),
    (r"科幻|未来|赛博", "sci-fi"),
    (r"商务|企业|专业", "professional"),
    (r"数据|图表|可视化", "data"),
    (r"教育|科普|教学", "educational"),
    (r"活泼|儿童|趣味", "playful"),
    (r"高端|奢华|时尚", "luxury"),
    (r"国潮|中国风|水墨", "chinese"),
    (r"复古|怀旧", "vintage"),
    (r"手绘|插画", "illustration"),
    (r"极简|简约|北欧", "minimal"),
    (r"营销|广告|宣传", "marketing"),
    (r"健康|医疗", "medical"),
]


def _infographic_dir() -> Path:
    return skill_path(INFOG_SKILL)


def _ref(name: str) -> Path:
    p = _infographic_dir() / "references" / name
    if not p.is_file():
        raise RunError(f"缺少 sn-infographic 参考文件: {p}")
    return p


def _progress(on_progress: ProgressFn | None, stage: str) -> None:
    if on_progress:
        on_progress(stage)


def _text_optimize(
    *,
    system_prompt_path: Path | None = None,
    system_prompt: str = "",
    user_prompt: str,
    timeout: float = 180,
) -> dict[str, Any]:
    args = ["sn-text-optimize", "--user-prompt", user_prompt, "-o", "json"]
    if system_prompt_path and system_prompt_path.is_file():
        args.extend(["--system-prompt-path", str(system_prompt_path)])
    elif system_prompt.strip():
        args.extend(["--system-prompt", system_prompt.strip()])
    return run_agent_runner(args, timeout=timeout)


def _result_text(data: dict[str, Any]) -> str:
    return (data.get("result") or data.get("text") or data.get("content") or "").strip()


def _parse_json_blob(text: str) -> dict[str, Any] | None:
    text = text.strip()
    if not text:
        return None
    try:
        parsed = json.loads(text)
        if isinstance(parsed, dict):
            return parsed
    except json.JSONDecodeError:
        pass
    match = re.search(r"\{[\s\S]*\}", text)
    if match:
        try:
            parsed = json.loads(match.group(0))
            if isinstance(parsed, dict):
                return parsed
        except json.JSONDecodeError:
            return None
    return None


def _weighted_pick(primary: str, alternatives: list[str], extras: list[str] | None = None) -> str:
    pool: list[str] = [primary] * 10 + alternatives * 9
    if extras:
        pool.extend(extras)
    if not pool:
        return primary
    return random.choice(pool)


def _infer_data_type(text: str, analysis: dict[str, Any] | None) -> str:
    if analysis:
        for key in ("data_type", "content_type", "type"):
            val = analysis.get(key)
            if isinstance(val, str) and val.strip():
                return val.strip().lower().replace(" ", "_").split("/")[0]
    combined = text.lower()
    for pattern, dtype in _DATA_TYPE_KEYWORDS:
        if re.search(pattern, combined, re.I):
            return dtype
    return "overview"


def _infer_style_context(text: str, analysis: dict[str, Any] | None, style_hint: str) -> str:
    if style_hint.strip():
        hint = style_hint.lower()
        for ctx in _STYLE_BY_CONTEXT:
            if ctx in hint:
                return ctx
    if analysis:
        for key in ("tone", "style_context", "domain", "audience"):
            val = analysis.get(key)
            if isinstance(val, str) and val.strip():
                token = val.strip().lower()
                for ctx in _STYLE_BY_CONTEXT:
                    if ctx in token:
                        return ctx
    combined = f"{text} {style_hint}".lower()
    for pattern, ctx in _STYLE_KEYWORDS:
        if re.search(pattern, combined, re.I):
            return ctx
    return "professional"


def _select_layout_style(
    user_prompt: str,
    analysis: dict[str, Any] | None,
    style_hint: str,
) -> tuple[str, str]:
    dtype = _infer_data_type(user_prompt, analysis)
    ctx = _infer_style_context(user_prompt, analysis, style_hint)

    layout_primary, layout_alts = _LAYOUT_BY_DATA_TYPE.get(
        dtype, (LAYOUT_FALLBACK, ["bento-grid", "linear-progression"])
    )
    style_primary, style_alts = _STYLE_BY_CONTEXT.get(
        ctx, (STYLE_FALLBACK, ["flat-design", "minimalism"])
    )

    all_layouts = {v[0] for v in _LAYOUT_BY_DATA_TYPE.values()} | {LAYOUT_FALLBACK}
    all_styles = {v[0] for v in _STYLE_BY_CONTEXT.values()} | {STYLE_FALLBACK}
    extra_layouts = random.sample(sorted(all_layouts - {layout_primary}), k=min(3, max(0, len(all_layouts) - 1)))
    extra_styles = random.sample(sorted(all_styles - {style_primary}), k=min(3, max(0, len(all_styles) - 1)))

    layout = _weighted_pick(layout_primary, layout_alts, extra_layouts)
    style = _weighted_pick(style_primary, style_alts, extra_styles)
    return layout, style


def _read_layout_style_defs(layout: str, style: str) -> tuple[str, str]:
    layouts_dir = _infographic_dir() / "references" / "layouts"
    styles_dir = _infographic_dir() / "references" / "styles"

    layout_path = layouts_dir / f"{layout}.md"
    if not layout_path.is_file():
        layout = LAYOUT_FALLBACK
        layout_path = layouts_dir / f"{layout}.md"

    style_path_file = styles_dir / f"{style}.md"
    if not style_path_file.is_file():
        style = STYLE_FALLBACK
        style_path_file = styles_dir / f"{style}.md"

    layout_def = layout_path.read_text(encoding="utf-8") if layout_path.is_file() else ""
    style_def = style_path_file.read_text(encoding="utf-8") if style_path_file.is_file() else ""
    return layout, style, layout_def, style_def


def _should_expand_auto(user_prompt: str) -> bool:
    data = _text_optimize(system_prompt_path=_ref("evaluation-standard.md"), user_prompt=user_prompt)
    eval_obj = _parse_json_blob(_result_text(data))
    if not eval_obj:
        return True

    required = eval_obj.get("required_results") or []
    optional = eval_obj.get("optional_results") or []

    def _yes(item: Any) -> bool:
        if not isinstance(item, dict):
            return False
        return str(item.get("answer", "")).strip().lower() == "yes"

    required_pass = bool(required) and all(_yes(r) for r in required)
    if optional:
        optional_pass = sum(1 for r in optional if _yes(r)) / len(optional) >= 0.6
    else:
        optional_pass = True
    return not (required_pass and optional_pass)


def _infer_aspect_ratio(user_prompt: str) -> str:
    text = user_prompt.lower()
    if re.search(r"竖屏|竖版|9:16|手机壁纸|story", text):
        return "9:16"
    if re.search(r"方形|1:1|头像", text):
        return "1:1"
    if re.search(r"海报|2:3|书封", text):
        return "2:3"
    if re.search(r"幻灯|ppt|4:3", text):
        return "4:3"
    if re.search(r"横幅|banner|21:9|电影", text):
        return "21:9"
    if re.search(r"横屏|横版|16:9|宽屏", text):
        return "16:9"
    return "16:9"


def _build_structured_content(
    user_prompt: str,
    analysis_text: str,
    style_hint: str,
) -> str:
    template = _ref("structured-content-template.md").read_text(encoding="utf-8")
    system = (
        f"{template}\n\n---\n\n"
        "根据以下分析结果与用户原文，按模板输出 Markdown 结构化内容。"
        "禁止编造原文没有的事实；短输入可合理展开视觉标签与分区，但主题必须来自用户。"
    )
    user = user_prompt
    if style_hint.strip():
        user += f"\n\n风格偏好: {style_hint.strip()}"
    if analysis_text.strip():
        user = f"## 内容分析\n{analysis_text}\n\n## 用户原文\n{user}"
    data = _text_optimize(system_prompt=system, user_prompt=user, timeout=240)
    return _result_text(data) or user_prompt


def _expand_prompt(
    structured_content: str,
    layout: str,
    style: str,
    layout_def: str,
    style_def: str,
    work_dir: Path,
) -> str:
    expand_base = inject_chinese_appendix(
        _ref("prompts-expand-system.md").read_text(encoding="utf-8")
    )
    base_prompt = _ref("base-prompt.md").read_text(encoding="utf-8")
    system_path = work_dir / "expand-system-prompt.md"
    system_path.write_text(
        "\n\n---\n\n".join(
            [
                expand_base,
                f"## Selected Layout: {layout}\n\n{layout_def}",
                f"## Selected Style: {style}\n\n{style_def}",
                f"## Output Template Reference\n\n{base_prompt}",
            ]
        ),
        encoding="utf-8",
    )
    data = _text_optimize(system_prompt_path=system_path, user_prompt=structured_content, timeout=300)
    raw = _result_text(data)
    parsed = _parse_json_blob(raw)
    if parsed and isinstance(parsed.get("result"), str):
        expanded = parsed["result"].strip()
    else:
        expanded = raw.strip()
    if not expanded:
        raise RunError("Prompt 扩写失败：模型返回为空")
    if len(expanded) < len(structured_content) * 0.5 and len(structured_content) > 80:
        raise RunError("Prompt 扩写结果过短，可能不完整")
    return expanded


def run_infographic_pipeline(
    content: str,
    *,
    style_hint: str = "",
    prompts_expand_mode: str = "auto",
    max_rounds: int = 1,
    on_progress: ProgressFn | None = None,
) -> dict[str, Any]:
    """Full sn-infographic expand → generate pipeline."""
    user_prompt = (content or "").strip()
    if not user_prompt:
        raise RunError("请输入信息图内容")

    mode = (prompts_expand_mode or "auto").strip().lower()
    if mode not in ("auto", "force", "disable"):
        raise RunError(f"无效的扩写模式: {prompts_expand_mode}")

    max_rounds = max(1, int(max_rounds))
    ts = datetime.now().strftime("%Y%m%d_%H%M%S")
    work_dir = studio_output_dir() / "infographic" / ts
    work_dir.mkdir(parents=True, exist_ok=True)

    aspect_ratio = _infer_aspect_ratio(user_prompt)
    prompts_expand_skipped = False
    analysis_text = ""
    layout = LAYOUT_FALLBACK
    style = STYLE_FALLBACK

    if mode == "disable":
        expanded_prompt = user_prompt
        prompts_expand_skipped = True
        _progress(on_progress, "生成图像")
    else:
        should_expand = True
        if mode == "auto":
            _progress(on_progress, "评估中")
            should_expand = _should_expand_auto(user_prompt)

        if not should_expand:
            expanded_prompt = user_prompt
            prompts_expand_skipped = True
            _progress(on_progress, "生成图像")
        else:
            _progress(on_progress, "分析版式")
            analysis_data = _text_optimize(
                system_prompt_path=_ref("analysis-framework.md"),
                user_prompt=user_prompt,
                timeout=240,
            )
            analysis_text = _result_text(analysis_data)
            (work_dir / "analysis.json").write_text(analysis_text, encoding="utf-8")
            analysis_obj = _parse_json_blob(analysis_text)

            layout, style = _select_layout_style(user_prompt, analysis_obj, style_hint)
            layout, style, layout_def, style_def = _read_layout_style_defs(layout, style)
            (work_dir / "layout-style.json").write_text(
                json.dumps({"layout": layout, "style": style}, ensure_ascii=False),
                encoding="utf-8",
            )

            structured = _build_structured_content(user_prompt, analysis_text, style_hint)
            (work_dir / "structured-content.md").write_text(structured, encoding="utf-8")

            _progress(on_progress, "扩写 Prompt")
            expanded_prompt = _expand_prompt(
                structured, layout, style, layout_def, style_def, work_dir
            )

            _progress(on_progress, "生成图像")

    expanded_path = work_dir / "expanded-prompt.txt"
    expanded_path.write_text(expanded_prompt, encoding="utf-8")

    save = work_dir / "round_1.png"
    gen_args = [
        "sn-image-generate",
        "--prompt",
        expanded_prompt,
        "--aspect-ratio",
        aspect_ratio,
        "--image-size",
        "2k",
        "--save-path",
        str(save),
        "-o",
        "json",
    ]
    gen_data = run_agent_runner(gen_args, timeout=600)
    image_path = str(gen_data.get("save_path") or gen_data.get("path") or save)

    log_lines = [
        f"扩写: {'跳过' if prompts_expand_skipped else '已执行'}",
        f"版式: {layout} · 风格: {style}",
        f"宽高比: {aspect_ratio}",
        f"扩写后 Prompt 长度: {len(expanded_prompt)} 字",
    ]
    if max_rounds > 1:
        log_lines.append("提示: max_rounds>1 的 VLM 评审请在 Cursor Agent 中使用完整 sn-infographic skill。")

    pipeline_stages: list[dict[str, str]] = []
    if prompts_expand_skipped:
        pipeline_stages.append({"id": "generate", "label": "生成图像"})
    else:
        pipeline_stages = [
            {"id": "evaluate", "label": "评估中"},
            {"id": "layout", "label": "分析版式"},
            {"id": "expand", "label": "扩写 Prompt"},
            {"id": "generate", "label": "生成图像"},
        ]

    return {
        **gen_data,
        "output_paths": [image_path, str(expanded_path)],
        "expanded_prompt": expanded_prompt,
        "expanded_prompt_path": str(expanded_path),
        "prompts_expand_skipped": prompts_expand_skipped,
        "prompts_expand_mode": mode,
        "pipeline_stages": pipeline_stages,
        "module_kind": "infographic",
        "layout": layout,
        "style": style,
        "aspect_ratio": aspect_ratio,
        "work_dir": str(work_dir),
        "log": "\n".join(log_lines),
    }
