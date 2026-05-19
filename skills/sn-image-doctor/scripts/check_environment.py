#!/usr/bin/env python3
"""SenseNova-Skills environment diagnostic tool.

Checks performed:

1. sn-image-base installation
   - Directory exists at skills/sn-image-base/
   - Required files: SKILL.md, requirements.txt,
     scripts/sn_image_base/__init__.py, scripts/sn_agent_runner.py

2. Python dependencies
   - Python version >= 3.9
   - All packages in sn-image-base/requirements.txt are installed

3. Environment variables
   Driven by sn_image_base.configs.Configs. The minimal shared-gateway setup is
   SN_BASE_URL + SN_API_KEY. Capability-specific variables override shared and
   global values when present.
"""

import argparse
import sys
from pathlib import Path
from textwrap import indent

SCRIPT_DIR = Path(__file__).resolve().parent
SKILLS_DIR = SCRIPT_DIR.parents[1]

BASE_SKILL_DIR = SKILLS_DIR / "sn-image-base"

_OK = "✅"
_FAIL = "❌"
_WARN = "⚠️"


def _configure_stdio() -> None:
    """Force UTF-8 on Windows consoles (default GBK breaks emoji markers)."""
    for stream in (sys.stdout, sys.stderr):
        reconfigure = getattr(stream, "reconfigure", None)
        if callable(reconfigure):
            try:
                reconfigure(encoding="utf-8", errors="replace")
            except (OSError, ValueError, AttributeError):
                pass


def _supports_unicode_markers() -> bool:
    for stream in (sys.stdout, sys.stderr):
        encoding = getattr(stream, "encoding", None) or ""
        try:
            f"{_OK}{_FAIL}{_WARN}".encode(encoding or "utf-8")
        except (LookupError, UnicodeEncodeError):
            return False
    return True


def _markers() -> tuple[str, str, str]:
    if _supports_unicode_markers():
        return _OK, _FAIL, _WARN
    return "[OK]", "[FAIL]", "[WARN]"


def _say(text: str) -> None:
    print(text, flush=True)


def check_installation(verbose: bool) -> bool:
    ok_mark, fail_mark, _ = _markers()
    _say("[1/3] Checking sn-image-base installation...")
    root = SKILLS_DIR
    base_skill = BASE_SKILL_DIR
    required = [
        base_skill / "SKILL.md",
        base_skill / "requirements.txt",
        base_skill / "scripts/sn_agent_runner.py",
    ]
    ok = True
    if not base_skill.exists():
        _say(f"  {fail_mark} sn-image-base directory not found")
        _say(f"  Expected location: {base_skill}")
        return False
    if verbose:
        _say(f"  {ok_mark} sn-image-base directory found: {base_skill}")
    for f in required:
        if f.exists():
            if verbose:
                _say(f"  {ok_mark} {f.relative_to(root)}")
        else:
            _say(f"  {fail_mark} Missing: {f.relative_to(root)}")
            ok = False
    if ok and not verbose:
        _say(f"  {ok_mark} Installation looks good")
    # Check skills
    for d in root.iterdir():
        if not d.is_dir():
            continue
        if (d / "SKILL.md").exists() and d.name.startswith("sn-"):
            _say(f"  {ok_mark} {d.name} skill found")
    return ok


def check_dependencies(verbose: bool) -> bool:
    root = SKILLS_DIR
    ok_mark, fail_mark, _ = _markers()
    _say("[2/3] Checking Python dependencies...")
    ok = True

    # Python version
    major, minor = sys.version_info[:2]
    if (major, minor) >= (3, 9):
        _say(f"  {ok_mark} Python {major}.{minor}.{sys.version_info[2]}")
    else:
        _say(f"  {fail_mark} Python {major}.{minor} is too old (need >= 3.9)")
        ok = False

    # Packages from requirements.txt
    req_file = BASE_SKILL_DIR / "requirements.txt"
    if not req_file.exists():
        # This should never happen, check_installation should have failed
        _say(f"  {fail_mark} requirements.txt not found: {req_file.relative_to(root)}")
        ok = False
        return ok

    import importlib.util

    # Some packages' import names are different from their names in requirements.txt
    pkg_map = {
        "pillow": "PIL",
        "python-dotenv": "dotenv",
    }

    missing = []
    for line in req_file.read_text().splitlines():
        line = line.strip()
        if not line or line.startswith("#"):
            continue
        # strip version specifier
        pkg_name = line.split(">=")[0].split("==")[0].split("<=")[0].strip().lower()
        import_name = pkg_map.get(pkg_name, pkg_name)
        found = importlib.util.find_spec(import_name) is not None
        if found:
            if verbose:
                _say(f"  {ok_mark} {pkg_name}")
        else:
            missing.append(pkg_name)

    if missing:
        _say(f"  {fail_mark} Missing packages: {', '.join(missing)}")
        _say("  Run: python -m pip install -r skills/sn-image-base/requirements.txt")
        ok = False
    elif not verbose:
        _say(f"  {ok_mark} All required packages installed")

    return ok


