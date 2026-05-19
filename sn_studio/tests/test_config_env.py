"""Unit tests for .env merge and secret masking."""

from __future__ import annotations

import tempfile
from pathlib import Path
from unittest import mock

from sn_studio.core.config import (
    apply_env_updates,
    mask_api_key_status,
    parse_env_dict,
    read_env_fields,
)


def test_mask_api_key_status_never_full_key() -> None:
    key = "sk-abcdefghijklmnopqrstuvwxyz1234"
    status = mask_api_key_status(key)
    assert key not in status
    assert "1234" in status
    assert "sk-" in status


def test_apply_env_updates_preserves_secret_when_none() -> None:
    with tempfile.TemporaryDirectory() as tmp:
        env = Path(tmp) / ".env"
        env.write_text(
            "SN_BASE_URL=https://example.com/v1\nSN_API_KEY=sk-secret-value\n",
            encoding="utf-8",
        )
        with mock.patch("sn_studio.core.config.env_file", return_value=env):
            merged = apply_env_updates(
                {"SN_API_KEY": None, "SN_BASE_URL": "https://new.example/v1"}
            )
        data = parse_env_dict(merged)
        assert data["SN_API_KEY"] == "sk-secret-value"
        assert data["SN_BASE_URL"] == "https://new.example/v1"


def test_apply_env_updates_replaces_secret_when_set() -> None:
    with tempfile.TemporaryDirectory() as tmp:
        env = Path(tmp) / ".env"
        env.write_text("SN_API_KEY=sk-old\n", encoding="utf-8")
        with mock.patch("sn_studio.core.config.env_file", return_value=env):
            merged = apply_env_updates({"SN_API_KEY": "sk-new-key-value"})
        assert "sk-new-key-value" in merged
        assert "sk-old" not in merged


def test_read_env_fields_uses_file() -> None:
    with tempfile.TemporaryDirectory() as tmp:
        env = Path(tmp) / ".env"
        env.write_text(
            "SN_BASE_URL=https://token.test/v1\nSN_API_KEY=sk-file-key-9999\n",
            encoding="utf-8",
        )
        with mock.patch("sn_studio.core.config.env_file", return_value=env):
            from sn_studio.core.config import read_env_fields

            fields = read_env_fields()
        assert fields["SN_BASE_URL"] == "https://token.test/v1"
        assert fields["SN_API_KEY"] == "sk-file-key-9999"


def test_apply_env_updates_strips_empty_optional_override_lines() -> None:
    with tempfile.TemporaryDirectory() as tmp:
        env = Path(tmp) / ".env"
        env.write_text(
            "SN_BASE_URL=https://token.test/v1\n"
            "SN_API_KEY=sk-global\n"
            "SN_IMAGE_GEN_API_KEY=\n"
            "SN_VISION_API_KEY=\n",
            encoding="utf-8",
        )
        with mock.patch("sn_studio.core.config.env_file", return_value=env):
            merged = apply_env_updates({"SN_BASE_URL": "https://token.test/v1"})
        assert "SN_IMAGE_GEN_API_KEY=" not in merged
        assert "SN_VISION_API_KEY=" not in merged
        assert "SN_API_KEY=sk-global" in merged


def test_read_env_fields_ignores_empty_optional_overrides() -> None:
    with tempfile.TemporaryDirectory() as tmp:
        env = Path(tmp) / ".env"
        env.write_text(
            "SN_API_KEY=sk-global\nSN_IMAGE_GEN_API_KEY=\n",
            encoding="utf-8",
        )
        with mock.patch("sn_studio.core.config.env_file", return_value=env):
            fields = read_env_fields()
        assert "SN_IMAGE_GEN_API_KEY" not in fields
        assert fields["SN_API_KEY"] == "sk-global"
