"""Pre-commit hook: block staged files under `data/private/` (except .gitkeep),
config/*.yml (non-example), and any .env* except .env.example.

Exit 0 = clean. Exit 1 = leak detected; commit blocked.
"""

from __future__ import annotations

import subprocess
import sys
from pathlib import PurePosixPath

ALLOWED_PRIVATE = {"data/private/.gitkeep"}


def staged_files() -> list[str]:
    result = subprocess.run(
        ["git", "diff", "--cached", "--name-only", "--diff-filter=ACMR"],
        capture_output=True,
        text=True,
        check=True,
    )
    return [line.strip().replace("\\", "/") for line in result.stdout.splitlines() if line.strip()]


def is_leak(path: str) -> str | None:
    p = PurePosixPath(path)
    if path.startswith("data/private/") and path not in ALLOWED_PRIVATE:
        return "private-data"
    if path.startswith("config/") and p.suffix == ".yml" and not path.endswith(".example.yml"):
        return "private-config"
    if p.name.startswith(".env") and path != ".env.example":
        return "env-secret"
    return None


def main() -> int:
    try:
        files = staged_files()
    except subprocess.CalledProcessError as e:
        print(f"no_private_leak: git diff failed: {e}", file=sys.stderr)
        return 1

    leaks: list[tuple[str, str]] = []
    for f in files:
        reason = is_leak(f)
        if reason:
            leaks.append((f, reason))

    if leaks:
        print(
            "\n[no_private_leak] Commit blocked. Private/sensitive files staged:\n", file=sys.stderr
        )
        for path, reason in leaks:
            print(f"  - {path}  ({reason})", file=sys.stderr)
        print(
            "\nUnstage them: `git rm --cached <file>` then re-commit.\n"
            "Aturan: lihat .docs/SECURITY.md §3.\n",
            file=sys.stderr,
        )
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
