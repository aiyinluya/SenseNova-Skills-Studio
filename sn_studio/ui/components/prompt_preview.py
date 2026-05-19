"""Collapsible expanded-prompt preview for image tabs."""

from __future__ import annotations

from typing import Any

import gradio as gr

from sn_studio.services.prompt_pipeline import pipeline_stages_summary


def build_prompt_preview_block() -> tuple[gr.Accordion, gr.Textbox]:
    """Returns (accordion, expanded_prompt_box). Pipeline stages live in stage bar only."""
    with gr.Accordion("扩写后的 Prompt", open=False) as accordion:
        expanded_tb = gr.Textbox(
            label="",
            lines=8,
            max_lines=24,
            interactive=False,
            placeholder="任务完成后显示扩写结果…",
            show_copy_button=True,
            elem_classes=["sn-expanded-prompt"],
        )
    return accordion, expanded_tb


def expanded_prompt_from_job_result(result: dict[str, Any] | None) -> str:
    if not result:
        return ""
    ep = result.get("expanded_prompt")
    return ep if isinstance(ep, str) else ""


def stages_line_from_job_result(result: dict[str, Any] | None) -> str:
    if not result:
        return ""
    stages = result.get("pipeline_stages")
    if isinstance(stages, list) and stages:
        return pipeline_stages_summary(stages)
    if result.get("prompts_expand_skipped"):
        return "已跳过扩写，直接生成"
    return ""
