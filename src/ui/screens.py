from textual.app import ComposeResult
from textual.screen import Screen
from textual.widgets import Header, Footer, Static, SelectionList, RadioSet, RadioButton, Label, Log, Button
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
    # CAMBIO: Usamos una acción personalizada para guardar antes de salir
    BINDINGS = [("escape", "save_and_exit", "Volver")]

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
            # Formato claro: [ID] Descripción
            label = f"[{p.id}] {p.desc}"
            selections.append(Selection(label, p.id, initial_state=is_on))
            
        yield SelectionList[str](*selections, id="plugin-list")
        yield Footer()

    def action_save_and_exit(self) -> None:
        """Guardar selección y cerrar pantalla."""
        try:
            selection_list = self.query_one("#plugin-list", SelectionList)
            self.selected_ids.clear()
            self.selected_ids.extend(selection_list.selected)
        except Exception:
            pass # Si falla, al menos cerramos
        self.app.pop_screen()

class ThemeSelectScreen(Screen):
    """Pantalla para seleccionar el tema de usuario."""
    BINDINGS = [("escape", "save_and_exit", "Volver")]

    def __init__(self, themes, current_theme, title="Seleccionar Tema"):
        super().__init__()
        self.themes = themes
        self.current_theme = current_theme
        self.screen_title = title
        self.selected_theme_id = current_theme

    def compose(self) -> ComposeResult:
        yield Header()
        yield Label(f"[bold magenta]{self.screen_title}[/]")
        with Vertical(id="theme-list-container"):
            with RadioSet(id="theme-radios"):
                for theme in self.themes:
                    yield RadioButton(f"{theme.id}", id=theme.id.replace("_", "-"), value=(theme.id == self.current_theme))
        yield Footer()
    
    def action_save_and_exit(self) -> None:
        # Recuperar el seleccionado antes de destruir widgets
        try:
            radios = self.query_one("#theme-radios", RadioSet)
            if radios.pressed_button:
                 # El ID del widget puede haber cambiado, pero intentamos recuperar el valor
                 # Una estrategia segura es usar el label si coincide con el ID
                 clean_id = str(radios.pressed_button.label)
                 if hasattr(self.app, "update_selected_theme"):
                     self.app.update_selected_theme(clean_id)
        except Exception:
            pass
        self.app.pop_screen()

from ..core.figlet import FigletManager
from textual.widgets import Header, Footer, Static, SelectionList, RadioSet, RadioButton, Label, Log, Button, Input, ListView, ListItem
from textual import on

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
        border: sunken $primary-muted;
        margin-top: 1;
    }
    """
    BINDINGS = [
        ("escape", "save_and_exit", "Volver"),
        ("ctrl+s", "save_and_exit", "Guardar")
    ]

    def __init__(self, current_header):
        super().__init__()
        self.current_header = current_header
        self.figlet = FigletManager()
        self._debounce_timer = None
        
        # Cargar valores actuales desde la app
        self.header_text = getattr(self.app, "header_text", "Omega")
        self.header_font = getattr(self.app, "header_font", "slant")

    def compose(self) -> ComposeResult:
        yield Header()
        
        with Horizontal():
            # Panel Izquierdo: Opciones principales
            with Vertical(id="header-sidebar"):
                yield Label("[bold yellow]Header Style:[/]")
                with RadioSet(id="header-radios"):
                    for h in DB_HEADERS:
                        yield RadioButton(h.desc, id=f"h-{h.id}", value=(h.id == self.current_header))
                
                # Configurador Figlet (Solo visible si figlet_custom está activo)
                with Vertical(id="figlet-config"):
                    yield Label("\n[bold cyan]Figlet Settings:[/]")
                    yield Input(placeholder="Banner Text", value=self.header_text, id="figlet-text-input")
                    yield Label("[dim]Select Font:[/]")
                    with ListView(id="figlet-fonts-list"):
                        for font in self.figlet.get_fonts():
                            yield ListItem(Label(font), id=f"font-{font}")

            # Panel Derecho: Vista Previa
            with Vertical(id="header-preview-container"):
                yield Label("[bold green]Preview:[/]")
                yield Static("", id="header-preview-area")
        
        yield Footer()

    def on_mount(self) -> None:
        self.update_ui_visibility()
        # Seleccionar la fuente actual en la lista
        try:
            list_view = self.query_one("#figlet-fonts-list", ListView)
            for idx, item in enumerate(list_view.children):
                if item.id == f"font-{self.header_font}":
                    list_view.index = idx
                    break
        except Exception:
            pass
        self.update_preview()

    def update_ui_visibility(self) -> None:
        """Muestra u oculta los controles de Figlet según la selección."""
        try:
            is_figlet = self.query_one("#h-figlet_custom", RadioButton).value
            self.query_one("#figlet-config").display = is_figlet
        except Exception:
            pass

    @on(RadioSet.Changed)
    def on_header_changed(self, event: RadioSet.Changed) -> None:
        self.current_header = event.pressed.id.replace("h-", "")
        self.update_ui_visibility()
        self.update_preview()

    @on(Input.Changed, "#figlet-text-input")
    def on_text_changed(self, event: Input.Changed) -> None:
        self.header_text = event.value
        # Debounce: Cancelar timer anterior si existe
        if self._debounce_timer:
            self._debounce_timer.stop()
        # Crear nuevo timer de 300ms
        self._debounce_timer = self.set_timer(0.3, self.update_preview)

    @on(ListView.Selected, "#figlet-fonts-list")
    def on_font_selected(self, event: ListView.Selected) -> None:
        self.header_font = event.item.id.replace("font-", "")
        self.update_preview()

    def update_preview(self) -> None:
        preview_area = self.query_one("#header-preview-area")
        
        if self.current_header == "none":
            preview_area.update("[dim]No header selected[/]")
        elif self.current_header == "fastfetch":
            preview_area.update("[bold blue]System Info Panel[/]\n(Simulated Fastfetch)")
        elif self.current_header == "cow":
            preview_area.update(" < Moo >\n ------\n        \\   ^__^\n         \\  (oo)\\_______\n            (__)\\       )\\/\\\n                ||----w |\n                ||     ||")
        elif self.current_header == "figlet_custom":
            # Usar ancho real para la preview si es posible
            width = preview_area.size.width or 60
            art = self.figlet.render(self.header_text, self.header_font, width=width - 4)
            preview_area.update(art)

    def action_save_and_exit(self) -> None:
        # Guardar todo en la app principal
        if hasattr(self.app, "update_header_config"):
            self.app.update_header_config(
                self.current_header, 
                self.header_text, 
                self.header_font
            )
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
