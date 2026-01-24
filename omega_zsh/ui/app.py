from textual.app import App, ComposeResult
from textual.widgets import Header, Footer, TabbedContent, TabPane
from textual.binding import Binding
from pathlib import Path
import threading
import logging

from .screens import DashboardScreen, PluginSelectScreen, ThemeSelectScreen, HeaderSelectScreen, InstallScreen
from ..core.context import SystemContext
from ..core.constants import THEMES_OMZ_BUILTIN, THEMES_ROOT, DB_PLUGINS, BIN_PLUGINS, ThemeDef
from ..core.generator import ConfigGenerator
from ..core.state import StateManager, AppState
from ..core.installer import PluginInstaller
from ..core.figlet import FigletManager
from ..platforms.termux import TermuxPlatform
from ..platforms.debian import DebianPlatform

class OmegaApp(App):
    TITLE = "Omega-ZSH"
    SUBTITLE = "Elite Python Edition"
    CSS = """
    Screen {
        background: #1e2127;
    }
    TabbedContent {
        height: 1fr;
    }
    """

    BINDINGS = [
        Binding("d", "switch_tab('dash')", "Dashboard"),
        Binding("p", "config_plugins", "Plugins"),
        Binding("t", "config_themes", "Themes"),
        Binding("h", "config_header", "Header"),
        Binding("i", "start_install", "INSTALL", show=True, priority=True),
        Binding("q", "quit", "Quit"),
    ]

    def __init__(self):
        super().__init__()
        logging.info("Inicializando OmegaApp...")
        self.context = SystemContext()
        self.generator = ConfigGenerator(Path(__file__).parent.parent / "assets/templates")
        self.state_manager = StateManager(self.context.home / ".omega-zsh")
        
        # Seleccionar plataforma
        if self.context.is_termux:
            self.platform = TermuxPlatform(use_nala=(self.context.package_manager_type == "nala"))
        else:
            self.platform = DebianPlatform(use_nala=(self.context.package_manager_type == "nala"))
            
        # Cargar Estado Persistente
        try:
            loaded_state = self.state_manager.load()
            self.selected_plugins = loaded_state.selected_plugins
            self.selected_theme = loaded_state.selected_theme
            self.selected_root_theme = loaded_state.selected_root_theme
            self.selected_header = loaded_state.selected_header
            self.header_text = loaded_state.header_text
            self.header_font = loaded_state.header_font
            logging.info(f"Estado cargado: {len(self.selected_plugins)} plugins seleccionados.")
        except Exception as e:
            logging.error(f"Fallo al cargar estado: {e}")
            self.selected_plugins = []
            self.selected_theme = "robbyrussell"
            self.selected_header = "fastfetch"
            self.selected_root_theme = "root_p10k_red"
            self.header_text = "Omega"
            self.header_font = "slant"

    def compose(self) -> ComposeResult:
        logging.info("Renderizando interfaz principal (compose)")
        yield Header(show_clock=True)
        with TabbedContent(initial="dash"):
            with TabPane("Dashboard", id="dash"):
                yield DashboardScreen()
        yield Footer()

    def action_switch_tab(self, tab_id: str) -> None:
        self.query_one(TabbedContent).active = tab_id

    # --- MANEJADORES DE ACCIONES ---

    def action_config_plugins(self) -> None:
        screen = PluginSelectScreen(DB_PLUGINS, self.selected_plugins)
        self.push_screen(screen)

    def action_config_themes(self) -> None:
        # Cargar temas dinámicamente de assets
        custom_themes_path = Path(__file__).parent.parent / "assets/themes"
        custom_themes = []
        if custom_themes_path.exists():
            for f in custom_themes_path.glob("*.zsh-theme"):
                custom_themes.append(ThemeDef(f.stem, "Local Custom Theme"))
        
        all_themes = THEMES_OMZ_BUILTIN + custom_themes
        screen = ThemeSelectScreen(all_themes, self.selected_theme, "Select User Theme")
        self.push_screen(screen)

    def update_selected_plugins(self, new_plugins: list[str]):
        """Actualiza la lista de plugins seleccionados y guarda el estado."""
        self.selected_plugins = new_plugins
        self._auto_save_state()

    def update_selected_theme(self, new_theme: str):
        self.selected_theme = new_theme
        self._auto_save_state()
        self.notify(f"Tema '{new_theme}' guardado.\nVe a la pestaña [INSTALL] para aplicar.", title="Cambio Pendiente", timeout=4)

    def action_config_header(self) -> None:
        """Lanza la pantalla de configuración del header."""
        screen = HeaderSelectScreen(self.selected_header)
        self.push_screen(screen)

    def update_header_config(self, header_choice: str, header_text: str, header_font: str):
        """Actualiza la configuración del header basado en la elección del usuario."""
        self.selected_header = header_choice
        self.header_text = header_text
        self.header_font = header_font
        self._auto_save_state()
        self.notify(f"Configuración de Header actualizada.")

    def _auto_save_state(self):
        """Guarda el estado actual en disco (Auto-save)."""
        try:
            current_state = AppState(
                selected_plugins=self.selected_plugins,
                selected_theme=self.selected_theme,
                selected_root_theme=self.selected_root_theme,
                selected_header=self.selected_header,
                header_text=self.header_text,
                header_font=self.header_font
            )
            self.state_manager.save(current_state)
        except Exception as e:
            logging.warning(f"Fallo al guardar auto-save: {e}")

    # --- PROCESO DE INSTALACIÓN ---

    def action_start_install(self) -> None:
        install_screen = InstallScreen()
        self.push_screen(install_screen)
        # Hilo daemon para no bloquear la UI
        threading.Thread(target=self.run_installation, args=(install_screen,), daemon=True).start()

    def run_installation(self, screen: InstallScreen):
        try:
            screen.write_log(">>> INICIANDO INSTALADOR OMEGA...")
            
            # 1. Guardar Estado
            current_state = AppState(
                selected_plugins=self.selected_plugins,
                selected_theme=self.selected_theme,
                selected_root_theme=self.selected_root_theme,
                selected_header=self.selected_header,
                header_text=self.header_text,
                header_font=self.header_font
            )
            self.state_manager.save(current_state)
            screen.write_log("Configuración guardada en ~/.omega-zsh/state.json")
            
            # 2. Inicializar Instalador
            installer = PluginInstaller(self.platform, self.context.home)
            installer.ensure_omz(screen.write_log)
            
            screen.write_log("Actualizando Repositorios...")
            self.platform.update_repos()
            
            # 3. Herramientas Base
            for tool in self.platform.get_essential_tools():
                screen.write_log(f"Verificando: {tool}")
                self.platform.install_package(tool, on_progress=screen.write_log)

            # 4. Instalar Plugins (Binarios o Git)
            screen.write_log("\n--- INSTALANDO PLUGINS SELECCIONADOS ---")
            installer.install_all(self.selected_plugins, screen.write_log)

            # 5. Instalar/Enlazar Tema
            screen.write_log(f"\n--- CONFIGURANDO TEMA: {self.selected_theme} ---")
            self._install_theme(self.selected_theme, screen)
                
            # 6. Generar Configuración Final
            screen.write_log("\n--- GENERANDO .zshrc ---")
            zshrc_path = self.context.home / ".zshrc"
            personal_path = self.context.home / ".omega-zsh/personal.zsh"
            custom_path = self.context.home / ".omega-zsh/custom.zsh"

            # Filtrar binarios del array de plugins de OMZ
            omz_plugins_list = [p for p in self.selected_plugins if p not in BIN_PLUGINS]

            gen_context = {
                "version": "2.0.0",
                "is_termux": self.context.is_termux,
                "omz_dir": str(self.context.home / ".oh-my-zsh"),
                "user_theme": self.selected_theme,
                "root_theme": self.selected_root_theme,
                "plugins": omz_plugins_list,
                "active_tools": self.selected_plugins,
                "personal_zsh": str(personal_path),
                "custom_zsh": str(custom_path),
                "header_cmd": self.selected_header_cmd()
            }
            
            self.generator.generate_personal_config(personal_path, {
                "extra_paths": ["/usr/local/bin", "$HOME/.cargo/bin", "$HOME/.local/bin"],
                "aliases": {"lg": "lazygit", "upd": "omega-update"}
            })

            if self.generator.generate_zshrc(zshrc_path, gen_context):
                screen.write_log("✅ .zshrc generado exitosamente.")
                self.generator.create_default_custom_zsh(custom_path)
            
            screen.write_log("\n[bold green]¡INSTALACIÓN COMPLETADA![/]")
            screen.write_log("[bold yellow]⚠ IMPORTANTE: Reinicia tu terminal o ejecuta 'source ~/.zshrc' para ver los cambios.[/]")
            screen.show_finish()
            
        except Exception as e:
            logging.error(f"Error en hilo de instalación: {e}", exc_info=True)
            screen.write_log(f"\n[bold red]ERROR CRÍTICO: {e}[/]")
            screen.show_finish()

    def _install_theme(self, theme_name: str, screen: InstallScreen):
        import shutil
        builtin_ids = [t.id for t in THEMES_OMZ_BUILTIN]
        if theme_name in builtin_ids:
            return

        assets_dir = Path(__file__).parent.parent / "assets/themes"
        omz_custom_themes = self.context.home / ".oh-my-zsh/custom/themes"
        
        theme_file = f"{theme_name}.zsh-theme"
        src = assets_dir / theme_file
        dst = omz_custom_themes / theme_file
        
        if src.exists():
            try:
                omz_custom_themes.mkdir(parents=True, exist_ok=True)
                shutil.copy2(src, dst)
                screen.write_log(f"Tema enlazado: {theme_name}")
            except Exception as e:
                screen.write_log(f"Error copiando tema: {e}")
        else:
            screen.write_log(f"Advertencia: No se encontró el archivo del tema {theme_file}")

    def selected_header_cmd(self) -> str:
        h = self.selected_header
        if h == "fastfetch": return "fastfetch"
        if h == "cow": return 'fortune | cowsay | lolcat'
        if h == "none": return ""
        if h == "figlet_custom":
            # Usar el generador seguro que escapa los caracteres
            return FigletManager().generate_safe_command(self.header_text, self.header_font)
        return "fastfetch"

    def on_button_pressed(self, event):
        if event.button.id == "finish-btn":
            self.exit()