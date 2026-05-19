"""SenseNova Skills Studio — Gradio application."""
from __future__ import annotations
import os
import subprocess
import sys
from pathlib import Path
from typing import Any
import gradio as gr
from sn_studio.core.config import reload_env
from sn_studio.core import jobs
from sn_studio.core.paths import find_repo_root, outputs_dir
from sn_studio.services import data_analysis, image, ppt, research, search, settings, update_helper
from sn_studio.ui.components.help_copy import (
    HELP_CSS,
    HELP_GEN_ALL,
    HELP_INFO_ALL,
    HELP_IMITATE_ALL,
    HELP_RESUME_ALL,
    HELP_SERIES_ALL,
    HELP_PPT_MODE,
    HELP_PPT_PAGES,
    HELP_RES_SCOPE,
    HELP_RES_TOPIC,
    HELP_SEARCH_CAT,
    HELP_SEARCH_LIMIT,
    HELP_SEARCH_PROV,
    help_md,
)
from sn_studio.ui.components.image_workspace import (
    SERIES_GALLERY_COLUMNS,
    ImageWorkspaceBuild,
    build_image_workspace,
    stage_indicator_update,
)
from sn_studio.ui.components.settings_panel import (
    SettingsPanelBuild,
    build_settings_panel,
    refresh_form_outputs,
)
from sn_studio.ui.components.job_status import (
    POLL_INTERVAL_SEC,
    _SKIP,
    on_submit,
    poll_pipeline_tick,
    poll_text_tick,
    toast,
    toast_for_terminal_job,
)
from sn_studio.ui.components.prompt_preview import (
    expanded_prompt_from_job_result,
    stages_line_from_job_result,
)
TITLE = "SenseNova Skills Studio"


def _open_folder(path: str) -> str:
    if not path:
        return "路径无效"
    p = Path(path)
    target = p if p.is_dir() else p.parent
    if not target.exists():
        return f"路径不存在: {target}"
    try:
        if sys.platform == "win32":
            os.startfile(str(target))  # noqa: S606
        elif sys.platform == "darwin":
            subprocess.run(["open", str(target)], check=False)
        else:
            subprocess.run(["xdg-open", str(target)], check=False)
    except OSError as exc:
        return f"无法打开文件夹（请手动复制路径）: {exc}"
    return f"已在资源管理器中打开: {target}"


def _open_job_output_folder(
    job_id: str,
    *,
    fallback_kind: str | None = None,
) -> str:
    folder = jobs.output_folder_for_open(job_id, fallback_kind=fallback_kind)
    if folder is None:
        return "请输入任务 ID"
    if not folder.exists():
        return f"路径不存在: {folder}"
    return _open_folder(str(folder))

def _stage_from_job(job_id: str) -> dict[str, Any]:
    if not job_id:
        return stage_indicator_update("")
    job = jobs.get_job(job_id)
    if job is None:
        return stage_indicator_update("任务不存在", failed=True)
    res = job.result if isinstance(job.result, dict) else {}
    if job.status == jobs.JobStatus.FAILED.value:
        line = stages_line_from_job_result(res) or jobs.preview_status_line(job)
        return stage_indicator_update(line, failed=True)
    if jobs.is_terminal(job) and job.status == jobs.JobStatus.DONE.value:
        line = jobs.preview_status_line(job).split("\n", 1)[0]
        return stage_indicator_update(line, done=True)
    line = stages_line_from_job_result(res) or jobs.preview_status_line(job)
    return stage_indicator_update(line)


def _submit_btn_from_job(job_id: str) -> dict[str, Any]:
    if not job_id:
        return gr.update(interactive=True)
    job = jobs.get_job(job_id)
    if job is None or jobs.is_terminal(job):
        return gr.update(interactive=True)
    return gr.update(interactive=False)


def _session_history_from_disk(
    *,
    kind: str | None = None,
    limit: int = 16,
) -> tuple[list, list[str]]:
    """Restore session thumb strip from ``outputs/.studio_jobs/jobs.json`` (or studio scan)."""
    return jobs.session_history_gallery(limit, kind=kind)


