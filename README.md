# ⚡ OMEGA-ZSH // Python Edition

[

![Python](https://img.shields.io/badge/Python-3.13%2B-ff006e?style=for-the-badge&logo=python)

](https://www.python.org/)
[

![Platform](https://img.shields.io/badge/Platform-Termux_%7C_Linux-00f5ff?style=for-the-badge)

](https://termux.dev/)
[

![Status](https://img.shields.io/badge/Status-Operativo-00ff9f?style=for-the-badge)

](https://github.com/SnakePilot10/omega-zsh-python)

> Gestor de shell Zsh con TUI interactiva. Controla plugins, temas y headers desde una interfaz visual sin editar `.zshrc` manualmente.

---

## Índice

1. [Arquitectura](#arquitectura)
2. [Instalación](#instalación)
3. [TUI — Interfaz Visual](#tui--interfaz-visual)
4. [CLI — Arsenal `oz`](#cli--arsenal-oz)
5. [Plugins](#plugins)
6. [Temas](#temas)
7. [Registro de Cambios](#registro-de-cambios)

---

## Arquitectura
omega-zsh-python/
├── omega_zsh/
│   ├── core/
│   │   ├── context.py      # Detección de entorno (Termux/Linux/Arch)
│   │   ├── generator.py    # Motor Jinja2 → genera .zshrc
│   │   ├── state.py        # Persistencia de configuración (JSON)
│   │   ├── installer.py    # Instalación de plugins y binarios
│   │   └── constants.py    # Definición de plugins, temas y headers
│   ├── ui/
│   │   ├── app.py          # Aplicación Textual principal
│   │   └── screens.py      # Pantallas: Dashboard, Plugins, Themes, Headers
│   ├── cli/
│   │   └── oz_tool.py      # Herramienta CLI oz
│   └── assets/
│       ├── templates/      # Plantillas Jinja2 (.zshrc.j2, personal.zsh.j2)
│       └── themes/         # Temas .zsh-theme God Tier
├── install.sh              # Instalador automático multi-distro
└── pyproject.toml
**Flujo de datos:**
TUI (Textual) → AppState → ConfigGenerator (Jinja2) → ~/.zshrc
---

## Instalación

```bash
git clone https://github.com/SnakePilot10/omega-zsh-python.git
cd omega-zsh-python
chmod +x install.sh
./install.sh
```

El instalador detecta automáticamente: Termux, Debian/Ubuntu, Arch Linux, Alpine y Fedora.
Auto-sanación: Si .venv está corrupto o la versión de Python cambió, el instalador lo recrea sin intervención manual.
Requisitos: python3, zsh, git, oh-my-zsh instalado previamente.
TUI — Interfaz Visual
omega
Tab
Función
Dashboard
Telemetría del sistema: OS, RAM, Disco, Uptime
Plugins
Activar/desactivar plugins OMZ y herramientas binarias
Themes
Selector con previsualización en vivo via subproceso zsh
Headers
Configurar banner de bienvenida: Fastfetch, Figlet, Cowsay, None
Atajos:
Tecla
Acción
a
Apply — genera .zshrc sin reinstalar paquetes
i
Install — instala paquetes faltantes + genera .zshrc
q
Salir
CLI — Arsenal oz
oz <comando>
Comando
Descripción
oz b
Banner — telemetría esencial del sistema
oz v
Velocidad — benchmark de latencia de arranque
oz p
Plugins — listado de módulos activos y sus alias
oz u
Update — sincronización con el repositorio
oz t
Themes — explorador de temas disponibles
oz s
Stats — análisis de patrones de uso
Plugins
Los plugins están divididos en dos categorías que el generador maneja por separado:
Plugins OMZ — van en plugins=() del .zshrc:
zsh-autosuggestions, zsh-syntax-highlighting, fzf-tab, zsh-completions, command-not-found, zsh-history-substring-search, magic-enter, fancy-ctrl-z, k, per-directory-history, zsh-navigation-tools, alias-tips, fzf, extract, web-search, copypath, copyfile, cp, gitignore, history, colored-man-pages, safe-paste
Herramientas binarias — instaladas vía gestor de paquetes, configuradas con alias:
zoxide, eza, yazi, fd, ripgrep, duf, ncdu, jq, httpie, tldr, lazygit, glow, chafa, lolcat, fastfetch, figlet, fortune, cowsay
Temas
Los temas God Tier se almacenan en omega_zsh/assets/themes/ y se enlazan automáticamente a ~/.oh-my-zsh/custom/themes/ al aplicar la configuración.
Tema
Estilo
bira_elegante
Art Deco — Royal Gold
bira_espacial
Space — Deep Purple
bira_futurista_neon
Cyberpunk — Neon
bira_gotico
Gothic — Dark
bira_matrix
Matrix — Green
bira_minimalista
Clean — Minimal
bira_naturaleza
Nature — Evergreen
bira_retro
Retro — Amber
catppuccin_block
Catppuccin Mocha
cyberpunk_block
Cyberpunk — Powerline
dracula_block
Dracula — Powerline
everforest_friendly
Everforest — True-color
gruvbox_block
Gruvbox — Powerline
kanagawa_block
Kanagawa — Powerline
monokai_block
Monokai — Powerline
nord_block
Nord — Powerline
rose_pine_block
Rosé Pine — Powerline
samsung_powerline
Samsung Blue/Red — Powerline (OMP port)
solarized_block
Solarized — Powerline
tokyo_block
Tokyo Night — Powerline
Registro de Cambios
2026-03-22 — Estabilización TUI:
context.py: restaurados atributos omega_dir, project_root, omz_dir, zshrc_path en SystemContext
app.py: sincronizado header_type → selected_header con AppState; corregido context_data con claves correctas del template Jinja2; filtrado de plugins OMZ vs binarios antes de generar .zshrc; auto-symlink de temas Omega a custom/themes
screens.py: reemplazado rich.Panel por Static (Textual); fix bin_plugins como lista de strings; IDs de ListItem por índice numérico; contexto OMZ inyectado en preview de temas; cowsay agregado como tipo de header
install.sh: renumeración de secciones (1–10); fix compatibilidad $? con set -e
2026-03-06 — Auto-Sanación y Fix CLI:
Bridge en __main__.py para separar ejecución CLI/TUI
Detección de corrupción en install.sh
Saneado 100% del código bajo reglas de Ruff
2026-03-05 — Migración Python 3.13:
Actualización de shebangs, reinstalación de dependencias en nuevo venv, corrección de rutas de fuentes figlet
# Entorno de desarrollo
python -m venv .venv && source .venv/bin/activate
pip install -e ".[dev]"
pytest --cov=omega_zsh   # Tests
ruff check .             # Linting
Copyright © 2026 SnakePilot10 · Janus & Tesavek ⚡
