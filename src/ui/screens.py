from textual.app import ComposeResult
from textual.screen import Screen
from textual.widgets import Header, Footer, Static, SelectionList, RadioButton, Label, Log, Button
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

class DashboardScreen(Static):
    """Pantalla principal con el resumen de configuración."""
    
    def on_mount(self) -> None:
        self.update_stats()

    def update_stats(self) -> None:
        pass # Placeholder for real-time stats updates

    def render(self) -> Panel:
        ctx = SystemContext()
        
        # System Info Panel
        sys_info = Table.grid(padding=1)
        sys_info.add_column(style="bold cyan")
        sys_info.add_column(style="white")
        
        sys_info.add_row("OS Type:", ctx.os_type.upper())
        sys_info.add_row("Distro:", ctx.distro_id.title())
        sys_info.add_row("Package Mgr:", ctx.package_manager_type)
        sys_info.add_row("Termux:", "✅ Yes" if ctx.is_termux else "❌ No")
        
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
            f"\n[bold magenta]Welcome to Omega-ZSH v14.0[/]\n"
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
    BINDINGS = [("escape", "app.pop_screen", "Volver")]

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
            # FORMATO: [ID] - Descripción
            label = f"[{p.id}] - {p.desc}"
            selections.append(Selection(label, p.id, initial_state=is_on))
            
        yield SelectionList[str](*selections, id="plugin-list")
        yield Footer()

    def on_unmount(self) -> None:
        selection_list = self.query_one("#plugin-list", SelectionList)
        self.selected_ids.clear()
        self.selected_ids.extend(selection_list.selected)

class ThemeSelectScreen(Screen):
    """Pantalla para seleccionar el tema de usuario."""
    BINDINGS = [("escape", "app.pop_screen", "Volver")]

    def __init__(self, themes, current_theme, title="Seleccionar Tema"):
        super().__init__()
        self.themes = themes
        self.current_theme = current_theme
        self.screen_title = title
        self.selected_theme_id = current_theme # Local state

    def compose(self) -> ComposeResult:
        yield Header()
        yield Label(f"[bold magenta]{self.screen_title}[/]")
        with Vertical(id="theme-list-container"):
            with RadioSet(id="theme-radios"):
                for theme in self.themes:
                    yield RadioButton(f"{theme.id}", id=theme.id.replace("_", "-"), value=(theme.id == self.current_theme))
        yield Footer()
    
        def on_radio_set_changed(self, event) -> None:
            # El ID del radio button puede tener '-' en lugar de '_' si lo cambiamos, 
            # pero aquí usamos el label o recuperamos el ID original si es posible.
            # Mejor estrategia: iterar themes y matchear.
            # Simplificación: Asumimos que el ID del componente matchea el theme id o usamos el index.
            # Textual RadioButton.value es un booleano. 
            # event.pressed.id es el ID del widget.
            pass
    def on_unmount(self) -> None:
        # Recuperar el seleccionado
        radios = self.query_one("#theme-radios", RadioSet)
        if radios.pressed_button:
             # El ID del widget es "THEME_ID"
             # En compose: RadioButton(label, id=theme.id ...)
             if radios.pressed_button.id:
                 self.selected_theme_id = str(radios.pressed_button.id).replace("-", "_") # Restaurar guiones bajos si es necesario
                 if hasattr(self.app, "update_selected_theme"):
                     self.app.update_selected_theme(self.selected_theme_id)

class HeaderSelectScreen(Screen):
    """Pantalla para seleccionar el Header (Logo)."""
    BINDINGS = [("escape", "app.pop_screen", "Volver")]

    def __init__(self, current_header):
        super().__init__()
        self.current_header = current_header
        self.selected_header_id = current_header

    def compose(self) -> ComposeResult:
        yield Header()
        yield Label("[bold yellow]Select Terminal Header Style:[/]")
        with RadioSet(id="header-radios"):
            for h in DB_HEADERS:
                label = f"{h.id} ({h.desc})"
                yield RadioButton(label, id=f"h-{h.id}", value=(h.id == self.current_header))
        yield Footer()

    def on_unmount(self) -> None:
        radios = self.query_one("#header-radios", RadioSet)
        if radios.pressed_button:
            if radios.pressed_button.id:
                self.selected_header_id = radios.pressed_button.id.replace("h-", "")
                if hasattr(self.app, "update_selected_header"):
                    self.app.update_selected_header(self.selected_header_id)

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