def _session_history_append(
    job_id: str,
    history_ids: list[str] | None,
    history_items: list | None,
) -> tuple[dict[str, Any], list[str], list]:
    """Append completed image job thumb to session strip (dedupe by job id)."""
    ids = list(history_ids or [])
    items = list(history_items or [])
    if not job_id or job_id in ids:
        return gr.update(value=items), ids, items
    job = jobs.get_job(job_id)
    if job is None or not jobs.is_terminal(job) or job.status != jobs.JobStatus.DONE.value:
        return gr.update(value=items), ids, items
    if not jobs.is_valid_image_series_job(job):
        return gr.update(value=items), ids, items
    imgs = jobs.image_paths_from_job(job)
    if not imgs:
        return gr.update(value=items), ids, items
    label = f"{job.kind.replace('image_', '')} · {job.id[:8]}"
    ids.append(job_id)
    items.append((imgs[0], label))
    return gr.update(value=items), ids, items


def _preview_from_job_id(job_id: str) -> tuple[Any, Any, Any, str]:
    """Load gallery, expanded prompt, stage bar, and job id for history pick."""
    if not job_id:
        return gr.update(), gr.update(), stage_indicator_update(""), ""
    job = jobs.get_job(job_id)
    if job is None:
        return gr.update(), gr.update(), stage_indicator_update("任务不存在", failed=True), ""
    res = job.result if isinstance(job.result, dict) else {}
    expanded = expanded_prompt_from_job_result(res)
    gal = jobs.gallery_update_for_job(job) if jobs.is_terminal(job) else gr.update()
    return gal, gr.update(value=expanded), _stage_from_job(job_id), job_id


def _wire_pipeline_image_job(
    ws: ImageWorkspaceBuild,
    submit_fn,
    job_state: gr.State,
    action_toast: gr.Markdown,
    detail: str,
    *,
    fallback_kind: str,
) -> None:
    poll_timer = ws.poll_timer
    poll_outputs = [
        ws.gallery,
        poll_timer,
        ws.expanded_tb,
        ws.stage_indicator,
        ws.submit_btn,
        ws.history_gallery,
        ws.history_job_ids,
        ws.history_items,
        action_toast,
    ]
    _poll_idle = (_SKIP,) * len(poll_outputs)

    def _submit(*args: Any):
        j = submit_fn(*args)
        jid, _status, timer_up = on_submit(j, detail)
        return (
            jid,
            timer_up,
            toast(f"⏳ {detail} · 已提交"),
            gr.update(value=""),
            stage_indicator_update(f"{detail} · 已提交，正在处理…"),
            gr.update(interactive=False),
        )

    def _poll(job_id: str, history_ids: list[str] | None, history_items: list | None):
        if not (job_id or "").strip():
            return _poll_idle
        gal, _log, timer, exp, _stages = poll_pipeline_tick(job_id)
        hist_gal, hist_ids, hist_items = _session_history_append(job_id, history_ids, history_items)
        job = jobs.get_job(job_id) if job_id else None
        toast_up = (
            toast_for_terminal_job(job)
            if job is not None and jobs.is_terminal(job)
            else _SKIP
        )
        return (
            gal,
            timer,
            exp,
            _stage_from_job(job_id),
            _submit_btn_from_job(job_id),
            hist_gal,
            hist_ids,
            hist_items,
            toast_up,
        )

    def _on_session_history_select(
        evt: gr.SelectData,
        history_ids: list[str] | None,
    ):
        ids = history_ids or []
        if evt is None or evt.index is None or evt.index < 0 or evt.index >= len(ids):
            return gr.skip(), gr.skip(), gr.skip(), gr.skip()
        gal, exp, stage, jid = _preview_from_job_id(ids[evt.index])
        return gal, exp, stage, jid

    ws.submit_btn.click(
        _submit,
        ws.submit_inputs,
        [
            job_state,
            poll_timer,
            action_toast,
            ws.expanded_tb,
            ws.stage_indicator,
            ws.submit_btn,
        ],
        show_progress="full",
    )
    poll_timer.tick(
        _poll,
        [job_state, ws.history_job_ids, ws.history_items],
        poll_outputs,
    )
    ws.open_output_btn.click(
        lambda jid: toast(_open_job_output_folder(jid, fallback_kind=fallback_kind)),
        job_state,
        action_toast,
    )
    ws.history_gallery.select(
        _on_session_history_select,
        [ws.history_job_ids],
        [ws.gallery, ws.expanded_tb, ws.stage_indicator, job_state],
    )

