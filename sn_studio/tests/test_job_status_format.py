"""Stage bar and status prefix formatting."""

from __future__ import annotations

import unittest

from sn_studio.ui.components.job_status import format_stage_message, strip_status_prefix


class TestStripStatusPrefix(unittest.TestCase):
    def test_strips_single_running_prefix(self) -> None:
        self.assertEqual(
            strip_status_prefix("⏳ 系列风格统一… (image_series)"),
            "系列风格统一… (image_series)",
        )

    def test_strips_double_running_prefix(self) -> None:
        self.assertEqual(
            strip_status_prefix("⏳ ⏳ 系列风格统一… (image_series)"),
            "系列风格统一… (image_series)",
        )

    def test_strips_done_prefix(self) -> None:
        self.assertEqual(strip_status_prefix("✅ 完成 · image_series"), "完成 · image_series")


class TestFormatStageMessage(unittest.TestCase):
    def test_running_from_preview_status_line(self) -> None:
        line = "⏳ 系列风格统一… (image_series)"
        self.assertEqual(
            format_stage_message(line),
            "⏳ 系列风格统一… (image_series)",
        )

    def test_done_no_duplicate_checkmark(self) -> None:
        line = "✅ 完成 · image_series"
        self.assertEqual(format_stage_message(line, done=True), "✅ **完成 · image_series**")

    def test_failed_strips_prefix(self) -> None:
        self.assertEqual(
            format_stage_message("❌ 失败: timeout", failed=True),
            "❌ **失败: timeout**",
        )


if __name__ == "__main__":
    unittest.main()
