"""Prompt template loader: front-matter parse + section split."""

from __future__ import annotations

from pathlib import Path

import pytest
from packages.core.ai.prompts import load_template


def _write_template(tmp_path: Path, name: str, version: int, body: str) -> Path:
    sub = tmp_path / "system"
    sub.mkdir(parents=True, exist_ok=True)
    f = sub / f"{name}.v{version}.md"
    f.write_text(body, encoding="utf-8")
    return f


def test_load_template_parses_front_matter_and_sections(tmp_path: Path) -> None:
    _write_template(
        tmp_path,
        "demo",
        1,
        """---
id: demo
version: 1
task: demo
---

# System

You are demo.

# User

Hello {name}.
""",
    )
    # invalidate lru cache by using fresh dir each test
    tpl = load_template("demo", 1, prompts_dir=str(tmp_path / "system"))
    assert tpl.id == "demo"
    assert tpl.version == 1
    assert "demo" in tpl.system.lower()
    assert tpl.render_user(name="alice") == "Hello alice."
    assert tpl.template_id == "demo.v1"


def test_load_template_missing_raises(tmp_path: Path) -> None:
    with pytest.raises(FileNotFoundError):
        load_template("missing", 1, prompts_dir=str(tmp_path))


def test_load_news_summary_v1_real_template() -> None:
    # Smoke test the actual checked-in template.
    tpl = load_template("news_summary", 1, prompts_dir="prompts/system")
    assert tpl.task == "news_summary"
    assert "news_id" in tpl.user_template
