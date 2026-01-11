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
from ..core.installer import PluginInstaller
from ..platforms.termux import TermuxPlatform
from ..platforms.debian import DebianPlatform

class OmegaApp(App):
    # ... (anterior código se mantiene igual en TITLE, SUBTITLE, etc)
    
    def run_installation(self, screen: InstallScreen):
        screen.write_log(">>> INITIALIZING OMEGA INSTALLER...")
        
        # 1. Initialize Tools
        installer = PluginInstaller(self.platform, self.context.home)
        
        # 2. Save State Persistence
        current_state = AppState(
            selected_plugins=self.selected_plugins,
            selected_theme=self.selected_theme,
            selected_root_theme=self.selected_root_theme,
            selected_header=self.selected_header
        )
        self.state_manager.save(current_state)
        screen.write_log("Configuration saved to ~/.omega-zsh/state.json")
        
        # 3. Prerequisites
        installer.ensure_omz(screen.write_log)
        screen.write_log("Updating Repositories...")
        self.platform.update_repos()
        
        # 4. Base System Tools
        for tool in self.platform.get_essential_tools():
            screen.write_log(f"Verifying Core Tool: {tool}")
            self.platform.install_package(tool, on_progress=screen.write_log)

        # 5. Install Selected Plugins (Dynamic: Binary or Git)
        screen.write_log("\n--- INSTALLING PLUGINS ---")
        installer.install_all(self.selected_plugins, screen.write_log)

        # 6. Install/Link Theme
        screen.write_log(f"\n--- CONFIGURING THEME: {self.selected_theme} ---")
        self._install_theme(self.selected_theme, screen)
            
        # 7. Generate Config
        screen.write_log("\n--- GENERATING FINAL CONFIG ---")
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