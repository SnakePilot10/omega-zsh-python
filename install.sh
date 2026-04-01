#!/usr/bin/env bash
set -e

# Colores para output
RED='\033[0;31m'
GREEN='\033[0;32m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

echo -e "${BLUE}>>> Iniciando Instalador de Omega-ZSH (Python Edition)${NC}"

# --- 1. CONFIGURACIÓN DE DEPENDENCIAS DEL SISTEMA ---
declare -a PKG_MANAGER_ARRAY
declare -a PRE_INSTALL_ARRAY
PACKAGES=""

echo -e "${BLUE}>> Detectando entorno del sistema...${NC}"

if [ -f "/etc/debian_version" ]; then
    echo -e "${GREEN}>> Entorno detectado: Debian/Ubuntu${NC}"
    PRE_INSTALL_ARRAY=(sudo apt-get update)
    PKG_MANAGER_ARRAY=(sudo apt-get install -y)
    # python3-venv es CRÍTICO en Ubuntu para que python3 -m venv funcione
    CORE_PACKAGES="python3 python3-venv zsh git curl wget debianutils"
    EXTRA_PACKAGES="figlet fastfetch fortune-mod cowsay fzf zoxide lolcat eza"
elif [ -d "/data/data/com.termux" ] || [ -n "$TERMUX_VERSION" ]; then
    echo -e "${GREEN}>> Entorno detectado: Android (Termux)${NC}"
    PKG_MANAGER_ARRAY=(pkg install -y)
    CORE_PACKAGES="python zsh git curl wget debianutils"
    EXTRA_PACKAGES="figlet fastfetch fortune cowsay fzf zoxide eza"
elif [ -f "/etc/arch-release" ]; then
    echo -e "${GREEN}>> Entorno detectado: Arch Linux${NC}"
    PKG_MANAGER_ARRAY=(sudo pacman -Sy --noconfirm --needed)
    CORE_PACKAGES="python zsh git curl wget which"
    EXTRA_PACKAGES="figlet fastfetch fortune-mod cowsay fzf zoxide lolcat eza"
elif [ -f "/etc/alpine-release" ]; then
    echo -e "${GREEN}>> Entorno detectado: Alpine Linux${NC}"
    PRE_INSTALL_ARRAY=(sudo apk update)
    PKG_MANAGER_ARRAY=(sudo apk add)
    CORE_PACKAGES="python3 py3-venv zsh git curl wget"
    EXTRA_PACKAGES="figlet fastfetch fortune cowsay fzf zoxide lolcat eza"
elif [ -f "/etc/fedora-release" ]; then
    echo -e "${GREEN}>> Entorno detectado: Fedora${NC}"
    PKG_MANAGER_ARRAY=(sudo dnf install -y)
    CORE_PACKAGES="python3 python3-virtualenv zsh git curl wget"
    EXTRA_PACKAGES="figlet fastfetch fortune-mod cowsay fzf zoxide lolcat eza"
else
    echo -e "${RED}⚠️  No se pudo detectar la distro automáticamente.${NC}"
    echo "Se asumirá que las dependencias (zsh, python3, etc.) ya están instaladas."
fi

