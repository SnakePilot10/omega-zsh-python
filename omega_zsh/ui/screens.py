import logging
import os
from pathlib import Path
import re
import shutil
import subprocess

from rich.table import Table
from rich.text import Text
from textual import on
from textual.app import ComposeResult
from textual.containers import Horizontal, Vertical
from textual.screen import Screen
from textual.widgets import (
    Button,
    Footer,
    Header,
    Input,
    Label,
    ListItem,
    ListView,
    Log,
    ProgressBar,
    RadioButton,
    RadioSet,
    SelectionList,
    Static,
)
from textual.widgets.selection_list import Selection

from ..core.constants import DB_HEADERS
from ..core.context import SystemContext
from ..core.figlet import FigletManager


class DashboardScreen(Static):
    """Pantalla principal con estética Neon Retro Informativa."""

    def compose(self) -> ComposeResult:
        self.context = SystemContext()
        stats = self._get_stats()

        header_art = Text.from_markup(
            "[bold #ff00ff]OMEGA[/][bold #00ffff] ZSH[/]\n"
            "[italic #39ff14]Elite Terminal Experience[/]"
        )

        yield Static(header_art, id="dashboard-title")

        # Telemetría del sistema
        telemetry = (
            f"[bold #00ffff]SISTEMA:[/] [white]{stats['os']}[/]\n"
            f"[bold #ff00ff]MEMORIA:[/] [white]{stats['mem_usage']}[/]\n"
            f"[bold #39ff14]DISCO:[/]   [white]{stats['disk_usage']}[/]\n"
            f"[bold yellow]UPTIME:[/]  [white]{stats['uptime']}[/]"
        )
        yield Static(
            f"[bold #ff00ff]◄ STATUS OMEGA ►[/]\n{telemetry}",
            id="dashboard-telemetry"
        )

        # Atajos rápidos
        help_text = (
            "• [bold #39ff14]A[/]: Apply config (Fast)\n"
            "• [bold #39ff14]I[/]: Full Installation\n"
            "• [bold #39ff14]Q[/]: Exit"
        )
        yield Static(
            f"[bold #ff00ff]◄ SHORTCUTS ►[/]\n{help_text}",
            id="dashboard-shortcuts"
        )

    def _get_stats(self):
        """Obtiene estadísticas del sistema sin depender de psutil."""
        try:
            # Memoria (Termux/Linux)
            mem_p = "N/A"
            if os.path.exists("/proc/meminfo"):
                with open("/proc/meminfo") as f:
                    lines = f.readlines()
                mem = {}
                for line in lines:
                    parts = line.split(":")
                    if len(parts) == 2:
                        mem[parts[0].strip()] = int(parts[1].split()[0].strip())
                total = mem.get("MemTotal", 1)
                free = mem.get("MemFree", 0)
                used = total - free
                mem_p = f"{int((used / total) * 100)}%"

            # Disco
            disk_p = "N/A"
            try:
                st = os.statvfs("/")
                total = st.f_blocks * st.f_frsize
                free = st.f_bavail * st.f_frsize
                used = total - free
                disk_p = f"{int((used / total) * 100)}%"
            except Exception:
                pass

            return {
                "os": "Android/Termux" if os.path.exists("/data/data/com.termux") else "Linux",
                "mem_usage": mem_p,
                "disk_usage": disk_p,
                "uptime": "N/A",
            }
        except Exception:
            return {"os": "Unknown", "mem_usage": "N/A", "disk_usage": "N/A", "uptime": "N/A"}


