"""Stable identifiers for inventory objects.

The MicroStrategy exports supplied for US Ad Sales carry no object GUIDs, so this module mints
deterministic *surrogate* identifiers from the object's natural key (type + folder path + name).
Re-running the agent on the same export yields the same identifiers, so the inventory can be
diffed across refreshes and referenced from tickets. When true MSTR GUIDs become available they
should be loaded into the separate ``MSTR GUID`` column rather than replacing these.
"""

import hashlib
import re
import unicodedata

NAMESPACE = "carl.usadsales.mstr.inventory.v1"


def normalize(value) -> str:
    """Aggressive key for *matching*: folds case, whitespace runs and unicode variants.

    Used to recognise the same object across exports. Not used for identifiers, because MSTR
    permits sibling objects that differ only by case or internal spacing.
    """
    if value is None:
        return ""
    text = unicodedata.normalize("NFKC", str(value))
    text = text.replace("\u00a0", " ").strip().strip("\\")
    text = re.sub(r"\s+", " ", text)
    return text.casefold()


def identity_key(value) -> str:
    """Conservative key for *identifiers*: preserves case and internal spacing.

    Only unicode form and surrounding whitespace/separators are normalised, so two objects that
    MSTR treats as distinct never collapse to the same identifier.
    """
    if value is None:
        return ""
    text = unicodedata.normalize("NFKC", str(value))
    return text.replace("\u00a0", " ").strip().strip("\\")


def natural_key(object_type: str, folder_path, name) -> str:
    return "|".join(
        [NAMESPACE, identity_key(object_type), identity_key(folder_path), identity_key(name)]
    )


def _digest(object_type: str, folder_path, name) -> str:
    key = natural_key(object_type, folder_path, name)
    return hashlib.sha256(key.encode("utf-8")).hexdigest()


def object_id(prefix: str, object_type: str, folder_path, name) -> str:
    """Short human-quotable id, e.g. ``RPT-3F9A2C1D5B07``."""
    return f"{prefix}-{_digest(object_type, folder_path, name)[:12].upper()}"


def surrogate_guid(object_type: str, folder_path, name) -> str:
    """32-character uppercase hex in MicroStrategy's GUID shape."""
    return _digest(object_type, folder_path, name)[:32].upper()


def full_path(folder_path, name) -> str:
    folder = "" if folder_path is None else str(folder_path).strip()
    label = "" if name is None else str(name).strip()
    if not folder:
        return label
    return folder.rstrip("\\") + "\\" + label
