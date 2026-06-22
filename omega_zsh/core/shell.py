import subprocess
from pathlib import Path
from shutil import which


def validate_zsh_syntax(path: Path) -> tuple[bool, str]:
    """Validate a zsh script with `zsh -n` when zsh is available."""
    zsh_bin = which("zsh")
    if not zsh_bin:
        return True, "zsh not found; syntax validation skipped"

    result = subprocess.run(
        [zsh_bin, "-n", str(path)],
        capture_output=True,
        text=True,
        timeout=10,
    )
    if result.returncode == 0:
        return True, "zsh syntax ok"
    return False, (result.stderr or result.stdout or "zsh syntax validation failed").strip()
