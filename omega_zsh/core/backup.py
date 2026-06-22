from datetime import datetime
from pathlib import Path
from shutil import copy2


def create_backup(path: Path, backup_dir: Path | None = None) -> Path | None:
    """Create a timestamped backup for an existing file."""
    if not path.exists() or not path.is_file():
        return None

    target_dir = backup_dir or path.parent / ".omega-backups"
    target_dir.mkdir(parents=True, exist_ok=True)
    stamp = datetime.now().strftime("%Y%m%d-%H%M%S")
    backup_path = target_dir / f"{path.name}.{stamp}.bak"
    counter = 1
    while backup_path.exists():
        backup_path = target_dir / f"{path.name}.{stamp}.{counter}.bak"
        counter += 1

    copy2(path, backup_path)
    return backup_path


def prune_backups(backup_dir: Path, file_name: str, keep: int = 10) -> list[Path]:
    """Keep the newest N backups for a file and remove older ones."""
    if keep < 1 or not backup_dir.exists():
        return []

    backups = sorted(
        backup_dir.glob(f"{file_name}.*.bak"),
        key=lambda p: p.stat().st_mtime,
        reverse=True,
    )
    removed = []
    for old_backup in backups[keep:]:
        old_backup.unlink(missing_ok=True)
        removed.append(old_backup)
    return removed


def restore_backup(backup_path: Path | None, target_path: Path) -> bool:
    """Restore a backup over the target path when a backup exists."""
    if backup_path is None or not backup_path.exists():
        return False
    target_path.parent.mkdir(parents=True, exist_ok=True)
    copy2(backup_path, target_path)
    return True
