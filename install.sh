#!/usr/bin/env bash
set -e

# --- Configuración básica ---
PROJECT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PYTHON_BIN="$(command -v python3 || command -v python || true)"

if [ -z "$PYTHON_BIN" ]; then
    echo "Python no está instalado. Saliendo."
    exit 1
fi

# --- Ejecutar Bootstrap Python ---
cd "$PROJECT_DIR"
PYTHONPATH="$PROJECT_DIR" "$PYTHON_BIN" -m omega_zsh.core.bootstrap "$@"

# --- Finalizar ---
echo "Instalación base completada."
