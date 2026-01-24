from textual.app import ComposeResult
from textual import on
from textual.screen import Screen
from textual.widgets import Header, Footer, Static, SelectionList, RadioSet, RadioButton, Label, Log, Button, Input, ListView, ListItem
from textual.containers import Vertical, Horizontal, Grid
from textual.widgets.selection_list import Selection
from rich.table import Table
from rich.panel import Panel
from rich.align import Align
from rich.text import Text
from ..core.constants import DB_PLUGINS, THEMES_OMZ_BUILTIN, THEMES_ROOT, DB_HEADERS
from ..core.context import SystemContext
import platform
import os
import shutil
import psutil
import subprocess
from datetime import datetime
import logging

class DashboardScreen(Static):
    """Pantalla principal con el resumen de configuración."""
    
    def on_mount(self) -> None:
        self.update_stats()

    def update_stats(self) -> None:
        """Actualiza las estadísticas del sistema en tiempo real."""
        try:
            mem = psutil.virtual_memory()
            disk = psutil.disk_usage('/')
            
            # Obtener uptime
            try:
                uptime = datetime.fromtimestamp(psutil.boot_time()).strftime("%H:%M")
            except Exception:
                uptime = "N/A"

            # Actualizar widgets si existen (en una versión más compleja, usaríamos Reactive)
            # Por ahora, como es Static y render se llama una vez, nos aseguramos
            # de que los datos estén disponibles para el renderizado inicial.
            self.stats = {
                "mem": f"{mem.percent}%",
                "disk": f"{disk.percent}%",
                "uptime": uptime
            }
        except Exception as e:
            logging.error(f"Error actualizando estadísticas: {e}")
            self.stats = {"mem": "N/A", "disk": "N/A", "uptime": "N/A"}

    def render(self) -> Panel:
        ctx = SystemContext()
        # Asegurarse de que tenemos stats
        if not hasattr(self, "stats"):
            self.update_stats()
        
        # System Info Panel
        sys_info = Table.grid(padding=1)
        sys_info.add_column(style="bold cyan")
        sys_info.add_column(style="white")
        
        sys_info.add_row("OS Type:", ctx.os_type.upper())
        sys_info.add_row("Distro:", ctx.distro_id.title())
        sys_info.add_row("Package Mgr:", ctx.package_manager_type)
        sys_info.add_row("Termux:", "✅ Yes" if ctx.is_termux else "❌ No")
        sys_info.add_row("RAM Usage:", self.stats.get("mem", "N/A"))
        sys_info.add_row("Disk Usage:", self.stats.get("disk", "N/A"))
        sys_info.add_row("Uptime:", self.stats.get("uptime", "N/A"))
        
        # Shortcuts Panel
        shortcuts = Table.grid(padding=1)
        shortcuts.add_column(style="bold yellow")
        shortcuts.add_column(style="white")
        shortcuts.add_row("P", "Plugins Manager")
        shortcuts.add_row("T", "Theme Selector")
        shortcuts.add_row("H", "Header Style")
        shortcuts.add_row("I", "INSTALL / APPLY")
        shortcuts.add_row("Q", "Quit")

        # Main Layout
        grid = Table.grid(expand=True)
        grid.add_column(ratio=1)
        grid.add_column(ratio=1)
        
        grid.add_row(
            Panel(sys_info, title="[bold blue]System Status[/]", border_style="blue"),
            Panel(shortcuts, title="[bold yellow]Quick Actions[/]", border_style="yellow")
        )
        
        welcome_msg = Text.from_markup(
            f"\n[bold magenta]Welcome to Omega-ZSH v2.0.0[/]\n"
            f"Detected User: [bold]{os.environ.get('USER', 'user')}[/]\n"
            f"Home: {ctx.home}\n",
            justify="center"
        )

        final_layout = Table.grid(expand=True)
        final_layout.add_row(Align.center(welcome_msg))
        final_layout.add_row(grid)

        return Panel(final_layout, title="[bold green]Dashboard[/]", border_style="green")

