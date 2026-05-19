"""PPT deck scaffolding and run_stage wrappers."""

from __future__ import annotations

import json
import re
from datetime import datetime
from pathlib import Path
from typing import Any

from sn_studio.core.paths import find_repo_root, ppt_decks_dir, skill_path
from sn_studio.core.runner import run_command, run_text_script


def _slug(text: str) -> str:
    s = re.sub(r"[^\w\u4e00-\u9fff-]+", "_", text.strip())[:40]
    return s or "deck"


def create_deck(
    topic: str,
    role: str,
    audience: str,
    scene: str,
    page_count: int,
    ppt_mode: str,
    reference_files: list[str] | None = None,
) -> dict[str, Any]:
    ts = datetime.now().strftime("%Y%m%d_%H%M%S")
    deck_dir = ppt_decks_dir() / f"{_slug(topic)}_{ts}"
    deck_dir.mkdir(parents=True, exist_ok=True)
    (deck_dir / "pages").mkdir(exist_ok=True)
    if ppt_mode == "standard":
        (deck_dir / "images").mkdir(exist_ok=True)

    task_pack = {
        "deck_dir": str(deck_dir.resolve()),
        "topic": topic,
        "role": role,
        "audience": audience,
        "scene": scene,
        "page_count": int(page_count),
        "ppt_mode": ppt_mode,
        "created_at": datetime.now().isoformat(),
    }
    info_pack: dict[str, Any] = {
        "topic": topic,
        "user_query": topic,
        "document_digest": None,
        "user_assets": {"reference_images": [], "reference_image_captions": {}},
    }

    if reference_files:
        entry_skill = skill_path("sn-ppt-entry")
        parse_script = entry_skill / "scripts" / "parse_user_docs.py"
        raw_json = deck_dir / "raw_documents.json"
        if parse_script.is_file():
            files_arg = []
            for f in reference_files:
                if Path(f).is_file():
                    files_arg.append(str(Path(f).resolve()))
            if files_arg:
                run_text_script(
                    parse_script,
                    ["--files", *files_arg, "--output", str(raw_json)],
                    cwd=find_repo_root(),
                    timeout=300,
                )

    (deck_dir / "task_pack.json").write_text(
        json.dumps(task_pack, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    (deck_dir / "info_pack.json").write_text(
        json.dumps(info_pack, ensure_ascii=False, indent=2), encoding="utf-8"
    )

    return {
        "deck_dir": str(deck_dir.resolve()),
        "task_pack": task_pack,
        "output_paths": [str(deck_dir)],
    }


STANDARD_STAGES = [
    "preflight",
    "style",
    "outline",
    "asset-plan",
    "batch-gen-image",
    "batch-page-html",
    "export",
]


def run_ppt_stage(deck_dir: str, stage: str, extra_args: list[str] | None = None) -> str:
    script = skill_path("sn-ppt-standard") / "scripts" / "run_stage.py"
    if stage not in STANDARD_STAGES and stage not in ("gen-image", "page-html"):
        raise ValueError(f"未知阶段: {stage}")

    cmd = [
        __import__("sys").executable,
        str(script),
        stage,
        "--deck-dir",
        deck_dir,
    ]
    if extra_args:
        cmd.extend(extra_args)

    code, out, err = run_command(cmd, cwd=find_repo_root(), timeout=900)
    text = (out or "").strip() or (err or "")
    if code != 0:
        return f"❌ 阶段 {stage} 失败 (code={code})\n{text}"
    return f"✅ 阶段 {stage} 完成\n{text}"
