"""Load, validate, and persist .env configuration."""

from __future__ import annotations

import os
import re
from pathlib import Path
from typing import Any

from dotenv import dotenv_values, load_dotenv

from sn_studio.core.paths import env_file, find_repo_root


def reload_env() -> Path:
    """Load .env into os.environ; return path used."""
    path = env_file()
    if path.is_file():
        load_dotenv(path, override=True)
    return path


def read_env_text() -> str:
    path = env_file()
    if path.is_file():
        return path.read_text(encoding="utf-8")
    example = find_repo_root() / ".env.example"
    if example.is_file():
        return example.read_text(encoding="utf-8")
    return "SN_BASE_URL=https://token.sensenova.cn/v1\nSN_API_KEY=\n"


def write_env_text(content: str) -> Path:
    path = env_file()
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")
    reload_env()
    return path


def parse_env_dict(content: str) -> dict[str, str]:
    result: dict[str, str] = {}
    for line in content.splitlines():
        line = line.strip()
        if not line or line.startswith("#"):
            continue
        if "=" not in line:
            continue
        key, _, val = line.partition("=")
        result[key.strip()] = val.strip().strip('"').strip("'")
    return result


def validate_env(content: str | None = None) -> tuple[list[str], list[str]]:
    """Return (errors, warnings)."""
    data = parse_env_dict(content) if content is not None else dict(dotenv_values(env_file()))
    errors: list[str] = []
    warnings: list[str] = []

    base = data.get("SN_BASE_URL", "") or os.environ.get("SN_BASE_URL", "")
    key = data.get("SN_API_KEY", "") or os.environ.get("SN_API_KEY", "")

    if not base:
        errors.append("缺少 SN_BASE_URL")
    elif not base.startswith("http"):
        errors.append("SN_BASE_URL 应以 http:// 或 https:// 开头")

    if not key:
        errors.append("缺少 SN_API_KEY（可在 https://platform.sensenova.cn 申请）")
    elif len(key) < 8:
        warnings.append("SN_API_KEY 似乎过短")

    return errors, warnings


def mask_secret(value: str, visible: int = 4) -> str:
    if not value:
        return "(未设置)"
    if len(value) <= visible * 2:
        return "***"
    return f"{value[:visible]}...{value[-visible:]}"


def mask_api_key_status(value: str) -> str:
    """Human-readable API key status for UI (never the full secret)."""
    if not value or not value.strip():
        return "未配置"
    v = value.strip()
    if v.startswith("sk-"):
        if len(v) <= 8:
            return "已配置 (sk-****)"
        return f"已配置 (sk-…{v[-4:]})"
    tail = v[-4:] if len(v) >= 4 else "****"
    return f"已配置 (…{tail})"


SECRET_ENV_KEYS = frozenset(
    {
        "SN_API_KEY",
        "SN_IMAGE_GEN_API_KEY",
        "SN_VISION_API_KEY",
        "SN_CHAT_API_KEY",
    }
)

FORM_ENV_KEYS = (
    "SN_BASE_URL",
    "SN_API_KEY",
    "SN_IMAGE_GEN_API_KEY",
    "SN_VISION_API_KEY",
    "SN_CHAT_API_KEY",
    "SN_IMAGE_GEN_MODEL",
    "SN_SKILLS_ROOT",
)

# Optional per-capability keys; blank means fall back to SN_API_KEY / SN_CHAT_API_KEY.
OPTIONAL_FALLBACK_ENV_KEYS = frozenset({
    "SN_IMAGE_GEN_API_KEY",
    "SN_VISION_API_KEY",
    "SN_CHAT_API_KEY",
})


def read_env_fields() -> dict[str, str]:
    """Read known .env keys (values as stored on disk, not for UI display of secrets)."""
    path = env_file()
    if path.is_file():
        data = dict(dotenv_values(path))
    else:
        data = parse_env_dict(read_env_text())
    reload_env()
    out: dict[str, str] = {}
    for key in FORM_ENV_KEYS:
        val = (data.get(key) or os.environ.get(key) or "").strip()
        if val:
            out[key] = val
    return out


def apply_env_updates(updates: dict[str, str | None]) -> str:
    """Merge updates into .env text. None for a key means keep the existing value."""
    path = env_file()
    if path.is_file():
        lines = path.read_text(encoding="utf-8").splitlines()
    else:
        lines = read_env_text().splitlines()

    seen: set[str] = set()
    new_lines: list[str] = []

    for line in lines:
        stripped = line.strip()
        if stripped and not stripped.startswith("#") and "=" in stripped:
            key, _, _rest = line.partition("=")
            key = key.strip()
            if key in updates:
                seen.add(key)
                val = updates[key]
                if val is None:
                    new_lines.append(line)
                elif val == "" and key in OPTIONAL_FALLBACK_ENV_KEYS:
                    continue  # drop empty override so SN_API_KEY fallback applies
                else:
                    new_lines.append(f"{key}={val}")
                continue
        if (
            stripped
            and not stripped.startswith("#")
            and "=" in stripped
            and stripped.split("=", 1)[0].strip() in OPTIONAL_FALLBACK_ENV_KEYS
            and not stripped.split("=", 1)[1].strip()
        ):
            continue  # strip legacy empty override lines on any save
        new_lines.append(line)

    for key in FORM_ENV_KEYS:
        if key in updates and key not in seen:
            val = updates[key]
            if val is None:
                continue
            if val == "" and key in OPTIONAL_FALLBACK_ENV_KEYS:
                continue
            new_lines.append(f"{key}={val}")

    return "\n".join(new_lines) + ("\n" if new_lines else "")


def config_summary() -> dict[str, Any]:
    reload_env()
    return {
        "SN_BASE_URL": os.environ.get("SN_BASE_URL", ""),
        "SN_API_KEY": mask_secret(os.environ.get("SN_API_KEY", "")),
        "SN_IMAGE_GEN_MODEL": os.environ.get("SN_IMAGE_GEN_MODEL", "(默认 sensenova-u1-fast)"),
        "SN_CHAT_MODEL": os.environ.get("SN_CHAT_MODEL", "(默认)"),
        "repo_root": str(find_repo_root()),
        "skills_count": len(__import__("sn_studio.core.paths", fromlist=["list_sn_skills"]).list_sn_skills()),
    }


def sanitize_log(text: str) -> str:
    """Remove likely secrets from log snippets."""
    patterns = [
        (r"sk-[A-Za-z0-9_-]{8,}", "sk-***"),
        (r"(SN_API_KEY=)([^\s]+)", r"\1***"),
        (r"(api[_-]?key[\"']?\s*[:=]\s*[\"']?)([^\"'\s]+)", r"\1***", re.I),
    ]
    out = text
    for item in patterns:
        if len(item) == 2:
            pat, repl = item
            flags = 0
        else:
            pat, repl, flags = item  # type: ignore[misc]
        out = re.sub(pat, repl, out, flags=flags)
    return out
