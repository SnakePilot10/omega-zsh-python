from dataclasses import dataclass
from importlib.metadata import PackageNotFoundError, version
from pathlib import Path
from typing import Any

from .constants import BIN_PLUGINS
from .figlet import FigletManager
from .generator import ConfigGenerator
from .manifest import record_managed_file, require_managed_or_absent
from .state import AppState


@dataclass
class ApplyResult:
    ok: bool
    message: str


def get_app_version() -> str:
    try:
        return version("omega-zsh")
    except PackageNotFoundError:
        return "dev"


def build_header_command(state: AppState) -> str:
    if state.selected_header == "figlet":
        return FigletManager().generate_safe_command(state.header_text, state.header_font)
    if state.selected_header == "fastfetch":
        return "(( $+commands[fastfetch] )) && fastfetch"
    if state.selected_header == "cowsay":
        return "(( $+commands[cowsay] )) && cowsay Omega-ZSH"
    return ""


def build_config_context(context: Any, state: AppState) -> dict[str, Any]:
    bin_set = set(BIN_PLUGINS)
    return {
        "version": get_app_version(),
        "omz_dir": str(context.omz_dir),
        "user_theme": state.selected_theme,
        "root_theme": state.selected_root_theme,
        "plugins": [p for p in state.selected_plugins if p not in bin_set],
        "header_cmd": build_header_command(state),
        "is_termux": context.is_termux,
        "active_tools": [p for p in state.selected_plugins if p in bin_set],
        "default_user": "",
        "personal_zsh": str(context.home / ".omega-zsh" / "personal.zsh"),
        "custom_zsh": str(context.home / ".omega-zsh" / "custom.zsh"),
    }


def link_omega_themes(assets_dir: Path, omz_dir: Path, manifest_path: Path | None = None) -> list[str]:
    omega_themes_dir = assets_dir / "themes"
    warnings: list[str] = []
    if not omega_themes_dir.exists():
        return warnings

    custom_themes = omz_dir / "custom" / "themes"
    custom_themes.mkdir(parents=True, exist_ok=True)

    for theme_file in omega_themes_dir.glob("*.zsh-theme"):
        link = custom_themes / theme_file.name
        metadata = {"source": str(theme_file)}
        try:
            if manifest_path and not require_managed_or_absent(
                manifest_path,
                link,
                "theme_symlink",
                metadata,
            ):
                warnings.append(f"Tema existente no gestionado por Omega; se omite: {link}")
                continue
            if link.is_symlink():
                if link.resolve(strict=False) == theme_file.resolve(strict=False):
                    if manifest_path:
                        record_managed_file(
                            manifest_path,
                            link,
                            "theme_symlink",
                            "verified",
                            metadata,
                        )
                    continue
                link.unlink()
            link.symlink_to(theme_file)
            if manifest_path:
                record_managed_file(
                    manifest_path,
                    link,
                    "theme_symlink",
                    "created",
                    metadata,
                )
        except Exception as exc:
            warnings.append(f"No se pudo crear symlink para {theme_file.name}: {exc}")
    return warnings


def render_config(context: Any, state: AppState) -> str:
    """Render .zshrc content without touching the filesystem."""
    generator = ConfigGenerator(context.assets_dir / "templates")
    return generator.render_zshrc(build_config_context(context, state))


def apply_config(context: Any, state: AppState) -> ApplyResult:
    """Apply the current state to shell config; installation remains out of scope."""
    try:
        generator = ConfigGenerator(context.assets_dir / "templates")
        warnings = []
        if (context.omz_dir / "oh-my-zsh.sh").exists():
            warnings = link_omega_themes(
                context.assets_dir,
                context.omz_dir,
                context.omega_dir / "manifest.json",
            )
        else:
            warnings.append(f"Oh My Zsh no encontrado en {context.omz_dir}; se omitió el link de temas")
        ok = generator.generate_zshrc(context.zshrc_path, build_config_context(context, state))
        if not ok:
            return ApplyResult(False, "Error al generar .zshrc. Revisa el log para detalles.")
        if warnings:
            return ApplyResult(True, "Configuración actualizada con advertencias: " + "; ".join(warnings))
        return ApplyResult(True, "Configuración actualizada con éxito.")
    except Exception as exc:
        return ApplyResult(False, f"Error al aplicar: {exc}")
