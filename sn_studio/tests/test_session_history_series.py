"""Session history rules for new ``outputs/studio/series/<id>/`` layout."""

from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from sn_studio.core import jobs
from sn_studio.core.jobs import Job, JobStatus


class TestSeriesRunLayout(unittest.TestCase):
    def test_is_series_run_dir_requires_marker_under_series(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            run = root / "series" / "20260518_120000"
            run.mkdir(parents=True)
            (run / "series-lines.txt").write_text("a\nb", encoding="utf-8")
            with patch.object(jobs, "studio_output_dir", return_value=root):
                self.assertTrue(jobs.is_series_run_dir(run))
                legacy = root / "series_20260518_120000"
                legacy.mkdir()
                (legacy / "series-lines.txt").write_text("x", encoding="utf-8")
                self.assertFalse(jobs.is_series_run_dir(legacy))

    def test_legacy_image_series_job_excluded_from_gallery(self) -> None:
        legacy = Job(
            id="legacy01",
            kind="image_series",
            status=JobStatus.DONE.value,
            created_at="2026-05-18T00:00:00+00:00",
            finished_at="2026-05-18T00:01:00+00:00",
            output_paths=[
                str(
                    Path("outputs/studio/series_20260518_092603/01.png").as_posix()
                )
            ],
            result={
                "series_dir": str(
                    Path("outputs/studio/series_20260518_092603").resolve()
                ),
                "items": [{"index": 1, "path": "outputs/studio/series_20260518_092603/01.png"}],
            },
        )
        self.assertFalse(jobs.is_valid_image_series_job(legacy))
        self.assertEqual(jobs.image_paths_from_job(legacy), [])

    def test_new_layout_job_resolves_thumbnail(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            run = root / "series" / "20260518_155613"
            run.mkdir(parents=True)
            (run / "series-lines.txt").write_text("line", encoding="utf-8")
            png = run / "01.png"
            png.write_bytes(b"\x89PNG\r\n\x1a\n")
            job = Job(
                id="newseries1",
                kind="image_series",
                status=JobStatus.DONE.value,
                created_at="2026-05-18T00:00:00+00:00",
                finished_at="2026-05-18T00:02:00+00:00",
                output_paths=[str(png), str(run / "manifest.json")],
                result={"series_dir": str(run), "items": [{"index": 1, "path": str(png)}]},
            )
            with patch.object(jobs, "studio_output_dir", return_value=root):
                self.assertTrue(jobs.is_valid_image_series_job(job))
                paths = jobs.image_paths_from_job(job)
                self.assertEqual(len(paths), 1)

    def test_disk_fallback_series_only_scans_timestamp_dirs(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            good = root / "series" / "20260518_200000"
            good.mkdir(parents=True)
            (good / "manifest.json").write_text("[]", encoding="utf-8")
            png = good / "01.png"
            png.write_bytes(b"\x89PNG\r\n\x1a\n")
            bad = root / "series" / "legacy_flat"
            bad.mkdir(parents=True)
            (bad / "01.png").write_bytes(b"\x89PNG\r\n\x1a\n")
            with patch.object(jobs, "studio_output_dir", return_value=root):
                items, ids = jobs._disk_fallback_series_session_history(8)
            self.assertEqual(len(items), 1)
            self.assertEqual(ids, [""])
            self.assertIn("20260518_200000", items[0][1])

    def test_session_history_gallery_filters_legacy_jobs(self) -> None:
        legacy = Job(
            id="legacy02",
            kind="image_series",
            status=JobStatus.DONE.value,
            created_at="2026-05-18T00:00:00+00:00",
            finished_at="2026-05-18T00:01:00+00:00",
            output_paths=["outputs/studio/series_old/01.png"],
        )
        with (
            patch.object(jobs, "list_jobs", return_value=[legacy]),
            patch.object(
                jobs, "_disk_fallback_series_session_history", return_value=([], [])
            ),
        ):
            items, ids = jobs.session_history_gallery(8, kind="image_series")
        self.assertEqual(items, [])
        self.assertEqual(ids, [])


if __name__ == "__main__":
    unittest.main()
