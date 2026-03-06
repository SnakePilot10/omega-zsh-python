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
        with open('/proc/meminfo', 'r') as f:
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
        with open('/proc/uptime', 'r') as f:
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
    if not plugin_path:
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
    console.print("[bold #00ffff]🚀 INICIANDO ANÁLISIS DE HIPERVELOCIDAD (Hyperdrive)...[/]")

    times = []
    active_items = get_omega_active_items()
    
    with Progress(
        SpinnerColumn(style="bold #ff00ff"), 
        TextColumn("[progress.description]{task.description}"), 
        transient=True
    ) as progress:
        task = progress.add_task("[bold cyan]Calculando entropía del arranque...", total=5)
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
        color, rating = "#39ff14", "⚡ DIOS DIGITAL (Instantáneo)"
        advice = "[#39ff14]Tu sistema es una obra de arte de la optimización.[/]\n[white]No hay cuellos de botella detectados. Mantén tu configuración limpia.[/]"
        steps = []
    elif avg_ms < 400:
        color, rating = "#00ffff", "💎 ELITE CORE (Optimizado)"
        advice = "[#00ffff]Rendimiento profesional.[/] [white]Tu shell es rápido, pero la carga de plugins visuales añade una latencia mínima.[/]"
        steps = ["Considera usar [bold]zsh-defer[/] para cargar plugins visuales en segundo plano."]
    else:
        # Casos de baja calificación (>400ms)
        color = "yellow" if avg_ms < 800 else "#ff00ff"
        rating = "⚠️ SOBRECARGA" if avg_ms < 800 else "🔥 COLAPSO CRÍTICO"
        
        advice = f"[{color}]SE HA DETECTADO LAG EN EL ARRANQUE DEL SHELL.[/] [white]Tu terminal tarda demasiado en estar lista para la acción.[/]"
        
        steps = [
            "Ejecuta [bold cyan]zsh -i -c 'zprof'[/] para ver exactamente qué función está frenando el inicio.",
            "Desactiva plugins pesados en la TUI (oz) que no uses frecuentemente.",
            "Evita comandos pesados como [bold magenta]'apt update'[/] o [bold magenta]'check-for-updates'[/] dentro de tu .zshrc."
        ]
        
        if "fastfetch" in active_items or "figlet_custom" in active_items:
            steps.append("Tu [bold yellow]Header visual[/] está consumiendo tiempo de CPU. Prueba el modo 'none' para velocidad pura.")
        
        if detected_heavy:
            steps.append(f"Culpables detectados en tu lista activa:\n  - " + "\n  - ".join(detected_heavy))

    # Renderizado del Reporte
    res_panel = Table.grid(expand=True)
    res_panel.add_row(f"\n[bold white]LATENCIA DE ARRANQUE:[/]\n[bold {color} size=30]{avg_ms:.2f} ms[/]\n")
    res_panel.add_row(f"[dim white]Calificación de Entropía:[/] [bold {color}]{rating}[/]\n")
    
    # Solo mostrar pasos si hay algo que mejorar
    if steps:
        steps_text = "\n".join([f"  [bold #ff00ff]»[/] {s}" for s in steps])
        res_panel.add_row(Panel(steps_text, title="[bold white]PASOS PARA OPTIMIZAR[/]", border_style=color, padding=(1, 2)))
    
    res_panel.add_row(f"\n[italic {color}]{advice}[/]")

    console.print(Panel(
        res_panel,
        title="[bold #ff00ff]◄ REPORTE TÉCNICO HYPERDRIVE ►[/]",
        border_style="#00ffff",
        padding=(1, 2)
    ))

