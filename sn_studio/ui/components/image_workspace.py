"""Left-control / right-preview layout shell for image Studio tabs."""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass
from typing import Any

import gradio as gr

from sn_studio.ui.components.job_status import POLL_INTERVAL_SEC, strip_status_prefix
from sn_studio.ui.components.prompt_preview import build_prompt_preview_block

# Main result preview: ~35–40% of 1080p viewport; click opens Gradio lightbox.
DEFAULT_GALLERY_HEIGHT = 340
# Series batch: up to 4 cols; Gradio clamps to min(columns, image count).
SERIES_GALLERY_COLUMNS = 4

@dataclass(frozen=True)
class ImageWorkspaceBuild:
    """Components returned for outer job wiring."""

    gallery: gr.Gallery
    poll_timer: gr.Timer
    expanded_tb: gr.Textbox
    stage_indicator: gr.Markdown
    submit_btn: gr.Button
    submit_inputs: list[Any]
    open_output_btn: gr.Button
    history_gallery: gr.Gallery
    history_job_ids: gr.State
    history_items: gr.State


def build_image_workspace(
    build_controls: Callable[[], list[Any]],
    *,
    job_state: gr.State,
    fallback_kind: str,
    gallery_columns: int = 2,
    gallery_height: int = DEFAULT_GALLERY_HEIGHT,
    button_label: str = "生成",
    help_markdown: str = "",
    empty_state: str = "尚无生成结果 · 在左侧输入描述后点击生成",
    session_history_items: list | None = None,
    session_history_job_ids: list[str] | None = None,
) -> ImageWorkspaceBuild:
    """
    Build a 40/60 left-control | right-preview Row (stacks below 960px via CSS).

    ``build_controls`` runs inside the left column and must return submit input
    components in wire order. The primary submit button is always placed at the
    bottom of the left column.
    """
    submit_inputs: list[Any] = []
    poll_timer = gr.Timer(value=POLL_INTERVAL_SEC, active=False)

    with gr.Row(
        elem_id="sn-image-workspace",
        equal_height=False,
    ):
        with gr.Column(scale=4, elem_classes=["sn-image-left"]):
            submit_inputs = build_controls()
            if help_markdown.strip():
                with gr.Accordion("参数说明", open=False):
                    gr.Markdown(help_markdown, elem_classes=["sn-help"])
            submit_btn = gr.Button(button_label, variant="primary", elem_classes=["sn-generate-btn"])

        with gr.Column(scale=6, elem_classes=["sn-image-right"]):
            stage_indicator = gr.Markdown(
                value="*等待生成…*",
                elem_classes=["sn-stage-bar"],
            )
            gr.Markdown(empty_state, elem_classes=["sn-gallery-empty-hint"])
            gallery = gr.Gallery(
                label="结果预览",
                columns=gallery_columns,
                height=gallery_height,
                object_fit="contain",
                allow_preview=True,
                elem_classes=["sn-gallery-main", "sn-result-preview"],
            )
            _hist_items = list(session_history_items or [])
            _hist_ids = list(session_history_job_ids or [])
            history_items = gr.State(_hist_items)
            history_job_ids = gr.State(_hist_ids)
            history_gallery = gr.Gallery(
                label="本会话历史（点击缩略图回看）",
                value=_hist_items or None,
                # Many columns + CSS flex pack: thumbs stay adjacent, row scrolls horizontally.
                columns=12,
                height=96,
                object_fit="cover",
                allow_preview=False,
                interactive=False,
                show_download_button=False,
                show_fullscreen_button=False,
                elem_classes=["sn-session-history"],
            )

            _, expanded_tb = build_prompt_preview_block()

            with gr.Row(elem_classes=["sn-open-output-row"]):
                open_output_btn = gr.Button("打开输出文件夹", size="sm")

    return ImageWorkspaceBuild(
        gallery=gallery,
        poll_timer=poll_timer,
        expanded_tb=expanded_tb,
        stage_indicator=stage_indicator,
        submit_btn=submit_btn,
        submit_inputs=submit_inputs,
        open_output_btn=open_output_btn,
        history_gallery=history_gallery,
        history_job_ids=history_job_ids,
        history_items=history_items,
    )


def stage_indicator_update(line: str, *, failed: bool = False, done: bool = False) -> dict[str, Any]:
    """Format pipeline stage text for the right-pane stage bar."""
    if failed:
        body = strip_status_prefix(line or "生成失败")
        return gr.update(value=f"❌ **{body}**", elem_classes=["sn-stage-bar", "sn-stage-failed"])

    if done:
        body = strip_status_prefix(line or "已完成")
        return gr.update(value=f"✅ **{body}**", elem_classes=["sn-stage-bar", "sn-stage-done"])

    if line:
        body = strip_status_prefix(line)
        return gr.update(value=f"⏳ {body}", elem_classes=["sn-stage-bar"])
    return gr.update(value="*处理中…*", elem_classes=["sn-stage-bar"])
