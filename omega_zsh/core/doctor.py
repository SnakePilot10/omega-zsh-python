import os
from pathlib import Path
from shutil import which
from typing import Any

from .constants import BIN_PLUGINS, EXTERNAL_URLS, THEMES_OMZ_BUILTIN
from .context import SystemContext
from .manifest import load_manifest
from .state import AppState, StateManager


def _check(check_id: str, status: str, severity: str, message: str, detail: str) -> dict[str, str]:
    return {
        "id": check_id,
        "status": status,
        "severity": severity,
        "message": message,
        "detail": detail,
    }


def _path_writable(path: Path) -> bool:
    target = path if path.exists() and path.is_dir() else path.parent
    return target.exists() and target.is_dir() and os.access(target, os.W_OK)


def _load_state(context: SystemContext) -> AppState:
    try:
        return StateManager(context.omega_dir).load()
    except Exception:
        return AppState()


def _theme_exists(context: SystemContext, theme_id: str) -> bool:
    if any(theme.id == theme_id for theme in THEMES_OMZ_BUILTIN):
        return True
    candidates = [
        context.assets_dir / "themes" / f"{theme_id}.zsh-theme",
        context.omz_dir / "themes" / f"{theme_id}.zsh-theme",
        context.omz_dir / "custom" / "themes" / f"{theme_id}.zsh-theme",
    ]
    return any(path.exists() for path in candidates)


def run_doctor(context: SystemContext | None = None) -> dict[str, Any]:
    """Return a read-only diagnostic report for the current Omega-ZSH setup."""
    context = context or SystemContext()
    state = _load_state(context)
    checks = []
    zsh_path = which("zsh")
    git_path = which("git")

    checks.append(
        _check(
            "zsh",
            "ok" if zsh_path else "missing",
            "ok" if zsh_path else "error",
            "zsh disponible" if zsh_path else "zsh no está en PATH",
            zsh_path or "Instala zsh antes de aplicar configuraciones de shell",
        )
    )
    checks.append(
        _check(
            "git",
            "ok" if git_path else "missing",
            "ok" if git_path else "error",
            "git disponible" if git_path else "git no está en PATH",
            git_path or "Instala git para clonar Oh My Zsh y plugins externos",
        )
    )

    omz_main = context.omz_dir / "oh-my-zsh.sh"
    checks.append(
        _check(
            "oh-my-zsh",
            "ok" if omz_main.exists() else "missing",
            "ok" if omz_main.exists() else "error",
            "Oh My Zsh instalado" if omz_main.exists() else "Oh My Zsh no encontrado",
            str(omz_main) if omz_main.exists() else f"No existe {omz_main}",
        )
    )
    checks.append(_check("ZSH", "ok", "ok", "$ZSH resuelto", str(context.omz_dir)))
    checks.append(
        _check(
            ".zshrc",
            "ok" if context.zshrc_path.exists() else "missing",
            "ok" if context.zshrc_path.exists() else "warning",
            ".zshrc presente" if context.zshrc_path.exists() else ".zshrc aún no existe",
            str(context.zshrc_path),
        )
    )
    omega_dir_writable = _path_writable(context.omega_dir)
    checks.append(
        _check(
            "omega-dir-writable",
            "ok" if omega_dir_writable else "warning",
            "ok" if omega_dir_writable else "warning",
            "directorio Omega escribible"
            if omega_dir_writable
            else "directorio Omega no parece escribible",
            str(context.omega_dir),
        )
    )
    zshrc_dir_writable = _path_writable(context.zshrc_path)
    checks.append(
        _check(
            "zshrc-dir-writable",
            "ok" if zshrc_dir_writable else "warning",
            "ok" if zshrc_dir_writable else "warning",
            "directorio de .zshrc escribible"
            if zshrc_dir_writable
            else "directorio de .zshrc no parece escribible",
            str(context.zshrc_path.parent),
        )
    )

    manifest_path = context.omega_dir / "manifest.json"
    manifest = load_manifest(manifest_path)
    checks.append(
        _check(
            "manifest",
            "ok" if manifest_path.exists() and manifest.get("files") is not None else "warning",
            "ok" if manifest_path.exists() and manifest.get("files") is not None else "warning",
            "manifest disponible" if manifest_path.exists() else "manifest aún no existe",
            str(manifest_path) if manifest_path.exists() else "manifest aún no existe",
        )
    )

    selected = state.selected_plugins
    missing_tools = [plugin for plugin in selected if plugin in BIN_PLUGINS and not which(plugin)]
    checks.append(
        _check(
            "binary-tools",
            "ok" if not missing_tools else "missing",
            "ok" if not missing_tools else "warning",
            "herramientas binarias disponibles"
            if not missing_tools
            else "faltan herramientas binarias seleccionadas",
            ", ".join(missing_tools) if missing_tools else "herramientas seleccionadas disponibles",
        )
    )

    missing_plugins = []
    for plugin in selected:
        if plugin in EXTERNAL_URLS:
            target = context.omz_dir / "custom" / "plugins" / plugin
            if not target.exists():
                missing_plugins.append(plugin)
    checks.append(
        _check(
            "external-plugins",
            "ok" if not missing_plugins else "missing",
            "ok" if not missing_plugins else "warning",
            "plugins externos disponibles" if not missing_plugins else "faltan plugins externos seleccionados",
            ", ".join(missing_plugins) if missing_plugins else "plugins externos presentes o no seleccionados",
        )
    )

    theme_exists = _theme_exists(context, state.selected_theme)
    checks.append(
        _check(
            "theme",
            "ok" if theme_exists else "missing",
            "ok" if theme_exists else "warning",
            "tema disponible" if theme_exists else "tema seleccionado no encontrado",
            state.selected_theme,
        )
    )

    severity_order = {"error": 2, "warning": 1, "ok": 0}
    overall = max(checks, key=lambda item: severity_order.get(item["severity"], 0))["severity"]
    return {"overall": overall, "checks": checks}
