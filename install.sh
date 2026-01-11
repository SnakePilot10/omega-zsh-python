#!/usr/bin/env bash
set -e

# Colores para output
RED='\033[0;31m'
GREEN='\033[0;32m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

echo -e "${BLUE}>>> Iniciando Instalador de Omega-ZSH (Python Edition)${NC}"

# --- 1. DETECCIÓN RÁPIDA DE ENTORNO PARA BOOTSTRAP ---
# Necesitamos instalar Python y venv ANTES de que corra el código Python.
PKG_INSTALL_CMD=""

if [ -d "/data/data/com.termux" ]; then
    echo -e "${GREEN}>> Entorno detectado: Android (Termux)${NC}"
    PKG_INSTALL_CMD="pkg install -y"
elif [ -f "/etc/debian_version" ]; then
    echo -e "${GREEN}>> Entorno detectado: Debian/Ubuntu${NC}"
    PKG_INSTALL_CMD="sudo apt update && sudo apt install -y"
elif [ -f "/etc/arch-release" ]; then
    echo -e "${GREEN}>> Entorno detectado: Arch Linux${NC}"
    PKG_INSTALL_CMD="sudo pacman -Sy --noconfirm"
elif [ -f "/etc/alpine-release" ]; then
    echo -e "${GREEN}>> Entorno detectado: Alpine Linux${NC}"
    PKG_INSTALL_CMD="sudo apk add"
elif [ -f "/etc/fedora-release" ]; then
    echo -e "${GREEN}>> Entorno detectado: Fedora${NC}"
    PKG_INSTALL_CMD="sudo dnf install -y"
else
    echo -e "${RED}⚠️  No se pudo detectar la distro automáticamente.${NC}"
    echo "Se intentará continuar asumiendo que Python ya está instalado."
fi

# --- 2. VERIFICACIÓN DE PYTHON ---
if ! command -v python3 &> /dev/null; then
    echo -e "${BLUE}>> Python3 no encontrado. Intentando instalar...${NC}"
    if [ -n "$PKG_INSTALL_CMD" ]; then
        $PKG_INSTALL_CMD python3
    else
        echo -e "${RED}❌ Error: Debes instalar Python 3.10+ manualmente.${NC}"
        exit 1
    fi
fi

# Verificar módulo venv (En Debian/Ubuntu suele ser un paquete separado python3-venv)
if ! python3 -c "import venv" &> /dev/null; then
    echo -e "${BLUE}>> Módulo 'venv' no encontrado. Intentando instalar...${NC}"
    if [[ "$PKG_INSTALL_CMD" == *"apt"* ]]; then
         $PKG_INSTALL_CMD python3-venv
    elif [[ "$PKG_INSTALL_CMD" == *"apk"* ]]; then
         # En Alpine python3 incluye venv usualmente, o es py3-virtualenv
         echo "Nota: En Alpine asegúrate de tener el paquete py3-virtualenv o similar si falla."
    fi
fi

# --- 3. CREACIÓN DEL ENTORNO VIRTUAL ---
PROJECT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
VENV_DIR="$PROJECT_DIR/.venv"

if [ ! -d "$VENV_DIR" ]; then
    echo -e "${BLUE}>> Creando entorno virtual aislado (.venv)...${NC}"
    python3 -m venv "$VENV_DIR"
    if [ $? -ne 0 ]; then
        echo -e "${RED}❌ Falló la creación del entorno virtual.${NC}"
        echo "Asegúrate de tener permisos de escritura y el módulo venv instalado."
        exit 1
    fi
fi

# --- 4. INSTALACIÓN DE DEPENDENCIAS ---
echo -e "${BLUE}>> Verificando dependencias...${NC}"
"$VENV_DIR/bin/pip" install --upgrade pip --quiet
"$VENV_DIR/bin/pip" install -r "$PROJECT_DIR/requirements.txt" --quiet

if [ $? -ne 0 ]; then
    echo -e "${RED}❌ Falló la instalación de librerías Python.${NC}"
    exit 1
fi

# --- 5. LANZAR APLICACIÓN ---
echo -e "${GREEN}>> Todo listo. Lanzando Omega-ZSH...${NC}"
# Pasamos todos los argumentos ($@) al script python
exec "$VENV_DIR/bin/python" "$PROJECT_DIR/main.py" "$@"
