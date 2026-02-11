#!/usr/bin/env python3
import os
import re
import sys
import time
import shutil
import platform
import psutil
import subprocess
from collections import Counter
from pathlib import Path
from rich.console import Console
from rich.panel import Panel
from rich.table import Table
from rich.layout import Layout
from rich.text import Text
from rich import box
from rich.progress import Progress, SpinnerColumn, TextColumn
from datetime import datetime

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

def get_system_stats():
    """Obtiene estadísticas básicas del sistema."""
    mem = psutil.virtual_memory()
    disk = psutil.disk_usage('/')
    try:
        uptime = datetime.fromtimestamp(psutil.boot_time()).strftime("%H:%M")
    except:
        uptime = "N/A"
    return {
        "os": "Android/Termux" if "Android" in platform.system() or os.path.exists("/system/build.prop") else platform.system(),
        "mem_usage": f"{mem.percent}%",
        "disk_usage": f"{disk.percent}%",
        "uptime": uptime
    }

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

# --- BENCHMARK CON DIAGNÓSTICO ---
def benchmark_shell():
    """Mide tiempo de inicio y da CONSEJOS de optimización."""
    console.print("[bold cyan]🚀 Iniciando prueba de velocidad (Hyperdrive)...[/]")
    
    times = []
    with Progress(SpinnerColumn(), TextColumn("[progress.description]{task.description}"), transient=True) as progress:
        task = progress.add_task("[green]Midiendo latencia de arranque...", total=5)
        for i in range(5):
            start = time.time()
            subprocess.run(["zsh", "-i", "-c", "exit"], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            times.append(time.time() - start)
            progress.advance(task)

    avg_ms = (sum(times) / len(times)) * 1000
    
    # Clasificación
    if avg_ms < 150:
        color, rating = "green", "GOD TIER (Instantáneo)"
        advice = "[green]¡Tu terminal vuela! No toques nada.[/]"
    elif avg_ms < 400:
        color, rating = "yellow", "ACEPTABLE (Estándar)"
        advice = "[yellow]Está bien, pero podrías mejorar desactivando plugins visuales pesados.[/]"
    else:
        color, rating = "red", "LENTO (Lag detectado)"
        advice = "[bold red]DETECTADO CUELLO DE BOTELLA:[/][red]\n1. Revisa si cargas [bold]NVM, RVM o Conda[/] al inicio. Usa carga perezosa (lazy load).\n2. El plugin [bold]zsh-syntax-highlighting[/] es pesado. Intenta desactivarlo temporalmente.\n3. El tema actual podría ser complejo. Prueba uno 'Minimalista'.\n4. Comandos pesados (como `brew update` o `apt update`) en el .zshrc frenan el inicio.\n[/]"

    console.print(Panel(
        f"\n[bold]Tiempo Promedio:[/]\n[bold {color} size=24]{avg_ms:.2f} ms[/]\n\n[grey]Rating:[/] [{color}]{rating}[/]\n\n[bold]Diagnóstico:[/]\n{advice}",
        title="⚡ RESULTADOS HYPERDRIVE",
        border_style=color
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
    """Muestra la ayuda."""
    console.print(Panel(
        f"[bold blue]OMEGA CLI (oz)[/] [white]v2.2.0[/]\n[italic]Herramienta de Gestión Avanzada[/]",
        border_style="blue"
    ))
    table = Table(box=box.SIMPLE)
    table.add_column("CMD", style="green bold")
    table.add_column("Alias", style="yellow")
    table.add_column("Función")
    
    table.add_row("--banner", "banner", "Estado del sistema")
    table.add_row("--bench", "bench", "Test de velocidad + Consejos de optimización")
    table.add_row("--stats", "stats", "Top comandos + Sugerencia de Alias")
    table.add_row("--themes", "themes", "Lista TODOS los temas instalados")
    table.add_row("--update", "update", "Actualiza Omega-ZSH a la última versión")
    table.add_row("--plugins", "plugins", "Explica tus plugins activos")
    
    console.print(table)

def main():
    if len(sys.argv) > 1:
        cmd = sys.argv[1].lstrip("-")
        if cmd in ["banner"]:
            show_banner()
        elif cmd in ["plugins", "p"]:
            show_plugins_detail()
        elif cmd in ["bench", "b"]:
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
    """Detalla todos los plugins y herramientas activas según el estado de Omega."""
    active_items = get_omega_active_items()
    if not active_items:
        console.print("[yellow]No se detectaron items activos en el estado de Omega-ZSH.[/]")
        return

    console.print(f"[bold green]✨ Arsenal Activo en Omega-ZSH ({len(active_items)})[/]\n")
    
    for item_id in active_items:
        info = inspect_plugin(item_id)
        
        if info["is_binary"]:
            title = f"[bold yellow]🛠️  {item_id}[/]"
            border = "yellow"
            footer = "[italic grey]Herramienta del sistema gestionada por Omega[/]"
        else:
            title = f"[bold cyan]📦 {item_id}[/]"
            border = "cyan"
            footer = ""

        content = [f"[bold white]{info['description']}[/]\n"]
        
        if info["aliases"]:
            content.append(f"[bold yellow]🔗 Alias ({len(info['aliases'])}):[/] [italic]" + ", ".join(info["aliases"][:8]) + ("..." if len(info['aliases'])>8 else "") + "[/]")
        if info["functions"]:
            content.append(f"[bold green]⚙️ Funciones ({len(info['functions'])}):[/] [italic]" + ", ".join(info["functions"][:5]) + ("..." if len(info['functions'])>5 else "") + "[/]")
        
        if footer:
            content.append(f"\n{footer}")

        console.print(Panel("\n".join(content), title=title, border_style=border))

def show_banner():
    stats = get_system_stats()
    console.print(Panel(f"[bold blue]OMEGA SHELL[/]\nOS: {stats['os']}\nRAM: {stats['mem_usage']}\nUP: {stats['uptime']}", border_style="blue"))

if __name__ == "__main__":
    main()
