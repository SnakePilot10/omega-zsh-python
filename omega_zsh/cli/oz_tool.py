#!/usr/bin/env python3
import os
import re
import subprocess
import sys
import time
from collections import Counter
from importlib.metadata import PackageNotFoundError, version
from pathlib import Path
from shutil import which

from rich import box
from rich.console import Console
from rich.panel import Panel
from rich.progress import Progress, SpinnerColumn, TextColumn
from rich.table import Table

try:
    from omega_zsh.core.plugins_db import get_description
    from omega_zsh.core.doctor import run_doctor, run_doctor_fix
except ImportError:

    def get_description(name):
        return "Sin descripción disponible."

    def run_doctor():
        return {"overall": "missing", "checks": []}

    def run_doctor_fix():
        return {"fixes": [], "report": run_doctor()}


try:
    from omega_zsh.core.constants import BIN_PLUGINS, DB_PLUGINS
    from omega_zsh.core.state import StateManager
except ImportError:
    BIN_PLUGINS = []
    DB_PLUGINS = []
    StateManager = None

console = Console()

HOME = Path.home()
ZSHRC = HOME / ".zshrc"
OMZ = HOME / ".oh-my-zsh"
CUSTOM_PLUGINS = OMZ / "custom/plugins"
STANDARD_PLUGINS = OMZ / "plugins"
CUSTOM_THEMES = OMZ / "custom/themes"
STANDARD_THEMES = OMZ / "themes"
PROJECT_ROOT = Path(__file__).parent.parent.parent
PROJECT_THEMES = PROJECT_ROOT / "omega_zsh/assets/themes"
OMEGA_CONFIG_DIR = HOME / ".omega-zsh"
COMMAND_TIMEOUT = 15


def get_app_version() -> str:
    try:
        return version("omega-zsh")
    except PackageNotFoundError:
        return "dev"


def require_command(command: str, install_hint: str | None = None) -> str | None:
    path = which(command)
    if path:
        return path

    hint = f"\n[dim]Instala `{command}`{f' con: {install_hint}' if install_hint else ''}.[/]"
    console.print(f"[bold red]Error:[/] no se encontró `{command}` en PATH.{hint}")
    return None


def run_command(
    cmd: list[str],
    *,
    cwd: Path | None = None,
    timeout: int = COMMAND_TIMEOUT,
) -> subprocess.CompletedProcess[str] | None:
    try:
        return subprocess.run(
            cmd,
            cwd=cwd,
            capture_output=True,
            text=True,
            timeout=timeout,
        )
    except subprocess.TimeoutExpired:
        console.print(f"[bold red]Timeout:[/] comando tardó más de {timeout}s: {' '.join(cmd)}")
    except OSError as exc:
        console.print(f"[bold red]Error ejecutando comando:[/] {exc}")
    return None


def _get_ram_usage() -> str:
    """Obtiene el uso de RAM leyendo /proc/meminfo de forma nativa."""
    try:
        with open("/proc/meminfo", encoding="utf-8") as f:
            lines = f.readlines()
        mem = {}
        for line in lines:
            parts = line.split(":")
            if len(parts) == 2:
                mem[parts[0].strip()] = int(parts[1].split()[0].strip())

        total = mem.get("MemTotal", 1)
        free = mem.get("MemFree", 0)
        buffers = mem.get("Buffers", 0)
        cached = mem.get("Cached", 0)
        used = total - free - buffers - cached
        return f"{int((used / total) * 100)}%"
    except Exception:
        return "N/A"


def _get_disk_usage(path: str = "/") -> str:
    """Obtiene el uso de disco usando os.statvfs."""
    try:
        st = os.statvfs(path)
        total = st.f_blocks * st.f_frsize
        free = st.f_bavail * st.f_frsize
        used = total - free
        return f"{int((used / total) * 100)}%"
    except Exception:
        return "N/A"


def _get_uptime_simple() -> str:
    """Obtiene el uptime leyendo /proc/uptime."""
    try:
        with open("/proc/uptime", encoding="utf-8") as f:
            uptime_seconds = float(f.readline().split()[0])
            hours, remainder = divmod(int(uptime_seconds), 3600)
            minutes, _ = divmod(remainder, 60)
            return f"{hours}h {minutes}m"
    except Exception:
        return "N/A"