# --- PANTALLA DE SELECCIÓN DE PLUGINS ---
class PluginSelectScreen(Vertical):
    """Interfaz para activar/desactivar plugins y herramientas binarias."""

    def __init__(self, all_plugins, bin_plugins, selected_plugins):
        super().__init__()
        self.all_plugins = all_plugins  # List[PluginDef]
        self.bin_plugins = bin_plugins  # List[PluginDef]
        self.selected_plugins = selected_plugins  # List[str]

    def compose(self) -> ComposeResult:
        yield Label("[bold #ff00ff]SELECCIÓN DE PLUGINS Y BINARIOS[/]")
        yield Label("[dim]Usa [bold]Espacio[/] para marcar/desmarcar[/]", id="plugin-hint")

        # Construir opciones para la lista
        options = []
        for p in self.all_plugins:
            # Prefijar ID con 'p-' para cumplir reglas de Textual (no empezar con número)
            options.append(Selection(p.id, p.id, p.id in self.selected_plugins))

        for p in self.bin_plugins:
            # bin_plugins puede ser lista de strings o de PluginDef
            pid = p if isinstance(p, str) else p.id
            options.append(Selection(f"📦 {pid}", pid, pid in self.selected_plugins))

        yield SelectionList(*options, id="plugin-list")

    def get_selected(self) -> list[str]:
        return self.query_one(SelectionList).selected


# --- PANTALLA DE SELECCIÓN DE TEMAS ---
class ThemeSelectScreen(Horizontal):
    """Interfaz dividida para elegir temas con previsualización en vivo."""

    def __init__(self, all_themes, selected_theme):
        super().__init__()
        self.all_themes = all_themes  # List[ThemeDef]
        self.selected_theme = selected_theme

    def compose(self) -> ComposeResult:
        # Columna Izquierda: Lista
        with Vertical(id="theme-list-container"):
            yield Label("[bold #ff00ff]TEMAS DISPONIBLES[/]")
            items = []
            selected_index = 0
            for i, t in enumerate(self.all_themes):
                # Prefijar ID con 't-' para cumplir reglas de Textual (no empezar con número)
                items.append(ListItem(Label(f"{t.id} [dim]({t.desc})[/]"), id=f"t-{i}"))
                if t.id == self.selected_theme:
                    selected_index = i

            lv = ListView(*items, id="theme-list")
            lv.index = selected_index
            yield lv

        # Columna Derecha: Preview
        with Vertical(id="theme-preview-container"):
            yield Label("[bold #00ffff]PREVISUALIZACIÓN[/]")
            yield Static("Select a theme to see preview...", id="theme-preview-box")

    def get_selected(self) -> str:
        idx = self.query_one(ListView).index
        if idx is not None and idx < len(self.all_themes):
            return self.all_themes[idx].id
        return self.selected_theme

    @on(ListView.Highlighted)
    def update_preview(self, event: ListView.Highlighted) -> None:
        """Lanza la previsualización del tema usando un subproceso de Zsh."""
        idx = self.query_one(ListView).index
        if idx is None:
            return

        theme = self.all_themes[idx]
        preview_box = self.query_one("#theme-preview-box")

        if not theme.path or not os.path.exists(theme.path):
            preview_box.update(Text("Preview not available (No path found)", style="red"))
            return

        preview_box.update(Text("Rendering...", style="yellow"))

        # Ejecución asíncrona simulada con subproceso (no bloquea UI de Textual si es rápido)
        # En una versión más pro, usaríamos un worker de Textual.
        zsh_bin = shutil.which("zsh")
        if not zsh_bin:
            preview_box.update(Text("Error: Zsh binary not found.", style="bold red"))
            return

        try:
            # Comando mágico para previsualizar tema sin cambiar el shell actual
            # 1. Sourcear el tema
            # 2. Forzar expansión de PROMPT
            # 3. Imprimir el prompt renderizado
            omz_dir = os.environ.get('ZSH', str(Path.home() / '.oh-my-zsh'))
            omz_lib = f'{omz_dir}/lib'
            cmd = (
                f'[[ -f ~/.cargo/env ]] && source ~/.cargo/env 2>/dev/null; export ZSH="{omz_dir}" && '
                f'fpath=("{omz_dir}/functions" "{omz_dir}/completions" $fpath) && '
                f'autoload -U colors && colors && '
                f'autoload -Uz vcs_info && '
                f'autoload -U compinit && '
                f'for _f in {omz_lib}/git.zsh {omz_lib}/theme-and-appearance.zsh'
                f' {omz_lib}/functions.zsh; do [[ -f $_f ]] && source $_f; done && '
                f'source {theme.path} && '
                f'print -P "$PROMPT" && print -P "$RPROMPT"'
            )
            result = subprocess.run(
                [zsh_bin, "-c", cmd], capture_output=True, text=True, timeout=1.5
            )

            # Mostrar stdout si existe, independiente del returncode
            # (los temas OMZ suelen generar warnings no fatales)
            if result.stdout.strip():
                try:
                    ansi_text = Text.from_ansi(result.stdout)
                    preview_box.update(ansi_text)
                except Exception as e:
                    preview_box.update(Text(f"Error parsing ANSI: {e}", style="red"))
            elif result.stderr:
                preview_box.update(Text(f"Preview Error:\n{result.stderr}", style="dim red"))
            else:
                preview_box.update(Text("Preview vacío (tema sin PROMPT definido)", style="dim"))
        except subprocess.TimeoutExpired:
            preview_box.update(Text("Preview timed out (Theme too slow?)", style="orange"))
        except Exception as e:
            preview_box.update(Text(f"Execution Error: {e}", style="red"))

    def _sanitize_id(self, text: str) -> str:
        """Sanitiza un string para que sea un ID válido de Textual."""
        return re.sub(r"[^a-zA-Z0-9_-]", "_", text)


