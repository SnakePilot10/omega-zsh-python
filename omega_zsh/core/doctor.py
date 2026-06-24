import json
import os
from pathlib import Path
from shutil import which
from typing import Any

from .backup import create_backup, restore_backup
from .constants import BIN_PLUGINS, EXTERNAL_URLS, THEMES_OMZ_BUILTIN
from .context import SystemContext
from .installer import BINARY_COMMANDS
from .manifest import load_manifest, record_managed_file, save_manifest
from .shell import validate_zsh_syntax
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


def _package_hint(context: SystemContext) -> str:
    if context.is_termux:
        return "pkg install zsh git curl"
    commands = {
        "pkg": "pkg install zsh git curl",
        "apt": "sudo apt install zsh git curl",
        "nala": "sudo nala install zsh git curl",
        "pacman": "sudo pacman -S zsh git curl",
        "dnf": "sudo dnf install zsh git curl",
        "apk": "sudo apk add zsh git curl",
        "zypper": "sudo zypper install zsh git curl",
        "xbps": "sudo xbps-install -S zsh git curl",
    }
    return commands.get(context.package_manager_type, "instala zsh, git y curl con tu gestor de paquetes")


def _omz_status(context: SystemContext) -> tuple[dict[str, str], dict[str, str]]:
    env = getattr(context, "_env", {})
    zsh_env = env.get("ZSH")
    default_omz = context.home / ".oh-my-zsh"
    omz_main = context.omz_dir / "oh-my-zsh.sh"
    install_hint = (
        f"Prerrequisitos: {_package_hint(context)}. "
        f"Instala Oh My Zsh en {context.omz_dir} y vuelve a ejecutar omega doctor."
    )

    if zsh_env:
        if context.omz_dir.exists():
            zsh_check = _check("ZSH", "ok", "ok", "$ZSH resuelto", f"$ZSH={context.omz_dir}")
        else:
            zsh_check = _check(
                "ZSH",
                "warning",
                "warning",
                "$ZSH apunta a ruta inexistente",
                f"$ZSH={context.omz_dir}. Corrige $ZSH o instala Oh My Zsh ahí.",
            )
    elif default_omz.exists():
        zsh_check = _check(
            "ZSH",
            "ok",
            "ok",
            "$ZSH no definido; usando ruta default",
            str(default_omz),
        )
    else:
        zsh_check = _check(
            "ZSH",
            "warning",
            "warning",
            "$ZSH no definido y ruta default ausente",
            f"Ruta default esperada: {default_omz}",
        )

    if not context.omz_dir.exists():
        omz_check = _check(
            "oh-my-zsh",
            "missing",
            "error",
            "directorio Oh My Zsh no existe",
            f"Ruta esperada: {context.omz_dir}. {install_hint}",
        )
    elif not omz_main.exists():
        omz_check = _check(
            "oh-my-zsh",
            "missing",
            "error",
            "oh-my-zsh.sh no encontrado",
            f"Ruta esperada: {omz_main}. Reinstala o repara Oh My Zsh en {context.omz_dir}.",
        )
    else:
        omz_check = _check("oh-my-zsh", "ok", "ok", "Oh My Zsh instalado", str(omz_main))

    return zsh_check, omz_check


def _binary_available(plugin_id: str) -> bool:
    return any(which(command) for command in BINARY_COMMANDS.get(plugin_id, [plugin_id]))


def _binary_detail(context: SystemContext, missing_tools: list[str]) -> str:
    if not missing_tools:
        return "herramientas seleccionadas disponibles"
    install_hint = _package_hint(context)
    details = []
    for tool in missing_tools:
        commands = "/".join(BINARY_COMMANDS.get(tool, [tool]))
        details.append(f"{tool} (comando: {commands}; instalar: {install_hint})")
    return "; ".join(details)


def _external_plugin_detail(context: SystemContext, missing_plugins: list[str]) -> str:
    if not missing_plugins:
        return "plugins externos presentes o no seleccionados"
    details = []
    for plugin in missing_plugins:
        target = context.omz_dir / "custom" / "plugins" / plugin
        details.append(f"{plugin}: falta {target}; origen {EXTERNAL_URLS[plugin]}")
    return "; ".join(details)


def _latest_valid_zshrc_backup(context: SystemContext) -> Path | None:
    backup_dir = context.zshrc_path.parent / ".omega-backups"
    if not backup_dir.exists():
        return None
    backups = sorted(
        backup_dir.glob(f"{context.zshrc_path.name}.*.bak"),
        key=lambda path: path.stat().st_mtime,
        reverse=True,
    )
    for backup in backups:
        valid, _ = validate_zsh_syntax(backup)
        if valid:
            return backup
    return None


def _fix_result(fix_id: str, status: str, message: str, detail: str) -> dict[str, str]:
    return {"id": fix_id, "status": status, "message": message, "detail": detail}


def _manifest_status(path: Path) -> tuple[str, str, str]:
    if not path.exists():
        return "warning", "manifest aún no existe", "manifest aún no existe"
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except Exception as exc:
        return "warning", "manifest corrupto", str(exc)
    if not isinstance(data, dict) or not isinstance(data.get("files"), dict):
        return "warning", "manifest schema inválido", str(path)
    return "ok", "manifest disponible", str(path)


