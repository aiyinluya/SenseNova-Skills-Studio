"""Stage bar text for terminal jobs."""

from __future__ import annotations

import unittest
from unittest.mock import patch

from sn_studio.core.jobs import Job, JobStatus
from sn_studio.ui.app import _stage_from_job


class TestStageFromJob(unittest.TestCase):
    def test_done_uses_completion_line_not_stale_submit_text(self) -> None:
        job = Job(
            id="abc12345",
            kind="image_series",
            status=JobStatus.DONE.value,
            created_at="2026-01-01T00:00:00Z",
            result={"pipeline_stages": [{"name": "expand", "status": "done"}]},
        )
        with patch("sn_studio.ui.app.jobs.get_job", return_value=job):
            with patch(
                "sn_studio.ui.app.jobs.preview_status_line",
                return_value="✅ 完成 · image_series",
            ):
                with patch(
                    "sn_studio.ui.app.stages_line_from_job_result",
                    return_value="系列风格统一… (image_series)",
                ):
                    upd = _stage_from_job("abc12345")
        self.assertIn("完成 · image_series", upd["value"])
        self.assertNotIn("已提交", upd["value"])


if __name__ == "__main__":
    unittest.main()