def _get_os_label() -> str:
    if os.path.exists("/data/data/com.termux") or "com.termux" in os.environ.get("PREFIX", ""):
        return "Android/Termux"

    os_release = Path("/etc/os-release")
    if os_release.exists():
        try:
            for line in os_release.read_text(encoding="utf-8", errors="ignore").splitlines():
                if line.startswith("PRETTY_NAME="):
                    return line.split("=", 1)[1].strip().strip('"')
        except Exception:
            pass

    return sys.platform


def get_system_stats() -> dict[str, str]:
    """Obtiene estadísticas básicas del sistema sin psutil."""
    return {
        "os": _get_os_label(),
        "mem_usage": _get_ram_usage(),
        "disk_usage": _get_disk_usage(),
        "uptime": _get_uptime_simple(),
    }


def _parse_zshrc_plugins(path: Path) -> list[str]:
    if not path.exists():
        return []
    content = path.read_text(errors="ignore")
    match = re.search(r"^plugins=\((.*?)\)", content, re.MULTILINE | re.DOTALL)
    if not match:
        return []
    cleaned = re.sub(r"#.*", "", match.group(1))
    return cleaned.split()


def get_omega_active_items() -> list[str]:
    """Lee el estado oficial de Omega para saber qué está activado."""
    if StateManager:
        try:
            return StateManager(OMEGA_CONFIG_DIR).load().selected_plugins
        except Exception as exc:
            console.print(f"[dim yellow]No se pudo leer state.json, usando .zshrc: {exc}[/]")

    return _parse_zshrc_plugins(ZSHRC)


def inspect_plugin(plugin_name: str) -> dict:
    """Obtiene la info del plugin/herramienta priorizando la base amigable."""
    paths = [
        CUSTOM_PLUGINS / plugin_name / f"{plugin_name}.plugin.zsh",
        STANDARD_PLUGINS / plugin_name / f"{plugin_name}.plugin.zsh",
        CUSTOM_PLUGINS / plugin_name / f"{plugin_name}.zsh",
        STANDARD_PLUGINS / plugin_name / f"{plugin_name}.zsh",
    ]
    plugin_path = next((p for p in paths if p.exists()), None)
    description = get_description(plugin_name)

    if (
        "Sin descripción" in description
        or description == "Plugin de Oh My Zsh (sin descripción documentada en la base de datos)."
    ):
        for p_def in DB_PLUGINS:
            if p_def.id == plugin_name:
                description = p_def.desc
                break

    if not plugin_path or plugin_name in BIN_PLUGINS:
        return {
            "found": False,
            "is_binary": True,
            "description": description,
            "aliases": [],
            "functions": [],
        }

    try:
        content = plugin_path.read_text(errors="ignore")
        aliases = re.findall(r"^alias\s+([\w-]+)=", content, re.MULTILINE)
        functions = re.findall(r"^function\s+([\w-]+)", content, re.MULTILINE)
        functions += re.findall(r"^([\w-]+)\(\)\s*\{", content, re.MULTILINE)
        functions = [f for f in functions if not f.startswith("_")]
    except Exception:
        aliases, functions = [], []

    return {
        "found": True,
        "is_binary": False,
        "path": str(plugin_path),
        "description": description,
        "aliases": sorted(set(aliases)),
        "functions": sorted(set(functions)),
    }


