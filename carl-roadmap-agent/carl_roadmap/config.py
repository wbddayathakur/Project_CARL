"""Load config.yaml and resolve credentials from the environment."""

from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import yaml


@dataclass
class Config:
    raw: dict
    root: Path

    @classmethod
    def load(cls, path: str | Path) -> "Config":
        p = Path(path).expanduser().resolve()
        if not p.exists():
            raise FileNotFoundError(f"no config at {p}")
        with p.open(encoding="utf-8") as fh:
            raw = yaml.safe_load(fh) or {}
        return cls(raw=raw, root=p.parent)

    def get(self, *keys: str, default: Any = None) -> Any:
        node: Any = self.raw
        for k in keys:
            if not isinstance(node, dict) or k not in node:
                return default
            node = node[k]
        return node

    def path(self, *keys: str, default: Any = None) -> Path | None:
        """A config value read as a path, resolved relative to config.yaml.

        Absolute paths — such as the OneDrive HTML target — pass through
        untouched.
        """
        value = self.get(*keys, default=default)
        if not value:
            return None
        p = Path(str(value)).expanduser()
        return p if p.is_absolute() else (self.root / p)

    def credentials(self, section: str) -> tuple[str, str]:
        user_env = self.get(section, "auth_env_user", default="JIRA_USER")
        token_env = self.get(section, "auth_env_token", default="JIRA_TOKEN")
        return os.environ.get(user_env, ""), os.environ.get(token_env, "")