# --- PANTALLA DE CONFIGURACIÓN DE HEADER ---
class HeaderSelectScreen(Vertical):
    """Configuración estética del Banner de bienvenida."""

    def __init__(self, selected_header, header_text, selected_font):
        super().__init__()
        self.selected_header = selected_header
        self.header_text = header_text
        self.selected_font = selected_font
        self.figlet = FigletManager()

    def compose(self) -> ComposeResult:
        yield Label("[bold #ff00ff]CONFIGURACIÓN DE HEADER[/]")

        with Horizontal(id="header-config-row"):
            with Vertical(id="header-type-col"):
                yield Label("Tipo:")
                yield RadioSet(
                    RadioButton("None", id="h-none", value=(self.selected_header == "none")),
                    RadioButton("Fastfetch", id="h-ff", value=(self.selected_header == "fastfetch")),
                    RadioButton("Figlet", id="h-fig", value=(self.selected_header == "figlet")),
                    RadioButton("Cowsay", id="h-cow", value=(self.selected_header == "cowsay")),
                    id="header-type-set",
                )

            with Vertical(id="header-text-col"):
                yield Label("Texto / Fuentes (solo Figlet):")
                yield Input(value=self.header_text, placeholder="Banner Text", id="header-input")
                # Lista de fuentes figlet
                fonts = self.figlet.get_fonts()
                selected_idx = 0
                items = []
                for i, f in enumerate(fonts):
                    items.append(ListItem(Label(f), id=f"font-{i}"))
                    if f == self.selected_font:
                        selected_idx = i

                lv = ListView(*items, id="font-list")
                lv.index = selected_idx
                yield lv

        yield Label("[bold #00ffff]PREVIEW:[/]")
        yield Static("", id="header-preview-area")

    def get_selected(self) -> tuple[str, str, str]:
        # Obtener tipo
        h_set = self.query_one("#header-type-set")
        if h_set.pressed_button.id == "h-ff":
            h_type = "fastfetch"
        elif h_set.pressed_button.id == "h-fig":
            h_type = "figlet"
        elif h_set.pressed_button.id == "h-cow":
            h_type = "cowsay"
        else:
            h_type = "none"

        text = self.query_one("#header-input").value
        idx = self.query_one("#font-list").index
        fonts = self.figlet.get_fonts()
        font = fonts[idx] if idx is not None else self.selected_font

        return h_type, text, font

    @on(RadioSet.Changed)
    @on(Input.Changed)
    @on(ListView.Highlighted)
    def update_header_preview(self) -> None:
        """Actualiza la previsualización del banner en tiempo real."""
        h_type, text, font = self.get_selected()
        preview_area = self.query_one("#header-preview-area")

        if h_type == "none":
            preview_area.update(Text("No header selected", style="dim"))
            return

        if h_type == "figlet":
            art = self.figlet.render(text, font)
            preview_area.update(Text(art))
            return

        if h_type == "cowsay":
            import shutil as _shutil
            cow_bin = _shutil.which("cowsay")
            if not cow_bin:
                preview_area.update(Text("cowsay no encontrado. Instala con: pkg install cowsay", style="red"))
                return
            try:
                import subprocess as _sp
                result = _sp.run([cow_bin, text or "Omega ZSH"], capture_output=True, text=True, timeout=2.0)
                if result.returncode == 0:
                    preview_area.update(Text(result.stdout))
                else:
                    preview_area.update(Text(f"Error: {result.stderr}", style="red"))
            except Exception as e:
                preview_area.update(Text(f"Error: {e}", style="red"))
            return

        if h_type == "fastfetch":
            preview_area.update(Text("Rendering live preview...", style="yellow"))
            ff_bin = shutil.which("fastfetch")
            if not ff_bin:
                preview_area.update(
                    Text("Fastfetch not found. Please install it first.", style="red")
                )
                return

            try:
                # Fastfetch puede tardar, lo ejecutamos con pipe
                result = subprocess.run(
                    [ff_bin, "--pipe"], capture_output=True, text=True, timeout=2.0
                )
                if result.returncode == 0:
                    try:
                        ansi_text = Text.from_ansi(result.stdout)
                        preview_area.update(ansi_text)
                    except Exception as e:
                        preview_area.update(Text(f"ANSI Parse Error: {e}", style="red"))
                else:
                    err = result.stderr or "Check if fastfetch is working."
                    preview_area.update(Text(f"Command execution failed:\n{err}", style="dim red"))
            except subprocess.TimeoutExpired:
                preview_area.update(Text("Preview timed out (Command took too long)", style="orange"))
            except Exception as e:
                preview_area.update(Text(f"Preview Error: {e}", style="red"))


