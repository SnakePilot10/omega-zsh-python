from textual.app import App, ComposeResult
from textual.widgets import Header, Footer, TabbedContent, TabPane
from textual.binding import Binding
from pathlib import Path
import threading

from .screens import DashboardScreen, PluginSelectScreen, ThemeSelectScreen, HeaderSelectScreen, InstallScreen
from ..core.context import SystemContext
from ..core.constants import THEMES_OMZ_BUILTIN, THEMES_ROOT, DB_PLUGINS, ThemeDef
from ..core.generator import ConfigGenerator
from ..core.state import StateManager, AppState
from ..platforms.termux import TermuxPlatform
from ..platforms.debian import DebianPlatform

class OmegaApp(App):
    TITLE = "Omega-ZSH"
    SUBTITLE = "Elite Python Edition"
    CSS = """
    Screen {
        background: #1e2127;
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
        self.context = SystemContext()
        self.generator = ConfigGenerator(Path(__file__).parent.parent.parent / "assets/templates")
        self.state_manager = StateManager(self.context.home / ".omega-zsh")
        
        if self.context.is_termux:
            self.platform = TermuxPlatform(use_nala=(self.context.package_manager_type == "nala"))
        else:
            self.platform = DebianPlatform(use_nala=(self.context.package_manager_type == "nala"))
            
        # Load State (Persistence)
        loaded_state = self.state_manager.load()
        self.selected_plugins = loaded_state.selected_plugins
        self.selected_theme = loaded_state.selected_theme
        self.selected_root_theme = loaded_state.selected_root_theme
        self.selected_header = loaded_state.selected_header

    def compose(self) -> ComposeResult:
        yield Header(show_clock=True)
        with TabbedContent(initial="dash"):
            with TabPane("Dashboard", id="dash"):
                yield DashboardScreen()
        yield Footer()

    def action_switch_tab(self, tab_id: str) -> None:
        self.query_one(TabbedContent).active = tab_id

    # --- ACTION HANDLERS WITH CALLBACKS ---

    def action_config_plugins(self) -> None:
        # Screen updates the list in-place via reference/callback logic in on_unmount
        # But to be safe with Textual flow, let's use the screen instance logic
        screen = PluginSelectScreen(DB_PLUGINS, self.selected_plugins)
        self.push_screen(screen) # La pantalla actualiza la lista "in-place" al desmontarse

    def action_config_themes(self) -> None:
        # 1. Load Custom Themes Dynamically
        custom_themes_path = Path(__file__).parent.parent.parent / "assets/themes"
        custom_themes = []
        if custom_themes_path.exists():
            for f in custom_themes_path.glob("*.zsh-theme"):
                theme_id = f.stem # filename without extension
                custom_themes.append(ThemeDef(theme_id, "Local Custom Theme"))
        
        all_themes = THEMES_OMZ_BUILTIN + custom_themes
        
        def set_theme(screen_ref):
            # Callback is tricky if screen is popped. 
            # We rely on the screen object updating a public attribute before pop.
            pass

        screen = ThemeSelectScreen(all_themes, self.selected_theme, "Select User Theme")
        # Override the on_unmount logic in the screen to call a setter on app? 
        # Easier: Define a callback wrapper.
        
        def on_theme_close(result):
            # Screen doesn't return result by default unless we use dismiss()
            # Let's inspect the screen instance if kept alive, but pop destroys it.
            # Better architecture: The screen should accept a callback function.
            pass
            
        # Hack for simple state management without complex callbacks:
        # The screen will have a reference to 'app' via 'self.app'
        # We will modify ThemeSelectScreen to update 'app.selected_theme' directly.
        self.push_screen(screen)

    def update_selected_theme(self, new_theme: str):
        self.selected_theme = new_theme
        self.notify(f"Theme set to: {new_theme}")

    def action_config_header(self) -> None:
        screen = HeaderSelectScreen(self.selected_header)
        self.push_screen(screen)

    def update_selected_header(self, new_header: str):
        self.selected_header = new_header
        self.notify(f"Header set to: {new_header}")

    # --- INSTALLATION LOGIC ---

    def action_start_install(self) -> None:
        install_screen = InstallScreen()
        self.push_screen(install_screen)
        threading.Thread(target=self.run_installation, args=(install_screen,), daemon=True).start()

    def run_installation(self, screen: InstallScreen):
        screen.write_log(">>> INITIALIZING OMEGA INSTALLER...")
        
        # Save State Persistence
        current_state = AppState(
            selected_plugins=self.selected_plugins,
            selected_theme=self.selected_theme,
            selected_root_theme=self.selected_root_theme,
            selected_header=self.selected_header
        )
        self.state_manager.save(current_state)
        screen.write_log("Configuration saved to ~/.omega-zsh/state.json")
        
        screen.write_log("Updating Repositories...")
        self.platform.update_repos()
        
        for tool in self.platform.get_essential_tools():
            screen.write_log(f"Installing Core Tool: {tool}")
            self.platform.install_package(tool, on_progress=screen.write_log)

        screen.write_log(f"Installing Theme: {self.selected_theme}")
        self._install_theme(self.selected_theme, screen)
            
        screen.write_log("Generating Configuration...")
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
            "active_tools": self.selected_plugins,
            "personal_zsh": str(personal_path),
            "custom_zsh": str(custom_path),
            "header_cmd": self.selected_header_cmd()
        }
        
        self.generator.generate_personal_config(personal_path, {
            "extra_paths": ["/usr/local/bin", "$HOME/.cargo/bin"],
            "aliases": {"lg": "lazygit", "upd": "omega-update"}
        })

        if self.generator.generate_zshrc(zshrc_path, gen_context):
            screen.write_log("✅ .zshrc successfully generated.")
            self.generator.create_default_custom_zsh(custom_path)
        
        screen.write_log("\n[bold green]INSTALLATION COMPLETE![/]")
        screen.show_finish()

    def _install_theme(self, theme_name: str, screen: InstallScreen):
        import shutil
        builtin_ids = [t.id for t in THEMES_OMZ_BUILTIN]
        if theme_name in builtin_ids:
            return

        assets_dir = Path(__file__).parent.parent.parent / "assets/themes"
        omz_custom_themes = self.context.home / ".oh-my-zsh/custom/themes"
        
        theme_file = f"{theme_name}.zsh-theme"
        src = assets_dir / theme_file
        dst = omz_custom_themes / theme_file
        
        if src.exists():
            try:
                omz_custom_themes.mkdir(parents=True, exist_ok=True)
                shutil.copy2(src, dst)
                screen.write_log(f"Linked Custom Theme: {theme_name}")
            except Exception as e:
                screen.write_log(f"Error copying theme: {e}")
        else:
            screen.write_log(f"Warning: Theme file {theme_file} not found in assets.")

    def selected_header_cmd(self) -> str:
        h = self.selected_header
        if h == "fastfetch": return "fastfetch"
        if h == "cow": return 'echo "Moo" | cowsay | lolcat'
        if h == "none": return ""
        if h.startswith("figlet_"):
            font = h.replace("figlet_", "")
            return f'figlet -f {font} "Termux" | lolcat'
        return "fastfetch"

    def on_button_pressed(self, event):
        if event.button.id == "finish-btn":
            self.exit()