class PluginSelectScreen(Screen):
    """Pantalla para seleccionar plugins."""
    BINDINGS = [("escape", "pop_screen", "Volver")]
    
    CSS = """
    SelectionList {
        height: 1fr;
        overflow-y: auto;
        scrollbar-size-vertical: 1;
        border: solid $primary;
    }
    """

    def __init__(self, all_plugins, selected_ids):
        super().__init__()
        self.all_plugins = all_plugins
        self.selected_ids = selected_ids

    def compose(self) -> ComposeResult:
        yield Header()
        yield Label("[bold cyan]Select Plugins (Space to toggle):[/]")
        
        selections = []
        for p in self.all_plugins:
            is_on = p.id in self.selected_ids
            label = f"[{p.id}] {p.desc}"
            selections.append(Selection(label, p.id, initial_state=is_on))
            
        yield SelectionList[str](*selections, id="plugin-list")
        yield Footer()

    @on(SelectionList.SelectedChanged)
    def on_selection_change(self, event: SelectionList.SelectedChanged) -> None:
        """Actualiza la lista de plugins en tiempo real."""
        self.selected_ids.clear()
        self.selected_ids.extend(event.selection_list.selected)
        if hasattr(self.app, "update_selected_plugins"):
            self.app.update_selected_plugins(self.selected_ids)

    def action_pop_screen(self) -> None:
        self.app.pop_screen()

class ThemeSelectScreen(Screen):
    """Pantalla para seleccionar el tema de usuario con previsualización."""
    BINDINGS = [("escape", "pop_screen", "Volver")]
    
    CSS = """
    #theme-sidebar {
        width: 35%;
        height: 100%;
        border-right: tall $primary;
        padding: 1;
    }
    #theme-list-container {
        height: 1fr;
        overflow-y: auto;
        scrollbar-size-vertical: 1;
    }
    #theme-preview-container {
        width: 65%;
        height: 100%;
        padding: 2;
        align: center middle;
    }
    #theme-preview-box {
        background: #000000;
        border: heavy $accent;
        width: 90%;
        height: auto;
        min-height: 5;
        padding: 1;
        color: $text;
    }
    """

    def __init__(self, themes, current_theme, title="Seleccionar Tema"):
        super().__init__()
        self.themes = themes
        self.current_theme = current_theme
        self.screen_title = title
        # Mapa rápido para buscar path por id
        self.themes_map = {t.id: t for t in themes}

    def compose(self) -> ComposeResult:
        yield Header()
        yield Label(f"[bold magenta]{self.screen_title}[/]")
        
        with Horizontal():
            # Panel Izquierdo: Lista de Temas
            with Vertical(id="theme-sidebar"):
                yield Label("[bold yellow]Available Themes:[/]")
                with Vertical(id="theme-list-container"):
                    with RadioSet(id="theme-radios"):
                        for theme in self.themes:
                            yield RadioButton(f"{theme.id}", id=theme.id.replace("_", "-"), value=(theme.id == self.current_theme))
            
            # Panel Derecho: Previsualización
            with Vertical(id="theme-preview-container"):
                yield Label("[bold green]Live Preview (Real Zsh Render):[/]")
                yield Static("Select a theme to preview...", id="theme-preview-box")
                yield Label("\n[dim]Note: Preview renders the prompt using a subprocess.[/]")

        yield Footer()

    def on_mount(self) -> None:
        # Generar preview inicial si hay un tema seleccionado
        if self.current_theme:
            self.generate_preview(self.current_theme)

    @on(RadioSet.Changed, "#theme-radios")
    def on_theme_changed(self, event: RadioSet.Changed) -> None:
        """Actualizar estado y generar preview al cambiar selección."""
        if event.pressed:
            theme_name = str(event.pressed.label)
            if hasattr(self.app, "update_selected_theme"):
                self.app.update_selected_theme(theme_name)
            
            self.generate_preview(theme_name)

    def generate_preview(self, theme_id: str) -> None:
        """Ejecuta una instancia aislada de Zsh para renderizar el prompt."""
        preview_box = self.query_one("#theme-preview-box", Static)
        theme = self.themes_map.get(theme_id)
        
        if not theme or not theme.path:
            preview_box.update(Text("Preview not available (No path found)", style="red"))
            return

        preview_box.update(Text("Rendering...", style="yellow"))
        
        # Encontrar binario de zsh
        zsh_bin = "/data/data/com.termux/files/usr/bin/zsh"
        if not os.path.exists(zsh_bin):
            zsh_bin = shutil.which("zsh")
        
        if not zsh_bin:
            preview_box.update(Text("Error: Zsh binary not found.", style="bold red"))
            return

        # Comando para simular el prompt
        # 1. Definir variables básicas para evitar errores
        # 2. Cargar el tema
        # 3. Imprimir el prompt expandido
        cmd_script = (
            f"source {theme.path} 2>/dev/null;"
            "print -P \"${PROMPT:-$PS1} ls -la\""
        )
        
        try:
            import subprocess
            result = subprocess.run(
                [zsh_bin, "-c", cmd_script],
                capture_output=True,
                text=True,
                timeout=2,
                env={**os.environ, "TERM": "xterm-256color"} # Forzar color
            )
            
            if result.returncode == 0 and result.stdout.strip():
                # Renderizar ANSI
                # Rich maneja ANSI automáticamente con Text.from_ansi
                try:
                    ansi_text = Text.from_ansi(result.stdout)
                    preview_box.update(ansi_text)
                except Exception as e:
                    preview_box.update(Text(f"Error parsing ANSI: {e}", style="red"))
            else:
                err_msg = result.stderr.strip() or "No output returned"
                preview_box.update(Text(f"Preview Error:\n{err_msg}", style="dim red"))
                
        except subprocess.TimeoutExpired:
            preview_box.update(Text("Preview timed out (Theme too slow?)", style="orange"))
        except Exception as e:
            preview_box.update(Text(f"Execution Error: {e}", style="red"))

