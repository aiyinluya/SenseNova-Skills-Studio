"""Settings, API test, environment doctors."""

from __future__ import annotations

import os
import time
from typing import Any

import httpx

from sn_studio.core.config import (
    apply_env_updates,
    mask_api_key_status,
    read_env_fields,
    reload_env,
    sanitize_log,
    validate_env,
    write_env_text,
)
from sn_studio.core.paths import find_repo_root, list_sn_skills, skill_path
from sn_studio.core.runner import run_command
from sn_studio.core import jobs


def _secret_update(incoming: str, existing: str) -> str | None:
    """Empty input preserves existing secret; non-empty replaces it."""
    s = (incoming or "").strip()
    if s:
        return s
    return None if existing else ""


def _optional_capability_key_update(incoming: str, existing: str) -> str | None:
    """Blank UI input removes optional override; non-empty sets a dedicated key."""
    s = (incoming or "").strip()
    if s:
        return s
    if existing:
        return ""  # remove override line from .env
    return None


def load_settings_form() -> dict[str, str]:
    """Values safe to show in UI (no full secrets)."""
    fields = read_env_fields()
    return {
        "base_url": fields.get(
            "SN_BASE_URL", "https://token.sensenova.cn/v1"
        ),
        "api_key_status": mask_api_key_status(fields.get("SN_API_KEY", "")),
        "image_gen_model": fields.get("SN_IMAGE_GEN_MODEL", ""),
        "skills_root": fields.get("SN_SKILLS_ROOT", ""),
        "image_gen_key_status": mask_api_key_status(
            fields.get("SN_IMAGE_GEN_API_KEY", "")
        ),
        "vision_key_status": mask_api_key_status(fields.get("SN_VISION_API_KEY", "")),
        "chat_key_status": mask_api_key_status(fields.get("SN_CHAT_API_KEY", "")),
        "skills_line": skills_compact_line(),
    }


def config_status_banner() -> str:
    """One-line API / env readiness for the Settings tab."""
    reload_env()
    errors, warnings = validate_env()
    if errors:
        return f"🔴 配置未完成：{errors[0]}"
    if warnings:
        return f"🟡 已配置（{warnings[0]}）"
    return "🟢 API 配置就绪"


def save_settings_form(
    base_url: str,
    api_key: str,
    image_gen_api_key: str = "",
    vision_api_key: str = "",
    chat_api_key: str = "",
    image_gen_model: str = "",
    skills_root: str = "",
) -> tuple[str, str, dict[str, str]]:
    """Persist form fields; returns (title, message, refreshed_form_display)."""
    fields = read_env_fields()
    updates: dict[str, str | None] = {
        "SN_BASE_URL": (base_url or "").strip(),
        "SN_API_KEY": _secret_update(api_key, fields.get("SN_API_KEY", "")),
        "SN_IMAGE_GEN_API_KEY": _optional_capability_key_update(
            image_gen_api_key, fields.get("SN_IMAGE_GEN_API_KEY", "")
        ),
        "SN_VISION_API_KEY": _optional_capability_key_update(
            vision_api_key, fields.get("SN_VISION_API_KEY", "")
        ),
        "SN_CHAT_API_KEY": _optional_capability_key_update(
            chat_api_key, fields.get("SN_CHAT_API_KEY", "")
        ),
        "SN_IMAGE_GEN_MODEL": (image_gen_model or "").strip() or None,
        "SN_SKILLS_ROOT": (skills_root or "").strip() or None,
    }
    content = apply_env_updates(updates)
    title, msg = save_settings(content)
    refreshed = load_settings_form()
    return title, msg, refreshed


def skills_compact_line() -> str:
    names = list_sn_skills()
    return f"已发现 **{len(names)}** 个技能（`skills/`）"


def save_settings(env_text: str) -> tuple[str, str]:
    errors, warnings = validate_env(env_text)
    if errors:
        return "保存失败", "\n".join(f"❌ {e}" for e in errors)
    path = write_env_text(env_text)
    msg = f"已保存到 {path}"
    if warnings:
        msg += "\n" + "\n".join(f"⚠️ {w}" for w in warnings)
    return "保存成功", msg