def benchmark_shell() -> None:
    """Mide la latencia con diagnóstico inteligente basado en plugins activos."""
    zsh_bin = require_command("zsh", "pkg install zsh")
    if not zsh_bin:
        return

    console.print("[bold #00f5ff]🚀 INICIANDO ANÁLISIS DE HIPERVELOCIDAD (Hyperdrive)...[/]")
    times = []
    active_items = get_omega_active_items()

    with Progress(
        SpinnerColumn(style="bold #ff006e"),
        TextColumn("[progress.description]{task.description}"),
        transient=True,
    ) as progress:
        task = progress.add_task("[bold #00f5ff]Calculando entropía del arranque...", total=5)
        for _ in range(5):
            start = time.perf_counter()
            result = run_command([zsh_bin, "-i", "-c", "exit"], timeout=8)
            if result is None:
                return
            times.append(time.perf_counter() - start)
            progress.advance(task)

    avg_ms = (sum(times) / len(times)) * 1000
    heavy_hitters = {
        "zsh-syntax-highlighting": "Resaltado de sintaxis (Alto impacto en CPU)",
        "zsh-autosuggestions": "Sugerencias de historial (Impacto en Disk I/O)",
        "fzf-tab": "Menú visual FZF (Carga memoria adicional)",
        "fastfetch": "Header de información (Llamada a binario externo)",
        "figlet_custom": "Generador de Banner (Procesamiento de fuentes ASCII)",
    }
    detected_heavy = [heavy_hitters[p] for p in active_items if p in heavy_hitters]

    if avg_ms < 150:
        color, rating = "#00ff9f", "⚡ DIOS DIGITAL (Instantáneo)"
        advice = (
            "[#00ff9f]Tu sistema es una obra de arte de la optimización.[/]\n"
            "[white]No hay cuellos de botella detectados. Mantén tu configuración limpia.[/]"
        )
        steps = []
    elif avg_ms < 400:
        color, rating = "#00f5ff", "💎 ELITE CORE (Optimizado)"
        advice = (
            "[#00f5ff]Rendimiento profesional.[/] [white]Tu shell es rápido, "
            "pero la carga de plugins visuales añade una latencia mínima.[/]"
        )
        steps = ["Considera usar [bold]zsh-defer[/] para cargar plugins visuales en segundo plano."]
    else:
        color = "#ffe600" if avg_ms < 800 else "#ff006e"
        rating = "⚠️ SOBRECARGA" if avg_ms < 800 else "🔥 COLAPSO CRÍTICO"
        advice = (
            f"[{color}]SE HA DETECTADO LAG EN EL ARRANQUE DEL SHELL.[/] "
            "[white]Tu terminal tarda demasiado en estar lista para la acción.[/]"
        )
        steps = [
            "Ejecuta [bold #00f5ff]oz profile[/] para un análisis automatizado.",
            "Desactiva plugins pesados en la TUI que no uses frecuentemente.",
            "Evita comandos pesados como [bold #ff006e]'apt update'[/] dentro de tu .zshrc.",
        ]
        if "fastfetch" in active_items or "figlet_custom" in active_items:
            steps.append("Tu [bold #ffe600]Header visual[/] consume CPU. Prueba el modo 'none'.")
        if detected_heavy:
            steps.append("Culpables detectados:\n  - " + "\n  - ".join(detected_heavy))

    res_panel = Table.grid(expand=True)
    res_panel.add_row(
        f"\n[bold white]LATENCIA DE ARRANQUE:[/]\n"
        f"[bold {color} size=30]{avg_ms:.2f} ms[/]\n"
    )
    res_panel.add_row(f"[dim white]Calificación de Entropía:[/] [bold {color}]{rating}[/]\n")

    if steps:
        steps_text = "\n".join([f"  [bold #ff006e]»[/] {s}" for s in steps])
        res_panel.add_row(
            Panel(
                steps_text,
                title="[bold white]PASOS PARA OPTIMIZAR[/]",
                border_style=color,
                padding=(1, 2),
            )
        )

    res_panel.add_row(f"\n[italic {color}]{advice}[/]")
    console.print(
        Panel(
            res_panel,
            title="[bold #ff006e]◄ REPORTE TÉCNICO HYPERDRIVE ►[/]",
            border_style="#00f5ff",
            padding=(1, 2),
        )
    )


def run_zprof_analysis() -> None:
    """Automatiza la ejecución de zprof inyectándolo dinámicamente."""
    zsh_bin = require_command("zsh", "pkg install zsh")
    if not zsh_bin:
        return

    console.print("[bold #00f5ff]🔍 INICIANDO PERFILADO PROFUNDO (Deep Probe)...[/]")
    with Progress(
        SpinnerColumn(style="bold #ff006e"),
        TextColumn("[progress.description]{task.description}"),
        transient=True,
    ) as progress:
        task = progress.add_task("[bold #00f5ff]Analizando secuencia de arranque...", total=100)
        cmd = "zmodload zsh/zprof && source ~/.zshrc && zprof | head -n 40"
        result = run_command([zsh_bin, "-i", "-c", cmd], timeout=10)
        progress.update(task, completed=100)

    if result is None:
        return

    if result.stdout:
        table = Table(title="TOP 20 FUNCIONES MÁS PESADAS (ms)", box=box.ROUNDED)
        table.add_column("Llamadas", justify="right", style="dim")
        table.add_column("Tiempo (ms)", justify="right", style="bold #ffe600")
        table.add_column("Función", style="cyan")

        data_lines = [line for line in result.stdout.splitlines() if line.strip()]
        data_lines = [line for line in data_lines if not line.startswith("num")]
        for line in data_lines[:20]:
            parts = line.split()
            if len(parts) >= 4:
                table.add_row(parts[0], parts[1], parts[3])

        console.print(table)
        console.print(
            "[#00f5ff]💡 TIP:[/] Los tiempos altos en 'compinit' o "
            "'syntax-highlighting' son normales en sistemas ARM."
        )
        return

    console.print("[red]No se pudo obtener datos de perfilado. Revisa tu configuración Zsh.[/]")
    if result.stderr:
        console.print(f"[dim red]Error: {result.stderr}[/]")