def _load_configs(root: Path):
    """Import and return Configs from sn-image-base, or None on failure."""
    base_path = root / "sn-image-base" / "scripts"
    sys.path.insert(0, str(base_path))
    try:
        from sn_image_base.configs import (  # pyright: ignore[reportMissingImports]
            global_configs,
        )

        return global_configs
    except ImportError:
        return None
    finally:
        if sys.path and sys.path[0] == str(base_path):
            sys.path.pop(0)


def check_env_vars(root: Path, _verbose: bool) -> bool:
    ok_mark, fail_mark, warn_mark = _markers()
    _say("[3/3] Checking environment variables...")

    configs = _load_configs(root)
    if configs is None:
        _say(f"  {warn_mark} Cannot import Configs from sn-image-base, skipping env check")
        return True

    is_ok = True
    errors, warnings = configs.validate_configs()
    if errors:
        is_ok = False
        _say(f"  {fail_mark} Environment check failed! Configuration errors:")
        for field, msg in errors:
            _say(f"    {fail_mark} {field}: {msg}")
    elif warnings:
        _say(f"  {ok_mark} Environment check passed! Although with some warnings:")
        for field, msg in warnings:
            _say(f"    {warn_mark} {field}: {msg}")
    else:
        _say(f"  {ok_mark} Environment check passed!")
    inspect_configs(_verbose)
    return is_ok


def inspect_configs(_verbose: bool):
    _, fail_mark, _ = _markers()
    global_configs = _load_configs(SKILLS_DIR)
    if global_configs is None:
        _say(
            f"{fail_mark} Cannot import Configs from sn-image-base, skipping config inspection",
        )
        return

    _say("Resolved configs:")
    if hasattr(global_configs, "to_string"):
        _say(indent(global_configs.to_string(), "  * "))
    else:
        _say(indent(str(global_configs), "  * "))


def _load_env_file(env_path: Path | None) -> None:
    if env_path is None:
        return
    try:
        from dotenv import load_dotenv
    except ImportError:
        return
    if env_path.is_file():
        load_dotenv(env_path, override=True)


def main() -> int:
    _configure_stdio()
    parser = argparse.ArgumentParser(description="SenseNova-Skills environment diagnostic")
    parser.add_argument("--verbose", action="store_true", help="Show detailed output")
    parser.add_argument(
        "--env-path",
        type=Path,
        default=None,
        help="Path to .env (default: repo root .env next to skills/)",
    )
    args = parser.parse_args()

    env_path = args.env_path or (SKILLS_DIR.parent / ".env")
    _load_env_file(env_path)

    ok_mark, fail_mark, _ = _markers()
    _say("=== SenseNova-Skills Environment Check ===\n")

    root = SKILLS_DIR
    if args.verbose:
        _say(f"Skills root directory: {root}\n")

    results = [
        check_installation(args.verbose),
        check_dependencies(args.verbose),
    ]
    results.append(check_env_vars(root, args.verbose))

    _say("\n=== Summary ===")
    if all(results):
        _say(f"  {ok_mark} Environment is properly configured")
        return 0
    _say(f"  {fail_mark} Environment check failed")
    _say("Please fix the errors above before using SenseNova-Skills.")
    return 1


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except SystemExit:
        raise
    except Exception as exc:  # pragma: no cover - guard for Studio / CI callers
        _configure_stdio()
        _, fail_mark, _ = _markers()
        _say(f"{fail_mark} Environment check crashed: {exc}")
        raise SystemExit(2) from exc
