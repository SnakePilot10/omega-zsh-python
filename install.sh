#!/usr/bin/env bash
set -e

# --- 0. CONFIGURACIÓN ESTÉTICA (COLORES) ---
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[0;33m'
BLUE='\033[0;34m'
MAGENTA='\033[0;35m'
CYAN='\033[0;36m'
BOLD='\033[1m'
NC='\033[0m' # No Color

# --- Iconos ---
CHECK="[ OK ]"
WARN="[WARN]"
ERROR="[FAIL]"
INFO="[INFO]"
STAR="***"

# --- 1. MANEJO DE INTERRUPCIONES ---
cleanup_and_exit() {
    echo -e "\n${RED}${ERROR}  Instalación interrumpida por el usuario. Saliendo...${NC}"
    pkill -P $$ || true
    exit 130
}
trap cleanup_and_exit SIGINT SIGTERM

# --- 2. FUNCIONES HELPERS ---
# Runner Neon Scanner (KITT Style) para tareas en background
run_with_spinner() {
    local msg=$1
    local cmd=$2
    local pid
    
    # Ocultar cursor
    tput civis 2>/dev/null || echo -ne "\033[?25l"
    
    echo -ne "   $msg  [    ]"
    
    # Ejecutar el comando en background
    eval "$cmd" &>/dev/null &
    pid=$!
    
    # Animación Neon Scanner
    local frames=("[=   ]" "[==  ]" "[ ===]" "[  ==]" "[   =]" "[  ==]" "[ ===]" "[==  ]")
    local i=0
    while kill -0 $pid 2>/dev/null; do
        echo -ne "\b\b\b\b\b\b${frames[$i]}"
        i=$(( (i+1) % 8 ))
        sleep 0.05
    done
    
    # Restaurar cursor
    tput cnorm 2>/dev/null || echo -ne "\033[?25h"
    
    # VERIFICACIÓN REAL DEL CÓDIGO DE SALIDA
    wait $pid
    local exit_code=$?
    
    if [ $exit_code -eq 0 ]; then
        echo -ne "\b\b\b\b\b\b${GREEN}${CHECK}${NC}\n"
        return 0
    else
        echo -ne "\b\b\b\b\b\b${RED}${ERROR}${NC}\n"
        return $exit_code
    fi
}

print_step() {
    local num=$1
    local total=$2
    local msg=$3
    echo -e "\n${BOLD}${BLUE}[$num/$total]${NC} ${CYAN}$msg${NC}"
}

ask_question() {
    local msg=$1
    local default=$2
    echo -ne "${BOLD}${YELLOW}>> $msg [$default]: ${NC}"
}

# --- 3. DETECCIÓN DE ENTORNO ---
print_step 1 9 "Detectando entorno del sistema..."
UPDATED=false

if [ -f "/etc/debian_version" ]; then
    OS_ID="debian"
    echo -e "   ${CHECK} Entorno detectado: ${BOLD}Debian/Ubuntu${NC}"
    PRE_INSTALL_ARRAY=(sudo apt-get update)
    PKG_MANAGER_ARRAY=(sudo apt-get install -y)
    CORE_PACKAGES="python3 python3-venv zsh git curl wget debianutils bc"
    EXTRA_PACKAGES="figlet fastfetch fortune-mod cowsay fzf zoxide lolcat eza"
elif [ -d "/data/data/com.termux" ] || [ -n "$TERMUX_VERSION" ]; then
    OS_ID="termux"
    echo -e "   ${CHECK} Entorno detectado: ${BOLD}Android (Termux)${NC}"
    PKG_MANAGER_ARRAY=(pkg install -y)
    CORE_PACKAGES="python zsh git curl wget debianutils bc"
    EXTRA_PACKAGES="figlet fastfetch fortune cowsay fzf zoxide lolcat eza ruby"
elif [ -f "/etc/arch-release" ]; then
    OS_ID="arch"
    echo -e "   ${CHECK} Entorno detectado: ${BOLD}Arch Linux${NC}"
    PKG_MANAGER_ARRAY=(sudo pacman -Sy --noconfirm --needed)
    CORE_PACKAGES="python zsh git curl wget which bc"
    EXTRA_PACKAGES="figlet fastfetch fortune-mod cowsay fzf zoxide lolcat eza"
else
    OS_ID="unknown"
    echo -e "   ${WARN} No se pudo detectar la distro automáticamente."
fi

# --- 4. ASEGURAR OH MY ZSH ---
print_step 2 9 "Asegurando motor Oh My Zsh..."
if [ ! -f "$HOME/.oh-my-zsh/oh-my-zsh.sh" ]; then
    # Si la carpeta existe pero el archivo no, es una instalación rota. Limpiar.
    if [ -d "$HOME/.oh-my-zsh" ]; then
        echo -e "   ${WARN} Detectada instalación de Oh My Zsh corrupta. Limpiando..."
        rm -rf "$HOME/.oh-my-zsh"
    fi
    
    # Verificar curl
    if ! command -v curl &>/dev/null; then
        echo -e "   ${INFO} Instalando curl temporalmente para bootstrap..."
        "${PKG_MANAGER_ARRAY[@]}" curl &>/dev/null
    fi

    run_with_spinner "Instalando Oh My Zsh (Bootstrap)" "RUNZSH=no KEEP_ZSHRC=yes sh -c \"\$(curl -fsSL https://raw.githubusercontent.com/ohmyzsh/ohmyzsh/master/tools/install.sh)\" --unattended"
else
    echo -e "   ${CHECK} Oh My Zsh ya está presente."
fi

# --- 5. INSTALACIÓN DE DEPENDENCIAS ---
print_step 3 9 "Asegurando dependencias del sistema..."

if [ "$OS_ID" != "unknown" ]; then
    # Verificar si ya tenemos los paquetes básicos instalados
    NEED_INSTALL=false
    for pkg in $CORE_PACKAGES; do
        if [ "$pkg" = "python3-venv" ] && [ "$OS_ID" = "debian" ]; then
            if ! dpkg -s python3-venv &>/dev/null; then NEED_INSTALL=true; break; fi
        elif ! command -v "$pkg" &>/dev/null && ! dpkg -s "$pkg" &>/dev/null && ! pacman -Qi "$pkg" &>/dev/null; then
            NEED_INSTALL=true
            break
        fi
    done

    if [ "$NEED_INSTALL" = true ]; then
        if [ ${#PRE_INSTALL_ARRAY[@]} -gt 0 ]; then
            echo -e "   ${INFO} Actualizando índices de paquetes..."
            "${PRE_INSTALL_ARRAY[@]}" &>/dev/null || echo -e "   ${WARN} Fallo al actualizar índices."
            UPDATED=true
        fi

        echo -e "   ${INFO} Instalando paquetes críticos..."
        "${PKG_MANAGER_ARRAY[@]}" $CORE_PACKAGES &>/dev/null
    else
        echo -e "   ${CHECK} Paquetes críticos ya instalados."
    fi
    
    # Preguntar por extras solo si no están instalados y no se ha declinado antes
    SKIP_EXTRAS_FLAG="$OMEGA_CONFIG_DIR/.skip_extras"
    MISSING_EXTRAS=""
    for pkg in $EXTRA_PACKAGES; do
        if ! command -v "$pkg" &>/dev/null && ! dpkg -s "$pkg" &>/dev/null && ! pacman -Qi "$pkg" &>/dev/null; then
            MISSING_EXTRAS="$MISSING_EXTRAS $pkg"
        fi
    done

    if [ -n "$MISSING_EXTRAS" ] && [ ! -f "$SKIP_EXTRAS_FLAG" ]; then
        echo -e "   ${INFO} Herramientas opcionales disponibles:${BOLD}${YELLOW}$MISSING_EXTRAS${NC}"
        ask_question "¿Deseas instalarlas ahora?" "S/n"
        read -n 1 opt_choice
        echo ""

        if [[ $opt_choice =~ ^[SsYy]$ ]] || [ -z "$opt_choice" ]; then
            # Forzar actualización si no se ha hecho
            if [ "$UPDATED" = false ] && [ ${#PRE_INSTALL_ARRAY[@]} -gt 0 ]; then
                echo -e "   ${INFO} Actualizando índices para asegurar extras..."
                "${PRE_INSTALL_ARRAY[@]}" &>/dev/null
                UPDATED=true
            fi

            echo -e "   ${INFO} Instalando extras..."
            for pkg in $EXTRA_PACKAGES; do
                if ! command -v "$pkg" &>/dev/null && ! dpkg -s "$pkg" &>/dev/null && ! pacman -Qi "$pkg" &>/dev/null; then
                    echo -ne "     + $pkg "
                    if "${PKG_MANAGER_ARRAY[@]}" "$pkg" &>/dev/null; then
                        echo -e "${GREEN}${CHECK}${NC}"
                    elif [ "$pkg" = "lolcat" ] && command -v gem &>/dev/null; then
                        # Fallback para lolcat via Ruby Gem (común en Termux)
                        gem install lolcat --no-document &>/dev/null && echo -e "${GREEN}${CHECK} (via gem)${NC}" || echo -e "${RED}${ERROR}${NC}"
                    else
                        echo -e "${RED}${ERROR}${NC}"
                    fi
                else
                    echo -e "     + $pkg [OK]"
                fi
            done
        else
            echo -e "   ${INFO} Declinado. No volveré a preguntar (puedes borrar $SKIP_EXTRAS_FLAG para resetear)."
            touch "$SKIP_EXTRAS_FLAG"
        fi
    elif [ -n "$MISSING_EXTRAS" ]; then
        echo -e "   ${INFO} Herramientas opcionales omitidas por elección previa."
    else
        echo -e "   ${CHECK} Herramientas adicionales ya instaladas."
    fi
fi

# --- 6. LIMPIEZA DE CONFLICTOS ---
print_step 4 9 "Limpiando conflictos de entorno..."
CLEAN_CMD="true"
if command -v pip3 &> /dev/null; then
    if pip3 show lolcat &> /dev/null; then
        CLEAN_CMD="sudo pip3 uninstall -y lolcat &>/dev/null || pip3 uninstall -y lolcat &>/dev/null || true"
    fi
fi
run_with_spinner "Eliminando lolcat (Python) global" "$CLEAN_CMD"

# --- 7. ENTORNO VIRTUAL ---
print_step 5 9 "Configurando entorno virtual aislado (.venv)..."
PROJECT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
VENV_DIR="$PROJECT_DIR/.venv"

VENV_VALID=true
if [ ! -d "$VENV_DIR" ] || [ ! -f "$VENV_DIR/bin/python" ] || [ ! -f "$VENV_DIR/bin/pip" ]; then
    VENV_VALID=false
fi

if [ "$VENV_VALID" = false ]; then
    if [ -d "$VENV_DIR" ]; then rm -rf "$VENV_DIR"; fi
    run_with_spinner "Creando venv con Python3" "python3 -m venv \"$VENV_DIR\""
else
    echo -e "   ${CHECK} Entorno virtual ya configurado."
fi

# --- 8. INSTALACIÓN APP ---
print_step 6 9 "Instalando Omega-ZSH y dependencias de Python..."
# Sistema de caché inteligente basado en Hash de pyproject.toml Y código fuente
ABS_PROJECT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
# Generar hash de pyproject.toml + archivos críticos de la app
CURR_HASH=$(cat "$ABS_PROJECT_DIR/pyproject.toml" "$ABS_PROJECT_DIR/omega_zsh/cli/oz_tool.py" 2>/dev/null | md5sum | cut -d' ' -f1)
LAST_HASH_FILE="$VENV_DIR/.last_install_hash"
LAST_HASH=$(cat "$LAST_HASH_FILE" 2>/dev/null || echo "")

if [ "$CURR_HASH" != "$LAST_HASH" ] || [ ! -f "$VENV_DIR/bin/omega" ] || [ ! -f "$VENV_DIR/bin/oz" ]; then
    run_with_spinner "Sincronizando código y dependencias" "\"$VENV_DIR/bin/pip\" install --upgrade pip --quiet && \"$VENV_DIR/bin/pip\" install -e \"$ABS_PROJECT_DIR\" --quiet"
    echo "$CURR_HASH" > "$LAST_HASH_FILE"
else
    echo -e "   ${CHECK} Código y dependencias ya sincronizados."
fi

# --- 9. DESCARGA DE PLUGINS Y TEMAS ZSH ---
print_step 7 9 "Sincronizando recursos de Zsh (Plugins/Temas)..."
run_with_spinner "Sincronizando repositorios y enlaces" "\"$VENV_DIR/bin/python\" -c \"
from omega_zsh.core.installer import PluginInstaller
from omega_zsh.platforms.debian import DebianPlatform
from omega_zsh.platforms.termux import TermuxPlatform
from omega_zsh.core.context import SystemContext
from omega_zsh.core.state import StateManager, AppState
from omega_zsh.core.constants import BIN_PLUGINS
from pathlib import Path
import os

ctx = SystemContext()
plat = TermuxPlatform() if ctx.is_termux else DebianPlatform()
inst = PluginInstaller(plat, Path.home())
sm = StateManager(ctx.omega_dir)

# Cargar estado real del usuario
try:
    state = sm.load()
    selected = state.selected_plugins
except Exception:
    # Fallback si no hay estado previo
    selected = ['zsh-autosuggestions', 'zsh-syntax-highlighting', 'fzf-tab', 'zsh-completions', 'k', 'alias-tips', 'zsh-history-substring-search']

# 1. Filtrar y descargar plugins (solo los que no son binarios)
bin_set = set(BIN_PLUGINS)
for p in selected:
    if p not in bin_set:
        inst.download_zsh_plugin(p)

# 2. Temas Omega (Symlinks)
custom_themes_dir = ctx.omz_dir / 'custom' / 'themes'
custom_themes_dir.mkdir(parents=True, exist_ok=True)
omega_themes_src = ctx.assets_dir / 'themes'

if omega_themes_src.exists():
    for tf in omega_themes_src.glob('*.zsh-theme'):
        link_path = custom_themes_dir / tf.name
        if os.path.lexists(link_path):
            os.unlink(link_path)
        os.symlink(tf, link_path)
\""

# --- 10. ACCESO GLOBAL ---
print_step 8 9 "Configurando acceso global (omega/oz)..."
if [ "$OS_ID" = "termux" ]; then
    BIN_DEST="/data/data/com.termux/files/usr/bin"
    SUDO_CMD=""
elif [ -w "/usr/local/bin" ]; then
    BIN_DEST="/usr/local/bin"
    SUDO_CMD=""
else
    BIN_DEST="$HOME/.local/bin"
    mkdir -p "$BIN_DEST"
    SUDO_CMD=""
fi

ln -sf "$VENV_DIR/bin/omega" "$BIN_DEST/omega" 2>/dev/null || $SUDO_CMD ln -sf "$VENV_DIR/bin/omega" "$BIN_DEST/omega"
ln -sf "$VENV_DIR/bin/oz" "$BIN_DEST/oz" 2>/dev/null || $SUDO_CMD ln -sf "$VENV_DIR/bin/oz" "$BIN_DEST/oz"
echo -e "   ${CHECK} Binarios en: ${BOLD}$BIN_DEST${NC}"

# --- 11. CONFIGURACIÓN DE SHELL ---
print_step 9 9 "Finalización y configuración de Shell..."

CURRENT_SHELL=$(basename "$SHELL")
if [ "$CURRENT_SHELL" != "zsh" ]; then
    ask_question "¿Deseas establecer Zsh como tu shell predeterminada?" "S/n"
    read -n 1 shell_choice
    echo ""
    
    if [[ $shell_choice =~ ^[SsYy]$ ]] || [ -z "$shell_choice" ]; then
        echo -e "   ${INFO} Cambiando shell predeterminada a Zsh..."
        if [ "$OS_ID" = "termux" ]; then
            chsh -s zsh
        else
            sudo chsh -s "$(which zsh)" "$USER" || chsh -s "$(which zsh)"
        fi
        echo -e "   ${CHECK} Shell cambiada. El cambio se aplicará en tu próxima sesión."
    fi
fi

echo -e "\n${BOLD}${GREEN}${STAR} ¡Instalación de Omega-ZSH completada con éxito! ${STAR}${NC}"

ask_question "¿Deseas iniciar la interfaz visual (omega) ahora?" "S/n"
read -n 1 launch_choice
echo ""

if [[ $launch_choice =~ ^[SsYy]$ ]] || [ -z "$launch_choice" ]; then
    # Lanzar inmediatamente
    if [ -f "$BIN_DEST/omega" ]; then
        export PATH="$PATH:$BIN_DEST"
        exec "$BIN_DEST/omega"
    else
        exec "$VENV_DIR/bin/omega"
    fi
else
    echo -e "${CYAN}Escribe ${BOLD}'omega'${NC}${CYAN} en cualquier momento para iniciar la interfaz visual.${NC}"
    exit 0
fi