def analyze_history() -> None:
    """Analiza historial y sugiere alias útiles."""
    hist_file = HOME / ".zsh_history"
    if not hist_file.exists():
        console.print("[red]No hay historial disponible.[/]")
        return

    console.print("[bold #00f5ff]📊 Analizando patrones de uso...[/]")
    try:
        content = hist_file.read_text(errors="ignore")
        cmds = re.findall(r"^: \d+:\d+;(.*?)(?:\s|$)", content, re.MULTILINE) or content.splitlines()
        top_10 = Counter(cmds).most_common(10)

        table = Table(title="TUS COMANDOS MÁS USADOS", box=box.SIMPLE)
        table.add_column("#", justify="right", style="cyan")
        table.add_column("Comando", style="green")
        table.add_column("Veces", style="#ffe600")
        table.add_column("Sugerencia", style="#ff006e italic")

        aliases_suggestion = []
        for idx, (cmd, count) in enumerate(top_10, 1):
            suggestion = ""
            if len(cmd) > 4 and count > 5:
                alias_name = "".join([word[0] for word in cmd.split() if word])
                suggestion = f"alias {alias_name}='{cmd}'"
                aliases_suggestion.append(f"[#00ff9f]alias {alias_name}='{cmd}'[/]")
            table.add_row(str(idx), cmd, str(count), suggestion if suggestion else "-")

        console.print(table)
        if aliases_suggestion:
            console.print(
                Panel(
                    "[white]Comandos largos frecuentes. Copia esto en tu [bold]custom.zsh[/]:[/]\n\n"
                    + "\n".join(aliases_suggestion),
                    title="💡 OPTIMIZACIÓN DE FLUJO",
                    border_style="#ff006e",
                )
            )
        else:
            console.print("[#7b8fa1]No se detectaron comandos largos repetitivos.[/]")
    except Exception as exc:
        console.print(f"[red]Error: {exc}[/]")


def list_themes() -> None:
    """Lista todos los temas disponibles."""
    console.print("[bold #00f5ff]🎨 Escaneando librería de temas...[/]")
    found_themes = {}

    for directory, origin in [
        (PROJECT_THEMES, "[bold #ff006e]Omega God Tier[/]"),
        (CUSTOM_THEMES, "[blue]Custom User[/]"),
        (STANDARD_THEMES, "[#7b8fa1]Standard OMZ[/]"),
    ]:
        if directory.exists():
            for theme in directory.glob("*.zsh-theme"):
                found_themes.setdefault(theme.stem, origin)

    sorted_themes = sorted(found_themes.items())
    table = Table(title=f"ARSENAL COMPLETO ({len(sorted_themes)} temas)", box=box.ROUNDED)
    table.add_column("Nombre del Tema", style="bold green")
    table.add_column("Origen / Colección", style="white")

    for name, origin in sorted_themes:
        table.add_row(name, origin)

    console.print(table)
    console.print("[#ffe600]Para usar uno:[/]")
    console.print("    Edita ~/.zshrc y cambia ZSH_THEME='nombre'")


def _detect_repo_dir() -> Path | None:
    for candidate in [PROJECT_ROOT, PROJECT_ROOT.parent, Path.home() / "Projects/omega-zsh-python"]:
        if (candidate / ".git").exists():
            return candidate
    return None


