from dataclasses import dataclass, field
from typing import Dict, List, Optional


@dataclass
class PluginDef:
    id: str
    desc: str
    category: str
    url: Optional[str] = None


@dataclass
class BinaryToolDef:
    id: str
    commands: List[str]
    packages: Dict[str, str] = field(default_factory=dict)
    supported_package_managers: List[str] | None = None

    def package_for(self, package_manager: str) -> str:
        return self.packages.get(package_manager, self.id)

    def supports(self, package_manager: str) -> bool:
        return self.supported_package_managers is None or package_manager in self.supported_package_managers


@dataclass
class ThemeDef:
    id: str
    desc: str
    path: Optional[str] = None


@dataclass
class HeaderDef:
    id: str
    desc: str


# --- EXTERNAL REPOS (GIT) ---
EXTERNAL_URLS: Dict[str, str] = {
    "zsh-autosuggestions": "https://github.com/zsh-users/zsh-autosuggestions.git",
    "zsh-syntax-highlighting": "https://github.com/zsh-users/zsh-syntax-highlighting.git",
    "fast-syntax-highlighting": "https://github.com/zdharma-continuum/fast-syntax-highlighting.git",
    "fzf-tab": "https://github.com/Aloxaf/fzf-tab.git",
    "zsh-completions": "https://github.com/zsh-users/zsh-completions.git",
    "you-should-use": "https://github.com/MichaelAquilina/zsh-you-should-use.git",
    "zsh-alias-finder": "https://github.com/akash329d/zsh-alias-finder.git",
    "powerlevel10k": "https://github.com/romkatv/powerlevel10k.git",
    "zsh-history-substring-search": "https://github.com/zsh-users/zsh-history-substring-search.git",
    "zsh-autopair": "https://github.com/hlissner/zsh-autopair.git",
    "k": "https://github.com/supercrabtree/k.git",
    "zsh-navigation-tools": "https://github.com/psprint/zsh-navigation-tools.git",
    "alias-tips": "https://github.com/djui/alias-tips.git",
}

# --- BINARY TOOLS (SYSTEM PACKAGES) ---
BIN_PLUGINS: List[str] = [
    "zoxide",
    "eza",
    "yazi",
    "fzf",
    "fd",
    "ripgrep",
    "duf",
    "ncdu",
    "procs",
    "jq",
    "httpie",
    "neofetch",
    "tldr",
    "lazygit",
    "glow",
    "chafa",
    "nano",
    "lolcat",
    "fastfetch",
    "figlet",
    "fortune",
    "cowsay",
]

BINARY_TOOLS: Dict[str, BinaryToolDef] = {
    tool_id: BinaryToolDef(tool_id, [tool_id]) for tool_id in BIN_PLUGINS
}
BINARY_TOOLS.update(
    {
        "bat": BinaryToolDef("bat", ["bat", "batcat"], {"apt": "bat", "nala": "bat"}),
        "fd": BinaryToolDef("fd", ["fd", "fdfind"], {"apt": "fd-find", "nala": "fd-find"}),
        "fortune": BinaryToolDef("fortune", ["fortune"], {"apt": "fortune-mod", "nala": "fortune-mod"}),
        "lolcat": BinaryToolDef("lolcat", ["lolcat"], supported_package_managers=["apt", "nala", "pkg"]),
        "ripgrep": BinaryToolDef("ripgrep", ["rg", "ripgrep"], {"apt": "ripgrep", "nala": "ripgrep"}),
        "httpie": BinaryToolDef("httpie", ["http", "httpie"], {"apt": "httpie", "nala": "httpie"}),
    }
)


def is_binary_tool(plugin_id: str) -> bool:
    return plugin_id in BINARY_TOOLS


def binary_commands(plugin_id: str) -> List[str]:
    tool = BINARY_TOOLS.get(plugin_id)
    return tool.commands if tool else [plugin_id]


def binary_package_name(plugin_id: str, package_manager: str) -> str:
    tool = BINARY_TOOLS.get(plugin_id)
    return tool.package_for(package_manager) if tool else plugin_id


