#!/usr/bin/env python3
import os
import re
import sys
import time
import shutil
import subprocess
from collections import Counter
from pathlib import Path
from rich.console import Console
from rich.panel import Panel
from rich.table import Table
from rich import box
from rich.progress import Progress, SpinnerColumn, TextColumn

try:
    from omega_zsh.core.plugins_db import get_description
except ImportError:
    def get_description(name): return "Sin descripción disponible."

try:
    from omega_zsh.core.state import StateManager
    from omega_zsh.core.constants import DB_PLUGINS
except ImportError:
    StateManager = None
    DB_PLUGINS = []

console = Console()


# --- CONFIGURACIÓN ---
HOME = Path.home()
ZSHRC = HOME / ".zshrc"
OMZ = HOME / ".oh-my-zsh"
CUSTOM_PLUGINS = OMZ / "custom/plugins"
STANDARD_PLUGINS = OMZ / "plugins"
CUSTOM_THEMES = OMZ / "custom/themes"
STANDARD_THEMES = OMZ / "themes"
PROJECT_ROOT = Path(__file__).parent.parent.parent
PROJECT_THEMES = PROJECT_ROOT / "omega_zsh/assets/themes"

# Gestor de estado oficial
OMEGA_CONFIG_DIR = HOME / ".omega-zsh"
state_manager = StateManager(OMEGA_CONFIG_DIR) if StateManager else None



def _get_ram_usage():
    """Obtiene el uso de RAM leyendo /proc/meminfo de forma nativa."""
    try:
        with open('/proc/meminfo', 'r', encoding="utf-8") as f:
            lines = f.readlines()
        mem = {}
        for line in lines:
            parts = line.split(':')
            if len(parts) == 2:
                mem[parts[0].strip()] = int(parts[1].split()[0].strip())

        total = mem.get('MemTotal', 1)
        free = mem.get('MemFree', 0)
        buffers = mem.get('Buffers', 0)
        cached = mem.get('Cached', 0)

        used = total - free - buffers - cached
        percent = (used / total) * 100
        return f"{int(percent)}%"
    except:
        return "N/A"


def _get_disk_usage(path='/'):
    """Obtiene el uso de disco usando os.statvfs."""
    try:
        st = os.statvfs(path)
        total = st.f_blocks * st.f_frsize
        free = st.f_bavail * st.f_frsize
        used = total - free
        percent = (used / total) * 100
        return f"{int(percent)}%"
    except:
        return "N/A"


def _get_uptime_simple():
    """Obtiene el uptime leyendo /proc/uptime."""
    try:
        with open('/proc/uptime', 'r', encoding="utf-8") as f:
            uptime_seconds = float(f.readline().split()[0])
            hours, remainder = divmod(int(uptime_seconds), 3600)
            minutes, _ = divmod(remainder, 60)
            return f"{hours}h {minutes}m"
    except:
        return "N/A"


def get_system_stats():
    """Obtiene estadísticas básicas del sistema con blindaje de permisos (Sin psutil)."""
    try:
        return {
            "os": "Android/Termux",
            "mem_usage": _get_ram_usage(),
            "disk_usage": _get_disk_usage(),
            "uptime": _get_uptime_simple()
        }
    except Exception as e:
        return {"os": "Unknown", "mem_usage": "N/A", "disk_usage": "N/A", "uptime": "N/A"}


def get_omega_active_items():
    """Lee el estado oficial de Omega para saber qué está activado (Plugins + Binarios)."""
    if not state_manager:
        # Fallback si no hay state_manager
        if not ZSHRC.exists(): return []
        content = ZSHRC.read_text(errors="ignore")
        match = re.search(r'^plugins=\((.*?)\)', content, re.MULTILINE | re.DOTALL)
        return match.group(1).split() if match else []

    state = state_manager.load()
    return state.selected_plugins


