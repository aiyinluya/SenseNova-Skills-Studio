"""Deep research directory scaffolding and md-to-html."""

from __future__ import annotations

import json
import re
from datetime import datetime
from pathlib import Path
from typing import Any

from sn_studio.core.paths import find_repo_root, research_dir, skill_path
from sn_studio.core.runner import run_text_script


def _slug(topic: str) -> str:
    return re.sub(r"[^\w\u4e00-\u9fff-]+", "_", topic.strip())[:50] or "topic"


def init_research(topic: str, scope: str = "") -> dict[str, Any]:
    ts = datetime.now().strftime("%Y%m%d_%H%M%S")
    report_dir = research_dir() / f"{_slug(topic)}_{ts}"
    report_dir.mkdir(parents=True, exist_ok=True)
    (report_dir / "sub_reports").mkdir(exist_ok=True)

    request_md = f"""# 研究请求

## 主题
{topic}

## 范围与约束
{scope or "（待补充）"}

## 关键问题
1. 
2. 
3. 

---
由 SenseNova Skills Studio 创建于 {datetime.now().isoformat()}
请在 Cursor/OpenClaw 中使用 sn-deep-research 继续：规划 → 分维度研究 → 综合 → 成稿。
"""
    (report_dir / "request.md").write_text(request_md, encoding="utf-8")

    return {
        "report_dir": str(report_dir.resolve()),
        "output_paths": [str(report_dir)],
    }


def report_progress(report_dir: str) -> dict[str, Any]:
    root = Path(report_dir)
    if not root.is_dir():
        return {"error": "目录不存在"}

    files = [
        "request.md",
        "plan.json",
        "synthesis.md",
        "report.md",
    ]
    status = {f: (root / f).is_file() for f in files}
    sub = list((root / "sub_reports").glob("*.md")) if (root / "sub_reports").is_dir() else []
    status["sub_reports_count"] = len(sub)
    return {"report_dir": str(root), "files": status, "sub_reports": [p.name for p in sub]}


def progress_markdown(report_dir: str) -> str:
    p = report_progress(report_dir)
    if "error" in p:
        return f"❌ {p['error']}"
    lines = [f"**目录**: `{p['report_dir']}`\n"]
    for f, ok in p["files"].items():
        if f == "sub_reports_count":
            lines.append(f"- 分维度报告: **{ok}** 篇")
        else:
            lines.append(f"- `{f}`: {'✅' if ok else '⬜'}")
    if p.get("sub_reports"):
        lines.append("\n已完成分报告: " + ", ".join(p["sub_reports"][:10]))
    return "\n".join(lines)


def md_to_html(md_path: str, html_path: str | None = None) -> dict[str, Any]:
    src = Path(md_path)
    if not src.is_file():
        raise FileNotFoundError(md_path)
    dst = Path(html_path) if html_path else src.with_suffix(".html")
    script = skill_path("sn-md-to-html-report") / "scripts" / "render_report.py"
    run_text_script(
        script,
        [str(src.resolve()), str(dst.resolve()), "--embed-images", "--with-js"],
        cwd=find_repo_root(),
        timeout=120,
    )
    return {"html": str(dst.resolve()), "output_paths": [str(dst.resolve())]}
