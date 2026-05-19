"""Unit tests for unified prompt pipeline (no API)."""

from __future__ import annotations

import unittest

from sn_studio.services.prompt_pipeline import (
    parse_series_scene_lines,
    pipeline_stages_summary,
    run_pipeline,
)
from sn_studio.services.prompt_text import (
    chinese_image_text_appendix,
    default_negative_prompt_chinese,
    inject_chinese_appendix,
)


class PromptPipelineUnitTests(unittest.TestCase):
    def test_chinese_appendix_keywords(self) -> None:
        text = chinese_image_text_appendix()
        self.assertIn("清晰可读", text)
        self.assertIn("乱码", text)

    def test_inject_chinese_idempotent(self) -> None:
        base = "你是扩写专家。"
        once = inject_chinese_appendix(base)
        twice = inject_chinese_appendix(once)
        self.assertEqual(once, twice)
        self.assertIn("中文", once)

    def test_default_negative_includes_garbled(self) -> None:
        neg = default_negative_prompt_chinese("extra blur")
        self.assertIn("garbled", neg)
        self.assertIn("extra blur", neg)

    def test_pipeline_stages_summary(self) -> None:
        s = pipeline_stages_summary(
            [{"id": "a", "label": "评估中"}, {"id": "b", "label": "生成图像"}]
        )
        self.assertEqual(s, "评估中 → 生成图像")

    def test_run_pipeline_disable_generate(self) -> None:
        # disable skips API except generate — mock not available; only test validation
        with self.assertRaises(Exception):
            run_pipeline("", module_kind="generate", prompts_expand_mode="disable")

    def test_parse_series_scene_lines_strips_numbering(self) -> None:
        raw = "1. 封面\n2) 步骤一\n- 步骤二"
        lines = parse_series_scene_lines(raw, 3)
        self.assertEqual(len(lines), 3)
        self.assertEqual(lines[0], "封面")
        self.assertEqual(lines[1], "步骤一")
        self.assertEqual(lines[2], "步骤二")

    def test_parse_series_scene_lines_pads_to_count(self) -> None:
        lines = parse_series_scene_lines("仅一张", 4)
        self.assertEqual(len(lines), 4)
        self.assertTrue(all(lines))


if __name__ == "__main__":
    unittest.main()
