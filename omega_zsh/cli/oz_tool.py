#!/usr/bin/env python3
import os
import re
import sys
import platform
import psutil
from pathlib import Path
from rich.console import Console
from rich.panel import Panel
from rich.table import Table
from rich.layout import Layout
from rich.text import Text
from rich import box
from datetime import datetime

console = Console()

# --- CONFIGURACIÓN ---
HOME = Path.home()
ZSHRC = HOME / ".zshrc"
OMZ = HOME / ".oh-my-zsh"
CUSTOM_PLUGINS = OMZ / "custom/plugins"
STANDARD_PLUGINS = OMZ / "plugins"

def get_system_stats():
    """Obtiene estadísticas básicas del sistema para el banner."""
    mem = psutil.virtual_memory()
    disk = psutil.disk_usage('/')
    
    # Calcular uso de memoria visualmente
    mem_percent = mem.percent
    disk_percent = disk.percent
    
    try:
        uptime = datetime.fromtimestamp(psutil.boot_time()).strftime("%H:%M")
    except:
        uptime = "N/A"
    
    return {
        "os": "Android/Termux" if "Android" in platform.system() or os.path.exists("/system/build.prop") else platform.system(),
        "mem_usage": f"{mem_percent}%",
        "disk_usage": f"{disk_percent}%",
        "uptime": uptime
    }

def get_active_plugins():
    """Lee .zshrc para encontrar plugins activos."""
    if not ZSHRC.exists():
        return []
    
    content = ZSHRC.read_text(errors="ignore")
    # Busca la línea plugins=(...)
    match = re.search(r'^plugins=\((.*?)\)', content, re.MULTILINE | re.DOTALL)
    if match:
        # Limpiar saltos de línea y separar por espacios
        raw_plugins = match.group(1).replace('\n', ' ').split()
        return [p for p in raw_plugins if p]
    return []

def inspect_plugin(plugin_name):
    """Busca un plugin y extrae sus alias/funciones principales."""
    # Buscar en custom primero, luego en standard
    paths = [
        CUSTOM_PLUGINS / plugin_name / f"{plugin_name}.plugin.zsh",
        STANDARD_PLUGINS / plugin_name / f"{plugin_name}.plugin.zsh",
        # A veces el archivo principal es solo .zsh
        CUSTOM_PLUGINS / plugin_name / f"{plugin_name}.zsh", 
        STANDARD_PLUGINS / plugin_name / f"{plugin_name}.zsh"
    ]
    
    plugin_path = next((p for p in paths if p.exists()), None)
    
    if not plugin_path:
        return {"found": False, "aliases": [], "functions": []}

    content = plugin_path.read_text(errors="ignore")
    
    # Regex simples para extraer capacidades
    aliases = re.findall(r"^alias\s+([\w-]+)=", content, re.MULTILINE)
    functions = re.findall(r"^function\s+([\w-]+)", content, re.MULTILINE)
    # Formato alternativo de funciones: nombre() {
    functions += re.findall(r"^([\w-]+)\(\)\s*\{", content, re.MULTILINE)
    
    return {
        "found": True, 
        "path": str(plugin_path),
        "aliases": sorted(list(set(aliases))),
        "functions": sorted(list(set(functions)))
    }

