"""Chinese help snippets for Studio inputs."""

from __future__ import annotations

import gradio as gr

HELP_CSS = """
.sn-help { font-size: 0.85rem; opacity: 0.85; margin: 0.2rem 0 0.6rem 0; }
.sn-toast { font-size: 0.95rem; padding: 0.35rem 0.6rem; border-radius: 6px;
  background: rgba(14,165,233,0.12); margin-bottom: 0.5rem; }
.sn-toast:empty,
.sn-toast p:empty { display: none !important; margin: 0 !important; padding: 0 !important; min-height: 0 !important; }
.sn-settings-status {
  font-size: 0.95rem; padding: 0.4rem 0.65rem; margin-bottom: 0.75rem;
  border-radius: 6px; background: rgba(22,163,74,0.08);
}
.sn-job-log-hidden,
.sn-job-log-hidden.wrap { display: none !important; height: 0 !important; min-height: 0 !important;
  margin: 0 !important; padding: 0 !important; border: none !important; overflow: hidden !important; }

/* Image workspace: left control ~40% | right preview ~60% */
#sn-image-workspace { gap: 1rem; align-items: flex-start !important; }
.sn-image-left {
  min-width: 360px; max-width: 480px; align-self: flex-start;
  flex: 0 1 auto !important;
}
.sn-image-left .accordion,
.sn-image-left details {
  flex: 0 0 auto !important;
  min-height: unset !important;
  height: auto !important;
}
.sn-image-left .form { align-items: flex-start; }
.sn-image-right { flex: 1; min-width: 0; align-self: stretch; }
.sn-expanded-prompt textarea {
  max-height: 240px !important;
  overflow-y: auto !important;
  resize: vertical;
}
.sn-session-history { margin-top: 0.35rem; }
.sn-session-history .grid-wrap {
  min-height: unset !important;
  max-height: 96px !important;
  overflow-x: auto !important;
  overflow-y: hidden !important;
}
/* Gradio 5: pack thumbs in a single left-aligned row (no 1fr column stretch) */
.sn-session-history .grid-container,
.sn-session-history .grid,
.sn-session-history .empty-gallery {
  display: flex !important;
  flex-wrap: nowrap !important;
  gap: 8px !important;
  justify-content: flex-start !important;
  align-items: flex-start !important;
  width: max-content !important;
  max-width: 100% !important;
}
.sn-session-history .gallery-item,
.sn-session-history .grid > *,
.sn-session-history .thumbnail-item,
.sn-session-history .grid-item,
.sn-session-history button.thumbnail-item,
.sn-session-history button.grid-item {
  width: 80px !important;
  min-width: 80px !important;
  max-width: 80px !important;
  height: 80px !important;
  min-height: 80px !important;
  max-height: 80px !important;
  flex: 0 0 80px !important;
  padding: 0 !important;
}
.sn-session-history .thumbnail-item img,
.sn-session-history .grid-item img,
.sn-session-history button img {
  width: 80px !important;
  height: 80px !important;
  max-width: 80px !important;
  max-height: 80px !important;
  object-fit: cover !important;
  display: block !important;
}
.sn-session-history .upload,
.sn-session-history .upload-container,
.sn-session-history .upload-box,
.sn-session-history .upload-area,
.sn-session-history [data-testid="upload-button"],
.sn-session-history label[for*="file"],
.sn-session-history .empty.large,
.sn-session-history .empty.small {
  display: none !important;
  visibility: hidden !important;
  height: 0 !important;
  min-height: 0 !important;
  padding: 0 !important;
  margin: 0 !important;
  overflow: hidden !important;
}
.sn-open-output-row { gap: 0.5rem; align-items: center; margin-top: 0.25rem; }
.sn-stage-bar {
  font-size: 0.9rem; padding: 0.5rem 0.65rem; margin-bottom: 0.35rem;
  border-left: 3px solid #0ea5e9; background: rgba(14,165,233,0.06);
  border-radius: 0 6px 6px 0;
}
.sn-stage-failed { border-left-color: #dc2626; background: rgba(220,38,38,0.08); }
.sn-stage-done { border-left-color: #16a34a; background: rgba(22,163,74,0.08); }
.sn-gallery-empty-hint {
  font-size: 0.85rem; opacity: 0.7; margin: 0 0 0.35rem 0;
}
/* Main result preview: in-panel grid only; lightbox uses Gradio .preview (do not style via button img) */
.sn-gallery-main,
.sn-result-preview {
  box-shadow: 0 1px 3px rgba(0,0,0,.08);
}
.sn-gallery-main .grid-wrap,
.sn-result-preview .grid-wrap {
  min-height: unset !important;
  max-height: 360px !important;
  overflow-y: auto !important;
}
/* Override Gradio 5 grid: repeat(N, minmax(100px, 1fr)) spreads columns across full width */
.sn-gallery-main .grid-container,
.sn-result-preview .grid-container {
  justify-content: start !important;
  align-content: start !important;
  justify-items: start !important;
  grid-template-columns: repeat(var(--grid-cols), minmax(120px, 160px)) !important;
  grid-auto-rows: minmax(120px, auto) !important;
  gap: 10px !important;
  width: fit-content !important;
  max-width: 100% !important;
}
.sn-gallery-main .grid-wrap .gallery-item,
.sn-result-preview .grid-wrap .gallery-item {
  width: 100% !important;
  max-width: 160px !important;
  height: auto !important;
}
/* In-panel thumbnails only — exclude .preview overlay (Gradio lightbox) */
.sn-gallery-main .grid-wrap .gallery-item .thumbnail-item,
.sn-gallery-main .grid-wrap .gallery-item .thumbnail-lg,
.sn-result-preview .grid-wrap .gallery-item .thumbnail-item,
.sn-result-preview .grid-wrap .gallery-item .thumbnail-lg {
  width: 140px !important;
  min-width: 120px !important;
  max-width: 160px !important;
  height: 140px !important;
  max-height: 160px !important;
  margin-inline: 0 !important;
}
.sn-gallery-main .grid-wrap .gallery-item .thumbnail-item img,
.sn-gallery-main .grid-wrap .gallery-item .thumbnail-lg img,
.sn-result-preview .grid-wrap .gallery-item .thumbnail-item img,
.sn-result-preview .grid-wrap .gallery-item .thumbnail-lg img {
  width: 100% !important;
  max-width: 160px !important;
  height: 100% !important;
  max-height: 160px !important;
  object-fit: contain !important;
  display: block !important;
  margin-inline: 0 !important;
}
/* Lightbox: restore natural aspect ratio (panel rules must not leak here) */
.sn-gallery-main .preview .media-button,
.sn-result-preview .preview .media-button {
  width: 100% !important;
  max-height: none !important;
  display: flex !important;
  align-items: center !important;
  justify-content: center !important;
}
.sn-gallery-main .preview .media-button img,
.sn-gallery-main .preview [data-testid="detailed-image"],
.sn-result-preview .preview .media-button img,
.sn-result-preview .preview [data-testid="detailed-image"] {
  width: auto !important;
  max-width: 100% !important;
  height: auto !important;
  max-height: min(85vh, 100%) !important;
  object-fit: contain !important;
  margin-inline: auto !important;
}
.sn-generate-btn { margin-top: 0.5rem; }

@media (max-width: 960px) {
  #sn-image-workspace { flex-direction: column !important; }
  .sn-image-left { min-width: unset; max-width: unset; width: 100%; }
  .sn-image-right { width: 100%; }
  .sn-gallery-main .grid-wrap,
  .sn-result-preview .grid-wrap { max-height: 280px !important; }
  .sn-gallery-main .grid-wrap .gallery-item .thumbnail-item,
  .sn-gallery-main .grid-wrap .gallery-item .thumbnail-lg,
  .sn-result-preview .grid-wrap .gallery-item .thumbnail-item,
  .sn-result-preview .grid-wrap .gallery-item .thumbnail-lg {
    width: 120px !important;
    height: 120px !important;
    max-height: 120px !important;
  }
  .sn-gallery-main .grid-wrap .gallery-item .thumbnail-item img,
  .sn-gallery-main .grid-wrap .gallery-item .thumbnail-lg img,
  .sn-result-preview .grid-wrap .gallery-item .thumbnail-item img,
  .sn-result-preview .grid-wrap .gallery-item .thumbnail-lg img {
    max-height: 120px !important;
  }
}
"""


