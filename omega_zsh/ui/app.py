import logging
from importlib.metadata import PackageNotFoundError, version
from pathlib import Path
from typing import Any

from textual.app import App, ComposeResult
from textual.binding import Binding
from textual.widgets import Footer, Header, TabbedContent, TabPane

from ..core.constants import BIN_PLUGINS, DB_PLUGINS, THEMES_OMZ_BUILTIN, ThemeDef
from ..core.context import SystemContext
from ..core.figlet import FigletManager
from ..core.generator import ConfigGenerator
from ..core.manifest import record_managed_file, require_managed_or_absent
from ..core.state import AppState, StateManager, normalize_app_state
from .screens import (
    DashboardScreen,
    HeaderSelectScreen,
    PluginSelectScreen,
    RecoveryScreen,
    ThemeSelectScreen,
)


def get_app_version() -> str:
    try:
        return version("omega-zsh")
    except PackageNotFoundError:
        return "dev"


def build_header_command(state: AppState) -> str:
    if state.selected_header == "figlet":
        return FigletManager().generate_safe_command(state.header_text, state.header_font)
    if state.selected_header == "fastfetch":
        return "(( $+commands[fastfetch] )) && fastfetch"
    if state.selected_header == "cowsay":
        return "(( $+commands[cowsay] )) && cowsay Omega-ZSH"
    return ""


def build_config_context(context: SystemContext, state: AppState) -> dict[str, Any]:
    bin_set = set(BIN_PLUGINS)
    return {
        "version": get_app_version(),
        "omz_dir": str(context.omz_dir),
        "user_theme": state.selected_theme,
        "root_theme": state.selected_root_theme,
        "plugins": [p for p in state.selected_plugins if p not in bin_set],
        "header_cmd": build_header_command(state),
        "is_termux": context.is_termux,
        "active_tools": [p for p in state.selected_plugins if p in bin_set],
        "default_user": "",
        "personal_zsh": str(context.home / ".omega-zsh" / "personal.zsh"),
        "custom_zsh": str(context.home / ".omega-zsh" / "custom.zsh"),
    }


def link_omega_themes(assets_dir: Path, omz_dir: Path, manifest_path: Path | None = None) -> None:
    omega_themes_dir = assets_dir / "themes"
    if not omega_themes_dir.exists():
        return

    custom_themes = omz_dir / "custom" / "themes"
    custom_themes.mkdir(parents=True, exist_ok=True)

    for theme_file in omega_themes_dir.glob("*.zsh-theme"):
        link = custom_themes / theme_file.name
        metadata = {"source": str(theme_file)}
        try:
            if manifest_path and not require_managed_or_absent(
                manifest_path,
                link,
                "theme_symlink",
                metadata,
            ):
                logging.warning("Tema existente no gestionado por Omega; se omite: %s", link)
                continue
            if link.is_symlink():
                if link.resolve(strict=False) == theme_file.resolve(strict=False):
                    if manifest_path:
                        record_managed_file(
                            manifest_path,
                            link,
                            "theme_symlink",
                            "verified",
                            metadata,
                        )
                    continue
                link.unlink()
            link.symlink_to(theme_file)
            if manifest_path:
                record_managed_file(
                    manifest_path,
                    link,
                    "theme_symlink",
                    "created",
                    metadata,
                )
        except Exception as e:
            logging.warning("No se pudo crear symlink para %s: %s", theme_file.name, e)


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
    """

    BINDINGS = [
        Binding("q", "quit", "Exit"),
        Binding("a", "apply_changes", "Apply"),
        Binding("d,1", "switch_tab('tab-dashboard')", "Dashboard"),
        Binding("p,2", "switch_tab('tab-plugins')", "Plugins"),
        Binding("t,3", "switch_tab('tab-themes')", "Themes"),
        Binding("h,4", "switch_tab('tab-headers')", "Headers"),
        Binding("r,5", "switch_tab('tab-recovery')", "Recovery"),
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
                    selected_header=self.state.selected_header,
                    header_text=self.state.header_text,
                    selected_font=self.state.header_font,
                )
            with TabPane("Recovery", id="tab-recovery"):
                yield RecoveryScreen()
        yield Footer()

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
        try:
            generator = ConfigGenerator(self.context.assets_dir / "templates")
            link_omega_themes(
                self.context.assets_dir,
                self.context.omz_dir,
                self.context.omega_dir / "manifest.json",
            )
            context_data = build_config_context(self.context, self.state)

            if generator.generate_zshrc(self.context.zshrc_path, context_data):
                self.notify("Configuración actualizada con éxito.")
            else:
                self.notify(
                    "Error al generar .zshrc. Revisa el log para detalles.",
                    severity="error",
                )
        except Exception as e:
            logging.error("Fallo en Apply: %s", e, exc_info=True)
            self.notify(f"Error al aplicar: {e}", severity="error")


def main():
    app = OmegaApp()
    app.run()


if __name__ == "__main__":
    main()
