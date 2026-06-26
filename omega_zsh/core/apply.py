from dataclasses import dataclass, field
from importlib.metadata import PackageNotFoundError, version
from pathlib import Path
from typing import Any

from .constants import is_binary_tool, unknown_plugin_ids, valid_selected_plugins
from .figlet import FigletManager
from .generator import ConfigGenerator
from .manifest import record_managed_file, require_managed_or_absent
from .operations import write_operation_log
from .state import AppState


@dataclass
class ApplyResult:
    ok: bool
    message: str
    changed: list[str] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)
    errors: list[str] = field(default_factory=list)
    dry_run: bool = False
    preview: str = ""


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
    selected_plugins = valid_selected_plugins(state.selected_plugins, state.allowed_custom_plugins)
    return {
        "version": get_app_version(),
        "omz_dir": str(context.omz_dir),
        "user_theme": state.selected_theme,
        "root_theme": state.selected_root_theme,
        "plugins": [p for p in selected_plugins if not is_binary_tool(p)],
        "header_cmd": build_header_command(state),
        "is_termux": context.is_termux,
        "active_tools": [p for p in selected_plugins if is_binary_tool(p)],
        "default_user": "",
        "personal_zsh": str(context.home / ".omega-zsh" / "personal.zsh"),
        "custom_zsh": str(context.home / ".omega-zsh" / "custom.zsh"),
    }


def link_omega_themes(assets_dir: Path, omz_dir: Path, manifest_path: Path | None = None) -> list[str]:
    omega_themes_dir = assets_dir / "themes"
    warnings: list[str] = []
    if not (omz_dir / "oh-my-zsh.sh").exists():
        return [f"Oh My Zsh no encontrado en {omz_dir}; se omitió el link de temas"]
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


def preview_config(context: Any, state: AppState) -> ApplyResult:
    """Return the rendered config and planned paths without writing files."""
    warnings = []
    unknown = unknown_plugin_ids(state.selected_plugins, state.allowed_custom_plugins)
    if unknown:
        warnings.append("IDs seleccionados desconocidos omitidos: " + ", ".join(unknown))
    if not (context.omz_dir / "oh-my-zsh.sh").exists():
        warnings.append(f"Oh My Zsh no encontrado en {context.omz_dir}; se omitió el link de temas")
    content = render_config(context, state)
    planned = [str(context.zshrc_path)]
    if not warnings:
        planned.append(str(context.omz_dir / "custom" / "themes"))
    return ApplyResult(
        True,
        f"Preview apply: se renderizarían {len(content)} bytes hacia {context.zshrc_path}.",
        changed=planned,
        warnings=warnings,
        dry_run=True,
        preview=content,
    )


def apply_config(context: Any, state: AppState, dry_run: bool = False) -> ApplyResult:
    """Apply the current state to shell config; installation remains out of scope."""
    try:
        generator = ConfigGenerator(context.assets_dir / "templates")
        warnings = []
        unknown = unknown_plugin_ids(state.selected_plugins, state.allowed_custom_plugins)
        if unknown:
            warnings.append("IDs seleccionados desconocidos omitidos: " + ", ".join(unknown))
        if not (context.omz_dir / "oh-my-zsh.sh").exists():
            warnings.append(f"Oh My Zsh no encontrado en {context.omz_dir}; se omitió el link de temas")
        if dry_run:
            return preview_config(context, state)

        if not warnings:
            warnings = link_omega_themes(
                context.assets_dir,
                context.omz_dir,
                context.omega_dir / "manifest.json",
            )
        ok = generator.generate_zshrc(context.zshrc_path, build_config_context(context, state))
        if not ok:
            result = ApplyResult(
                False,
                "Error al generar .zshrc. Revisa el log para detalles.",
                warnings=warnings,
                errors=["generate_zshrc failed"],
            )
            _log_apply(context, result)
            return result
        if warnings:
            result = ApplyResult(
                True,
                "Configuración actualizada con advertencias: " + "; ".join(warnings),
                changed=[str(context.zshrc_path)],
                warnings=warnings,
            )
            _log_apply(context, result)
            return result
        result = ApplyResult(True, "Configuración actualizada con éxito.", changed=[str(context.zshrc_path)])
        _log_apply(context, result)
        return result
    except Exception as exc:
        result = ApplyResult(False, f"Error al aplicar: {exc}", errors=[str(exc)])
        _log_apply(context, result)
        return result


def _log_apply(context: Any, result: ApplyResult) -> None:
    write_operation_log(
        context.omega_dir,
        "apply",
        [
            f"ok={result.ok}",
            f"message={result.message}",
            "changed=" + ", ".join(result.changed),
            "warnings=" + ", ".join(result.warnings),
            "errors=" + ", ".join(result.errors),
        ],
    )
