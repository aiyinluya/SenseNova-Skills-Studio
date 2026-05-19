"""Subprocess wrappers for skill scripts."""

from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path
from typing import Any

from sn_studio.core.config import reload_env, sanitize_log
from sn_studio.core.paths import agent_runner, find_repo_root


class RunError(Exception):
    def __init__(self, message: str, returncode: int = 1, stdout: str = "", stderr: str = ""):
        super().__init__(message)
        self.returncode = returncode
        self.stdout = stdout
        self.stderr = stderr


def _run(
    cmd: list[str],
    *,
    cwd: Path | None = None,
    timeout: float | None = 600,
    env_extra: dict[str, str] | None = None,
) -> subprocess.CompletedProcess[str]:
    import os

    reload_env()
    env = os.environ.copy()
    # Child scripts may print Unicode markers; force UTF-8 on Windows consoles.
    env.setdefault("PYTHONIOENCODING", "utf-8")
    if sys.platform == "win32":
        env.setdefault("PYTHONUTF8", "1")
    if env_extra:
        env.update(env_extra)

    return subprocess.run(
        cmd,
        cwd=str(cwd or find_repo_root()),
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
        timeout=timeout,
        env=env,
    )


def _strip_traceback_tail(text: str, max_lines: int = 40) -> str:
    """Drop Python traceback blocks from captured script output."""
    lines = text.splitlines()
    out: list[str] = []
    for line in lines:
        if line.startswith("Traceback (most recent call last):"):
            break
        out.append(line)
    trimmed = "\n".join(out).strip()
    if trimmed:
        return trimmed
    return "\n".join(lines[-max_lines:]).strip()


def run_command(
    cmd: list[str],
    *,
    cwd: Path | None = None,
    timeout: float | None = 600,
) -> tuple[int, str, str]:
    proc = _run(cmd, cwd=cwd, timeout=timeout)
    return proc.returncode, proc.stdout, proc.stderr


def run_agent_runner(args: list[str], *, timeout: float = 600) -> dict[str, Any]:
    """Run sn_agent_runner.py; parse last JSON line from stdout."""
    runner = agent_runner()
    if not runner.is_file():
        raise RunError(f"未找到 runner: {runner}")

    cmd = [sys.executable, str(runner), *args]
    code, out, err = run_command(cmd, timeout=timeout)
    log = sanitize_log((out or "") + "\n" + (err or ""))

    if code != 0:
        raise RunError(f"sn_agent_runner 失败 (code={code})", code, out, err)

    for line in reversed((out or "").strip().splitlines()):
        line = line.strip()
        if line.startswith("{"):
            try:
                return json.loads(line)
            except json.JSONDecodeError:
                continue

    raise RunError("未解析到 JSON 输出", code, out, err)


def run_json_script(
    script: Path,
    script_args: list[str],
    *,
    cwd: Path | None = None,
    timeout: float = 120,
) -> dict[str, Any]:
    """Run a skill script that prints JSON to stdout."""
    if not script.is_file():
        raise RunError(f"脚本不存在: {script}")

    cmd = [sys.executable, str(script), *script_args]
    code, out, err = run_command(cmd, cwd=cwd or script.parent, timeout=timeout)
    text = (out or "").strip()
    if not text and err:
        text = err.strip()

    try:
        data = json.loads(text)
    except json.JSONDecodeError as exc:
        raise RunError(
            f"JSON 解析失败: {exc}\n{sanitize_log(text[:500])}",
            code,
            out,
            err,
        ) from exc

    if code != 0 and not data.get("success", True):
        raise RunError(data.get("error", f"exit {code}"), code, out, err)

    return data


def run_text_script(
    script: Path,
    script_args: list[str],
    *,
    cwd: Path | None = None,
    timeout: float = 300,
) -> str:
    if not script.is_file():
        raise RunError(f"脚本不存在: {script}")
    cmd = [sys.executable, str(script), *script_args]
    code, out, err = run_command(cmd, cwd=cwd or script.parent, timeout=timeout)
    combined = sanitize_log((out or "") + ("\n" + err if err else ""))
    if code != 0:
        user_text = _strip_traceback_tail(combined) or combined
        raise RunError(f"脚本失败 (code={code})\n{user_text}", code, out, err)
    return combined