def help_md(text: str) -> gr.Markdown:
    return gr.Markdown(text, elem_classes=["sn-help"])


# ── Image ──
HELP_GEN_PROMPT = "描述画面主体、风格与构图；中英文均可。"
HELP_GEN_RATIO = "输出宽高比：16:9 横屏、9:16 竖屏、1:1 方图等。"
HELP_GEN_SEED = "≥0 可复现同一张图；-1 表示每次随机。"
HELP_GEN_NEG = "不希望出现的元素，可留空。"
HELP_EXPAND_MODE = (
    "**扩写模式**（所有图像 Tab 通用）：`auto` 先评估再决定是否走完整流水线；"
    "`force` 始终执行 评估→分析→版式/风格→扩写→出图；`disable` 原文直出图（调试用）。"
)
HELP_PROMPT_ACCORDION = (
    "任务完成后在 **「扩写后的 Prompt」** 折叠区查看最终生图字符串；"
    "可复制核对图中中文文案。文件路径见 `expanded_prompt_path`。"
)
HELP_INFO_VS_GEN = (
    "**信息图**：完整 `sn-infographic`（含 layout/style 参考文件）。"
    "**文生图**：轻量五段流水线（分析+版式关键词+扩写）。两者均不会在未扩写时把短句直送生图（`disable` 除外）。"
)
HELP_INFO_EXPAND = HELP_EXPAND_MODE
HELP_INFO_MAX_ROUNDS = (
    "Studio 当前执行第 1 轮出图；`max_rounds>1` 的多轮 VLM 评审请在 Cursor 中加载完整 `sn-infographic` skill。"
)