def _manifest_needs_rewrite(path: Path) -> bool:
    status, _, _ = _manifest_status(path)
    return status != "ok"


def _create_minimal_zshrc(context: SystemContext) -> dict[str, str]:
    if context.zshrc_path.exists():
        return _fix_result("zshrc", "skipped", ".zshrc existente preservado", str(context.zshrc_path))

    backup_path = _latest_valid_zshrc_backup(context)
    if backup_path:
        try:
            restore_backup(backup_path, context.zshrc_path)
            record_managed_file(
                context.omega_dir / "manifest.json",
                context.zshrc_path,
                "config",
                "doctor-restored",
                {"source": str(backup_path)},
            )
            return _fix_result("zshrc", "fixed", ".zshrc restaurado desde backup válido", str(backup_path))
        except Exception as exc:
            return _fix_result("zshrc", "failed", "no se pudo restaurar backup de .zshrc", str(exc))

    content = "# Created by Omega-ZSH doctor --fix\n# Run omega to configure your shell.\n"
    temp_path = context.zshrc_path.with_suffix(".tmp")
    created_zshrc = False
    try:
        temp_path.write_text(content, encoding="utf-8")
        valid, message = validate_zsh_syntax(temp_path)
        if not valid:
            temp_path.unlink(missing_ok=True)
            return _fix_result("zshrc", "failed", "validación zsh falló", message)
        temp_path.replace(context.zshrc_path)
        created_zshrc = True
        record_managed_file(context.omega_dir / "manifest.json", context.zshrc_path, "config", "doctor-created")
        return _fix_result("zshrc", "fixed", ".zshrc mínimo creado", str(context.zshrc_path))
    except Exception as exc:
        temp_path.unlink(missing_ok=True)
        if created_zshrc:
            context.zshrc_path.unlink(missing_ok=True)
        return _fix_result("zshrc", "failed", "no se pudo crear .zshrc", str(exc))


def run_doctor_fix(context: SystemContext | None = None) -> dict[str, Any]:
    """Apply conservative, local doctor repairs and return the updated report."""
    context = context or SystemContext()
    fixes = []
    omega_dir_ready = False

    if context.omega_dir.exists() and context.omega_dir.is_dir():
        omega_dir_ready = True
        fixes.append(_fix_result("omega-dir", "skipped", "directorio Omega ya existe", str(context.omega_dir)))
    elif context.omega_dir.exists():
        fixes.append(_fix_result("omega-dir", "failed", "ruta Omega existe y no es directorio", str(context.omega_dir)))
    else:
        try:
            context.omega_dir.mkdir(parents=True, exist_ok=True)
            omega_dir_ready = True
            fixes.append(_fix_result("omega-dir", "fixed", "directorio Omega creado", str(context.omega_dir)))
        except Exception as exc:
            fixes.append(_fix_result("omega-dir", "failed", "no se pudo crear directorio Omega", str(exc)))

    manifest_path = context.omega_dir / "manifest.json"
    manifest_ready = False
    if not omega_dir_ready:
        fixes.append(_fix_result("manifest", "failed", "manifest omitido porque Omega dir no está listo", str(manifest_path)))
    elif _manifest_needs_rewrite(manifest_path):
        try:
            backup_path = create_backup(manifest_path, context.omega_dir / "backups")
            save_manifest(manifest_path, load_manifest(manifest_path))
            manifest_ready = True
            if backup_path:
                record_managed_file(
                    manifest_path,
                    backup_path,
                    "backup",
                    "doctor-created",
                    {"source": str(manifest_path)},
                )
            fixes.append(
                _fix_result(
                    "manifest",
                    "fixed",
                    "manifest inicializado" if backup_path is None else "manifest reparado con backup",
                    str(manifest_path),
                )
            )
        except Exception as exc:
            fixes.append(_fix_result("manifest", "failed", "no se pudo reparar manifest", str(exc)))
    else:
        manifest_ready = True
        fixes.append(_fix_result("manifest", "skipped", "manifest válido preservado", str(manifest_path)))

    if manifest_ready:
        fixes.append(_create_minimal_zshrc(context))
    else:
        fixes.append(
            _fix_result(
                "zshrc",
                "skipped",
                ".zshrc no creado porque manifest no está listo",
                str(context.zshrc_path),
            )
        )
    return {"fixes": fixes, "report": run_doctor(context)}


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

    zsh_check, omz_check = _omz_status(context)
    checks.append(omz_check)
    checks.append(zsh_check)
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
    manifest_status, manifest_message, manifest_detail = _manifest_status(manifest_path)
    checks.append(
        _check(
            "manifest",
            manifest_status,
            manifest_status,
            manifest_message,
            manifest_detail,
        )
    )

    selected = state.selected_plugins
    missing_tools = [plugin for plugin in selected if plugin in BIN_PLUGINS and not _binary_available(plugin)]
    checks.append(
        _check(
            "binary-tools",
            "ok" if not missing_tools else "missing",
            "ok" if not missing_tools else "warning",
            "herramientas binarias disponibles"
            if not missing_tools
            else "faltan herramientas binarias seleccionadas",
            _binary_detail(context, missing_tools),
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
            _external_plugin_detail(context, missing_plugins),
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
