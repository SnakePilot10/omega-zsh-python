import re
from dataclasses import dataclass, field
from pathlib import Path

from .backup import create_backup, restore_backup
from .context import SystemContext
from .shell import validate_zsh_syntax


OMEGA_RE = re.compile(r"omega[-_]?zsh|omega_zsh|omegazsh|omega-zsh-python", re.IGNORECASE)


@dataclass
class RecoveryResult:
    ok: bool
    action: str
    changed: list[str] = field(default_factory=list)
    backups: list[str] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)
    errors: list[str] = field(default_factory=list)
    messages: list[str] = field(default_factory=list)

    @property
    def summary(self) -> str:
        if self.errors:
            return "; ".join(self.errors)
        if self.warnings:
            return "; ".join(self.warnings)
        return "; ".join(self.messages) if self.messages else "Recovery action finished."


def _config_files(context: SystemContext) -> list[Path]:
    return [
        context.home / ".zshrc",
        context.home / ".bashrc",
        context.home / ".profile",
        context.home / ".bash_profile",
    ]


def _backup_dir(context: SystemContext) -> Path:
    return context.home / ".omega-zsh-recovery"


def _safe_name(path: Path) -> str:
    return str(path).replace("/", "__")


def _record_backup(result: RecoveryResult, backup_path: Path | None) -> None:
    if backup_path:
        result.backups.append(str(backup_path))


def _backup_file(context: SystemContext, path: Path, result: RecoveryResult, dry_run: bool) -> None:
    if not path.exists() or not path.is_file():
        return
    if dry_run:
        result.messages.append(f"Would back up {path}")
        return
    _record_backup(result, create_backup(path, _backup_dir(context)))


def _clean_shell_file(context: SystemContext, path: Path, result: RecoveryResult, dry_run: bool) -> None:
    if not path.exists() or not path.is_file():
        return
    content = path.read_text(encoding="utf-8", errors="ignore")
    if not OMEGA_RE.search(content):
        return
    _backup_file(context, path, result, dry_run)
    result.messages.append(f"Omega references found in {path}")
    if dry_run:
        result.messages.append(f"Would remove Omega references from {path}")
        return

    cleaned: list[str] = []
    skip_block = False
    for line in content.splitlines(keepends=True):
        stripped = line.strip().lower()
        if re.match(r"#?\s*>>>\s*(omega[-_]?zsh|omega_zsh|omegazsh|omega-zsh-python)", stripped):
            skip_block = True
            continue
        if re.match(r"#?\s*<<<\s*(omega[-_]?zsh|omega_zsh|omegazsh|omega-zsh-python)", stripped):
            skip_block = False
            continue
        if skip_block or OMEGA_RE.search(line):
            continue
        cleaned.append(line)
    path.write_text("".join(cleaned), encoding="utf-8")
    result.changed.append(str(path))


def _path_block() -> str:
    return """# Safe PATH
if [ -n "${PREFIX:-}" ]; then
  export PATH="$PREFIX/bin:$PATH"
fi
if [ -d "$HOME/.local/bin" ]; then
  export PATH="$HOME/.local/bin:$PATH"
fi"""


def _minimal_zshrc() -> str:
    return f"""# ~/.zshrc rebuilt by Omega ZSH recovery

{_path_block()}

export HISTFILE="$HOME/.zsh_history"
export HISTSIZE=5000
export SAVEHIST=5000
setopt autocd extendedglob notify hist_ignore_dups share_history 2>/dev/null || true
autoload -Uz compinit 2>/dev/null && compinit 2>/dev/null || true

alias ll='ls -la'
alias la='ls -A'
alias l='ls -CF'

PROMPT='%F{{cyan}}%n@%m%f:%F{{blue}}%~%f %# '
"""


