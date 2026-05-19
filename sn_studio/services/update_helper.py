"""sn-update helper — git status and safe pull hints."""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path

from sn_studio.core.paths import find_repo_root, list_sn_skills


def git_status() -> str:
    root = find_repo_root()
    try:
        proc = subprocess.run(
            ["git", "status", "-sb"],
            cwd=str(root),
            capture_output=True,
            text=True,
            encoding="utf-8",
            timeout=30,
        )
        branch = subprocess.run(
            ["git", "rev-parse", "--abbrev-ref", "HEAD"],
            cwd=str(root),
            capture_output=True,
            text=True,
            encoding="utf-8",
            timeout=10,
        )
        remote = subprocess.run(
            ["git", "remote", "-v"],
            cwd=str(root),
            capture_output=True,
            text=True,
            encoding="utf-8",
            timeout=10,
        )
        lines = [
            f"仓库: {root}",
            f"分支: {(branch.stdout or '').strip()}",
            "",
            (proc.stdout or proc.stderr or "").strip(),
            "",
            "Remote:",
            (remote.stdout or "(无)").strip(),
            "",
            f"本地 sn-* 技能 ({len(list_sn_skills())}):",
            ", ".join(list_sn_skills()[:12]),
            ("…" if len(list_sn_skills()) > 12 else ""),
            "",
            "完整更新请阅读 skills/sn-update/SKILL.md。",
            "若确认无本地修改，可在仓库根执行: git pull",
        ]
        return "\n".join(lines)
    except FileNotFoundError:
        return "未安装 git，请手动下载最新 SenseNova-Skills  release。"
    except subprocess.TimeoutExpired:
        return "git 命令超时"


def git_pull() -> str:
    root = find_repo_root()
    proc = subprocess.run(
        ["git", "pull", "--ff-only"],
        cwd=str(root),
        capture_output=True,
        text=True,
        encoding="utf-8",
        timeout=120,
    )
    out = (proc.stdout or "") + (proc.stderr or "")
    if proc.returncode != 0:
        return f"❌ pull 失败 (code={proc.returncode})\n{out}\n请解决冲突后重试。"
    return f"✅ 更新完成\n{out}"
