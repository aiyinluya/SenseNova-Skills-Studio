#!/usr/bin/env python3
"""Headless smoke tests for sn_studio (no Gradio required)."""

from __future__ import annotations

import sys
from pathlib import Path

_REPO = Path(__file__).resolve().parents[1]
if str(_REPO) not in sys.path:
    sys.path.insert(0, str(_REPO))


def main() -> int:
    from sn_studio.core.config import reload_env, validate_env
    from sn_studio.core.paths import find_repo_root, list_sn_skills
    from sn_studio.services.settings import test_api

    reload_env()
    root = find_repo_root()
    skills = list_sn_skills()
    print(f"repo_root={root}")
    print(f"skills={len(skills)}")

    errors, _ = validate_env()
    if errors:
        print("ENV_ERRORS:", errors)
        return 1

    api = test_api()
    print("api_test:", api.replace("\u2705", "OK").replace("\u274c", "FAIL")[:120])

    if "HTTP 200" in api or "网关响应" in api:
        print("smoke: PASS (settings)")
    else:
        print("smoke: WARN (api)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
