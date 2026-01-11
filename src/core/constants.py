from typing import List, Dict, Optional
from dataclasses import dataclass

@dataclass
class PluginDef:
    id: str
    desc: str
    category: str
    url: Optional[str] = None

@dataclass
class ThemeDef:
    id: str
    desc: str

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
    "zoxide", "eza", "bat", "yazi", "fd", "ripgrep", "duf", "ncdu", "procs", 
    "jq", "httpie", "neofetch", "tldr", "lazygit", "glow", "chafa", "micro", 
    "lolcat", "fastfetch", "figlet", "fortune", "cowsay", "nala",
]

# --- ALL PLUGINS LIST (UI DATA) ---
DB_PLUGINS: List[PluginDef] = [
    PluginDef("zsh-autosuggestions", "Predice lo que escribes (Must Have)", "CORE", EXTERNAL_URLS["zsh-autosuggestions"]),
    PluginDef("zsh-syntax-highlighting", "Colores en tiempo real", "CORE", EXTERNAL_URLS["zsh-syntax-highlighting"]),
    PluginDef("fzf-tab", "Menú autocompletado visual", "CORE", EXTERNAL_URLS["fzf-tab"]),
    PluginDef("zsh-completions", "Más definiciones de tabulación", "CORE", EXTERNAL_URLS["zsh-completions"]),
    PluginDef("command-not-found", "Sugiere paquetes faltantes", "SYS"),
    PluginDef("zsh-history-substring-search", "Busca historial con Flecha Arriba", "NAV", EXTERNAL_URLS["zsh-history-substring-search"]),
    PluginDef("zsh-autopair", "Cierra paréntesis/comillas auto", "UX", EXTERNAL_URLS["zsh-autopair"]),
    PluginDef("magic-enter", "Enter en vacío hace 'ls'", "UX"),
    PluginDef("fancy-ctrl-z", "Ctrl-Z minimiza y restaura", "UX"),
    PluginDef("k", "ls con esteroides y stats de git", "UI", EXTERNAL_URLS["k"]),
    PluginDef("per-directory-history", "Historial único por carpeta", "NAV"),
    PluginDef("zsh-navigation-tools", "Interfaz visual (n-history, etc)", "UI", EXTERNAL_URLS["zsh-navigation-tools"]),
    PluginDef("alias-tips", "Te recuerda usar tus alias", "EDU", EXTERNAL_URLS["alias-tips"]),
    PluginDef("zoxide", "El 'cd' inteligente (z)", "NAV"),
    PluginDef("eza", "El 'ls' moderno con iconos", "UI"),
    PluginDef("bat", "El 'cat' con alas y colores", "UI"),
    PluginDef("yazi", "Gestor de archivos TUI rápido", "NAV"),
    PluginDef("fzf", "Buscador difuso universal", "NAV"),
    PluginDef("fd", "Alternativa rápida a 'find'", "UTIL"),
    PluginDef("ripgrep", "Alternativa turbo a 'grep'", "UTIL"),
    PluginDef("duf", "Uso de disco visual (df)", "SYS"),
    PluginDef("ncdu", "Analizador de espacio interactivo", "SYS"),
    PluginDef("procs", "Monitor de procesos visual (ps)", "SYS"),
    PluginDef("nala", "Frontend moderno para APT", "SYS"),
    PluginDef("tldr", "Manuales (man) simplificados", "DOC"),
    PluginDef("lazygit", "Interfaz visual para Git", "DEV"),
    PluginDef("glow", "Lector de Markdown en terminal", "DOC"),
    PluginDef("chafa", "Ver imágenes en la terminal", "IMG"),
    PluginDef("httpie", "Cliente HTTP (mejor que curl)", "WEB"),
    PluginDef("jq", "Procesador de JSON en terminal", "DEV"),
    PluginDef("neofetch", "Info del sistema clásica", "SYS"),
    PluginDef("lolcat", "Arcoiris para cualquier output", "FUN"),
    PluginDef("micro", "Editor de texto amigable (vs nano)", "EDIT"),
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
    HeaderDef("figlet_slant", "Figlet: Slant (Dinámico)"),
    HeaderDef("figlet_standard", "Figlet: Standard (Clásico)"),
    HeaderDef("figlet_big", "Figlet: Big (Grande)"),
    HeaderDef("figlet_banner", "Figlet: Banner (Gigante)"),
    HeaderDef("figlet_digital", "Figlet: Digital (Retro)"),
    HeaderDef("figlet_shadow", "Figlet: Shadow (Con Sombra)"),
    HeaderDef("figlet_small", "Figlet: Small (Pequeño)"),
    HeaderDef("cow", "Vaca Sabia (Fortune)"),
    HeaderDef("none", "Ninguno (Limpio)"),
]