def test_api(show_raw: bool = False) -> str:
    reload_env()
    base = (os.environ.get("SN_BASE_URL") or "").rstrip("/")
    key = os.environ.get("SN_API_KEY") or ""
    if not base or not key:
        return "❌ 请先配置 SN_BASE_URL 与 SN_API_KEY"

    url = f"{base}/models"
    try:
        t0 = time.perf_counter()
        with httpx.Client(timeout=15.0) as client:
            resp = client.get(url, headers={"Authorization": f"Bearer {key}"})
        ms = int((time.perf_counter() - t0) * 1000)

        if resp.status_code == 200:
            lines = [f"✅ API 可达 · 延迟约 {ms} ms · HTTP {resp.status_code}"]
            try:
                body = resp.json()
                data = body.get("data") if isinstance(body, dict) else None
                if isinstance(data, list) and data:
                    ids = [str(m.get("id", m)) for m in data[:5]]
                    lines.append("模型示例: " + ", ".join(ids))
                    if len(data) > 5:
                        lines.append(f"（共 {len(data)} 个，仅显示前 5 个）")
                elif show_raw:
                    lines.append(sanitize_log(resp.text[:1200]))
            except (ValueError, TypeError):
                if show_raw:
                    lines.append(sanitize_log(resp.text[:800]))
            return "\n".join(lines)

        if resp.status_code == 404:
            return (
                f"✅ 网关响应 · 约 {ms} ms · HTTP {resp.status_code}\n"
                "（部分部署无 /models 端点，密钥已发送）\n"
                f"Base: {base}"
            )
        return f"⚠️ HTTP {resp.status_code} · {ms} ms\n{sanitize_log(resp.text[:300])}"
    except httpx.HTTPError as exc:
        return f"❌ 连接失败: {exc}"


def _format_doctor_log(which: str, code: int, combined: str) -> str:
    """Readable doctor output for Studio (no raw traceback prefix)."""
    label = "图像" if which == "image" else "PPT"
    body = (combined or "").strip()
    if "Traceback (most recent call last)" in body:
        lines = body.splitlines()
        summary_lines: list[str] = []
        for line in reversed(lines):
            stripped = line.strip()
            if stripped.startswith("UnicodeEncodeError:"):
                summary_lines.insert(
                    0,
                    "控制台编码无法显示检查结果（常见于 Windows GBK）。请更新 sn-image-doctor 后重试。",
                )
                break
            if stripped and not stripped.startswith("File "):
                summary_lines.insert(0, stripped)
                if len(summary_lines) >= 3:
                    break
        if summary_lines:
            body = "\n".join(summary_lines) + ("\n\n---\n" + body if body else "")
    if code == 0:
        return body or f"✅ {label}环境检查通过"
    header = f"检查完成（存在失败项，exit code={code}）"
    return f"{header}\n\n{body}" if body else header


def run_image_doctor() -> str:
    import sys

    script = skill_path("sn-image-doctor") / "scripts" / "check_environment.py"
    if not script.is_file():
        return f"❌ 未找到诊断脚本: {script}"
    env_path = find_repo_root() / ".env"
    cmd = [sys.executable, str(script)]
    if env_path.is_file():
        cmd.extend(["--env-path", str(env_path)])
    code, out, err = run_command(
        cmd,
        cwd=find_repo_root(),
        timeout=120,
    )
    combined = sanitize_log((out or "") + ("\n" + err if err else ""))
    return _format_doctor_log("image", code, combined)


def run_ppt_doctor(non_interactive: bool = True) -> str:
    ppt_doctor_dir = skill_path("sn-ppt-doctor")
    args = ["-m", "ppt_doctor", "--env-path", str(find_repo_root() / ".env")]
    if non_interactive:
        args.append("--non-interactive")
    from sn_studio.core.runner import run_command

    code, out, err = run_command(
        [__import__("sys").executable, *args],
        cwd=ppt_doctor_dir,
        timeout=180,
    )
    text = sanitize_log((out or "") + ("\n" + err if err else ""))
    return _format_doctor_log("ppt", code, text)


def skills_overview() -> str:
    """Deprecated alias; use skills_compact_line + top status banner."""
    return skills_compact_line()


def submit_doctor_job(which: str) -> jobs.Job:
    def _run() -> dict[str, Any]:
        log = run_image_doctor() if which == "image" else run_ppt_doctor()
        return {"log": log, "output_paths": []}

    return jobs.submit(f"doctor_{which}", {"which": which}, _run)
