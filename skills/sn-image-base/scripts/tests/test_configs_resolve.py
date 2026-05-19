"""Tests for env var fallback resolution in sn_image_base.configs."""

from __future__ import annotations

import os
import sys
import unittest
from pathlib import Path
from unittest import mock

SCRIPTS_DIR = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(SCRIPTS_DIR))

from sn_image_base.configs import Configs, Field  # noqa: E402


class TestFieldResolve(unittest.TestCase):
    def test_empty_override_falls_back_to_shared_key(self) -> None:
        field = Field("SN_IMAGE_GEN_API_KEY", "SN_API_KEY", required=True, secret=True)
        env = {
            "SN_IMAGE_GEN_API_KEY": "",
            "SN_API_KEY": "sk-global",
        }
        with mock.patch.dict(os.environ, env, clear=False):
            self.assertEqual(field.resolve(), "sk-global")

    def test_dedicated_override_wins_over_shared_key(self) -> None:
        field = Field("SN_IMAGE_GEN_API_KEY", "SN_API_KEY", required=True, secret=True)
        env = {
            "SN_IMAGE_GEN_API_KEY": "sk-image",
            "SN_API_KEY": "sk-global",
        }
        with mock.patch.dict(os.environ, env, clear=False):
            self.assertEqual(field.resolve(), "sk-image")

    def test_whitespace_only_treated_as_unset(self) -> None:
        field = Field("SN_IMAGE_GEN_API_KEY", "SN_API_KEY", required=True, secret=True)
        env = {
            "SN_IMAGE_GEN_API_KEY": "   ",
            "SN_API_KEY": "sk-global",
        }
        with mock.patch.dict(os.environ, env, clear=False):
            self.assertEqual(field.resolve(), "sk-global")


class TestConfigsValidation(unittest.TestCase):
    def test_validate_passes_with_global_key_only(self) -> None:
        env = {
            "SN_API_KEY": "sk-global-key-value",
            "SN_IMAGE_GEN_API_KEY": "",
            "SN_BASE_URL": "https://token.sensenova.cn/v1",
        }
        with mock.patch.dict(os.environ, env, clear=False):
            cfg = Configs()
            errors, _warnings = cfg.validate_configs()
            image_errors = [e for e in errors if e[0] == "SN_IMAGE_GEN_API_KEY"]
            self.assertEqual(image_errors, [])
            self.assertEqual(cfg.SN_IMAGE_GEN_API_KEY, "sk-global-key-value")


if __name__ == "__main__":
    unittest.main()
