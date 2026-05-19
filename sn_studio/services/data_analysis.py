"""Excel probe and image caption."""

from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path
from typing import Any

from sn_studio.core.paths import skill_path, studio_output_dir
from sn_studio.core.runner import run_text_script
from sn_studio.core import jobs

_LARGE_FILE_THRESHOLD = 10_000


def probe_excel(file_path: str) -> dict[str, Any]:
    path = Path(file_path)
    if not path.is_file():
        raise FileNotFoundError(f"文件不存在: {file_path}")

    import pandas as pd

    xl = pd.ExcelFile(path)
    sheets_info: list[dict[str, Any]] = []
    total_rows = 0

    for name in xl.sheet_names:
        df = pd.read_excel(path, sheet_name=name, nrows=5)
        # count rows with openpyxl for accuracy without loading all
        import openpyxl

        wb = openpyxl.load_workbook(path, read_only=True, data_only=True)
        ws = wb[name]
        rows = max(0, ws.max_row - 1)  # minus header guess
        wb.close()
        total_rows += rows
        sheets_info.append(
            {
                "sheet": name,
                "rows": rows,
                "columns": list(df.columns.astype(str)),
                "preview": df.head(3).to_dict(orient="records"),
            }
        )

    large_mode = total_rows >= _LARGE_FILE_THRESHOLD
    report = {
        "file": str(path.resolve()),
        "sheet_count": len(sheets_info),
        "total_rows": total_rows,
        "large_file_mode_recommended": large_mode,
        "sheets": sheets_info,
        "hint": (
            "数据量≥1万行，建议在 Agent 中使用 sn-da-large-file-analysis + Parquet 流程"
            if large_mode
            else "可使用 sn-da-excel-workflow 在 Cursor 中执行完整分析"
        ),
    }

    out_dir = studio_output_dir() / "excel"
    out_dir.mkdir(parents=True, exist_ok=True)
    out_file = out_dir / f"probe_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
    out_file.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
    report["output_paths"] = [str(out_file)]
    return report


def probe_excel_markdown(file_path: str) -> str:
    r = probe_excel(file_path)
    lines = [
        f"**文件**: `{r['file']}`",
        f"**Sheet 数**: {r['sheet_count']} | **估算总行数**: {r['total_rows']}",
        f"**大文件模式**: {'建议启用' if r['large_file_mode_recommended'] else '否'}",
        f"\n> {r['hint']}\n",
    ]
    for s in r["sheets"]:
        lines.append(f"### {s['sheet']} ({s['rows']} 行)")
        lines.append(f"列: {', '.join(s['columns'][:15])}")
        if len(s["columns"]) > 15:
            lines.append("…")
    lines.append(f"\n报告已保存: `{r['output_paths'][0]}`")
    return "\n".join(lines)


def caption_image(image_path: str, custom_prompt: str = "") -> str:
    script = skill_path("sn-da-image-caption") / "scripts" / "caption.py"
    args = [image_path]
    if custom_prompt.strip():
        args.extend(["--prompt", custom_prompt.strip()])
    return run_text_script(script, args, timeout=180)


def submit_excel_probe(file_path: str) -> jobs.Job:
    return jobs.submit("excel_probe", {"file": file_path}, lambda: probe_excel(file_path))


def submit_caption(file_path: str, prompt: str = "") -> jobs.Job:
    def _run() -> dict[str, Any]:
        text = caption_image(file_path, prompt)
        return {"caption": text, "log": text, "output_paths": []}

    return jobs.submit("image_caption", {"file": file_path}, _run)