# ── PPT ──
HELP_PPT_MODE = (
    "**standard**：按 `run_stage.py` 分阶段生成结构化 PPT。\n"
    "**creative**：每页独立 PNG，更自由、耗时更长。"
)
HELP_PPT_PAGES = "建议 8–15 页；页数过多会显著增加生成时间。"

# ── Search ──
HELP_SEARCH_CAT = "学术 / 代码 / 社交对应不同 skill 搜索脚本。"
HELP_SEARCH_PROV = "如 arXiv、GitHub；部分社交源需环境变量 cookie，失败时见状态行。"
HELP_SEARCH_LIMIT = "返回条数 1–30；过大可能超时。"

# ── Research ──
HELP_RES_TOPIC = "写入 `request.md` 标题；完整多轮调研请在 Cursor 中继续 Agent。"
HELP_RES_SCOPE = "时间范围、地域、对比对象等边界说明。"

# ── Image workspace (merged help for left-panel Accordion) ──
HELP_GEN_ALL = "\n\n".join(
    [
        f"**画面描述** — {HELP_GEN_PROMPT}",
        f"**宽高比** — {HELP_GEN_RATIO}",
        f"**Seed** — {HELP_GEN_SEED}",
        f"**负向描述** — {HELP_GEN_NEG}",
        HELP_EXPAND_MODE,
        HELP_PROMPT_ACCORDION,
    ]
)
HELP_INFO_ALL = "\n\n".join(
    [
        HELP_INFO_VS_GEN,
        HELP_INFO_EXPAND,
        HELP_INFO_MAX_ROUNDS,
        HELP_PROMPT_ACCORDION,
    ]
)
HELP_SERIES_THEME = (
    "用一句话描述整组图的题材与调性；系统会自动拆成多张分镜并统一视觉风格。"
)
HELP_SERIES_COUNT = "生成张数 3–8；张数越多耗时越长。"
HELP_SERIES_STYLE_ANCHOR = "可选：配色、画风、固定角色等关键词，会写入共享风格块。"
HELP_SERIES_ALL = "\n\n".join(
    [
        f"**系列主题** — {HELP_SERIES_THEME}",
        f"**张数** — {HELP_SERIES_COUNT}",
        f"**风格锚点** — {HELP_SERIES_STYLE_ANCHOR}",
        HELP_EXPAND_MODE,
        HELP_PROMPT_ACCORDION,
    ]
)
HELP_IMITATE_ALL = "\n\n".join(
    [
        "**参考图** — 上传风格参考；**新内容** — 要在同风格下呈现的主题。",
        HELP_EXPAND_MODE,
        HELP_PROMPT_ACCORDION,
    ]
)
HELP_RESUME_ALL = "\n\n".join(
    [
        "**简历文本** — 粘贴或输入简历正文；**风格备注** — 可选视觉偏好。",
        HELP_EXPAND_MODE,
        HELP_PROMPT_ACCORDION,
    ]
)
