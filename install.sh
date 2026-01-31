#!/usr/bin/env bash
set -e

# Colores para output
RED='\033[0;31m'
GREEN='\033[0;32m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

echo -e "${BLUE}>>> Iniciando Instalador de Omega-ZSH (Python Edition)${NC}"

# --- 1. CONFIGURACIÓN DE DEPENDENCIAS DEL SISTEMA ---
PKG_MANAGER=""
PRE_INSTALL_CMD=""
PACKAGES=""

echo -e "${BLUE}>> Detectando entorno del sistema...${NC}"

if [ -d "/data/data/com.termux" ]; then
    echo -e "${GREEN}>> Entorno detectado: Android (Termux)${NC}"
    PKG_MANAGER="pkg install -y"
    PACKAGES="python zsh figlet fastfetch fortune cowsay git curl wget fzf zoxide eza debianutils"
elif [ -f "/etc/debian_version" ]; then
    echo -e "${GREEN}>> Entorno detectado: Debian/Ubuntu${NC}"
    PRE_INSTALL_CMD="sudo apt-get update"
    PKG_MANAGER="sudo apt-get install -y"
    PACKAGES="python3 python3-venv zsh figlet fastfetch fortune-mod cowsay git curl wget fzf zoxide lolcat eza debianutils"
elif [ -f "/etc/arch-release" ]; then
    echo -e "${GREEN}>> Entorno detectado: Arch Linux${NC}"
    PKG_MANAGER="sudo pacman -Sy --noconfirm --needed"
    PACKAGES="python zsh figlet fastfetch fortune-mod cowsay git curl wget fzf zoxide lolcat eza which"
elif [ -f "/etc/alpine-release" ]; then
    echo -e "${GREEN}>> Entorno detectado: Alpine Linux${NC}"
    PRE_INSTALL_CMD="sudo apk update"
    PKG_MANAGER="sudo apk add"
    PACKAGES="python3 py3-venv zsh figlet fastfetch fortune cowsay git curl wget fzf zoxide lolcat eza"
elif [ -f "/etc/fedora-release" ]; then
    echo -e "${GREEN}>> Entorno detectado: Fedora${NC}"
    PKG_MANAGER="sudo dnf install -y"
    PACKAGES="python3 python3-virtualenv zsh figlet fastfetch fortune-mod cowsay git curl wget fzf zoxide lolcat eza"
else
    echo -e "${RED}⚠️  No se pudo detectar la distro automáticamente.${NC}"
    echo "Se asumirá que las dependencias (zsh, python3, etc.) ya están instaladas."
fi

# --- 2. INSTALACIÓN DE DEPENDENCIAS DEL SISTEMA ---
# Si se detectó un gestor de paquetes, se ejecuta para asegurar que todo esté instalado.
if [ -n "$PKG_MANAGER" ]; then
    echo -e "${BLUE}>> Asegurando que todas las dependencias del sistema estén instaladas...${NC}"
    
    if [ -n "$PRE_INSTALL_CMD" ]; then
        echo -e "${BLUE}>> Actualizando índices de paquetes...${NC}"
        $PRE_INSTALL_CMD
    fi

    echo "Paquetes: $PACKAGES"
    $PKG_MANAGER $PACKAGES
    if [ $? -ne 0 ]; then
        echo -e "${RED}❌ Falló la instalación de dependencias del sistema. Revisa los errores del gestor de paquetes.${NC}"
        exit 1
    fi
fi

# --- 3. VERIFICACIÓN CRÍTICA DE DEPENDENCIAS ---
# Después de intentar instalar, verificamos que los comandos esenciales existan.
echo -e "${BLUE}>> Verificando la instalación de dependencias críticas...${NC}"
if ! command -v zsh &> /dev/null; then
    echo -e "${RED}❌ Error Crítico: El comando 'zsh' no se encontró después de la instalación.${NC}"
    echo -e "${RED}   Por favor, revisa los errores del gestor de paquetes más arriba.${NC}"
    exit 1
fi
if ! command -v python3 &> /dev/null; then
    echo -e "${RED}❌ Error Crítico: El comando 'python3' no se encontró después de la instalación.${NC}"
    echo -e "${RED}   Por favor, revisa los errores del gestor de paquetes más arriba.${NC}"
    exit 1
fi
if ! python3 -c "import venv" &> /dev/null; then
    echo -e "${RED}❌ Error Crítico: El módulo 'venv' de Python no está disponible.${NC}"
    echo -e "${RED}   El instalador intentó instalarlo pero falló. Revisa los errores del gestor de paquetes.${NC}"
    exit 1
fi
echo -e "${GREEN}>> Dependencias críticas verificadas con éxito.${NC}"

# --- 4. CREACIÓN DEL ENTORNO VIRTUAL ---
PROJECT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
VENV_DIR="$PROJECT_DIR/.venv"

# Si el directorio .venv existe pero está incompleto (p.ej. sin pip), se elimina para forzar su recreación.
if [ -d "$VENV_DIR" ] && [ ! -f "$VENV_DIR/bin/pip" ]; then
    echo -e "${BLUE}>> Entorno virtual (.venv) detectado pero está incompleto. Se recreará.${NC}"
    rm -rf "$VENV_DIR"
fi

