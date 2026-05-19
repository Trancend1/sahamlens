"""Versioned prompt template loader.

Templates live in `prompts/system/<name>.v<version>.md` with YAML front-matter:
  ---
  id: <name>
  version: <int>
  task: <name>
  ---
  # System
  <system text>

  # User
  <user template>

User template uses `str.format`-style placeholders, e.g. `{title}`, `{published_at}`.
"""

from __future__ import annotations

from dataclasses import dataclass
from functools import lru_cache
from pathlib import Path

import yaml

PROMPTS_DIR = Path("prompts/system")


@dataclass(frozen=True)
class PromptTemplate:
    id: str
    version: int
    task: str
    system: str
    user_template: str

    @property
    def template_id(self) -> str:
        return f"{self.id}.v{self.version}"

    def render_user(self, **kwargs: object) -> str:
        return self.user_template.format(**kwargs)


@lru_cache(maxsize=32)
def load_template(name: str, version: int = 1, *, prompts_dir: str | None = None) -> PromptTemplate:
    root = Path(prompts_dir) if prompts_dir else PROMPTS_DIR
    path = root / f"{name}.v{version}.md"
    if not path.exists():
        raise FileNotFoundError(f"prompt template not found: {path}")
    raw = path.read_text(encoding="utf-8")
    front_matter, body = _split_front_matter(raw)
    meta = yaml.safe_load(front_matter) or {}
    system, user_template = _split_sections(body)
    return PromptTemplate(
        id=str(meta.get("id", name)),
        version=int(meta.get("version", version)),
        task=str(meta.get("task", name)),
        system=system.strip(),
        user_template=user_template.strip(),
    )


def _split_front_matter(raw: str) -> tuple[str, str]:
    if not raw.startswith("---"):
        return "", raw
    end = raw.find("\n---", 3)
    if end == -1:
        return "", raw
    return raw[3:end].strip(), raw[end + 4 :]


def _split_sections(body: str) -> tuple[str, str]:
    parts = body.split("# User", 1)
    if len(parts) != 2:
        raise ValueError("prompt body missing '# User' section")
    system = parts[0].replace("# System", "", 1)
    return system, parts[1]