# --- 2. INSTALACIÓN DE DEPENDENCIAS DEL SISTEMA ---
if [ ${#PKG_MANAGER_ARRAY[@]} -gt 0 ]; then
    echo -e "${BLUE}>> Asegurando dependencias del sistema...${NC}"
    
    if [ ${#PRE_INSTALL_ARRAY[@]} -gt 0 ]; then
        echo -e "${BLUE}>> Actualizando índices de paquetes...${NC}"
        "${PRE_INSTALL_ARRAY[@]}" || echo -e "${RED}⚠️  Fallo al actualizar índices. Intentando continuar...${NC}"
    fi

    echo -e "${BLUE}>> Instalando paquetes críticos: $CORE_PACKAGES${NC}"
    "${PKG_MANAGER_ARRAY[@]}" $CORE_PACKAGES
    if [ $? -ne 0 ]; then
        echo -e "${RED}❌ Falló la instalación de dependencias CRÍTICAS.${NC}"
        exit 1
    fi

    echo -e "${BLUE}>> Instalando herramientas adicionales (opcional): $EXTRA_PACKAGES${NC}"
    # Instalamos una por una para que si una falla (ej: fastfetch no en PPA), no detenga el resto
    for pkg in $EXTRA_PACKAGES; do
        echo -e "${BLUE}   + Instalando $pkg...${NC}"
        "${PKG_MANAGER_ARRAY[@]}" "$pkg" &>/dev/null || echo -e "${RED}   ⚠️  No se pudo instalar $pkg. Continuando...${NC}"
    done
fi

# --- 3. LIMPIEZA DE CONFLICTOS (lolcat) ---
if command -v pip3 &> /dev/null; then
    if pip3 show lolcat &> /dev/null; then
        echo -e "${BLUE}>> Detectado conflicto: lolcat (versión Python) está instalado globalmente.${NC}"
        echo -e "${BLUE}   Eliminando para preferir la versión de sistema más estable...${NC}"
        sudo pip3 uninstall -y lolcat &> /dev/null || pip3 uninstall -y lolcat &> /dev/null || true
    fi
fi

# --- 4. VERIFICACIÓN CRÍTICA DE DEPENDENCIAS ---
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

# Detección inteligente de entornos virtuales rotos o de versiones diferentes
SHOULD_RECREATE=false

if [ -d "$VENV_DIR" ]; then
    # Caso 1: Falta el binario de pip
    if [ ! -f "$VENV_DIR/bin/pip" ]; then
        echo -e "${BLUE}>> Entorno virtual (.venv) incompleto (falta pip). Se recreará.${NC}"
        SHOULD_RECREATE=true
    # Caso 2: El entorno es de una versión de Python diferente a la del sistema
    else
        VENV_PY_VER=$("$VENV_DIR/bin/python" --version 2>&1 | cut -d' ' -f2 | cut -d'.' -f1,2)
        SYS_PY_VER=$(python3 --version 2>&1 | cut -d' ' -f2 | cut -d'.' -f1,2)
        
        if [ "$VENV_PY_VER" != "$SYS_PY_VER" ]; then
            echo -e "${BLUE}>> Versión de Python cambió ($VENV_PY_VER -> $SYS_PY_VER). Recreando entorno...${NC}"
            SHOULD_RECREATE=true
        # Caso 3: El entorno está corrupto (ej: ModuleNotFoundError en pip)
        elif ! "$VENV_DIR/bin/pip" --version &> /dev/null; then
            echo -e "${BLUE}>> Entorno virtual (.venv) detectado como CORRUPTO. Se recreará.${NC}"
            SHOULD_RECREATE=true
        fi
    fi
fi

if [ "$SHOULD_RECREATE" = true ]; then
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

# --- 5. INSTALACIÓN DE LA APLICACIÓN Y DEPENDENCIAS ---
echo -e "${BLUE}>> Instalando la aplicación y sus dependencias...${NC}"
"$VENV_DIR/bin/pip" install --upgrade pip --quiet
"$VENV_DIR/bin/pip" install "$PROJECT_DIR" --quiet || {
    echo -e "${RED}❌ Falló la instalación de Omega-ZSH.${NC}"
    exit 1
}

# --- 6. CREAR ENLACES SIMBÓLICOS PARA ACCESO GLOBAL ---
echo -e "${BLUE}>> Configurando acceso global para 'omega' y 'oz'...${NC}"

# 1. Determinar el mejor directorio de binarios
if [ -d "/data/data/com.termux/files/usr/bin" ]; then
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

echo -e "${BLUE}>> Instalando binarios en: $BIN_DEST${NC}"

# 2. Crear symlinks
ln -sf "$VENV_DIR/bin/omega" "$BIN_DEST/omega" 2>/dev/null || $SUDO_CMD ln -sf "$VENV_DIR/bin/omega" "$BIN_DEST/omega"
ln -sf "$VENV_DIR/bin/oz" "$BIN_DEST/oz" 2>/dev/null || $SUDO_CMD ln -sf "$VENV_DIR/bin/oz" "$BIN_DEST/oz"

if [ $? -ne 0 ]; then
    echo -e "${RED}⚠️  No se pudieron crear los enlaces simbólicos automáticamente.${NC}"
    echo -e "   Puedes ejecutar la app directamente usando: ${GREEN}$VENV_DIR/bin/omega${NC}"
else
    echo -e "${GREEN}>> Enlaces creados correctamente en $BIN_DEST.${NC}"
fi

# 3. Verificar si el destino está en el PATH
if [[ ":$PATH:" != *":$BIN_DEST:"* ]]; then
    echo -e "${RED}⚠️  AVISO: $BIN_DEST no está en tu PATH.${NC}"
    echo -e "   Para arreglarlo, añade esto a tu ~/.zshrc:"
    echo -e "   ${BLUE}export PATH=\"\$PATH:$BIN_DEST\"${NC}"
fi

# --- 7. FINALIZACIÓN Y LANZAMIENTO ---
echo -e "${GREEN}>> ✅ ¡Instalación completada con éxito!${NC}"
echo -e "${BLUE}>> Lanzando Omega-ZSH para configuración inicial...${NC}"

# Ejecutar la aplicación inmediatamente
if [ -f "$BIN_DEST/omega" ]; then
    export PATH="$PATH:$BIN_DEST"
    exec "$BIN_DEST/omega"
elif [ -f "$VENV_DIR/bin/omega" ]; then
    exec "$VENV_DIR/bin/omega"
else
    echo -e "${RED}❌ No se pudo lanzar la aplicación automáticamente.${NC}"
    echo -e "   Ejecútala manualmente con: ${GREEN}omega${NC}"
fi