def show_banner():
    """Muestra el Dashboard Inteligente."""
    stats = get_system_stats()
    plugins = get_active_plugins()
    
    # Header ASCII
    ascii_art = Text(f"""
   ▀▀▀▀ ▀▀ █▪ ▀  ▀ ·▀  ▀ ▀▀▀
   Ω OMEGA SHELL :: {stats['os']}
""", style="bold blue")

    # Tabla de Estado
    grid = Table.grid(expand=True)
    grid.add_column()
    grid.add_column(justify="right")
    grid.add_row(f"RAM: [yellow]{stats['mem_usage']}[/]", f"DISK: [yellow]{stats['disk_usage']}[/]")
    grid.add_row(f"UP:  [cyan]{stats['uptime']}[/]", f"PLUGINS: [green]{len(plugins)}[/]")
    
    panel_stats = Panel(grid, style="grey39", border_style="grey39")
    
    console.print(ascii_art)
    console.print(panel_stats)
    
    # Mostrar herramientas nativas (Hardcoded + Custom)
    table = Table(box=box.SIMPLE, show_header=False, padding=(0, 2))
    table.add_column("CMD", style="cyan bold")
    table.add_column("Desc")
    
    # Leer descripciones de personal.zsh y custom.zsh
    config_files = [HOME / ".omega-zsh/personal.zsh", HOME / ".omega-zsh/custom.zsh"]
    for cfg in config_files:
        if cfg.exists():
            lines = cfg.read_text(errors="ignore").splitlines()
            for line in lines:
                if "# Desc:" in line and "alias" in line:
                    parts = line.split("alias ")[1].split("=")
                    name = parts[0]
                    desc = line.split("# Desc: ")[1].strip()
                    table.add_row(name, desc)
                elif "# Desc:" in line and "function" in line:
                    # Intento básico para funciones
                    continue
    
    # Agregar nuestra nueva herramienta
    table.add_row("oz", "[bold yellow]Gestor Omega (Plugins, Info, Update)[/]")
    
    console.print(Panel(table, title="[bold]HERRAMIENTAS ACTIVAS[/]", border_style="blue", expand=False))

def show_plugins_detail():
    """Detalla todos los plugins instalados."""
    plugins = get_active_plugins()
    console.print(f"[bold green]Detectados {len(plugins)} plugins activos en .zshrc[/]\n")
    
    for p_name in plugins:
        info = inspect_plugin(p_name)
        
        title = f"[bold cyan]{p_name}[/]"
        if not info["found"]:
            console.print(Panel(f"No se encontró el archivo fuente.", title=title, border_style="red"))
            continue
            
        content = []
        if info["aliases"]:
            content.append(f"[bold]Alias ({len(info['aliases'])}):[/] " + ", ".join(info["aliases"][:10]) + ("..." if len(info['aliases'])>10 else ""))
        if info["functions"]:
            content.append(f"[bold]Funciones ({len(info['functions'])}):[/] " + ", ".join(info["functions"][:5]))
            
        if not content:
            content = ["Plugin de sistema (sin alias/funciones exportadas explícitamente)"]
            
        console.print(Panel("\n".join(content), title=title, border_style="grey50"))

VERSION = "2.0.0"

def show_help():
    """Muestra la ayuda profesional."""
    
    # Título y Versión
    console.print(Panel(
        f"[bold blue]OMEGA CLI (oz)[/] [white]v{VERSION}[/]\n"
        "[italic grey62]Herramienta de gestión avanzada para Omega-ZSH[/]",
        border_style="blue"
    ))

    # Tabla de Comandos
    table = Table(box=box.ROUNDED, show_header=True, header_style="bold cyan")
    table.add_column("Comando", style="green")
    table.add_column("Alias", style="yellow")
    table.add_column("Descripción")

    table.add_row("--banner", "", "Muestra el Dashboard con estado del sistema y herramientas.")
    table.add_row("--plugins", "-p, plugins", "Inspecciona el código fuente de los plugins activos.")
    table.add_row("--help", "-h", "Muestra esta pantalla de ayuda.")
    table.add_row("--version", "-v", "Muestra la versión instalada.")

    console.print(table)

    # Pie de página
    console.print("[grey50]Ejemplo de uso:[/]")
    console.print("  [green]oz --banner[/]   -> Ver estado del sistema")
    console.print("  [green]oz plugins[/]    -> Ver qué hacen tus plugins\n")

def main():
    if len(sys.argv) > 1:
        cmd = sys.argv[1]
        if cmd == "--banner":
            show_banner()
        elif cmd in ["--plugins", "-p", "plugins"]:
            show_plugins_detail()
        elif cmd in ["--version", "-v"]:
             console.print(f"Omega-ZSH CLI [bold cyan]v{VERSION}[/]")
        elif cmd in ["--help", "-h"]:
            show_help()
        else:
             console.print(f"[bold red]❌ Error:[/][red] Comando desconocido '{cmd}'[/]")
             console.print("Usa [bold yellow]oz --help[/] para ver los comandos disponibles.")
    else:
        # Por defecto muestra ayuda
        show_help()

if __name__ == "__main__":
    main()
