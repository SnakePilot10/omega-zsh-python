from textual.app import ComposeResult
from textual.screen import Screen
from textual.widgets import Header, Footer, Static, SelectionList, RadioSet, RadioButton, Label, Log, Button
from textual.containers import Container, Vertical, Horizontal
from textual.widgets.selection_list import Selection
from ..core.constants import DB_PLUGINS, THEMES_OMZ_BUILTIN, THEMES_ROOT

class DashboardScreen(Static):
    """Pantalla principal con el resumen de configuración."""
    def render(self) -> str:
        return "[bold blue]OMEGA-ZSH Python Edition[/bold blue]\n\n" \
               "Usa el menú inferior para configurar tu entorno.\n" \
               "Presiona [bold]i[/bold] para instalar los cambios."

class PluginSelectScreen(Screen):
    """Pantalla para seleccionar plugins."""
    BINDINGS = [("escape", "app.pop_screen", "Volver")]

    def compose(self) -> ComposeResult:
        yield Header()
        yield Label("Selecciona los Plugins que deseas instalar:")
        yield SelectionList[str](
            * [Selection(p.desc, p.id) for p in DB_PLUGINS]
        )
        yield Footer()

class ThemeSelectScreen(Screen):
    """Pantalla para seleccionar el tema de usuario."""
    BINDINGS = [("escape", "app.pop_screen", "Volver")]

    def __init__(self, themes, current_theme, title="Seleccionar Tema"):
        super().__init__()
        self.themes = themes
        self.current_theme = current_theme
        self.screen_title = title

    def compose(self) -> ComposeResult:
        yield Header()
        yield Label(self.screen_title)
        with Vertical(id="theme-list"):
            for theme in self.themes:
                yield RadioButton(theme.id, value=(theme.id == self.current_theme))
        yield Footer()

class InstallScreen(Screen):
    """Pantalla que muestra el progreso de la instalación."""
    def compose(self) -> ComposeResult:
        yield Header()
        yield Label("Instalando Omega-ZSH...")
        yield Log(id="install-log")
        yield Button("Finalizar", id="finish-btn", variant="success")
        yield Footer()

    def on_mount(self) -> None:
        self.query_one("#finish-btn").visible = False

    def write_log(self, message: str):
        self.query_one("#install-log").write_line(message)
        
    def show_finish(self):
        self.query_one("#finish-btn").visible = True