from ..core.figlet import FigletManager

class HeaderSelectScreen(Screen):
    """Pantalla avanzada para seleccionar y personalizar el Header."""
    CSS = """
    #header-sidebar {
        width: 40%;
        height: 100%;
        border-right: tall $primary;
        padding: 1;
    }
    #header-preview-container {
        width: 60%;
        height: 100%;
        padding: 1;
        align: center middle;
    }
    #header-preview-area {
        background: $surface;
        border: double $accent;
        width: 100%;
        height: 15;
        content-align: center middle;
        color: $text;
    }
    #figlet-config {
        margin-top: 1;
        border-top: dashed $primary-muted;
    }
    #figlet-fonts-list {
        height: 1fr;
        border: heavy $primary-muted;
        margin-top: 1;
    }
    """
    BINDINGS = [
        ("escape", "pop_screen", "Volver"),
    ]

    def __init__(self, current_header):
        super().__init__()
        self.current_header = current_header
        self.figlet = FigletManager()
        self._debounce_timer = None
        
        self.header_text = getattr(self.app, "header_text", "Omega")
        self.header_font = getattr(self.app, "header_font", "slant")

    def _sanitize_id(self, name: str) -> str:
        """Sanitiza un string para que sea un ID válido de Textual."""
        return name.lower().replace(" ", "_").replace(".", "_").replace("+", "_")

    def compose(self) -> ComposeResult:
        yield Header()
        
        with Horizontal():
            # Panel Izquierdo: Opciones principales
            with Vertical(id="header-sidebar"):
                yield Label("[bold yellow]Header Style:[/]")
                with RadioSet(id="header-radios"):
                    for h in DB_HEADERS:
                        yield RadioButton(h.desc, id=f"h-{h.id}", value=(h.id == self.current_header))
                
                # Configurador Figlet
                with Vertical(id="figlet-config"):
                    yield Label("\n[bold cyan]Figlet Settings:[/]")
                    yield Input(placeholder="Banner Text", value=self.header_text, id="figlet-text-input")
                    yield Label("[dim]Select Font:[/]")
                    with ListView(id="figlet-fonts-list"):
                        for idx, font in enumerate(self.figlet.get_fonts()):
                            # Usamos name para guardar el nombre real de la fuente
                            yield ListItem(Label(font), id=f"font-idx-{idx}", name=font)

            # Panel Derecho: Vista Previa
            with Vertical(id="header-preview-container"):
                yield Label("[bold green]Preview:[/]")
                yield Static("", id="header-preview-area", markup=False)
        
        yield Footer()

    def on_mount(self) -> None:
        self.update_ui_visibility()
        try:
            list_view = self.query_one("#figlet-fonts-list", ListView)
            # Seleccionar por name en lugar de ID
            for idx, item in enumerate(list_view.children):
                if item.name == self.header_font:
                    list_view.index = idx
                    break
        except Exception as e:
            logging.warning(f"No se pudo restaurar la selección de fuente Figlet: {e}")
        self.update_preview()

    def update_ui_visibility(self) -> None:
        try:
            is_figlet = self.query_one("#h-figlet_custom", RadioButton).value
            self.query_one("#figlet-config").display = is_figlet
        except Exception as e:
            logging.error(f"Error actualizando visibilidad de UI: {e}")

    def _sync_state(self):
        """Sincroniza el estado actual con la aplicación principal."""
        if hasattr(self.app, "update_header_config"):
            self.app.update_header_config(
                self.current_header, 
                self.header_text, 
                self.header_font
            )

    @on(RadioSet.Changed, "#header-radios")
    def on_header_changed(self, event: RadioSet.Changed) -> None:
        self.current_header = event.pressed.id.replace("h-", "")
        self.update_ui_visibility()
        self.update_preview()
        self._sync_state()

    @on(Input.Changed, "#figlet-text-input")
    def on_text_changed(self, event: Input.Changed) -> None:
        self.header_text = event.value
        if self._debounce_timer:
            self._debounce_timer.stop()
        self._debounce_timer = self.set_timer(0.3, self._finalize_text_change)

    def _finalize_text_change(self):
        self.update_preview()
        self._sync_state()

    @on(ListView.Selected, "#figlet-fonts-list")
    def on_font_selected(self, event: ListView.Selected) -> None:
        # Recuperación robusta usando el atributo 'name'
        if event.item.name:
            self.header_font = event.item.name
            self.update_preview()
            self._sync_state()

    def update_preview(self) -> None:
        preview_area = self.query_one("#header-preview-area")
        
        if self.current_header == "none":
            preview_area.update(Text("No header selected", style="dim"))
            return

        # Renderizado en vivo para Figlet (Interno, rápido)
        if self.current_header == "figlet_custom":
            width = preview_area.size.width or 60
            art = self.figlet.render(self.header_text, self.header_font, width=width - 4)
            preview_area.update(Text(art))
            return

        # Renderizado basado en comandos externos (Fastfetch, Cow)
        preview_area.update(Text("Rendering live preview...", style="yellow"))
        
        cmd = None
        if self.current_header == "fastfetch":
            # Forzamos color y estructura reducida si es posible
            if shutil.which("fastfetch"):
                cmd = ["fastfetch", "--pipe", "false"] 
            else:
                preview_area.update(Text("Fastfetch not installed.\nInstall it via 'oz plugins' or system manager.", style="red"))
                return
                
        elif self.current_header == "cow":
            # Intentamos pipeline completo: fortune | cowsay | lolcat
            # Nota: lolcat a veces da problemas en subprocess no interactivos, probamos sin el o forzando
            has_fortune = shutil.which("fortune")
            has_cowsay = shutil.which("cowsay")
            
            if has_fortune and has_cowsay:
                # Ejecutamos vía shell para soportar pipes
                cmd_str = "fortune | cowsay"
                if shutil.which("lolcat"):
                    cmd_str += " | lolcat --force"
                cmd = ["sh", "-c", cmd_str]
            else:
                preview_area.update(Text("Need 'fortune' and 'cowsay' installed.", style="red"))
                return

        if cmd:
            try:
                # Ejecución asíncrona simulada (bloqueante pero con timeout corto)
                result = subprocess.run(
                    cmd,
                    capture_output=True,
                    text=True,
                    timeout=2.0,
                    env={**os.environ, "TERM": "xterm-256color", "FORCE_COLOR": "1"}
                )
                
                if result.returncode == 0 and result.stdout.strip():
                    try:
                        ansi_text = Text.from_ansi(result.stdout)
                        preview_area.update(ansi_text)
                    except Exception as e:
                        preview_area.update(Text(f"ANSI Parse Error: {e}", style="red"))
                else:
                    err = result.stderr or "No output"
                    preview_area.update(Text(f"Command execution failed:\n{err}", style="dim red"))
            
            except subprocess.TimeoutExpired:
                preview_area.update(Text("Preview timed out (Command took too long)", style="orange"))
            except Exception as e:
                preview_area.update(Text(f"Preview Error: {e}", style="red"))

    def action_pop_screen(self) -> None:
        self.app.pop_screen()


class InstallScreen(Screen):
    """Pantalla que muestra el progreso de la instalación."""
    def compose(self) -> ComposeResult:
        yield Header()
        yield Label("[bold green]INSTALLING OMEGA-ZSH...[/]")
        yield Log(id="install-log")
        yield Button("Finalizar y Salir", id="finish-btn", variant="success")
        yield Footer()

    def on_mount(self) -> None:
        self.query_one("#finish-btn").visible = False

    def write_log(self, message: str):
        self.query_one("#install-log").write_line(message)
        
    def show_finish(self):
        self.query_one("#finish-btn").visible = True