if [ ! -d "$VENV_DIR" ]; then
    echo -e "${BLUE}>> Creando entorno virtual aislado (.venv)...${NC}"
    python3 -m venv "$VENV_DIR"
    if [ $? -ne 0 ]; then
        echo -e "${RED}❌ Falló la creación del entorno virtual.${NC}"
        echo "Asegúrate de tener permisos de escritura y el módulo venv instalado."
        exit 1
    fi
fi

# --- 4. INSTALACIÓN DE LA APLICACIÓN Y DEPENDENCIAS ---
echo -e "${BLUE}>> Instalando la aplicación y sus dependencias...${NC}"
"$VENV_DIR/bin/pip" install --upgrade pip --quiet
"$VENV_DIR/bin/pip" install "$PROJECT_DIR" --quiet

if [ $? -ne 0 ]; then
    echo -e "${RED}❌ Falló la instalación de Omega-ZSH.${NC}"
    exit 1
fi

# --- 5. CREAR ENLACES SIMBÓLICOS PARA ACCESO GLOBAL ---
echo -e "${BLUE}>> Creando enlaces simbólicos para 'omega' y 'oz'...${NC}"

# Definir directorio de destino para binarios
if [ -w "/usr/local/bin" ]; then
    BIN_DEST="/usr/local/bin"
    SUDO_CMD=""
elif command -v sudo &> /dev/null && sudo -n true 2>/dev/null; then
    BIN_DEST="/usr/local/bin"
    SUDO_CMD="sudo"
else
    # Fallback para usuarios sin root (como Termux estándar)
    BIN_DEST="$HOME/.local/bin"
    mkdir -p "$BIN_DEST"
    SUDO_CMD=""
    
    # Asegurarse de que el directorio esté en el PATH
    if [[ ":$PATH:" != *":$BIN_DEST:"* ]]; then
        echo -e "${BLUE}>> Agregando $BIN_DEST a tu PATH temporalmente...${NC}"
        export PATH="$BIN_DEST:$PATH"
    fi
fi

echo -e "${BLUE}>> Instalando binarios en $BIN_DEST...${NC}"
$SUDO_CMD ln -sf "$VENV_DIR/bin/omega" "$BIN_DEST/omega"
$SUDO_CMD ln -sf "$VENV_DIR/bin/oz" "$BIN_DEST/oz"

if [ $? -ne 0 ]; then
    echo -e "${RED}❌ Falló la creación de enlaces simbólicos.${NC}"
    echo -e "Intentando copia directa como último recurso..."
    cp "$VENV_DIR/bin/omega" "$BIN_DEST/omega" 2>/dev/null || true
    cp "$VENV_DIR/bin/oz" "$BIN_DEST/oz" 2>/dev/null || true
fi

# --- 6. FINALIZACIÓN ---
echo -e "${GREEN}>> ✅ ¡Instalación completada!${NC}"
echo -e "Ahora puedes ejecutar ${BLUE}'omega'${NC} o ${BLUE}'oz'${NC}."

# --- 7. CONFIGURAR ZSH COMO SHELL PREDETERMINADA ---
REAL_USER="${SUDO_USER:-$(whoami)}"

# Obtener la home del usuario real
if [ "$REAL_USER" = "root" ]; then
    REAL_HOME="/root"
elif [ -d "/data/data/com.termux" ]; then
    REAL_HOME="/data/data/com.termux/files/home"
else
    if [ "$(uname)" = "Linux" ]; then
         REAL_HOME=$(getent passwd "$REAL_USER" | cut -d: -f6 2>/dev/null || echo "$HOME")
    else
         REAL_HOME="$HOME"
    fi
fi

if command -v zsh &> /dev/null; then
    ZSH_PATH=$(which zsh)
    
    # En Termux no se usa chsh de la misma manera o no es necesario si ya se usa proot/login
    if [ -d "/data/data/com.termux" ]; then
        echo -e "${GREEN}>> Entorno Termux detectado. Asegúrate de que tu terminal inicie con zsh.${NC}"
    else
        CURRENT_SHELL=$(getent passwd "$REAL_USER" | cut -d: -f7 2>/dev/null || echo "$SHELL")
        if [ "$CURRENT_SHELL" != "$ZSH_PATH" ]; then
            echo -e "${BLUE}>> Intentando configurar Zsh como shell predeterminada...${NC}"
            if command -v chsh &> /dev/null; then
                if [ "$(id -u)" -eq 0 ]; then
                     chsh -s "$ZSH_PATH" "$REAL_USER"
                elif command -v sudo &> /dev/null; then
                     sudo chsh -s "$ZSH_PATH" "$REAL_USER"
                else
                     chsh -s "$ZSH_PATH" || echo -e "${RED}⚠️  Ejecuta: chsh -s $ZSH_PATH manualmente.${NC}"
                fi
            fi
        fi
    fi
else
    echo -e "${RED}❌ Zsh no está instalado.${NC}"
fi

# --- 8. VERIFICAR CONFIGURACIÓN INICIAL ---
# Si no existe .zshrc, sugerir correr omega
if [ ! -f "$REAL_HOME/.zshrc" ]; then
    echo -e "${BLUE}>> AVISO: No se detectó un archivo .zshrc.${NC}"
    echo -e "   Para generar tu configuración, ejecuta: ${GREEN}omega${NC}"
fi

# --- 9. FINALIZACIÓN Y LANZAMIENTO ---
# Si estamos en una terminal (stdout es TTY), lanzamos zsh ahora mismo.
if [ -t 1 ]; then
    echo -e "${BLUE}>> Cambiando a Zsh...${NC}"
    exec zsh -l
fi

