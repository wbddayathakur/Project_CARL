"""Load and validate config.yaml."""

from __future__ import annotations

import os
from dataclasses import dataclass, field
from pathlib import Path
from typing import Optional

import yaml

PLACEHOLDER = "REPLACE_ME"


@dataclass
class ConfluenceConfig:
    enabled: bool = False
    base_url: str = ""
    space_key: str = ""
    page_id: str = ""
    page_title: str = "CARL Iceberg & Cube — what's available"
    auth_env_user: str = "CONFLUENCE_USER"
    auth_env_token: str = "CONFLUENCE_TOKEN"

    @property
    def user(self) -> Optional[str]:
        return os.environ.get(self.auth_env_user)

    @property
    def token(self) -> Optional[str]:
        return os.environ.get(self.auth_env_token)

    def problems(self) -> list:
        """Everything that would stop a publish, reported together.

        Collected rather than raised one at a time so a first-time setup gets
        the whole list in one run instead of discovering it across four.
        """
        issues = []
        for name in ("base_url", "space_key", "page_id"):
            value = getattr(self, name)
            if not value or PLACEHOLDER in str(value):
                issues.append(f"confluence.{name} is not set in config.yaml")
        if not self.user:
            issues.append(f"${self.auth_env_user} is not set in the environment")
        if not self.token:
            issues.append(f"${self.auth_env_token} is not set in the environment")
        return issues


@dataclass
class Config:
    root: Path
    window_days: int = 14
    timezone: str = "Asia/Kolkata"
    iceberg_only: bool = True
    output_dir: Path = Path("out")
    environments: list = field(default_factory=list)
    exclude_databases: list = field(default_factory=list)
    sandbox_patterns: list = field(default_factory=list)
    domains: dict = field(default_factory=dict)
    products_path: Optional[Path] = None
    cube_model_path: Optional[Path] = None
    intake_form_url: str = ""
    intake_log_path: Optional[Path] = None
    targets: dict = field(default_factory=dict)
    confluence: ConfluenceConfig = field(default_factory=ConfluenceConfig)

    @property
    def intake_configured(self) -> bool:
        return bool(self.intake_form_url) and PLACEHOLDER not in self.intake_form_url


def load(path: str | Path) -> Config:
    file = Path(path).resolve()
    raw = yaml.safe_load(file.read_text(encoding="utf-8")) or {}
    root = file.parent

    run = raw.get("run", {}) or {}
    registry = raw.get("registry", {}) or {}
    intake = raw.get("intake", {}) or {}
    confluence = raw.get("confluence", {}) or {}

    return Config(
        root=root,
        window_days=int(run.get("window_days", 14)),
        timezone=run.get("timezone", "Asia/Kolkata"),
        iceberg_only=bool(run.get("iceberg_only", True)),
        output_dir=_resolve(root, run.get("output_dir", "out")),
        environments=raw.get("environments", []) or [],
        exclude_databases=raw.get("exclude_databases", []) or [],
        sandbox_patterns=raw.get("sandbox_patterns", []) or [],
        domains=raw.get("domains", {}) or {},
        products_path=_resolve(root, registry.get("products")),
        cube_model_path=_resolve(root, registry.get("cube_model")),
        intake_form_url=intake.get("form_url") or "",
        intake_log_path=_resolve(root, intake.get("log_path")),
        targets={k: v for k, v in (raw.get("targets") or {}).items() if v is not None},
        confluence=ConfluenceConfig(**confluence) if confluence else ConfluenceConfig(),
    )


def _resolve(root: Path, value) -> Optional[Path]:
    if not value:
        return None
    path = Path(value)
    return path if path.is_absolute() else root / path