def inspect_plugin(plugin_name):
    """Obtiene la info del plugin/herramienta priorizando el JSON amigable."""
    # Buscar si es un plugin físico de Zsh
    paths = [
        CUSTOM_PLUGINS / plugin_name / f"{plugin_name}.plugin.zsh",
        STANDARD_PLUGINS / plugin_name / f"{plugin_name}.plugin.zsh",
        CUSTOM_PLUGINS / plugin_name / f"{plugin_name}.zsh",
        STANDARD_PLUGINS / plugin_name / f"{plugin_name}.zsh"
    ]
    plugin_path = next((p for p in paths if p.exists()), None)

    # Obtener descripción desde nuestro JSON
    description = get_description(plugin_name)

    # Fallback a la descripción corta de constants.py si el JSON no la tiene
    if "Sin descripción" in description or description == "Plugin de Oh My Zsh (sin descripción documentada en la base de datos).":
        for p_def in DB_PLUGINS:
            if p_def.id == plugin_name:
                description = p_def.desc
                break

    # Si no tiene script .zsh, es una herramienta binaria
    # Verificar contra lista oficial de binarios
    try:
        from omega_zsh.core.constants import BIN_PLUGINS as _BIN
    except ImportError:
        _BIN = []
    if not plugin_path or plugin_name in _BIN:
        return {
            "found": False,
            "is_binary": True,
            "description": description,
            "aliases": [],
            "functions": []
        }

    try:
        content = plugin_path.read_text(errors="ignore")
        aliases = re.findall(r"^alias\s+([\w-]+)=", content, re.MULTILINE)
        functions = re.findall(r"^function\s+([\w-]+)", content, re.MULTILINE)
        functions += re.findall(r"^([\w-]+)\(\)\s*\{", content, re.MULTILINE)
        # Filtrar funciones privadas (prefijo _) — no son invocables por el usuario
        functions = [f for f in functions if not f.startswith("_")]
    except:
        aliases, functions = [], []

    return {
        "found": True,
        "is_binary": False,
        "path": str(plugin_path),
        "description": description,
        "aliases": sorted(list(set(aliases))),
        "functions": sorted(list(set(functions)))
    }

# --- BENCHMARK CON DIAGNÓSTICO INTELIGENTE NEON ---


