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
# Runner ASCII animado para tareas en background
run_with_spinner() {
    local msg=$1
    local cmd=$2
    local pid
    
    echo -ne "   $msg  [ - ]"
    
    # Ejecutar el comando en background
    eval "$cmd" &>/dev/null &
    pid=$!
    
    # Animación de hélice (Runner)
    local spin='|/-\'
    local i=0
    while kill -0 $pid 2>/dev/null; do
        i=$(( (i+1) % 4 ))
        # Retroceder 4 espacios para sobreescribir [ x ]
        echo -ne "\b\b\b\b[ ${spin:$i:1} ]"
        sleep 0.1
    done
    
    # Limpiar spinner y mostrar estado final
    echo -ne "\b\b\b\b${GREEN}${CHECK}${NC}\n"
    
    wait $pid || return 1
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
print_step 1 7 "Detectando entorno del sistema..."

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
    EXTRA_PACKAGES="figlet fastfetch fortune cowsay fzf zoxide eza"
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

# --- 4. INSTALACIÓN DE DEPENDENCIAS ---
print_step 2 7 "Asegurando dependencias del sistema..."

if [ "$OS_ID" != "unknown" ]; then
    if [ ${#PRE_INSTALL_ARRAY[@]} -gt 0 ]; then
        echo -e "   ${INFO} Actualizando índices de paquetes..."
        "${PRE_INSTALL_ARRAY[@]}" &>/dev/null || echo -e "   ${WARN} Fallo al actualizar índices."
    fi

    echo -e "   ${INFO} Instalando paquetes críticos..."
    "${PKG_MANAGER_ARRAY[@]}" $CORE_PACKAGES &>/dev/null
    
    ask_question "¿Deseas instalar herramientas estéticas adicionales? (figlet, lolcat, etc.)" "S/n"
    read -t 15 -n 1 opt_choice || opt_choice="s"
    echo ""

    if [[ $opt_choice =~ ^[SsYy]$ ]] || [ -z "$opt_choice" ]; then
        echo -e "   ${INFO} Instalando extras..."
        for pkg in $EXTRA_PACKAGES; do
            echo -ne "     + $pkg "
            "${PKG_MANAGER_ARRAY[@]}" "$pkg" &>/dev/null && echo -e "${GREEN}${CHECK}${NC}" || echo -e "${RED}${ERROR}${NC}"
        done
    fi
fi

# --- 5. LIMPIEZA DE CONFLICTOS ---
print_step 3 7 "Limpiando conflictos de entorno..."
CLEAN_CMD="true"
if command -v pip3 &> /dev/null; then
    if pip3 show lolcat &> /dev/null; then
        CLEAN_CMD="sudo pip3 uninstall -y lolcat &>/dev/null || pip3 uninstall -y lolcat &>/dev/null || true"
    fi
fi
run_with_spinner "Eliminando lolcat (Python) global" "$CLEAN_CMD"

# --- 6. ENTORNO VIRTUAL ---
print_step 4 7 "Configurando entorno virtual aislado (.venv)..."
PROJECT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
VENV_DIR="$PROJECT_DIR/.venv"

if [ -d "$VENV_DIR" ]; then
    rm -rf "$VENV_DIR"
fi

run_with_spinner "Creando venv con Python3" "python3 -m venv \"$VENV_DIR\""

# --- 7. INSTALACIÓN APP ---
print_step 5 7 "Instalando Omega-ZSH y dependencias de Python..."
run_with_spinner "Descargando dependencias de Python" "\"$VENV_DIR/bin/pip\" install --upgrade pip --quiet && \"$VENV_DIR/bin/pip\" install \"$PROJECT_DIR\" --quiet"

# --- 8. ACCESO GLOBAL ---
print_step 6 7 "Configurando acceso global (omega/oz)..."
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

# --- 9. CONFIGURACIÓN DE SHELL ---
print_step 7 7 "Finalización y configuración de Shell..."

CURRENT_SHELL=$(basename "$SHELL")
if [ "$CURRENT_SHELL" != "zsh" ]; then
    ask_question "¿Deseas establecer Zsh como tu shell predeterminada?" "S/n"
    read -t 15 -n 1 shell_choice || shell_choice="s"
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
echo -e "${CYAN}Escribe ${BOLD}'omega'${NC}${CYAN} para iniciar la interfaz visual.${NC}"

# Lanzar inmediatamente
if [ -f "$BIN_DEST/omega" ]; then
    export PATH="$PATH:$BIN_DEST"
    exec "$BIN_DEST/omega"
else
    exec "$VENV_DIR/bin/omega"
fi