def build_app(theme: gr.themes.Base | None = None) -> gr.Blocks:
    block_kwargs: dict = {
        "title": TITLE,
        "css": HELP_CSS,
    }
    if theme is not None:
        block_kwargs["theme"] = theme
    with gr.Blocks(**block_kwargs) as app:
        gr.Markdown(f"# {TITLE}")
        action_toast = gr.Markdown("", elem_classes=["sn-toast"], visible=True)
        settings_poll_timer = gr.Timer(value=POLL_INTERVAL_SEC, active=False)
        with gr.Tabs():
            # ─── 设置 ───
            with gr.Tab("⚙️ 设置"):
                sp: SettingsPanelBuild = build_settings_panel()
                _form_refresh_targets = [
                    sp.base_url,
                    sp.api_key,
                    sp.api_key_status,
                    sp.image_gen_model,
                    sp.skills_root,
                    sp.image_gen_api_key,
                    sp.vision_api_key,
                    sp.chat_api_key,
                    sp.image_gen_key_status,
                    sp.vision_key_status,
                    sp.chat_key_status,
                    sp.skills_md,
                ]

                def _save(
                    base_url: str,
                    api_key: str,
                    image_gen_api_key: str,
                    vision_api_key: str,
                    chat_api_key: str,
                    image_gen_model: str,
                    skills_root: str,
                ):
                    title, msg, refreshed = settings.save_settings_form(
                        base_url,
                        api_key,
                        image_gen_api_key=image_gen_api_key,
                        vision_api_key=vision_api_key,
                        chat_api_key=chat_api_key,
                        image_gen_model=image_gen_model,
                        skills_root=skills_root,
                    )
                    icon = "✅" if title == "保存成功" else "❌"
                    return [
                        f"{icon} {title}\n{msg}",
                        *refresh_form_outputs(refreshed),
                        settings.config_status_banner(),
                    ]

                sp.save_btn.click(
                    _save,
                    [
                        sp.base_url,
                        sp.api_key,
                        sp.image_gen_api_key,
                        sp.vision_api_key,
                        sp.chat_api_key,
                        sp.image_gen_model,
                        sp.skills_root,
                    ],
                    [sp.settings_out, *_form_refresh_targets, sp.config_banner],
                    show_progress="full",
                )
                sp.test_btn.click(
                    settings.test_api,
                    sp.api_raw,
                    sp.settings_out,
                    show_progress="full",
                )

                def _refresh():
                    refreshed = settings.load_settings_form()
                    return [
                        settings.config_status_banner(),
                        *refresh_form_outputs(refreshed),
                        "已刷新环境",
                    ]

                sp.refresh_btn.click(
                    _refresh,
                    outputs=[sp.config_banner, *_form_refresh_targets, sp.settings_out],
                )

                def _doc_submit(which: str):
                    j = settings.submit_doctor_job(which)
                    label = "图像" if which == "image" else "PPT"
                    jid, line, timer_up = on_submit(j, f"{label} 诊断")
                    return jid, f"⏳ {label} 环境诊断中…\n{line}", timer_up

                sp.img_doc_btn.click(
                    lambda: _doc_submit("image"),
                    outputs=[sp.settings_job, sp.settings_out, settings_poll_timer],
                    show_progress="full",
                )
                sp.ppt_doc_btn.click(
                    lambda: _doc_submit("ppt"),
                    outputs=[sp.settings_job, sp.settings_out, settings_poll_timer],
                    show_progress="full",
                )
                settings_poll_timer.tick(
                    poll_text_tick,
                    sp.settings_job,
                    [sp.settings_out, settings_poll_timer],
                )
            # ─── 图像（左右分栏：左控制 / 右预览，见 image_workspace.py）───
            with gr.Tab("🖼️ 图像"):
                with gr.Tabs():
                    with gr.Tab("文生图"):
                        gen_job = gr.State("")

                        def _build_gen_controls():
                            gen_prompt = gr.Textbox(
                                label="画面描述",
                                lines=4,
                                placeholder="描述你想生成的画面…",
                            )
                            with gr.Row():
                                gen_ratio = gr.Dropdown(
                                    ["16:9", "9:16", "1:1", "4:3", "3:4"],
                                    value="16:9",
                                    label="宽高比",
                                )
                                gen_expand_mode = gr.Dropdown(
                                    choices=["auto", "force", "disable"],
                                    value="auto",
                                    label="扩写模式",
                                )
                            with gr.Accordion("高级参数", open=False):
                                gen_seed = gr.Number(label="Seed", value=-1, precision=0)
                                gen_neg = gr.Textbox(label="负向描述", lines=1)
                            return [gen_prompt, gen_ratio, gen_seed, gen_neg, gen_expand_mode]

                        _gen_hist_items, _gen_hist_ids = _session_history_from_disk(
                            kind="image_generate"
                        )
                        gen_ws = build_image_workspace(
                            _build_gen_controls,
                            job_state=gen_job,
                            fallback_kind="image_generate",
                            help_markdown=HELP_GEN_ALL,
                            session_history_items=_gen_hist_items,
                            session_history_job_ids=_gen_hist_ids,
                        )

                        def _submit_gen(prompt, ratio, seed, neg, mode):
                            seed_v = None if seed is None or int(seed) < 0 else int(seed)
                            return image.submit_image_job(
                                "generate",
                                prompt=prompt,
                                aspect_ratio=ratio,
                                seed=seed_v,
                                negative_prompt=neg or "",
                                prompts_expand_mode=mode,
                            )

                        _wire_pipeline_image_job(
                            gen_ws,
                            _submit_gen,
                            gen_job,
                            action_toast,
                            "文生图",
                            fallback_kind="image_generate",
                        )
                    with gr.Tab("信息图"):
                        info_job = gr.State("")

                        def _build_info_controls():
                            info_content = gr.Textbox(label="内容与数据", lines=6)
                            info_style = gr.Textbox(label="风格说明（可选）", lines=2)
                            with gr.Row():
                                info_expand_mode = gr.Dropdown(
                                    choices=["auto", "force", "disable"],
                                    value="auto",
                                    label="扩写模式",
                                )
                                info_max_rounds = gr.Slider(
                                    1,
                                    5,
                                    value=1,
                                    step=1,
                                    label="最大生成轮次",
                                )
                            return [info_content, info_style, info_expand_mode, info_max_rounds]

                        _info_hist_items, _info_hist_ids = _session_history_from_disk(
                            kind="image_infographic"
                        )
                        info_ws = build_image_workspace(
                            _build_info_controls,
                            job_state=info_job,
                            fallback_kind="image_infographic",
                            help_markdown=HELP_INFO_ALL,
                            button_label="生成信息图",
                            session_history_items=_info_hist_items,
                            session_history_job_ids=_info_hist_ids,
                        )

                        def _submit_info(c, s, mode, rounds):
                            return image.submit_image_job(
                                "infographic",
                                content=c,
                                style_hint=s or "",
                                prompts_expand_mode=mode,
                                max_rounds=int(rounds),
                            )

                        _wire_pipeline_image_job(
                            info_ws,
                            _submit_info,
                            info_job,
                            action_toast,
                            "信息图",
                            fallback_kind="image_infographic",
                        )
                    with gr.Tab("系列批量"):
                        series_job = gr.State("")

                        def _build_series_controls():
                            series_theme = gr.Textbox(
                                label="系列主题",
                                lines=4,
                                placeholder="例如：颈椎健康科普插画系列，温暖扁平风",
                            )
                            with gr.Row():
                                series_count = gr.Dropdown(
                                    choices=["3", "4", "5", "6", "7", "8"],
                                    value="6",
                                    label="张数",
                                )
                                series_ratio = gr.Dropdown(
                                    ["16:9", "9:16", "1:1"],
                                    value="16:9",
                                    label="宽高比",
                                )
                            series_style_hint = gr.Textbox(
                                label="风格锚点（可选）",
                                lines=2,
                                placeholder="如：扁平插画、蓝绿配色、同一卡通医生角色",
                            )
                            series_expand_mode = gr.Dropdown(
                                choices=["auto", "force", "disable"],
                                value="auto",
                                label="扩写模式",
                            )
                            return [
                                series_theme,
                                series_count,
                                series_style_hint,
                                series_ratio,
                                series_expand_mode,
                            ]

                        _series_hist_items, _series_hist_ids = _session_history_from_disk(
                            kind="image_series"
                        )
                        series_ws = build_image_workspace(
                            _build_series_controls,
                            job_state=series_job,
                            fallback_kind="image_series",
                            help_markdown=HELP_SERIES_ALL,
                            button_label="批量生成",
                            gallery_columns=SERIES_GALLERY_COLUMNS,
                            session_history_items=_series_hist_items,
                            session_history_job_ids=_series_hist_ids,
                        )

                        _wire_pipeline_image_job(
                            series_ws,
                            lambda theme, cnt, style, ratio, mode: image.submit_image_job(
                                "series",
                                theme=theme or "",
                                count=int(cnt or 6),
                                style_hint=style or "",
                                aspect_ratio=ratio,
                                prompts_expand_mode=mode,
                            ),
                            series_job,
                            action_toast,
                            "系列批量",
                            fallback_kind="image_series",
                        )
                    with gr.Tab("风格模仿"):
                        imitate_job = gr.State("")

                        def _build_imitate_controls():
                            imitate_ref = gr.Image(label="参考图", type="filepath", height=200)
                            imitate_content = gr.Textbox(label="新内容", lines=4)
                            imitate_expand_mode = gr.Dropdown(
                                choices=["auto", "force", "disable"],
                                value="auto",
                                label="扩写模式",
                            )
                            return [imitate_ref, imitate_content, imitate_expand_mode]

                        _imitate_hist_items, _imitate_hist_ids = _session_history_from_disk(
                            kind="image_imitate"
                        )
                        imitate_ws = build_image_workspace(
                            _build_imitate_controls,
                            job_state=imitate_job,
                            fallback_kind="image_imitate",
                            help_markdown=HELP_IMITATE_ALL,
                            button_label="模仿风格生成",
                            gallery_columns=1,
                            session_history_items=_imitate_hist_items,
                            session_history_job_ids=_imitate_hist_ids,
                        )

                        def _submit_imitate(ref, content, mode):
                            path = ref if isinstance(ref, str) else (ref or "")
                            return image.submit_image_job(
                                "imitate",
                                reference_image=path or "",
                                new_content=content or "",
                                prompts_expand_mode=mode,
                            )

                        _wire_pipeline_image_job(
                            imitate_ws,
                            _submit_imitate,
                            imitate_job,
                            action_toast,
                            "风格模仿",
                            fallback_kind="image_imitate",
                        )
                    with gr.Tab("简历图"):
                        resume_job = gr.State("")

                        def _build_resume_controls():
                            resume_text = gr.Textbox(label="简历文本", lines=10)
                            resume_style = gr.Textbox(label="风格备注", lines=2)
                            resume_expand_mode = gr.Dropdown(
                                choices=["auto", "force", "disable"],
                                value="auto",
                                label="扩写模式",
                            )
                            return [resume_text, resume_style, resume_expand_mode]

                        _resume_hist_items, _resume_hist_ids = _session_history_from_disk(
                            kind="image_resume"
                        )
                        resume_ws = build_image_workspace(
                            _build_resume_controls,
                            job_state=resume_job,
                            fallback_kind="image_resume",
                            help_markdown=HELP_RESUME_ALL,
                            button_label="生成简历海报",
                            gallery_columns=1,
                            session_history_items=_resume_hist_items,
                            session_history_job_ids=_resume_hist_ids,
                        )

                        _wire_pipeline_image_job(
                            resume_ws,
                            lambda t, s, mode: image.submit_image_job(
                                "resume",
                                resume_text=t,
                                style_notes=s or "",
                                prompts_expand_mode=mode,
                            ),
                            resume_job,
                            action_toast,
                            "简历图",
                            fallback_kind="image_resume",
                        )
            # ─── PPT ───
            with gr.Tab("📊 PPT"):
                ppt_topic = gr.Textbox(label="主题", lines=1)
                ppt_role = gr.Textbox(label="演讲者身份", value="产品经理")
                ppt_audience = gr.Textbox(label="受众", value="业务团队")
                ppt_scene = gr.Textbox(label="场景", value="内部分享")
                ppt_pages = gr.Slider(4, 30, value=10, step=1, label="页数")
                help_md(HELP_PPT_PAGES)
                ppt_mode = gr.Radio(["standard", "creative"], value="standard", label="模式")
                help_md(HELP_PPT_MODE)
                ppt_files = gr.File(label="参考文档 (pdf/docx/md/txt)", file_count="multiple")
                ppt_create = gr.Button("创建 Deck 目录与 JSON", variant="primary")
                ppt_deck_path = gr.Textbox(label="Deck 目录")
                ppt_stage = gr.Dropdown(ppt.STANDARD_STAGES, value="preflight", label="Standard 阶段")
                ppt_run = gr.Button("运行所选阶段")
                ppt_open = gr.Button("打开 Deck 文件夹")
                ppt_out = gr.Textbox(label="输出", lines=8)
                def _create_deck(topic, role, aud, scene, pages, mode, files):
                    paths = []
                    if files:
                        for f in files:
                            paths.append(f if isinstance(f, str) else f.name)
                    r = ppt.create_deck(topic, role, aud, scene, int(pages), mode, paths or None)
                    return r["deck_dir"], f"✅ 已创建:\n{r['deck_dir']}", toast("✅ Deck 已创建")
                ppt_create.click(
                    _create_deck,
                    [ppt_topic, ppt_role, ppt_audience, ppt_scene, ppt_pages, ppt_mode, ppt_files],
                    [ppt_deck_path, ppt_out, action_toast],
                    show_progress="full",
                )
                def _run_stage(d, s, progress=gr.Progress()):
                    if not d:
                        return "请先创建 Deck", toast("请先创建 Deck")
                    progress(0, desc="运行阶段…")
                    out = ppt.run_ppt_stage(d, s)
                    return out[:8000], toast(f"✅ 阶段 {s} 完成")
                ppt_run.click(
                    _run_stage,
                    [ppt_deck_path, ppt_stage],
                    [ppt_out, action_toast],
                    show_progress="full",
                )
                ppt_open.click(
                    lambda p: (_open_folder(p), toast("已在资源管理器中打开")),
                    ppt_deck_path,
                    [ppt_out, action_toast],
                )
            # ─── 数据分析 ───
            with gr.Tab("📈 数据分析"):
                excel_file = gr.File(label="Excel 文件 (.xlsx)", file_types=[".xlsx", ".xls"])
                excel_btn = gr.Button("探查 Sheet / 行数", variant="primary")
                excel_md = gr.Markdown()
                cap_image = gr.Image(label="图片 Caption", type="filepath")
                cap_prompt = gr.Textbox(label="自定义 Prompt（可选）", lines=2)
                cap_btn = gr.Button("运行 caption.py")
                cap_out = gr.Textbox(label="Caption 结果", lines=10)
                def _probe(f, progress=gr.Progress()):
                    if f is None:
                        return "请上传 Excel", toast("请上传 Excel")
                    progress(0, desc="探查中…")
                    path = f if isinstance(f, str) else f.name
                    md = data_analysis.probe_excel_markdown(path)
                    return md, toast("✅ Excel 探查完成")
                excel_btn.click(
                    _probe,
                    excel_file,
                    [excel_md, action_toast],
                    show_progress="full",
                )
                def _cap(img, pr, progress=gr.Progress()):
                    if not img:
                        return "请上传图片", toast("请上传图片")
                    progress(0, desc="识别中…")
                    path = img if isinstance(img, str) else img
                    text = data_analysis.caption_image(path, pr or "")
                    return text, toast("✅ Caption 完成")
                cap_btn.click(_cap, [cap_image, cap_prompt], [cap_out, action_toast], show_progress="full")
            # ─── 深度研究 ───
            with gr.Tab("🔬 深度研究"):
                res_topic = gr.Textbox(label="研究主题", lines=2)
                help_md(HELP_RES_TOPIC)
                res_scope = gr.Textbox(label="范围说明", lines=3)
                help_md(HELP_RES_SCOPE)
                res_init = gr.Button("创建 report_dir + request.md", variant="primary")
                res_dir = gr.Textbox(label="report_dir")
                res_refresh = gr.Button("刷新进度")
                res_progress = gr.Markdown()
                res_md = gr.File(label="report.md", file_types=[".md"])
                res_html_btn = gr.Button("导出 HTML (sn-md-to-html-report)")
                res_html_out = gr.Textbox(label="HTML 路径", lines=2)
                def _init_research_ui(topic: str, scope: str):
                    r = research.init_research(topic, scope or "")
                    d = r["report_dir"]
                    return d, research.progress_markdown(d), toast("✅ 研究目录已创建")
                res_init.click(
                    _init_research_ui,
                    [res_topic, res_scope],
                    [res_dir, res_progress, action_toast],
                    show_progress="full",
                )
                res_refresh.click(
                    lambda d: (
                        research.progress_markdown(d) if d else "无目录",
                        toast("已刷新进度"),
                    ),
                    res_dir,
                    [res_progress, action_toast],
                )
                def _html(f):
                    if f is None:
                        return "请上传 report.md", toast("请上传 report.md")
                    path = f if isinstance(f, str) else getattr(f, "name", str(f))
                    r = research.md_to_html(path)
                    return r["html"], toast("✅ HTML 已导出")
                res_html_btn.click(_html, res_md, [res_html_out, action_toast], show_progress="full")
            # ─── 搜索 ───
            with gr.Tab("🔍 搜索"):
                search_cat = gr.Dropdown(search.list_categories(), value="academic", label="类别")
                help_md(HELP_SEARCH_CAT)
                search_prov = gr.Dropdown(search.list_providers("academic"), value="arxiv", label="提供商")
                help_md(HELP_SEARCH_PROV)
                search_q = gr.Textbox(label="关键词", lines=1)
                search_limit = gr.Slider(1, 30, value=10, step=1, label="条数")
                help_md(HELP_SEARCH_LIMIT)
                search_btn = gr.Button("搜索", variant="primary")
                search_table = gr.Dataframe(
                    headers=["标题", "链接", "摘要"],
                    label="结果",
                    wrap=True,
                )
                search_err = gr.Textbox(label="状态", lines=2, interactive=False)
                def _on_cat(cat):
                    provs = search.list_providers(cat)
                    return gr.Dropdown(choices=provs, value=provs[0])
                search_cat.change(_on_cat, search_cat, search_prov)
                def _do_search(cat, prov, q, lim, progress=gr.Progress()):
                    if not q.strip():
                        yield [], "请输入关键词", toast("请输入关键词")
                        return
                    progress(0, desc="搜索中…")
                    yield [], "🔍 搜索中…", toast("🔍 搜索中…")
                    try:
                        data = search.search(cat, prov, q.strip(), int(lim))
                        rows = search.format_results_table(data)
                        if not rows:
                            yield [], f"无结果 ({data.get('provider')})", toast("无结果")
                            return
                        msg = f"✅ {len(rows)} 条 · {data.get('provider')}"
                        yield rows, msg, toast(msg)
                    except Exception as exc:
                        err = f"❌ {exc}"
                        yield [], err, toast(err)
                search_btn.click(
                    _do_search,
                    [search_cat, search_prov, search_q, search_limit],
                    [search_table, search_err, action_toast],
                    show_progress="full",
                )
            # ─── 更新 ───
            with gr.Tab("🔄 更新"):
                upd_status = gr.Textbox(label="Git 状态", lines=14, value=update_helper.git_status())
                upd_refresh = gr.Button("刷新状态")
                upd_pull = gr.Button("git pull --ff-only", variant="secondary")
                upd_out = gr.Textbox(label="结果", lines=6)
                upd_refresh.click(
                    lambda: (update_helper.git_status(), toast("已刷新 Git 状态")),
                    outputs=[upd_status, action_toast],
                )
                upd_pull.click(
                    lambda: (update_helper.git_pull(), toast("git pull 完成")),
                    outputs=[upd_out, action_toast],
                    show_progress="full",
                )
    return app

def _studio_allowed_paths() -> list[str]:
    roots = {str(find_repo_root().resolve()), str(outputs_dir().resolve())}
    return sorted(roots)


def launch(host: str = "127.0.0.1", port: int = 7860, share: bool = False, theme: str = "dark") -> None:
    reload_env()
    if theme == "light":
        th = gr.themes.Default(primary_hue="sky")
    else:
        th = gr.themes.Base(primary_hue="sky")
    app = build_app(theme=th)
    app.launch(
        server_name=host,
        server_port=port,
        share=share,
        show_error=True,
        allowed_paths=_studio_allowed_paths(),
    )
if __name__ == "__main__":
    launch()