# --- PANTALLA DE INSTALACIÓN (MODAL-LIKE) ---
class InstallScreen(Screen):
    """Pantalla de progreso de instalación."""

    def compose(self) -> ComposeResult:
        with Vertical(id="install-container"):
            yield Label("[bold #ff00ff]PROCESO DE INSTALACIÓN OMEGA[/]")
            yield ProgressBar(total=100, show_eta=False, id="install-progress")
            yield Log(id="install-log")
            yield Button("Cancelar", variant="error", id="btn-cancel")
            yield Button("Finalizar", variant="success", id="btn-finish", disabled=True)

    def on_mount(self) -> None:
        self.query_one(Log).write_line("Iniciando instalador...")
        self.app.run_installation(self.on_installation_message)

    def on_installation_message(self, message: str) -> None:
        self.query_one(Log).write_line(message)

    def on_installation_finished(self, success: bool) -> None:
        if success:
            self.query_one(Log).write_line("\n[bold #39ff14]¡INSTALACIÓN COMPLETADA CON ÉXITO![/]")
            self.query_one(ProgressBar).progress = 100
            self.query_one("#btn-finish").disabled = False
            self.query_one("#btn-cancel").disabled = True
        else:
            self.query_one(Log).write_line("\n[bold red]LA INSTALACIÓN HA FALLADO O SE CANCELÓ.[/]")
            self.query_one("#btn-cancel").label = "Volver"

    @on(Button.Pressed, "#btn-finish")
    def finish_install(self) -> None:
        self.dismiss(True)

    @on(Button.Pressed, "#btn-cancel")
    def cancel_install(self) -> None:
        self.dismiss(False)