def _minimal_bashrc() -> str:
    return f"""# ~/.bashrc rebuilt by Omega ZSH recovery

{_path_block()}

export HISTSIZE=5000
export HISTFILESIZE=5000
alias ll='ls -la'
alias la='ls -A'
alias l='ls -CF'
PS1='\\u@\\h:\\w\\$ '
"""


def _minimal_profile() -> str:
    return f"""# ~/.profile rebuilt by Omega ZSH recovery

{_path_block()}
"""


def _write_minimal(path: Path, content: str, result: RecoveryResult, dry_run: bool) -> None:
    if dry_run:
        result.messages.append(f"Would write minimal safe config to {path}")
        return
    path.write_text(content, encoding="utf-8")
    result.changed.append(str(path))


def _latest_valid_zshrc_backup(context: SystemContext) -> Path | None:
    candidates: list[Path] = []
    omega_backups = context.zshrc_path.parent / ".omega-backups"
    if omega_backups.exists():
        candidates.extend(omega_backups.glob(f"{context.zshrc_path.name}.*.bak"))
    legacy_recovery = _backup_dir(context)
    if legacy_recovery.exists():
        legacy = legacy_recovery / _safe_name(context.zshrc_path)
        if legacy.exists():
            candidates.append(legacy)
        candidates.extend(legacy_recovery.glob(f"{context.zshrc_path.name}.*.bak"))

    candidates = sorted(
        [path for path in candidates if path.is_file()],
        key=lambda path: path.stat().st_mtime,
        reverse=True,
    )
    for backup in candidates:
        valid, _ = validate_zsh_syntax(backup)
        if valid:
            return backup
    return None


def restore_latest_zshrc_backup(context: SystemContext | None = None, dry_run: bool = False) -> RecoveryResult:
    context = context or SystemContext()
    result = RecoveryResult(ok=True, action="restore-zshrc")
    backup = _latest_valid_zshrc_backup(context)
    if not backup:
        result.ok = False
        result.errors.append("No valid .zshrc backup found.")
        return result
    if dry_run:
        result.messages.append(f"Would restore {backup} -> {context.zshrc_path}")
        return result
    _backup_file(context, context.zshrc_path, result, dry_run=False)
    restore_backup(backup, context.zshrc_path)
    result.changed.append(str(context.zshrc_path))
    result.messages.append(f"Restored .zshrc from {backup}")
    return result


def cleanup_shell_files(context: SystemContext | None = None, dry_run: bool = False) -> RecoveryResult:
    context = context or SystemContext()
    result = RecoveryResult(ok=True, action="cleanup")
    for path in _config_files(context):
        _clean_shell_file(context, path, result, dry_run)
    if not result.changed and not result.messages:
        result.messages.append("No Omega shell references found.")
    return result


def nuclear_fix_shell(context: SystemContext | None = None, dry_run: bool = False) -> RecoveryResult:
    context = context or SystemContext()
    result = RecoveryResult(ok=True, action="nuclear-fix")
    for path in _config_files(context):
        _backup_file(context, path, result, dry_run)
    _write_minimal(context.home / ".zshrc", _minimal_zshrc(), result, dry_run)
    _write_minimal(context.home / ".bashrc", _minimal_bashrc(), result, dry_run)
    _write_minimal(context.home / ".profile", _minimal_profile(), result, dry_run)
    bash_profile = context.home / ".bash_profile"
    if bash_profile.exists():
        if dry_run:
            result.messages.append(f"Would remove {bash_profile} to allow .profile fallback")
        else:
            bash_profile.unlink()
            result.changed.append(str(bash_profile))
    return result


def recovery_dry_run(context: SystemContext | None = None) -> RecoveryResult:
    context = context or SystemContext()
    result = RecoveryResult(ok=True, action="dry-run")
    for partial in (cleanup_shell_files(context, dry_run=True), nuclear_fix_shell(context, dry_run=True)):
        result.messages.extend(partial.messages)
        result.warnings.extend(partial.warnings)
        result.errors.extend(partial.errors)
    result.ok = not result.errors
    return result