def binary_supported(plugin_id: str, package_manager: str) -> bool:
    tool = BINARY_TOOLS.get(plugin_id)
    return tool.supports(package_manager) if tool else False


def unsupported_binary_tools(plugin_ids: List[str], package_manager: str) -> List[str]:
    return [plugin_id for plugin_id in plugin_ids if is_binary_tool(plugin_id) and not binary_supported(plugin_id, package_manager)]

# --- ALL PLUGINS LIST (UI DATA) ---
DB_PLUGINS: List[PluginDef] = [
    PluginDef(
        "zsh-autosuggestions",
        "Predice lo que escribes (Must Have)",
        "CORE",
        EXTERNAL_URLS["zsh-autosuggestions"],
    ),
    PluginDef(
        "zsh-syntax-highlighting",
        "Colores en tiempo real",
        "CORE",
        EXTERNAL_URLS["zsh-syntax-highlighting"],
    ),
    PluginDef(
        "fzf-tab", "Menú autocompletado visual", "CORE", EXTERNAL_URLS["fzf-tab"]
    ),
    PluginDef(
        "zsh-completions",
        "Más definiciones de tabulación",
        "CORE",
        EXTERNAL_URLS["zsh-completions"],
    ),
    PluginDef("command-not-found", "Sugiere paquetes faltantes", "SYS"),
    PluginDef(
        "zsh-history-substring-search",
        "Busca historial con Flecha Arriba",
        "NAV",
        EXTERNAL_URLS["zsh-history-substring-search"],
    ),
    PluginDef(
        "zsh-autopair",
        "Cierra paréntesis/comillas auto",
        "UX",
        EXTERNAL_URLS["zsh-autopair"],
    ),
    PluginDef("magic-enter", "Enter en vacío hace 'ls'", "UX"),
    PluginDef("fancy-ctrl-z", "Ctrl-Z minimiza y restaura", "UX"),
    PluginDef("k", "ls con esteroides y stats de git", "UI", EXTERNAL_URLS["k"]),
    PluginDef("per-directory-history", "Historial único por carpeta", "NAV"),
    PluginDef(
        "zsh-navigation-tools",
        "Interfaz visual (n-history, etc)",
        "UI",
        EXTERNAL_URLS["zsh-navigation-tools"],
    ),
    PluginDef(
        "alias-tips", "Te recuerda usar tus alias", "EDU", EXTERNAL_URLS["alias-tips"]
    ),
    PluginDef("zoxide", "El 'cd' inteligente (z)", "NAV"),
    PluginDef("eza", "El 'ls' moderno con iconos", "UI"),
    PluginDef("yazi", "Gestor de archivos TUI rápido", "NAV"),
    PluginDef("fzf", "Buscador difuso universal", "NAV"),
    PluginDef("fd", "Alternativa rápida a 'find'", "UTIL"),
    PluginDef("ripgrep", "Alternativa turbo a 'grep'", "UTIL"),
    PluginDef("duf", "Uso de disco visual (df)", "SYS"),
    PluginDef("ncdu", "Analizador de espacio interactivo", "SYS"),
    PluginDef("procs", "Monitor de procesos visual (ps)", "SYS"),
    PluginDef("tldr", "Manuales (man) simplificados", "DOC"),
    PluginDef("lazygit", "Interfaz visual para Git", "DEV"),
    PluginDef("glow", "Lector de Markdown en terminal", "DOC"),
    PluginDef("chafa", "Ver imágenes en la terminal", "IMG"),
    PluginDef("httpie", "Cliente HTTP (mejor que curl)", "WEB"),
    PluginDef("jq", "Procesador de JSON en terminal", "DEV"),
    PluginDef("neofetch", "Info del sistema clásica", "SYS"),
    PluginDef("lolcat", "Arcoiris para cualquier output", "FUN"),
    PluginDef("nano", "Editor de texto (Estándar en Android)", "EDIT"),
    PluginDef("extract", "Descomprime cualquier archivo", "UTIL"),
    PluginDef("web-search", "Googlear desde terminal", "WEB"),
    PluginDef("copypath", "Copiar ruta actual al clipboard", "CLIP"),
    PluginDef("copyfile", "Copiar contenido de archivo", "CLIP"),
    PluginDef("cp", "Copia con barra de progreso", "UTIL"),
    PluginDef("gitignore", "Genera .gitignore (gi)", "DEV"),
    PluginDef("history", "Alias útiles para historial", "SYS"),
    PluginDef("colored-man-pages", "Manuales con color", "DOC"),
    PluginDef("safe-paste", "Evita ejecución al pegar", "SEC"),
    PluginDef("sudo", "Doble ESC pone sudo/tsu", "UTIL"),
]

