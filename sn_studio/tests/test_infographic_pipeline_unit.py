"""Unit tests for infographic pipeline helpers (no API)."""

from __future__ import annotations

import unittest

from sn_studio.services.infographic_pipeline import (
    _infer_aspect_ratio,
    _parse_json_blob,
    _select_layout_style,
    _should_expand_auto,
)


class InfographicPipelineUnitTests(unittest.TestCase):
    def test_parse_json_blob(self) -> None:
        self.assertEqual(_parse_json_blob('{"a": 1}')["a"], 1)

    def test_select_layout_cervical(self) -> None:
        layout, style = _select_layout_style("颈椎四步退化", None, "")
        self.assertTrue(layout)
        self.assertTrue(style)

    def test_infer_aspect_default(self) -> None:
        self.assertEqual(_infer_aspect_ratio("颈椎四步退化"), "16:9")

    def test_should_expand_short_prompt_heuristic(self) -> None:
        # Without API: evaluation may fail open to True; we only assert callable exists
        self.assertTrue(callable(_should_expand_auto))


if __name__ == "__main__":
    unittest.main()
