"""
App version: the root VERSION file plus "+<commit count>.<short sha>" from git.

The frontend computes the same string in vite.config.ts. Set APP_VERSION to override
(Docker builds have no git history or VERSION file in their build context).
"""

import subprocess
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[3]


def _git(*args: str) -> str:
    return subprocess.run(
        ["git", *args], cwd=REPO_ROOT, capture_output=True, text=True, check=True, timeout=5
    ).stdout.strip()


def get_app_version() -> str:
    try:
        base = (REPO_ROOT / "VERSION").read_text().strip()
    except OSError:
        return "dev"
    try:
        return (
            f"{base}+{_git('rev-list', '--count', 'HEAD')}.{_git('rev-parse', '--short', 'HEAD')}"
        )
    except (OSError, subprocess.SubprocessError):
        return base
