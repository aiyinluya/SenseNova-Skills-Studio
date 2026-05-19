"""Settings tab: structured .env form without exposing secrets."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

import gradio as gr

from sn_studio.services import settings


@dataclass
class SettingsPanelBuild:
    config_banner: gr.Markdown
    base_url: gr.Textbox
    api_key: gr.Textbox
    api_key_status: gr.Markdown
    image_gen_model: gr.Textbox
    skills_root: gr.Textbox
    image_gen_api_key: gr.Textbox
    vision_api_key: gr.Textbox
    chat_api_key: gr.Textbox
    image_gen_key_status: gr.Markdown
    vision_key_status: gr.Markdown
    chat_key_status: gr.Markdown
    save_btn: gr.Button
    test_btn: gr.Button
    refresh_btn: gr.Button
    api_raw: gr.Checkbox
    settings_out: gr.Textbox
    skills_md: gr.Markdown
    img_doc_btn: gr.Button
    ppt_doc_btn: gr.Button
    settings_job: gr.State


def build_settings_panel() -> SettingsPanelBuild:
    form = settings.load_settings_form()
    with gr.Group():
        config_banner = gr.Markdown(
            settings.config_status_banner(),
            elem_classes=["sn-settings-status"],
        )
        gr.Markdown("### API 连接")
        base_url = gr.Textbox(
            label="SN_BASE_URL",
            value=form["base_url"],
            info="OpenAI 兼容网关地址",
        )
        api_key_status = gr.Markdown(f"**SN_API_KEY：** {form['api_key_status']}")
        api_key = gr.Textbox(
            label="SN_API_KEY",
            type="password",
            value="",
            placeholder="输入新密钥以更新；留空则保留已保存的值",
        )
        with gr.Accordion("可选配置", open=False):
            image_gen_model = gr.Textbox(
                label="SN_IMAGE_GEN_MODEL",
                value=form["image_gen_model"],
                placeholder="默认 sensenova-u1-fast",
            )
            skills_root = gr.Textbox(
                label="SN_SKILLS_ROOT",
                value=form["skills_root"],
                placeholder="留空则自动发现仓库根目录",
            )
            image_gen_key_status = gr.Markdown(
                f"**SN_IMAGE_GEN_API_KEY：** {form['image_gen_key_status']}"
            )
            image_gen_api_key = gr.Textbox(
                label="SN_IMAGE_GEN_API_KEY",
                type="password",
                value="",
                placeholder="留空不修改",
            )
            vision_key_status = gr.Markdown(
                f"**SN_VISION_API_KEY：** {form['vision_key_status']}"
            )
            vision_api_key = gr.Textbox(
                label="SN_VISION_API_KEY",
                type="password",
                value="",
                placeholder="留空不修改",
            )
            chat_key_status = gr.Markdown(
                f"**SN_CHAT_API_KEY：** {form['chat_key_status']}"
            )
            chat_api_key = gr.Textbox(
                label="SN_CHAT_API_KEY",
                type="password",
                value="",
                placeholder="留空不修改",
            )
        with gr.Row():
            save_btn = gr.Button("保存配置", variant="primary")
            test_btn = gr.Button("测试 API")
            refresh_btn = gr.Button("刷新状态")
        api_raw = gr.Checkbox(label="显示 API 原始响应", value=False)
        settings_out = gr.Textbox(label="操作结果", lines=5, max_lines=12)
        skills_md = gr.Markdown(form["skills_line"])
        with gr.Row():
            img_doc_btn = gr.Button("图像环境诊断")
            ppt_doc_btn = gr.Button("PPT 环境诊断")

    return SettingsPanelBuild(
        config_banner=config_banner,
        base_url=base_url,
        api_key=api_key,
        api_key_status=api_key_status,
        image_gen_model=image_gen_model,
        skills_root=skills_root,
        image_gen_api_key=image_gen_api_key,
        vision_api_key=vision_api_key,
        chat_api_key=chat_api_key,
        image_gen_key_status=image_gen_key_status,
        vision_key_status=vision_key_status,
        chat_key_status=chat_key_status,
        save_btn=save_btn,
        test_btn=test_btn,
        refresh_btn=refresh_btn,
        api_raw=api_raw,
        settings_out=settings_out,
        skills_md=skills_md,
        img_doc_btn=img_doc_btn,
        ppt_doc_btn=ppt_doc_btn,
        settings_job=gr.State(""),
    )


def refresh_form_outputs(form: dict[str, str]) -> list[Any]:
    """Gradio outputs after save/refresh (clears password fields)."""
    return [
        form["base_url"],
        "",
        gr.update(value=f"**SN_API_KEY：** {form['api_key_status']}"),
        form["image_gen_model"],
        form["skills_root"],
        "",
        "",
        "",
        gr.update(value=f"**SN_IMAGE_GEN_API_KEY：** {form['image_gen_key_status']}"),
        gr.update(value=f"**SN_VISION_API_KEY：** {form['vision_key_status']}"),
        gr.update(value=f"**SN_CHAT_API_KEY：** {form['chat_key_status']}"),
        form["skills_line"],
    ]


SAVE_FORM_INPUTS = [
    "base_url",
    "api_key",
    "image_gen_api_key",
    "vision_api_key",
    "chat_api_key",
    "image_gen_model",
    "skills_root",
]
