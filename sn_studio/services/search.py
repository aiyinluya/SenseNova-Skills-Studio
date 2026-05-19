"""Unified search across sn-search-* skills."""

from __future__ import annotations

from pathlib import Path
from typing import Any

from sn_studio.core.paths import skill_path
from sn_studio.core.runner import run_json_script

# category -> provider -> script filename (without path)
SEARCH_REGISTRY: dict[str, dict[str, str]] = {
    "academic": {
        "arxiv": "arxiv_search.py",
        "pubmed": "pubmed_search.py",
        "wikipedia": "wikipedia_search.py",
        "semantic_scholar": "semantic_scholar_search.py",
    },
    "code": {
        "github": "github_search.py",
        "stackoverflow": "stackoverflow_search.py",
        "hackernews": "hackernews_search.py",
        "huggingface": "huggingface_search.py",
    },
    "social_cn": {
        "bilibili": "bilibili_search.py",
        "zhihu": "zhihu_search.py",
        "douyin": "douyin_search.py",
    },
    "social_en": {
        "reddit": "reddit_search.py",
        "twitter": "twitter_search.py",
        "youtube": "youtube_search.py",
    },
}

CATEGORY_LABELS = {
    "academic": "学术",
    "code": "代码/开源",
    "social_cn": "中文社交",
    "social_en": "英文社交",
}

SKILL_DIR_MAP = {
    "academic": "sn-search-academic",
    "code": "sn-search-code",
    "social_cn": "sn-search-social-cn",
    "social_en": "sn-search-social-en",
}


def list_categories() -> list[str]:
    return list(SEARCH_REGISTRY.keys())


def list_providers(category: str) -> list[str]:
    return list(SEARCH_REGISTRY.get(category, {}).keys())


def search(category: str, provider: str, query: str, limit: int = 10) -> dict[str, Any]:
    if category not in SEARCH_REGISTRY:
        raise ValueError(f"未知类别: {category}")
    scripts = SEARCH_REGISTRY[category]
    if provider not in scripts:
        raise ValueError(f"未知提供商: {provider}")

    skill = SKILL_DIR_MAP[category]
    script = skill_path(skill) / "scripts" / scripts[provider]
    extra: list[str] = []
    if provider == "github":
        extra = ["--type", "repositories"]

    return run_json_script(
        script,
        [query, "--limit", str(max(1, min(limit, 50))), *extra],
        cwd=script.parent,
        timeout=60,
    )


def format_results_table(data: dict[str, Any]) -> list[list[str]]:
    rows: list[list[str]] = []
    for item in data.get("items") or []:
        rows.append(
            [
                str(item.get("title", ""))[:120],
                str(item.get("url", ""))[:200],
                str(item.get("snippet", ""))[:300],
            ]
        )
    return rows
