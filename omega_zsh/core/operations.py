from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path
from typing import Iterable


def write_operation_log(omega_dir: Path, operation: str, lines: Iterable[str]) -> Path | None:
    """Append an auditable operation log under ~/.omega-zsh/logs/.

    Callers decide when logging is appropriate. Read-only flows should not call
    this helper because it creates the log directory on demand.
    """
    try:
        safe_name = "".join(ch if ch.isalnum() or ch in {"-", "_"} else "-" for ch in operation)
        log_dir = omega_dir / "logs"
        log_dir.mkdir(parents=True, exist_ok=True)
        log_path = log_dir / f"{safe_name}.log"
        timestamp = datetime.now(timezone.utc).isoformat(timespec="seconds")
        entry = [f"[{timestamp}] {operation}"]
        entry.extend(str(line) for line in lines)
        log_path.open("a", encoding="utf-8").write("\n".join(entry) + "\n")
        return log_path
    except Exception:
        return None