DB_ZSH_PLUGINS: List[PluginDef] = [plugin for plugin in DB_PLUGINS if not is_binary_tool(plugin.id)]
DB_BINARY_TOOLS: List[PluginDef] = [plugin for plugin in DB_PLUGINS if is_binary_tool(plugin.id)]
NATIVE_ZSH_PLUGIN_IDS = {"git"}


def known_plugin_ids(custom_plugin_ids: List[str] | None = None) -> set[str]:
    custom = set(custom_plugin_ids or [])
    return {plugin.id for plugin in DB_PLUGINS} | set(EXTERNAL_URLS) | set(BINARY_TOOLS) | NATIVE_ZSH_PLUGIN_IDS | custom


def unknown_plugin_ids(plugin_ids: List[str], custom_plugin_ids: List[str] | None = None) -> List[str]:
    known = known_plugin_ids(custom_plugin_ids)
    return [plugin_id for plugin_id in plugin_ids if plugin_id not in known]


def valid_selected_plugins(plugin_ids: List[str], custom_plugin_ids: List[str] | None = None) -> List[str]:
    known = known_plugin_ids(custom_plugin_ids)
    return [plugin_id for plugin_id in plugin_ids if plugin_id in known]


def selected_custom_plugin_ids(plugin_ids: List[str], custom_plugin_ids: List[str]) -> List[str]:
    custom = set(custom_plugin_ids)
    return [plugin_id for plugin_id in plugin_ids if plugin_id in custom]


STARTUP_IMPACT: Dict[str, str] = {
    "zsh-autosuggestions": "medium",
    "zsh-syntax-highlighting": "medium",
    "fast-syntax-highlighting": "medium",
    "fzf-tab": "medium",
    "zsh-completions": "medium",
    "zsh-navigation-tools": "high",
    "zsh-history-substring-search": "medium",
    "powerlevel10k": "high",
    "k": "medium",
    "zoxide": "low",
    "eza": "low",
    "yazi": "low",
    "fzf": "low",
    "fastfetch": "high",
    "neofetch": "high",
    "figlet": "medium",
    "cowsay": "medium",
    "lolcat": "medium",
}


def startup_impact(plugin_id: str) -> str:
    return STARTUP_IMPACT.get(plugin_id, "low")

THEMES_OMZ_BUILTIN: List[ThemeDef] = [
    ThemeDef("robbyrussell", "Clásico (Default)"),
    ThemeDef("agnoster", "Powerline Style"),
    ThemeDef("bira", "Doble línea"),
    ThemeDef("fox", "Simple"),
    ThemeDef("gentoo", "Gentoo Style"),
    ThemeDef("kphoen", "PHP Style"),
    ThemeDef("lambda", "Lambda"),
    ThemeDef("linuxonly", "Kernel Info"),
    ThemeDef("cloud", "Nubes"),
    ThemeDef("arrow", "Flecha"),
    ThemeDef("random", "Aleatorio"),
]

THEMES_ROOT: List[ThemeDef] = [
    ThemeDef("root_p10k_red", "Root (P10K Red)"),
    ThemeDef("root_warning", "Root (Simple Warning)"),
    ThemeDef("kali_red", "Kali Style (Red)"),
    ThemeDef("parrot_root", "Parrot OS Style"),
]

DB_HEADERS: List[HeaderDef] = [
    HeaderDef("fastfetch", "Info del Sistema (Moderno)"),
    HeaderDef("figlet", "Figlet: Banner Personalizado ✨"),
    HeaderDef("cowsay", "Vaca Sabia (Fortune)"),
    HeaderDef("none", "Ninguno (Limpio)"),
]