def self_update() -> None:
    """Actualiza el código fuente de Omega-ZSH."""
    git_bin = require_command("git", "pkg install git")
    if not git_bin:
        return

    console.print("[bold #00f5ff]🔄 Actualizando Sistema Omega-ZSH...[/]")
    repo_dir = _detect_repo_dir()
    if repo_dir is None:
        console.print("[red]Error: No se detectó un repositorio git. ¿Instalaste con git clone?[/]")
        return

    console.print(f"[dim]Repositorio: {repo_dir}[/]\n")
    res = run_command([git_bin, "pull"], cwd=repo_dir, timeout=45)
    if res is None:
        return
    if res.returncode != 0:
        console.print(f"[red]Error en git pull:\n{res.stderr}[/]")
        return

    output = res.stdout.strip()
    console.print(f"[#00ff9f]{output}[/]")
    if "Already up to date" in output or "Ya está actualizado" in output:
        console.print("[#00ff9f]✅ Ya tienes la última versión.[/]")
        return

    console.print("[bold #00f5ff]>> Aplicando cambios (pip install)...[/]")
    venv_pip = repo_dir / ".venv" / "bin" / "pip"
    pip_cmd = str(venv_pip) if venv_pip.exists() else which("pip")
    if not pip_cmd:
        console.print("[red]No se encontró pip para reinstalar el paquete.[/]")
        return

    res2 = run_command([pip_cmd, "install", "-e", str(repo_dir), "--quiet"], timeout=120)
    if res2 and res2.returncode == 0:
        console.print("[#00ff9f]✅ Actualización completada. Reinicia la terminal.[/]")
    elif res2:
        console.print(f"[#ffe600]⚠ Pull OK pero pip falló: {res2.stderr[:200]}[/]")


def show_help() -> None:
    """Muestra la ayuda con estética Neon."""
    console.print(
        Panel(
            f"[bold #ff006e]OMEGA CLI (oz)[/] [white]v{get_app_version()}[/]\n"
            "[italic cyan]Manual de Comando y Control[/]",
            border_style="#00f5ff",
        )
    )
    table = Table(box=box.DOUBLE_EDGE, border_style="#00f5ff")
    table.add_column("COMANDO", style="bold #00ff9f")
    table.add_column("ALIAS", style="bold #ffe600")
    table.add_column("DESCRIPCIÓN", style="cyan")

    table.add_row("oz banner", "oz b", "Muestra telemetría del sistema")
    table.add_row("oz plugins", "oz p", "Manual detallado de tus herramientas")
    table.add_row("oz bench", "oz v", "Prueba de velocidad de arranque")
    table.add_row("oz profile", "oz vp", "Perfilado profundo automático")
    table.add_row("oz stats", "oz s", "Análisis de historial y sugerencia de alias")
    table.add_row("oz themes", "oz t", "Explorador de temas")
    table.add_row("oz update", "oz u", "Sincroniza Omega con el repositorio")
    console.print(table)


def show_plugins_detail() -> None:
    """Detalla plugins y herramientas activas con estética Neon Retro."""
    active_items = get_omega_active_items()
    if not active_items:
        console.print("[bold #ffe600]No se detectaron items activos en Omega-ZSH.[/]")
        return

    console.print(
        f"\n[bold #ff006e]█▓▒░ MANUAL DE OPERACIONES OMEGA ({len(active_items)} módulos) ░▒▓█[/]\n"
    )
    tips = {
        "zoxide": "Usa [bold #00ff9f]z <carpeta>[/] para saltar sin usar cd.",
        "eza": "Usa [bold #00ff9f]ls[/] o [bold #00ff9f]ll[/] para ver iconos.",
        "zsh-autosuggestions": "Presiona [bold #00ff9f]Flecha Derecha[/] para completar.",
        "fzf-tab": "Presiona [bold #00ff9f]Tab[/] y usa flechas para navegar.",
        "yazi": "Usa [bold #00ff9f]yy[/] para abrir el gestor de archivos.",
        "fzf": "Usa [bold #00ff9f]Ctrl+R[/] para buscar historial.",
        "lazygit": "Escribe [bold #00ff9f]lg[/] para gestionar repos visualmente.",
        "tldr": "Escribe [bold #00ff9f]tldr <comando>[/] para ejemplos rápidos.",
    }

    for item_id in active_items:
        info = inspect_plugin(item_id)
        if info["is_binary"]:
            title = f"[bold #00ff9f]󱓞 HERRAMIENTA BINARIA: {item_id.upper()}[/]"
            border = "#00ff9f"
            type_tag = "[bold #00ff9f][ BIN ][/]"
        else:
            title = f"[bold #ff006e]󰏗 PLUGIN ZSH: {item_id.upper()}[/]"
            border = "#ff006e"
            type_tag = "[bold #00f5ff][ ZSH ][/]"

        content = [f"{type_tag} [bold #00f5ff]{info['description']}[/]"]
        if info["aliases"]:
            useful_aliases = info["aliases"][:10]
            suffix = "..." if len(info["aliases"]) > 10 else ""
            content.append("\n[bold white]⌨️ ALIAS CRÍTICOS:[/]")
            content.append("  [#00f5ff]" + ", ".join(useful_aliases) + suffix + "[/]")

        if info["functions"]:
            useful_funcs = info["functions"][:5]
            suffix = "..." if len(info["functions"]) > 5 else ""
            content.append("\n[bold white]⚙️ FUNCIONES DISPONIBLES:[/]")
            content.append("  [#00ff9f]" + ", ".join(useful_funcs) + suffix + "[/]")

        if item_id in tips:
            content.append(f"\n[bold #ffe600]💡 TIP DE ELITE:[/] [italic white]{tips[item_id]}[/]")

        console.print(
            Panel(
                "\n".join(content),
                title=title,
                border_style=border,
                title_align="left",
                padding=(1, 2),
            )
        )


