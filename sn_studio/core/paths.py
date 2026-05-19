"""Repository and skills path discovery."""

from __future__ import annotations

import os
from functools import lru_cache
from pathlib import Path


def _has_skills_root(path: Path) -> bool:
    return (path / "skills" / "sn-image-base" / "scripts" / "sn_agent_runner.py").is_file()


@lru_cache(maxsize=1)
def find_repo_root() -> Path:
    """Locate SenseNova-Skills content root (contains skills/ and .env)."""
    env_root = os.environ.get("SN_SKILLS_ROOT")
    if env_root:
        candidate = Path(env_root).expanduser().resolve()
        if _has_skills_root(candidate):
            return candidate

    # From sn_studio package: .../SenseNova-Skills/sn_studio/core/paths.py -> repo is parent of sn_studio
    here = Path(__file__).resolve()
    for parent in [here.parents[2], here.parents[3], here.parents[1]]:
        if _has_skills_root(parent):
            return parent

    cwd = Path.cwd().resolve()
    if _has_skills_root(cwd):
        return cwd
    nested = cwd / "SenseNova-Skills"
    if _has_skills_root(nested):
        return nested

    raise FileNotFoundError(
        "Cannot find skills/sn-image-base. Set SN_SKILLS_ROOT or run from the repo directory."
    )


def skills_dir() -> Path:
    return find_repo_root() / "skills"


def env_file() -> Path:
    return find_repo_root() / ".env"


def outputs_dir() -> Path:
    d = find_repo_root() / "outputs"
    d.mkdir(parents=True, exist_ok=True)
    return d


def studio_output_dir() -> Path:
    d = outputs_dir() / "studio"
    d.mkdir(parents=True, exist_ok=True)
    return d


def jobs_store_path() -> Path:
    d = outputs_dir() / ".studio_jobs"
    d.mkdir(parents=True, exist_ok=True)
    return d / "jobs.json"


def ppt_decks_dir() -> Path:
    d = find_repo_root() / "ppt_decks"
    d.mkdir(parents=True, exist_ok=True)
    return d


def research_dir() -> Path:
    d = find_repo_root() / "research"
    d.mkdir(parents=True, exist_ok=True)
    return d


def skill_path(name: str) -> Path:
    return skills_dir() / name


def agent_runner() -> Path:
    return skill_path("sn-image-base") / "scripts" / "sn_agent_runner.py"


def list_sn_skills() -> list[str]:
    root = skills_dir()
    if not root.is_dir():
        return []
    return sorted(
        p.name
        for p in root.iterdir()
        if p.is_dir() and p.name.startswith("sn-") and (p / "SKILL.md").is_file()
    )