# --- STATS CON SUGERENCIAS DE ALIAS ---
def analyze_history():
    """Analiza historial y sugiere ALIAS útiles."""
    hist_file = HOME / ".zsh_history"
    if not hist_file.exists():
        console.print("[red]No hay historial disponible.[/]")
        return

    console.print("[bold cyan]📊 Analizando patrones de uso...[/]")
    try:
        content = hist_file.read_text(errors="ignore")
        cmds = re.findall(r"^: \d+:\d+;(.*?)(?:\s|$)", content, re.MULTILINE) or content.splitlines()
        
        counter = Counter(cmds)
        top_10 = counter.most_common(10)
        
        table = Table(title="TUS COMANDOS MÁS USADOS", box=box.SIMPLE)
        table.add_column("#", justify="right", style="cyan")
        table.add_column("Comando", style="green")
        table.add_column("Veces", style="yellow")
        table.add_column("Sugerencia", style="magenta italic")
        
        aliases_suggestion = []

        for idx, (cmd, count) in enumerate(top_10, 1):
            suggestion = ""
            if len(cmd) > 4 and count > 5:
                # Generar alias sugerido: primeras letras
                alias_name = "".join([w[0] for w in cmd.split() if w])
                suggestion = f"alias {alias_name}='{cmd}'"
                aliases_suggestion.append(f"[green]alias {alias_name}='{cmd}'[/]")
            
            table.add_row(str(idx), cmd, str(count), suggestion if suggestion else "-")
            
        console.print(table)
        
        if aliases_suggestion:
            console.print(Panel(
                "[white]Se detectaron comandos largos frecuentes. Copia esto en tu [bold]custom.zsh[/]:[/]\n\n" + "\n".join(aliases_suggestion),
                title="💡 OPTIMIZACIÓN DE FLUJO", border_style="magenta"
            ))
        else:
            console.print("[grey]Tu flujo es eficiente. No se detectaron comandos largos repetitivos.[/]")

    except Exception as e:
        console.print(f"[red]Error: {e}[/]")

# --- LISTAR TODOS LOS TEMAS ---
def list_themes():
    """Lista ABSOLUTAMENTE TODOS los temas disponibles."""
    console.print("[bold cyan]🎨 Escaneando librería de temas...[/]")
    
    found_themes = {} # nombre -> origen

    # 1. Temas Omega (God Tier)
    if PROJECT_THEMES.exists():
        for t in PROJECT_THEMES.glob("*.zsh-theme"):
            found_themes[t.stem] = "[bold magenta]Omega God Tier[/]"
    
    # 2. Temas Custom Usuario
    if CUSTOM_THEMES.exists():
        for t in CUSTOM_THEMES.glob("*.zsh-theme"):
            if t.stem not in found_themes: # Prioridad a Omega si hay conflicto
                found_themes[t.stem] = "[blue]Custom User[/]"

    # 3. Temas Oficiales OMZ
    if STANDARD_THEMES.exists():
        for t in STANDARD_THEMES.glob("*.zsh-theme"):
            if t.stem not in found_themes:
                found_themes[t.stem] = "[grey]Standard OMZ[/]"

    # Ordenar
    sorted_themes = sorted(found_themes.items())

    table = Table(title=f"ARSENAL COMPLETO ({len(sorted_themes)} temas)", box=box.ROUNDED)
    table.add_column("Nombre del Tema", style="bold green")
    table.add_column("Origen / Colección", style="white")
    
    for name, origin in sorted_themes:
        table.add_row(name, origin)
        
    console.print(table)
    console.print("[yellow]Para usar uno:[/]")
    console.print("    Edita ~/.zshrc y cambia ZSH_THEME='nombre'")

# --- ACTUALIZADOR ---
def self_update():
    """Actualiza el código fuente de Omega-ZSH."""
    console.print("[bold cyan]🔄 Actualizando Sistema Omega-ZSH...[/]")
    console.print("[italic grey]Esto descarga las últimas mejoras, temas God Tier y correcciones del repositorio oficial.[/]\n")
    
    repo_dir = PROJECT_ROOT
    if not (repo_dir / ".git").exists():
        console.print("[red]Error: No se detectó un repositorio git. ¿Instalaste manualmente?[/]")
        return

    try:
        # Git Pull
        res = subprocess.run(["git", "pull"], cwd=repo_dir, capture_output=True, text=True)
        if res.returncode == 0:
            console.print(f"[green]{res.stdout.strip()}[/]")
            if "Already up to date" in res.stdout:
                console.print("[green]✅ Ya tienes la última versión.[/]")
            else:
                console.print("[bold yellow]⚠ Cambios detectados. Se recomienda reiniciar la terminal o ejecutar ./install.sh[/]")
        else:
            console.print(f"[red]Error en git pull: {res.stderr}[/]")
            
    except Exception as e:
        console.print(f"[bold red]❌ Error crítico: {e}[/]")