def show_banner() -> None:
    stats = get_system_stats()
    banner_content = (
        f"[bold #00f5ff]SISTEMA:[/] [white]{stats['os']}[/]\n"
        f"[bold #ff006e]MEMORIA:[/] [white]{stats['mem_usage']}[/]\n"
        f"[bold #00ff9f]DISCO:[/]   [white]{stats['disk_usage']}[/]\n"
        f"[bold #ffe600]UPTIME:[/]  [white]{stats['uptime']}[/]"
    )
    console.print(
        Panel(
            banner_content,
            title="[bold #ff006e]◄ STATUS OMEGA ►[/]",
            border_style="#00f5ff",
            subtitle="[dim white]Entropy Engine Active[/]",
        )
    )


def _print_doctor_report(report: dict) -> None:
    table = Table(title=f"OMEGA DOCTOR ({report['overall'].upper()})", box=box.ROUNDED)
    table.add_column("Check", style="bold cyan")
    table.add_column("Status", style="bold")
    table.add_column("Mensaje", style="white")
    table.add_column("Detalle", style="dim white")

    colors = {"ok": "green", "warning": "yellow", "missing": "red"}
    for check in report["checks"]:
        status = check["status"]
        table.add_row(
            check["id"],
            f"[{colors.get(status, 'white')}]{status}[/]",
            check["message"],
            check["detail"],
        )
    console.print(table)


def show_doctor(*, fix: bool = False) -> None:
    """Muestra diagnóstico read-only de la instalación Omega."""
    if fix:
        result = run_doctor_fix()
        table = Table(title="OMEGA DOCTOR FIX", box=box.ROUNDED)
        table.add_column("Fix", style="bold cyan")
        table.add_column("Status", style="bold")
        table.add_column("Mensaje", style="white")
        table.add_column("Detalle", style="dim white")
        colors = {"fixed": "green", "skipped": "yellow", "failed": "red"}
        for fix_result in result["fixes"]:
            status = fix_result["status"]
            table.add_row(
                fix_result["id"],
                f"[{colors.get(status, 'white')}]{status}[/]",
                fix_result["message"],
                fix_result["detail"],
            )
        console.print(table)
        _print_doctor_report(result["report"])
        return

    report = run_doctor()
    _print_doctor_report(report)


def main() -> None:
    if len(sys.argv) <= 1:
        show_help()
        return

    cmd = sys.argv[1].lstrip("-")
    if cmd in {"doctor", "doc"}:
        show_doctor(fix="--fix" in sys.argv[2:])
        return

    actions = {
        "banner": show_banner,
        "b": show_banner,
        "plugins": show_plugins_detail,
        "p": show_plugins_detail,
        "bench": benchmark_shell,
        "v": benchmark_shell,
        "speed": benchmark_shell,
        "profile": run_zprof_analysis,
        "vp": run_zprof_analysis,
        "stats": analyze_history,
        "s": analyze_history,
        "themes": list_themes,
        "t": list_themes,
        "update": self_update,
        "u": self_update,
        "help": show_help,
        "h": show_help,
    }
    actions.get(cmd, show_help)()


if __name__ == "__main__":
    main()
