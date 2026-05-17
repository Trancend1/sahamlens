"""Cross-cutting guard: gagal kalau path `data/private/**` (selain .gitkeep) tercommit.

Dipanggil di pre-commit + CI. Mirror SECURITY.md §3.2.
"""

from __future__ import annotations

import subprocess
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
PRIVATE_PREFIX = "data/private/"
ALLOWED = {"data/private/.gitkeep"}


def _git_tracked_files() -> list[str]:
    result = subprocess.run(
        ["git", "ls-files"],
        cwd=REPO_ROOT,
        capture_output=True,
        text=True,
        check=True,
    )
    return [line.strip().replace("\\", "/") for line in result.stdout.splitlines() if line.strip()]


def test_no_private_data_tracked() -> None:
    tracked = _git_tracked_files()
    leaks = [f for f in tracked if f.startswith(PRIVATE_PREFIX) and f not in ALLOWED]
    assert not leaks, (
        f"Private files leaked into git: {leaks}. "
        f"They must live under {PRIVATE_PREFIX} but never be tracked."
    )


def test_no_private_config_tracked() -> None:
    tracked = _git_tracked_files()
    leaks = [
        f
        for f in tracked
        if f.startswith("config/") and f.endswith(".yml") and not f.endswith(".example.yml")
    ]
    assert not leaks, f"Private config leaked into git: {leaks}"


def test_no_env_local_tracked() -> None:
    tracked = _git_tracked_files()
    leaks = [f for f in tracked if f.startswith(".env") and f != ".env.example"]
    assert not leaks, f".env files leaked into git: {leaks}"
