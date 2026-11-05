"""Cube Jinja template context: environment-specific value resolution.

Registers functions callable from ``{{ ... }}`` expressions in YAML model files.
Cube executes this file via its Python bridge during model compilation, so a
single committed model tree resolves to the right per-environment values at
compile time — no external pre-processing / bake step.

The one function today is ``catalog()``, which maps a logical catalog key to the
environment-specific Glue database name for the current ``CUBE_ENV`` (a required
runtime input; see ``_get_env`` and the eager module-level validation). See
``model/globals.json`` for the mappings and ``docs/tutorial-local.md`` /
``.kiro/steering/local-dev.md`` for how to author and run this locally.
"""

from __future__ import annotations

import json
import os
from pathlib import Path

from cube import TemplateContext

template = TemplateContext()


class SafeString(str):
    """Bypass Cube's Jinja auto-escaping for this value.

    Cube's Jinja auto-escaping is on by default and wraps a plain ``str`` return
    value in quotes, producing broken SQL like ``""carl_dwhprd_gold_dev".table``
    instead of ``carl_dwhprd_gold_dev.table``. Returning a ``SafeString`` (with
    ``is_safe = True``) marks the value as already-safe so Cube leaves it alone,
    which avoids a per-file ``| safe`` filter in every model.
    See https://docs.cube.dev/docs/data-modeling/dynamic/jinja (Escaping).
    """

    is_safe = True


# Path resolution: Cube executes globals.py with CWD=/cube/conf and
# __file__='globals.py' (NOT an absolute path), so Path(__file__).parent does not
# work. The model directory is /cube/conf/model/ by default, overridable via
# CUBEJS_SCHEMA_PATH. globals.json sits at the root of that model directory,
# alongside this file.
_MODEL_DIR = Path(os.environ.get("CUBEJS_SCHEMA_PATH", "model"))
_GLOBALS_FILE = _MODEL_DIR / "globals.json"

_VALID_ENVS = {"dev", "qa", "stage", "prod"}


def _load_values() -> dict:
    """Load globals.json fresh on every call.

    The file is <1KB, so re-reading has no meaningful cost. Reading fresh avoids
    adding a second caching layer on top of whatever module caching Cube's Python
    bridge does: if Cube re-imports globals.py per compile cycle, a mappings
    change delivered via EFS takes effect immediately; if Cube caches the module
    for the process lifetime, a change still needs a task restart either way.

    Read lazily (not validated at import like CUBE_ENV) because it's mutable
    state delivered via EFS: it can change between compiles, and a missing file
    already fails loudly via catalog() with the exact path named.
    """
    if not _GLOBALS_FILE.exists():
        raise RuntimeError(
            f"globals.json not found at {_GLOBALS_FILE.resolve()}. "
            f"Expected at the root of the model directory "
            f"(set CUBEJS_SCHEMA_PATH if the model dir is not ./model)."
        )
    return json.loads(_GLOBALS_FILE.read_text())


def _get_env() -> str:
    """Read and validate CUBE_ENV, returning the validated env name.

    Required input: every model resolves a catalog() against it, so a missing or
    invalid value fails the whole model tree. Set per-env on the ECS task def
    (carl-infra `cube/main.tf`) and by docker-compose locally.
    """
    # strip() + falsy check so empty/whitespace (a wiped TF var or `value = ""`)
    # gets the "not set" message; os.environ.get returns "" not None in that case.
    # Normalize whitespace but not case, so a `CUBE_ENV=DEV` typo still surfaces.
    env = os.environ.get("CUBE_ENV", "").strip()
    if not env:
        raise RuntimeError(
            "CUBE_ENV is not set. Set it to one of: dev, qa, stage, prod. "
            "It is required by model/globals.py to resolve {{ catalog(...) }} "
            "references. It is set per-env on the ECS task definition (carl-infra "
            "cube/main.tf); for local dev, docker-compose.yml defaults it to dev "
            "(or add CUBE_ENV=dev to your .env)."
        )
    if env not in _VALID_ENVS:
        raise RuntimeError(f"CUBE_ENV='{env}' is not valid. Must be one of: {sorted(_VALID_ENVS)}")
    return env


# Validate at import (Cube imports this before rendering any model YAML). A bad
# CUBE_ENV fails the compile either way, but validating here points the traceback
# straight at globals.py instead of an arbitrary model file. CARL-3727.
_get_env()


@template.function("catalog")
def catalog(key: str) -> str:
    """Resolve a catalog key to the environment-specific Glue database name.

    Usage in YAML (the surrounding quotes are consumed by YAML; Cube renders the
    Jinja on the raw text before YAML parsing, so the SQL receives the bare
    resolved name)::

        sql_table: "{{ catalog('dwhprd_gold') }}.my_table"

    Returns a SafeString to bypass Cube's Jinja auto-escaping. Raises a compile
    error with an actionable message on an unknown key or a missing env mapping.
    """
    env = _get_env()
    values = _load_values()
    catalogs = values.get("catalogs")
    if catalogs is None:
        raise RuntimeError("globals.json is missing the 'catalogs' key")
    if key not in catalogs:
        raise ValueError(
            f"Unknown catalog key: '{key}'. "
            f"Available keys: {sorted(catalogs.keys())}. "
            f"Add it to model/globals.json if this is a new catalog."
        )
    env_map = catalogs[key]
    if env not in env_map:
        raise ValueError(
            f"Catalog '{key}' has no mapping for CUBE_ENV='{env}'. "
            f"Available envs for this key: {sorted(env_map.keys())}. "
            f"Add '{env}' to this key in model/globals.json."
        )
    return SafeString(env_map[env])
