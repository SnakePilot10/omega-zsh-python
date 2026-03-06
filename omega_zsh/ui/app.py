import logging
import shutil
import threading
from pathlib import Path
from typing import Callable

from textual.app import App, ComposeResult
from textual.binding import Binding
from textual.widgets import Footer, Header, TabbedContent, TabPane

from ..core.constants import BIN_PLUGINS, DB_PLUGINS, THEMES_OMZ_BUILTIN, ThemeDef
from ..core.context import SystemContext
from ..core.figlet import FigletManager
from ..core.generator import ConfigGenerator
from ..core.installer import PluginInstaller
from ..core.state import AppState, StateManager
from ..platforms.debian import DebianPlatform
from ..platforms.termux import TermuxPlatform
from .screens import (
    DashboardScreen,
    HeaderSelectScreen,
    InstallScreen,
    PluginSelectScreen,
    ThemeSelectScreen,
)



class OmegaApp(App):
    TITLE = "Omega-ZSH"
    SUBTITLE = "Elite Python Edition"
    CSS = """
    Screen {
        background: #0d0221;
        color: #00ffff;
    }
    Header {
        background: #ff00ff;
        color: white;
        text-style: bold;
    }
    Footer {
        background: #0d0221;
        color: #39ff14;
    }
    TabbedContent {
        height: 1fr;
    }
    TabPane {
        padding: 1 2;
        background: #0d0221;
    }
    Tabs {
        background: #1a0a33;
        border: none;
    }
    Tabs > Underline {
        background: #ff00ff;
    }
    Tab {
        color: #00ffff;
    }
    Tab:hover {
        background: #2b0b52;
    }
    Tab.--active {
        background: #2b0b52;
        color: #39ff14;
    }
    #preview-area {
        height: 1fr;
        border: double #00ffff;
        background: #000000;
        padding: 1 2;
        margin: 1 0;
    }
    """

    BINDINGS = [
        Binding("q", "quit", "Exit"),
        Binding("a", "apply_changes", "Apply (Fast)"),
        Binding("i", "install_full", "Install (Complete)"),
    ]

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        logging.info("Inicializando OmegaApp...")
        self.context = SystemContext()

        # Determinar plataforma
        if self.context.os_type == "android":
            self.platform = TermuxPlatform()
        else:
            self.platform = DebianPlatform()

        # Configuración
        self.state_manager = StateManager(self.context.omega_dir)

        # Cargar estado previo
        try:
            self.state = self.state_manager.load()
            logging.info(
                f"Estado cargado: {len(self.state.selected_plugins)} plugins, {self.state.selected_theme} tema"
            )
        except Exception as e:
            logging.error(f"Fallo al cargar estado: {e}")
            self.state = AppState()

    def compose(self) -> ComposeResult:
        logging.info("Renderizando interfaz principal (compose)")
        yield Header()
        with TabbedContent():
            with TabPane("Dashboard", id="tab-dashboard"):
                yield DashboardScreen()
            with TabPane("Plugins", id="tab-plugins"):
                yield PluginSelectScreen(
                    all_plugins=DB_PLUGINS,
                    bin_plugins=BIN_PLUGINS,
                    selected_plugins=self.state.selected_plugins,
                )
            with TabPane("Themes", id="tab-themes"):
                yield ThemeSelectScreen(
                    all_themes=self._get_all_themes(),
                    selected_theme=self.state.selected_theme,
                )
            with TabPane("Headers", id="tab-headers"):
                yield HeaderSelectScreen(
                    selected_header=self.state.header_type,
                    header_text=self.state.header_text,
                    selected_font=self.state.header_font,
                )
        yield Footer()

    def _get_all_themes(self) -> list[ThemeDef]:
        """Escanea todos los directorios de temas posibles para construir el catálogo."""
        omega_themes = []
        omz_themes = []
        user_themes = []

        # 1. Temas de Omega (Assets locales)
        omega_dir = self.context.project_root / "omega_zsh" / "assets" / "themes"
        if omega_dir.exists():
            for f in omega_dir.glob("*.zsh-theme"):
                omega_themes.append(ThemeDef(f.stem, "Omega God Tier", str(f)))

        # 2. Temas incorporados de OMZ
        omz_builtin_dir = self.context.omz_dir / "themes"
        if omz_builtin_dir.exists():
            for f in omz_builtin_dir.glob("*.zsh-theme"):
                omz_themes.append(ThemeDef(f.stem, "Standard OMZ", str(f)))

        # 3. Temas personalizados del usuario
        user_custom_dir = self.context.omz_dir / "custom" / "themes"
        if user_custom_dir.exists():
            for f in user_custom_dir.glob("*.zsh-theme"):
                if f.stem not in THEMES_OMZ_BUILTIN:
                    user_themes.append(ThemeDef(f.stem, "User Custom", str(f)))

        # 4. Combinar todo en un mapa para unicidad (ID -> ThemeDef)
        themes_map = {}
        for t in omz_themes:
            themes_map[t.id] = t
        for t in user_themes:
            themes_map[t.id] = t
        for t in omega_themes:
            themes_map[t.id] = t  # Omega tiene prioridad máxima sobre IDs repetidos

        return sorted(themes_map.values(), key=lambda x: x.id.lower())

    # --- Acciones ---
    def action_switch_tab(self, tab_id: str) -> None:
        """Cambia programáticamente a un Tab por su ID."""
        try:
            self.query_one(TabbedContent).active = tab_id
        except Exception:
            logging.warning("No se pudo cambiar de tab: TabbedContent no encontrado.")

    def save_state(self) -> None:
        """Sincroniza el estado actual de la UI con el objeto AppState y el archivo JSON."""
        try:
            # Obtener plugins del widget
            try:
                plugin_screen = self.query_one(PluginSelectScreen)
                selected_plugins = plugin_screen.get_selected()
            except Exception:
                selected_plugins = self.state.selected_plugins

            # Obtener tema del widget
            try:
                theme_screen = self.query_one(ThemeSelectScreen)
                selected_theme = theme_screen.get_selected()
            except Exception:
                selected_theme = self.state.selected_theme

            # Obtener header del widget
            try:
                header_screen = self.query_one(HeaderSelectScreen)
                h_type, h_text, h_font = header_screen.get_selected()
            except Exception:
                h_type, h_text, h_font = (
                    self.state.header_type,
                    self.state.header_text,
                    self.state.header_font,
                )

            current_state = AppState(
                selected_plugins=selected_plugins,
                selected_theme=selected_theme,
                header_type=h_type,
                header_text=h_text,
                header_font=h_font,
            )
            self.state = current_state
            self.state_manager.save(current_state)
        except Exception as e:
            logging.warning(f"Fallo al guardar auto-save: {e}")

    def action_apply_changes(self) -> None:
        """Genera .zshrc sin reinstalar paquetes. Rápido."""
        self.save_state()
        try:
            generator = ConfigGenerator(
                self.context.project_root / "omega_zsh" / "assets" / "templates"
            )

            # Generar Header Figlet si es necesario
            header_cmd = ""
            if self.state.header_type == "figlet":
                header_cmd = FigletManager().generate_safe_command(
                    self.state.header_text, self.state.header_font
                )
            elif self.state.header_type == "fastfetch":
                header_cmd = "fastfetch"

            context_data = {
                "theme": self.state.selected_theme,
                "plugins": self.state.selected_plugins,
                "header_cmd": header_cmd,
                "project_root": str(self.context.project_root),
                "omega_dir": str(self.context.omega_dir),
            }

            if generator.generate_zshrc(self.context.zshrc_path, context_data):
                self.notify("Configuración actualizada con éxito (A).", severity="information")
                # Cerrar app tras éxito para que el usuario pueda probar el shell
                self.exit()
        except Exception as e:
            logging.error(f"Fallo en Apply: {e}", exc_info=True)
            self.notify(f"Error al aplicar: {e}", severity="error")

    def action_install_full(self) -> None:
        """Inicia el flujo de instalación completa (paquetes + config)."""
        self.save_state()
        self.push_screen(InstallScreen(), callback=self._handle_install_finished)

    def _handle_install_finished(self, success: bool) -> None:
        if success:
            # Una vez instalados los paquetes, aplicar la config
            self.action_apply_changes()
        else:
            self.notify("La instalación fue cancelada o falló.", severity="warning")

    # --- Worker de Instalación ---
    def run_installation(self, on_message: Callable) -> None:
        """Ejecuta el proceso de instalación en un hilo secundario."""
        threading.Thread(
            target=self._installation_worker, args=(on_message,), daemon=True
        ).start()

    def _installation_worker(self, on_message: Callable) -> None:
        try:
            # 1. Asegurar directorios
            on_message("Preparando directorios del sistema...")
            self.context.omega_dir.mkdir(parents=True, exist_ok=True)

            # 2. Instalar binarios faltantes
            installer = PluginInstaller(self.platform)
            current_state = AppState(
                selected_plugins=self.state.selected_plugins,
                selected_theme=self.state.selected_theme,
            )

            missing = installer.get_missing_binaries(current_state.selected_plugins)
            if missing:
                for plugin in missing:
                    on_message(f"Instalando binario: {plugin}...")
                    if installer.install_binary(plugin):
                        on_message(f"✅ {plugin} instalado correctamente.")
                    else:
                        on_message(f"❌ Error al instalar {plugin}.")

            # 3. Descargar plugins ZSH faltantes
            zsh_missing = installer.get_missing_zsh_plugins(current_state.selected_plugins)
            if zsh_missing:
                for plugin in zsh_missing:
                    on_message(f"Descargando plugin Zsh: {plugin}...")
                    if installer.download_zsh_plugin(plugin):
                        on_message(f"✅ {plugin} descargado.")
                    else:
                        on_message(f"❌ Error al descargar {plugin}.")

            on_message("Finalizando instalación...")
            self.call_from_thread(self._installation_complete, True)

        except Exception as e:
            logging.error(f"Error en hilo de instalación: {e}", exc_info=True)
            on_message(f"ERROR FATAL: {e}")
            self.call_from_thread(self._installation_complete, False)

    def _installation_complete(self, success: bool) -> None:
        screen = self.get_screen("InstallScreen")
        if screen:
            screen.on_installation_finished(success)



def main():
    app = OmegaApp()
    app.run()


if __name__ == "__main__":
    main()
