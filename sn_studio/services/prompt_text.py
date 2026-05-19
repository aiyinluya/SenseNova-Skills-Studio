"""Chinese legibility helpers for image prompt expansion (no pipeline imports)."""

from __future__ import annotations

CHINESE_IMAGE_TEXT_APPENDIX = """
## 图中中文可读性（必须遵守）
- 用户要求出现在图上的中文必须用引号逐字列出，不得改写、不得用拼音或英文替代（除非用户明确要求英文）。
- 主标题字号须足够大、占画面宽度约 50–70%；正文层级分明，使用黑体/思源黑体类无衬线高对比字体。
- 禁止乱码、缺笔画、笔画粘连、过小脚注、模糊文字。
- 禁止在无用户要求时用英文标签替代中文。
- 若画面含步骤/列表，每一步的中文标签须清晰可读、对齐整齐。
""".strip()

DEFAULT_NEGATIVE_PROMPT_CHINESE = (
    "garbled text, illegible Chinese characters, wrong glyphs, broken characters, "
    "watermark, logo overlay, blurry text, tiny unreadable fonts, "
    "random English labels, messy typography, pinyin instead of Chinese"
)


def chinese_image_text_appendix() -> str:
    return CHINESE_IMAGE_TEXT_APPENDIX


def default_negative_prompt_chinese(user_negative: str = "") -> str:
    parts = [DEFAULT_NEGATIVE_PROMPT_CHINESE]
    if user_negative.strip():
        parts.append(user_negative.strip())
    return ", ".join(parts)


def inject_chinese_appendix(system_prompt: str) -> str:
    if CHINESE_IMAGE_TEXT_APPENDIX in system_prompt:
        return system_prompt
    return f"{system_prompt.rstrip()}\n\n{CHINESE_IMAGE_TEXT_APPENDIX}"
