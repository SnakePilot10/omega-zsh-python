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

# --- DATA ---
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

BIN_PLUGINS: List[str] = [
    "zoxide", "eza", "bat", "yazi", "fd", "ripgrep", "duf", "ncdu", "procs", 
    "jq", "httpie", "neofetch", "tldr", "lazygit", "glow", "chafa", "micro", 
    "lolcat", "fastfetch", "figlet", "fortune", "cowsay", "nala",
]

DB_PLUGINS: List[PluginDef] = [
    PluginDef("zsh-autosuggestions", "Predice lo que escribes (Must Have)", "CORE", EXTERNAL_URLS["zsh-autosuggestions"]),
    PluginDef("zsh-syntax-highlighting", "Colores en tiempo real", "CORE", EXTERNAL_URLS["zsh-syntax-highlighting"]),
    PluginDef("fzf-tab", "Menú autocompletado visual", "CORE", EXTERNAL_URLS["fzf-tab"]),
    PluginDef("zsh-completions", "Más definiciones de tabulación", "CORE", EXTERNAL_URLS["zsh-completions"]),
    PluginDef("zsh-history-substring-search", "Busca historial con Flecha Arriba", "NAV", EXTERNAL_URLS["zsh-history-substring-search"]),
    PluginDef("zsh-autopair", "Cierra paréntesis/comillas auto", "UX", EXTERNAL_URLS["zsh-autopair"]),
    PluginDef("zoxide", "El 'cd' inteligente (z)", "NAV"),
    PluginDef("eza", "El 'ls' moderno con iconos", "UI"),
    PluginDef("bat", "El 'cat' con alas y colores", "UI"),
    PluginDef("yazi", "Gestor de archivos TUI rápido", "NAV"),
    PluginDef("fzf", "Buscador difuso universal", "NAV"),
    PluginDef("fd", "Alternativa rápida a 'find'", "UTIL"),
    PluginDef("ripgrep", "Alternativa turbo a 'grep'", "UTIL"),
    PluginDef("nala", "Frontend moderno para APT", "SYS"),
    PluginDef("tldr", "Manuales (man) simplificados", "DOC"),
    PluginDef("lazygit", "Interfaz visual para Git", "DEV"),
    PluginDef("micro", "Editor de texto amigable (vs nano)", "EDIT"),
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
    ThemeDef("cloud", "Nubes"),
    ThemeDef("arrow", "Flecha"),
    ThemeDef("random", "Aleatorio"),
]

THEMES_ROOT: List[ThemeDef] = [
    ThemeDef("root_p10k_red", "Root (P10K Red)"),
    ThemeDef("root_warning", "Root (Simple Warning)"),
    ThemeDef("kali_red", "Kali Style (Red)"),
]

DB_HEADERS: List[HeaderDef] = [
    HeaderDef("fastfetch", "Info del Sistema (Moderno)"),
    HeaderDef("figlet_slant", "Figlet: Slant (Dinámico)"),
    HeaderDef("figlet_standard", "Figlet: Standard (Clásico)"),
    HeaderDef("cow", "Vaca Sabia (Fortune)"),
    HeaderDef("none", "Ninguno (Limpio)"),
]
