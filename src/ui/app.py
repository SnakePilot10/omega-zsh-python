from textual.app import App, ComposeResult
from textual.widgets import Header, Footer, Static, TabbedContent, TabPane
from textual.binding import Binding
from .screens import DashboardScreen, PluginSelectScreen, ThemeSelectScreen, InstallScreen
from ..core.context import SystemContext
from ..core.constants import THEMES_OMZ_BUILTIN, THEMES_ROOT, DB_PLUGINS
from ..core.generator import ConfigGenerator
from ..platforms.termux import TermuxPlatform
from ..platforms.debian import DebianPlatform
import threading
from pathlib import Path

class OmegaApp(App):
    TITLE = "Omega-ZSH"
    SUBTITLE = "Professional Shell Manager"
    CSS = """
    Screen {
        background: #1e222a;
    }
    TabbedContent {
        height: 1fr;
    }
    """

    BINDINGS = [
        Binding("d", "switch_tab('dash')", "Dashboard"),
        Binding("p", "push_screen('plugins')", "Plugins"),
        Binding("t", "push_screen('themes')", "Temas"),
        Binding("i", "start_install", "INSTALAR", show=True, priority=True),
        Binding("q", "quit", "Salir"),
    ]

    def __init__(self):
        super().__init__()
        self.context = SystemContext()
        self.generator = ConfigGenerator(Path(__file__).parent.parent.parent / "assets/templates")
        
        # Seleccionar plataforma
        if self.context.is_termux:
            self.platform = TermuxPlatform(use_nala=(self.context.package_manager_type == "nala"))
        else:
            self.platform = DebianPlatform(use_nala=(self.context.package_manager_type == "nala"))
            
        # Estado inicial
        self.selected_plugins = []
        self.selected_theme = "robbyrussell"
        self.selected_root_theme = "root_p10k_red"

    def compose(self) -> ComposeResult:
        yield Header()
        with TabbedContent(initial="dash"):
            with TabPane("Dashboard", id="dash"):
                yield DashboardScreen()
        yield Footer()

    def action_switch_tab(self, tab_id: str) -> None:
        self.query_one(TabbedContent).active = tab_id

    def action_push_screen(self, screen_type: str) -> None:
        if screen_type == "plugins":
            self.push_screen(PluginSelectScreen())
        elif screen_type == "themes":
            self.push_screen(ThemeSelectScreen(THEMES_OMZ_BUILTIN, self.selected_theme))

    def action_start_install(self) -> None:
        install_screen = InstallScreen()
        self.push_screen(install_screen)
        
        # Ejecutar instalación en un hilo aparte para no bloquear la UI
        threading.Thread(target=self.run_installation, args=(install_screen,), daemon=True).start()

    def run_installation(self, screen: InstallScreen):
        screen.write_log(">>> Iniciando instalación...")
        
        # 1. Actualizar repos
        screen.write_log("Actualizando repositorios...")
        self.platform.update_repos()
        
        # 2. Instalar herramientas base
        for tool in self.platform.get_essential_tools():
            screen.write_log(f"Verificando herramienta: {tool}")
            self.platform.install_package(tool, on_progress=screen.write_log)
            
        # 3. Generar Config
        screen.write_log("Generando .zshrc y archivos personales...")
        zshrc_path = self.context.home / ".zshrc"
        personal_path = self.context.home / ".omega-zsh/personal.zsh"
        custom_path = self.context.home / ".omega-zsh/custom.zsh"

        gen_context = {
            "version": "14.0",
            "is_termux": self.context.is_termux,
            "omz_dir": str(self.context.home / ".oh-my-zsh"),
            "user_theme": self.selected_theme,
            "root_theme": self.selected_root_theme,
            "plugins": self.selected_plugins,
            "active_tools": ["zoxide", "eza", "bat", "micro"],
            "personal_zsh": str(personal_path),
            "custom_zsh": str(custom_path),
            "header_cmd": 'fastfetch'
        }
        
        # Generar personal.zsh (Solo si no existe)
        self.generator.generate_personal_config(personal_path, {
            "extra_paths": ["/usr/local/bin", "$HOME/.cargo/bin"],
            "aliases": {"lg": "lazygit", "upd": "omega-update"}
        })

        if self.generator.generate_zshrc(zshrc_path, gen_context):
            screen.write_log("✅ .zshrc generado exitosamente.")
            self.generator.create_default_custom_zsh(custom_path)
        
        screen.write_log("\n¡Instalación completada!")
        screen.show_finish()

    def on_button_pressed(self, event):
        if event.button.id == "finish-btn":
            self.app.exit()