def show_help():
    """Muestra la ayuda con estética Neon."""
    console.print(Panel(
        f"[bold #ff00ff]OMEGA CLI (oz)[/] [white]v2.2.0[/]\n[italic cyan]Manual de Comando y Control[/]",
        border_style="#00ffff"
    ))
    table = Table(box=box.DOUBLE_EDGE, border_style="#00ffff")
    table.add_column("COMANDO", style="bold #39ff14")
    table.add_column("ALIAS", style="bold yellow")
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
        console.print("[bold yellow]No se detectaron items activos en el estado de Omega-ZSH.[/]")
        return

    console.print(f"\n[bold magenta]█▓▒░ MANUAL DE OPERACIONES OMEGA ({len(active_items)} módulos) ░▒▓█[/]\n")
    
    for item_id in active_items:
        info = inspect_plugin(item_id)
        
        # Estética diferenciada
        if info["is_binary"]:
            title = f"[bold #39ff14]󱓞 HERRAMIENTA BINARIA: {item_id.upper()}[/]"
            border = "#39ff14"
            type_tag = "[on #39ff14][black] BIN [/]"
        else:
            title = f"[bold #ff00ff]󰏗 PLUGIN ZSH: {item_id.upper()}[/]"
            border = "#ff00ff"
            type_tag = "[on #ff00ff][black] ZSH [/]"

        # Construir contenido de alta fidelidad
        content = []
        content.append(f"{type_tag} [bold cyan]{info['description']}[/]")
        
        if info["aliases"]:
            # Mostrar solo los alias más útiles/comunes
            useful_aliases = info["aliases"][:10]
            content.append(f"\n[bold white]⌨️ ALIAS CRÍTICOS:[/]")
            content.append(f"  [#00ffff]" + ", ".join(useful_aliases) + ("..." if len(info['aliases'])>10 else "") + "[/]")
        
        if info["functions"]:
            useful_funcs = info["functions"][:5]
            content.append(f"\n[bold white]⚙️ FUNCIONES DISPONIBLES:[/]")
            content.append(f"  [#39ff14]" + ", ".join(useful_funcs) + ("..." if len(info['functions'])>5 else "") + "[/]")

        # Añadir un "Tip de Pro" basado en el nombre
        tips = {
            "zoxide": "Usa [bold green]z <carpeta>[/] para saltar instantáneamente sin usar cd.",
            "eza": "Usa [bold green]ls[/] o [bold green]ll[/] para ver iconos y carpetas primero.",
            "zsh-autosuggestions": "Presiona [bold green]Flecha Derecha[/] para completar el comando sugerido.",
            "fzf-tab": "Presiona [bold green]Tab[/] y usa las flechas para navegar el menú visual.",
            "yazi": "Usa [bold green]yy[/] para abrir el gestor y al salir quedarte en esa carpeta.",
            "fzf": "Presiona [bold green]Ctrl+R[/] para buscar en el historial o [bold green]Ctrl+T[/] para buscar archivos.",
            "lazygit": "Simplemente escribe [bold green]lg[/] para gestionar tus repositorios visualmente.",
            "tldr": "Escribe [bold green]tldr <comando>[/] para ver ejemplos de uso rápidos.",
        }
        
        if item_id in tips:
            content.append(f"\n[bold yellow]💡 TIP DE ELITE:[/] [italic white]{tips[item_id]}[/]")

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
        f"[bold #00ffff]SISTEMA:[/] [white]{stats['os']}[/]\n"
        f"[bold #ff00ff]MEMORIA:[/] [white]{stats['mem_usage']}[/]\n"
        f"[bold #39ff14]DISCO:[/]   [white]{stats['disk_usage']}[/]\n"
        f"[bold yellow]UPTIME:[/]  [white]{stats['uptime']}[/]"
    )
    console.print(Panel(
        banner_content, 
        title="[bold #ff00ff]◄ STATUS OMEGA ►[/]", 
        border_style="#00ffff",
        subtitle="[dim white]Entropy Engine Active[/]"
    ))

if __name__ == "__main__":
    main()
