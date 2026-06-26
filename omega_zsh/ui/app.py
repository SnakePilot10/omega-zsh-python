import logging
from pathlib import Path

from textual.app import App, ComposeResult
from textual.binding import Binding
from textual.widgets import Footer, Header, TabbedContent, TabPane

from ..core.apply import apply_config, build_config_context, build_header_command, link_omega_themes
from ..core.constants import BIN_PLUGINS, DB_PLUGINS, THEMES_OMZ_BUILTIN, ThemeDef
from ..core.context import SystemContext
from ..core.state import AppState, StateManager, normalize_app_state
from .screens import (
    DashboardScreen,
    FirstRunScreen,
    HeaderSelectScreen,
    PluginSelectScreen,
    RecoveryScreen,
    ThemeSelectScreen,
)


class OmegaApp(App):
    TITLE = "Omega-ZSH"
    SUBTITLE = "Elite Python Edition"
    CSS = """
    Screen {
        background: #020408;
        color: #00f5ff;
    }
    Header {
        background: #ff006e;
        color: white;
        text-style: bold;
    }
    Footer {
        background: #020408;
        color: #00ff9f;
    }
    TabbedContent {
        height: 1fr;
    }
    TabPane {
        padding: 1 2;
        background: #020408;
    }
    Tabs {
        background: #060d14;
        border: none;
    }
    Tabs > Underline {
        background: #ff006e;
    }
    Tab {
        color: #00f5ff;
    }
    Tab:hover {
        background: #0d1f2d;
    }
    Tab.--active {
        background: #0d1f2d;
        color: #00ff9f;
    }
    #header-config-row {
        height: 14;
    }
    #header-type-col {
        width: 20;
    }
    #header-text-col {
        width: 1fr;
    }
    #font-list, #theme-list, #plugin-list {
        height: 1fr;
        border: solid #00f5ff;
    }
    #header-input {
        margin-bottom: 1;
    }
    #preview-area {
        height: 1fr;
        border: double #00f5ff;
        background: #000000;
        padding: 1 2;
        margin: 1 0;
    }
    #recovery-help {
        border: double #ff006e;
        padding: 1 2;
        margin-bottom: 1;
    }
    #recovery-actions {
        height: 3;
        margin-bottom: 1;
    }
    #recovery-actions Button {
        margin-right: 1;
    }
    #recovery-log {
        height: 1fr;
        border: solid #00f5ff;
        background: #000000;
    }
    #first-run-help {
        border: double #00f5ff;
        padding: 1 2;
        margin-bottom: 1;
    }
    #first-run-actions {
        height: 3;
    }
    #first-run-actions Button {
        margin-right: 1;
    }
    """

    BINDINGS = [
        Binding("q", "quit", "Exit"),
        Binding("a", "apply_changes", "Apply"),
        Binding("d,1", "switch_tab('tab-dashboard')", "Dashboard"),
        Binding("p,2", "switch_tab('tab-plugins')", "Plugins"),
        Binding("t,3", "switch_tab('tab-themes')", "Themes"),
        Binding("h,4", "switch_tab('tab-headers')", "Headers"),
        Binding("r,5", "switch_tab('tab-recovery')", "Recovery"),
        Binding("s,6", "switch_tab('tab-setup')", "Setup"),
    ]

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        logging.info("Inicializando OmegaApp...")
        self.context = SystemContext()
        self.state_manager = StateManager(self.context.omega_dir)

        try:
            self.state = self.state_manager.load()
            logging.info(
                "Estado cargado: %s plugins, %s tema",
                len(self.state.selected_plugins),
                self.state.selected_theme,
            )
        except Exception as e:
            logging.error("Fallo al cargar estado: %s", e)
            self.state = AppState()
        self.first_run = self._detect_first_run()

    def compose(self) -> ComposeResult:
        logging.info("Renderizando interfaz principal (compose)")
        yield Header()
        with TabbedContent():
            if self.first_run:
                with TabPane("Setup", id="tab-setup"):
                    yield FirstRunScreen(omz_found=self._omz_found())
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
                    selected_header=self.state.selected_header,
                    header_text=self.state.header_text,
                    selected_font=self.state.header_font,
                )
            with TabPane("Recovery", id="tab-recovery"):
                yield RecoveryScreen()
        yield Footer()

    def _detect_first_run(self) -> bool:
        """True when Omega has no saved state and no existing shell config to import."""
        try:
            state_exists = self.state_manager.config_path.exists()
        except Exception:
            state_exists = False
        try:
            zshrc_exists = self.context.zshrc_path.exists()
        except Exception:
            zshrc_exists = False
        return not state_exists and not zshrc_exists

    def _omz_found(self) -> bool:
        try:
            return (self.context.omz_dir / "oh-my-zsh.sh").exists()
        except Exception:
            return False

    def _get_all_themes(self) -> list[ThemeDef]:
        """Escanea todos los directorios de temas posibles para construir el catálogo."""
        omega_themes = []
        omz_themes = []
        user_themes = []
        builtin_theme_ids = {theme.id for theme in THEMES_OMZ_BUILTIN}

        omega_dir = Path(str(self.context.assets_dir / "themes"))
        if omega_dir.exists():
            for f in omega_dir.glob("*.zsh-theme"):
                omega_themes.append(ThemeDef(f.stem, "Omega God Tier", str(f)))

        omz_builtin_dir = self.context.omz_dir / "themes"
        if omz_builtin_dir.exists():
            for f in omz_builtin_dir.glob("*.zsh-theme"):
                omz_themes.append(ThemeDef(f.stem, "Standard OMZ", str(f)))

        user_custom_dir = self.context.omz_dir / "custom" / "themes"
        if user_custom_dir.exists():
            for f in user_custom_dir.glob("*.zsh-theme"):
                if f.stem not in builtin_theme_ids:
                    user_themes.append(ThemeDef(f.stem, "User Custom", str(f)))

        themes_map = {}
        for t in omz_themes:
            themes_map[t.id] = t
        for t in user_themes:
            themes_map[t.id] = t
        for t in omega_themes:
            themes_map[t.id] = t

        return sorted(themes_map.values(), key=lambda x: x.id.lower())

    def action_switch_tab(self, tab_id: str) -> None:
        """Cambia programáticamente a un Tab por su ID."""
        try:
            self.query_one(TabbedContent).active = tab_id
        except Exception:
            logging.warning("No se pudo cambiar de tab: %s", tab_id)

    def save_state(self) -> None:
        """Sincroniza el estado actual de la UI con AppState y el archivo JSON."""
        try:
            try:
                plugin_screen = self.query_one(PluginSelectScreen)
                selected_plugins = plugin_screen.get_selected()
            except Exception:
                selected_plugins = self.state.selected_plugins

            try:
                theme_screen = self.query_one(ThemeSelectScreen)
                selected_theme = theme_screen.get_selected()
            except Exception:
                selected_theme = self.state.selected_theme

            try:
                header_screen = self.query_one(HeaderSelectScreen)
                h_type, h_text, h_font = header_screen.get_selected()
            except Exception:
                h_type, h_text, h_font = (
                    self.state.selected_header,
                    self.state.header_text,
                    self.state.header_font,
                )

            current_state = AppState(
                selected_plugins=selected_plugins,
                allowed_custom_plugins=self.state.allowed_custom_plugins,
                selected_theme=selected_theme,
                selected_root_theme=self.state.selected_root_theme,
                selected_header=h_type,
                header_text=h_text,
                header_font=h_font,
            )
            self.state = normalize_app_state(current_state.__dict__)
            self.state_manager.save(self.state)
        except Exception as e:
            logging.warning("Fallo al guardar auto-save: %s", e)

    def action_apply_changes(self) -> None:
        """Genera .zshrc sin instalar paquetes."""
        self.save_state()
        result = apply_config(self.context, self.state)
        if result.ok:
            self.notify(result.message)
        else:
            logging.error("Fallo en Apply: %s", result.message)
            self.notify(result.message, severity="error")

    def action_first_run_minimal(self) -> None:
        """Persist a conservative first-run baseline without touching shell files."""
        self.state = normalize_app_state(
            {
                "selected_plugins": [],
                "allowed_custom_plugins": self.state.allowed_custom_plugins,
                "selected_theme": "robbyrussell",
                "selected_root_theme": self.state.selected_root_theme,
                "selected_header": "none",
                "header_text": self.state.header_text,
                "header_font": self.state.header_font,
            }
        )
        self.state_manager.save(self.state)
        self.notify("Safe minimal profile saved. Press Apply when ready.")


def main():
    app = OmegaApp()
    app.run()


if __name__ == "__main__":
    main()
