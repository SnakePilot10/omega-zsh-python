import json
import logging
import re
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import List


@dataclass
class AppState:
    selected_plugins: List[str] = field(default_factory=list)
    selected_theme: str = "robbyrussell"
    selected_root_theme: str = "root_p10k_red"
    selected_header: str = "fastfetch"
    header_text: str = "Omega"
    header_font: str = "slant"


VALID_HEADERS = {"fastfetch", "figlet", "cowsay", "none"}


def _clean_string(value, default: str) -> str:
    return value.strip() if isinstance(value, str) and value.strip() else default


def _clean_plugins(value) -> List[str]:
    if isinstance(value, str):
        value = [value]
    if not isinstance(value, list):
        return []
    plugins = []
    seen = set()
    for plugin in value:
        if not isinstance(plugin, str):
            continue
        plugin_id = plugin.strip().lower()
        if len(plugin_id) >= 2 and plugin_id[0] == plugin_id[-1] and plugin_id[0] in {"'", '"'}:
            plugin_id = plugin_id[1:-1].strip()
        if not plugin_id or plugin_id in seen:
            continue
        plugins.append(plugin_id)
        seen.add(plugin_id)
    return plugins


def normalize_app_state(data) -> AppState:
    """Normalize untrusted JSON-like state data into a safe AppState."""
    defaults = AppState()
    if not isinstance(data, dict):
        return defaults

    selected_header = _clean_string(data.get("selected_header"), defaults.selected_header)
    if selected_header not in VALID_HEADERS:
        selected_header = defaults.selected_header

    return AppState(
        selected_plugins=_clean_plugins(data.get("selected_plugins", defaults.selected_plugins)),
        selected_theme=_clean_string(data.get("selected_theme"), defaults.selected_theme),
        selected_root_theme=_clean_string(
            data.get("selected_root_theme"),
            defaults.selected_root_theme,
        ),
        selected_header=selected_header,
        header_text=_clean_string(data.get("header_text"), defaults.header_text),
        header_font=_clean_string(data.get("header_font"), defaults.header_font),
    )


class StateManager:
    def __init__(self, config_dir: Path):
        self.config_path = config_dir / "state.json"
        self.zshrc_path = config_dir.parent / ".zshrc"  # ~/.zshrc

    def load(self) -> AppState:
        """Carga el estado desde JSON, o intenta importarlo de .zshrc."""
        # 1. Prioridad: Archivo de estado propio
        if self.config_path.exists():
            try:
                with open(self.config_path, "r", encoding="utf-8") as f:
                    data = json.load(f)
                return normalize_app_state(data)
            except Exception as e:
                logging.warning(
                    "No se pudo cargar state.json, usando .zshrc como fallback: %s", e
                )

        # 2. Fallback: Intentar leer el .zshrc existente
        return self._import_from_zshrc()

    def save(self, state: AppState):
        """Guarda el estado actual en JSON."""
        self.config_path.parent.mkdir(parents=True, exist_ok=True)
        temp_path = self.config_path.with_suffix(".tmp")
        clean_state = normalize_app_state(asdict(state))
        temp_path.write_text(
            json.dumps(asdict(clean_state), indent=4, ensure_ascii=False),
            encoding="utf-8",
        )
        temp_path.replace(self.config_path)

    def _import_from_zshrc(self) -> AppState:
        """Intenta adivinar la configuración leyendo el .zshrc."""
        state = AppState()
        if not self.zshrc_path.exists():
            return state

        try:
            # Leer con tolerancia a errores de caracteres
            with open(self.zshrc_path, "r", encoding="utf-8", errors="ignore") as f:
                content = f.read()

            # Detectar Tema (Buscamos la asignación del usuario, que suele estar en el 'else' o al final)
            # Estrategia: Buscar todas las asignaciones y tomar la última que no sea root, o usar lógica específica
            themes_found = re.findall(r'ZSH_THEME="([^"]+)"', content)
            for t in themes_found:
                if "root" in t:
                    state.selected_root_theme = t
                else:
                    state.selected_theme = t

            # Detectar Plugins (Mejorado para multiline)
            # Buscamos desde 'plugins=(' hasta el primer ')'
            plugins_match = re.search(r"plugins=\((.*?)\)", content, re.DOTALL)
            if plugins_match:
                raw_plugins = plugins_match.group(1)
                # Limpiar: Quitar saltos de linea, comentarios #..., y dividir por espacios
                cleaned = re.sub(r"#.*", "", raw_plugins)  # Quitar comentarios
                state.selected_plugins = cleaned.split()

            # Detectar Header (Heurística)
            if "fastfetch" in content:
                state.selected_header = "fastfetch"
            elif "figlet" in content:
                state.selected_header = "figlet"
            elif "cowsay" in content:
                state.selected_header = "cowsay"
            else:
                state.selected_header = "none"

        except Exception as e:
            logging.warning(f"No se pudo importar configuración de .zshrc: {e}")

        return normalize_app_state(asdict(state))