def benchmark_shell():
    """Mide la latencia con precisión y ofrece un diagnóstico inteligente basado en plugins activos."""
    console.print("[bold #00f5ff]🚀 INICIANDO ANÁLISIS DE HIPERVELOCIDAD (Hyperdrive)...[/]")

    times = []
    active_items = get_omega_active_items()

    with Progress(
        SpinnerColumn(style="bold #ff006e"),
        TextColumn("[progress.description]{task.description}"),
        transient=True
    ) as progress:
        task = progress.add_task("[bold #00f5ff]Calculando entropía del arranque...", total=5)
        for i in range(5):
            start = time.perf_counter()
            subprocess.run(["zsh", "-i", "-c", "exit"], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            times.append(time.perf_counter() - start)
            progress.advance(task)

    avg_ms = (sum(times) / len(times)) * 1000

    # Identificar posibles culpables (Heavy Hitters)
    heavy_hitters = {
        "zsh-syntax-highlighting": "Resaltado de sintaxis (Alto impacto en CPU)",
        "zsh-autosuggestions": "Sugerencias de historial (Impacto en Disk I/O)",
        "fzf-tab": "Menú visual FZF (Carga memoria adicional)",
        "fastfetch": "Header de información (Llamada a binario externo)",
        "figlet_custom": "Generador de Banner (Procesamiento de fuentes ASCII)",
    }

    detected_heavy = [heavy_hitters[p] for p in active_items if p in heavy_hitters]

    # Lógica de Diagnóstico
    if avg_ms < 150:
        color, rating = "#00ff9f", "⚡ DIOS DIGITAL (Instantáneo)"
        advice = "[#00ff9f]Tu sistema es una obra de arte de la optimización.[/]\n[white]No hay cuellos de botella detectados. Mantén tu configuración limpia.[/]"
        steps = []
    elif avg_ms < 400:
        color, rating = "#00f5ff", "💎 ELITE CORE (Optimizado)"
        advice = "[#00f5ff]Rendimiento profesional.[/] [white]Tu shell es rápido, pero la carga de plugins visuales añade una latencia mínima.[/]"
        steps = ["Considera usar [bold]zsh-defer[/] para cargar plugins visuales en segundo plano."]
    else:
        # Casos de baja calificación (>400ms)
        color = "#ffe600" if avg_ms < 800 else "#ff006e"
        rating = "⚠️ SOBRECARGA" if avg_ms < 800 else "🔥 COLAPSO CRÍTICO"

        advice = f"[{color}]SE HA DETECTADO LAG EN EL ARRANQUE DEL SHELL.[/] [white]Tu terminal tarda demasiado en estar lista para la acción.[/]"

        steps = [
            "Ejecuta [bold #00f5ff]zsh -i -c 'zprof'[/] para ver exactamente qué función está frenando el inicio.",
            "Desactiva plugins pesados en la TUI (oz) que no uses frecuentemente.",
            "Evita comandos pesados como [bold #ff006e]'apt update'[/] o [bold #ff006e]'check-for-updates'[/] dentro de tu .zshrc."
        ]

        if "fastfetch" in active_items or "figlet_custom" in active_items:
            steps.append("Tu [bold #ffe600]Header visual[/] está consumiendo tiempo de CPU. Prueba el modo 'none' para velocidad pura.")

        if detected_heavy:
            steps.append(f"Culpables detectados en tu lista activa:\n  - " + "\n  - ".join(detected_heavy))

    # Renderizado del Reporte
    res_panel = Table.grid(expand=True)
    res_panel.add_row(f"\n[bold white]LATENCIA DE ARRANQUE:[/]\n[bold {color} size=30]{avg_ms:.2f} ms[/]\n")
    res_panel.add_row(f"[dim white]Calificación de Entropía:[/] [bold {color}]{rating}[/]\n")

    # Solo mostrar pasos si hay algo que mejorar
    if steps:
        steps_text = "\n".join([f"  [bold #ff006e]»[/] {s}" for s in steps])
        res_panel.add_row(Panel(steps_text, title="[bold white]PASOS PARA OPTIMIZAR[/]", border_style=color, padding=(1, 2)))

    res_panel.add_row(f"\n[italic {color}]{advice}[/]")

    console.print(Panel(
        res_panel,
        title="[bold #ff006e]◄ REPORTE TÉCNICO HYPERDRIVE ►[/]",
        border_style="#00f5ff",
        padding=(1, 2)
    ))

# --- STATS CON SUGERENCIAS DE ALIAS ---


def analyze_history():
    """Analiza historial y sugiere ALIAS útiles."""
    hist_file = HOME / ".zsh_history"
    if not hist_file.exists():
        console.print("[red]No hay historial disponible.[/]")
        return

    console.print("[bold #00f5ff]📊 Analizando patrones de uso...[/]")
    try:
        content = hist_file.read_text(errors="ignore")
        cmds = re.findall(r"^: \d+:\d+;(.*?)(?:\s|$)", content, re.MULTILINE) or content.splitlines()

        counter = Counter(cmds)
        top_10 = counter.most_common(10)

        table = Table(title="TUS COMANDOS MÁS USADOS", box=box.SIMPLE)
        table.add_column("#", justify="right", style="cyan")
        table.add_column("Comando", style="green")
        table.add_column("Veces", style="#ffe600")
        table.add_column("Sugerencia", style="#ff006e italic")

        aliases_suggestion = []

        for idx, (cmd, count) in enumerate(top_10, 1):
            suggestion = ""
            if len(cmd) > 4 and count > 5:
                # Generar alias sugerido: primeras letras
                alias_name = "".join([w[0] for w in cmd.split() if w])
                suggestion = f"alias {alias_name}='{cmd}'"
                aliases_suggestion.append(f"[#00ff9f]alias {alias_name}='{cmd}'[/]")

            table.add_row(str(idx), cmd, str(count), suggestion if suggestion else "-")

        console.print(table)

        if aliases_suggestion:
            console.print(Panel(
                "[white]Se detectaron comandos largos frecuentes. Copia esto en tu [bold]custom.zsh[/]:[/]\n\n" + "\n".join(aliases_suggestion),
                title="💡 OPTIMIZACIÓN DE FLUJO", border_style="#ff006e"
            ))
        else:
            console.print("[#7b8fa1]Tu flujo es eficiente. No se detectaron comandos largos repetitivos.[/]")

    except Exception as e:
        console.print(f"[red]Error: {e}[/]")

# --- LISTAR TODOS LOS TEMAS ---


def list_themes():
    """Lista ABSOLUTAMENTE TODOS los temas disponibles."""
    console.print("[bold #00f5ff]🎨 Escaneando librería de temas...[/]")

    found_themes = {} # nombre -> origen

    # 1. Temas Omega (God Tier)
    if PROJECT_THEMES.exists():
        for t in PROJECT_THEMES.glob("*.zsh-theme"):
            found_themes[t.stem] = "[bold #ff006e]Omega God Tier[/]"

    # 2. Temas Custom Usuario
    if CUSTOM_THEMES.exists():
        for t in CUSTOM_THEMES.glob("*.zsh-theme"):
            if t.stem not in found_themes: # Prioridad a Omega si hay conflicto
                found_themes[t.stem] = "[blue]Custom User[/]"

    # 3. Temas Oficiales OMZ
    if STANDARD_THEMES.exists():
        for t in STANDARD_THEMES.glob("*.zsh-theme"):
            if t.stem not in found_themes:
                found_themes[t.stem] = "[#7b8fa1]Standard OMZ[/]"

    # Ordenar
    sorted_themes = sorted(found_themes.items())

    table = Table(title=f"ARSENAL COMPLETO ({len(sorted_themes)} temas)", box=box.ROUNDED)
    table.add_column("Nombre del Tema", style="bold green")
    table.add_column("Origen / Colección", style="white")

    for name, origin in sorted_themes:
        table.add_row(name, origin)

    console.print(table)
    console.print("[#ffe600]Para usar uno:[/]")
    console.print("    Edita ~/.zshrc y cambia ZSH_THEME='nombre'")

# --- ACTUALIZADOR ---


def self_update():
    """Actualiza el código fuente de Omega-ZSH."""
    console.print("[bold #00f5ff]🔄 Actualizando Sistema Omega-ZSH...[/]")

    # Buscar el repo git subiendo desde PROJECT_ROOT
    repo_dir = PROJECT_ROOT
    for candidate in [PROJECT_ROOT, PROJECT_ROOT.parent, Path.home() / "Projects/omega-zsh-python"]:
        if (candidate / ".git").exists():
            repo_dir = candidate
            break
    else:
        console.print("[red]Error: No se detectó un repositorio git. ¿Instalaste con git clone?[/]")
        return

    console.print(f"[dim]Repositorio: {repo_dir}[/]\n")

    try:
        # 1. Git Pull
        res = subprocess.run(["git", "pull"], cwd=repo_dir, capture_output=True, text=True)
        if res.returncode != 0:
            console.print(f"[red]Error en git pull:\n{res.stderr}[/]")
            return

        output = res.stdout.strip()
        console.print(f"[#00ff9f]{output}[/]")

        if "Already up to date" in output:
            console.print("[#00ff9f]✅ Ya tienes la última versión.[/]")
            return

        # 2. Reinstalar paquete para aplicar cambios en Python
        console.print("[bold #00f5ff]>> Aplicando cambios (pip install)...[/]")
        venv_pip = repo_dir / ".venv" / "bin" / "pip"
        pip_cmd = str(venv_pip) if venv_pip.exists() else "pip"
        res2 = subprocess.run(
            [pip_cmd, "install", "-e", str(repo_dir), "--quiet"],
            capture_output=True, text=True
        )
        if res2.returncode == 0:
            console.print("[#00ff9f]✅ Actualización completada. Reinicia la terminal para aplicar cambios.[/]")
        else:
            console.print(f"[#ffe600]⚠ Pull OK pero pip falló: {res2.stderr[:200]}[/]")

    except Exception as e:
        console.print(f"[bold red]❌ Error crítico: {e}[/]")


def show_help():
    """Muestra la ayuda con estética Neon."""
    console.print(Panel(
        f"[bold #ff006e]OMEGA CLI (oz)[/] [white]v2.2.0[/]\n[italic cyan]Manual de Comando y Control[/]",
        border_style="#00f5ff"
    ))
    table = Table(box=box.DOUBLE_EDGE, border_style="#00f5ff")
    table.add_column("COMANDO", style="bold #00ff9f")
    table.add_column("ALIAS", style="bold #ffe600")
    table.add_column("DESCRIPCIÓN", style="cyan")

    table.add_row("oz banner", "oz b", "Muestra telemetría del sistema")
    table.add_row("oz plugins", "oz p", "Manual detallado de tus herramientas")
    table.add_row("oz bench", "oz v", "Prueba de velocidad de arranque (Hiperdrive)")
    table.add_row("oz stats", "oz s", "Análisis de historial y sugerencia de alias")
    table.add_row("oz themes", "oz t", "Explorador de la librería de temas")
    table.add_row("oz update", "oz u", "Sincroniza Omega con el repositorio central")

    console.print(table)


def main():
    if len(sys.argv) > 1:
        cmd = sys.argv[1].lstrip("-")
        # Mapeo unificado de alias
        if cmd in ["banner", "b"]:
            show_banner()
        elif cmd in ["plugins", "p"]:
            show_plugins_detail()
        elif cmd in ["bench", "v", "speed"]:
            benchmark_shell()
        elif cmd in ["stats", "s"]:
            analyze_history()
        elif cmd in ["themes", "t"]:
            list_themes()
        elif cmd in ["update", "u"]:
            self_update()
        elif cmd in ["help", "h"]:
            show_help()
        else:
            show_help()
    else:
        show_help()


def show_plugins_detail():
    """Detalla todos los plugins y herramientas activas con estética Neon Retro y utilidad máxima."""
    active_items = get_omega_active_items()
    if not active_items:
        console.print("[bold #ffe600]No se detectaron items activos en el estado de Omega-ZSH.[/]")
        return

    console.print(f"\n[bold #ff006e]█▓▒░ MANUAL DE OPERACIONES OMEGA ({len(active_items)} módulos) ░▒▓█[/]\n")

    for item_id in active_items:
        info = inspect_plugin(item_id)

        # Estética diferenciada
        if info["is_binary"]:
            title = f"[bold #00ff9f]󱓞 HERRAMIENTA BINARIA: {item_id.upper()}[/]"
            border = "#00ff9f"
            type_tag = "[bold #00ff9f][ BIN ][/]"
        else:
            title = f"[bold #ff006e]󰏗 PLUGIN ZSH: {item_id.upper()}[/]"
            border = "#ff006e"
            type_tag = "[bold #00f5ff][ ZSH ][/]"

        # Construir contenido de alta fidelidad
        content = []
        content.append(f"{type_tag} [bold #00f5ff]{info['description']}[/]")

        if info["aliases"]:
            # Mostrar solo los alias más útiles/comunes
            useful_aliases = info["aliases"][:10]
            content.append(f"\n[bold white]⌨️ ALIAS CRÍTICOS:[/]")
            content.append(f"  [#00f5ff]" + ", ".join(useful_aliases) + ("..." if len(info['aliases'])>10 else "") + "[/]")

        if info["functions"]:
            useful_funcs = info["functions"][:5]
            content.append(f"\n[bold white]⚙️ FUNCIONES DISPONIBLES:[/]")
            content.append(f"  [#00ff9f]" + ", ".join(useful_funcs) + ("..." if len(info['functions'])>5 else "") + "[/]")

        # Añadir un "Tip de Pro" basado en el nombre
        tips = {
            "zoxide": "Usa [bold #00ff9f]z <carpeta>[/] para saltar instantáneamente sin usar cd.",
            "eza": "Usa [bold #00ff9f]ls[/] o [bold #00ff9f]ll[/] para ver iconos y carpetas primero.",
            "zsh-autosuggestions": "Presiona [bold #00ff9f]Flecha Derecha[/] para completar el comando sugerido.",
            "fzf-tab": "Presiona [bold #00ff9f]Tab[/] y usa las flechas para navegar el menú visual.",
            "yazi": "Usa [bold #00ff9f]yy[/] para abrir el gestor y al salir quedarte en esa carpeta.",
            "fzf": "Presiona [bold #00ff9f]Ctrl+R[/] para buscar en el historial o [bold #00ff9f]Ctrl+T[/] para buscar archivos.",
            "lazygit": "Simplemente escribe [bold #00ff9f]lg[/] para gestionar tus repositorios visualmente.",
            "tldr": "Escribe [bold #00ff9f]tldr <comando>[/] para ver ejemplos de uso rápidos.",
        }

        if item_id in tips:
            content.append(f"\n[bold #ffe600]💡 TIP DE ELITE:[/] [italic white]{tips[item_id]}[/]")

        console.print(Panel(
            "\n".join(content),
            title=title,
            border_style=border,
            title_align="left",
            padding=(1, 2)
        ))


def show_banner():
    stats = get_system_stats()
    banner_content = (
        f"[bold #00f5ff]SISTEMA:[/] [white]{stats['os']}[/]\n"
        f"[bold #ff006e]MEMORIA:[/] [white]{stats['mem_usage']}[/]\n"
        f"[bold #00ff9f]DISCO:[/]   [white]{stats['disk_usage']}[/]\n"
        f"[bold #ffe600]UPTIME:[/]  [white]{stats['uptime']}[/]"
    )
    console.print(Panel(
        banner_content,
        title="[bold #ff006e]◄ STATUS OMEGA ►[/]",
        border_style="#00f5ff",
        subtitle="[dim white]Entropy Engine Active[/]"
    ))

if __name__ == "__main__":
    main()
