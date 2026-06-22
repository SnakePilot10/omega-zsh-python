import json
import os
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


def default_manifest_path(home: Path) -> Path:
    return home / ".omega-zsh" / "manifest.json"


def load_manifest(path: Path) -> dict[str, Any]:
    if not path.exists():
        return {"version": 1, "files": {}}
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return {"version": 1, "files": {}}
    if not isinstance(data, dict):
        return {"version": 1, "files": {}}
    data.setdefault("version", 1)
    data.setdefault("files", {})
    if not isinstance(data["files"], dict):
        data["files"] = {}
    return data


def save_manifest(path: Path, data: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temp_path = path.with_suffix(".tmp")
    temp_path.write_text(json.dumps(data, indent=2, ensure_ascii=False), encoding="utf-8")
    temp_path.replace(path)


def record_managed_file(
    manifest_path: Path,
    file_path: Path,
    kind: str,
    action: str,
    metadata: dict[str, Any] | None = None,
) -> None:
    manifest = load_manifest(manifest_path)
    key = str(file_path.expanduser())
    manifest["files"][key] = {
        "kind": kind,
        "action": action,
        "updated_at": datetime.now(timezone.utc).isoformat(),
        "metadata": metadata or {},
    }
    save_manifest(manifest_path, manifest)


def get_managed_file(manifest_path: Path, file_path: Path) -> dict[str, Any] | None:
    manifest = load_manifest(manifest_path)
    entry = manifest.get("files", {}).get(str(file_path.expanduser()))
    return entry if isinstance(entry, dict) else None


def is_managed_file(
    manifest_path: Path,
    file_path: Path,
    kind: str | None = None,
    metadata: dict[str, Any] | None = None,
) -> bool:
    entry = get_managed_file(manifest_path, file_path)
    if entry is None:
        return False
    if kind is not None and entry.get("kind") != kind:
        return False
    if metadata:
        entry_metadata = entry.get("metadata") if isinstance(entry.get("metadata"), dict) else {}
        for key, value in metadata.items():
            if entry_metadata.get(key) != value:
                return False
    return True


def path_exists_or_is_symlink(path: Path) -> bool:
    return os.path.lexists(path)


def require_managed_or_absent(
    manifest_path: Path,
    file_path: Path,
    kind: str,
    metadata: dict[str, Any] | None = None,
) -> bool:
    if not path_exists_or_is_symlink(file_path):
        return True
    return is_managed_file(manifest_path, file_path, kind, metadata)
