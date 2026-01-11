import json
import re
from pathlib import Path
from dataclasses import dataclass, field, asdict
from typing import List, Optional

@dataclass
class AppState:
    selected_plugins: List[str] = field(default_factory=list)
    selected_theme: str = "robbyrussell"
    selected_root_theme: str = "root_p10k_red"
    selected_header: str = "fastfetch"

class StateManager:
    def __init__(self, config_dir: Path):
        self.config_path = config_dir / "state.json"
        self.zshrc_path = config_dir.parent / ".zshrc" # ~/.zshrc

    def load(self) -> AppState:
        """Carga el estado desde JSON, o intenta importarlo de .zshrc."""
        # 1. Prioridad: Archivo de estado propio
        if self.config_path.exists():
            try:
                with open(self.config_path, "r") as f:
                    data = json.load(f)
                return AppState(**data)
            except Exception:
                pass # Si falla, fallback

        # 2. Fallback: Intentar leer el .zshrc existente
        return self._import_from_zshrc()

    def save(self, state: AppState):
        """Guarda el estado actual en JSON."""
        self.config_path.parent.mkdir(parents=True, exist_ok=True)
        with open(self.config_path, "w") as f:
            json.dump(asdict(state), f, indent=4)

    def _import_from_zshrc(self) -> AppState:
        """Intenta adivinar la configuración leyendo el .zshrc."""
        state = AppState()
        if not self.zshrc_path.exists():
            return state

        try:
            content = self.zshrc_path.read_text()
            
            # Detectar Tema
            theme_match = re.search(r'ZSH_THEME="([^"]+)"', content)
            if theme_match:
                theme = theme_match.group(1)
                if "root" in theme:
                    state.selected_root_theme = theme
                else:
                    state.selected_theme = theme

            # Detectar Plugins (Básico)
            plugins_match = re.search(r'plugins=\(([^)]+)\)', content, re.DOTALL)
            if plugins_match:
                plugins_str = plugins_match.group(1)
                # Limpiar saltos de línea y espacios
                state.selected_plugins = plugins_str.split()

            # Detectar Header (Heurística)
            if "fastfetch" in content: state.selected_header = "fastfetch"
            elif "figlet" in content: state.selected_header = "figlet_slant" # Aproximado
            elif "cowsay" in content: state.selected_header = "cow"
            
        except Exception:
            pass # Si falla el parsing, devolvemos default
            
        return state
