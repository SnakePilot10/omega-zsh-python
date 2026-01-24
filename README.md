# 🐍 Omega-ZSH (Python Edition)

[![Python](https://img.shields.io/badge/Python-3.10%2B-blue?style=for-the-badge&logo=python)](https://www.python.org/)
[![Platform](https://img.shields.io/badge/Platform-Linux%20%7C%20Android%20(Termux)-green?style=for-the-badge)](https://termux.dev/)
[![License](https://img.shields.io/badge/License-MIT-yellow?style=for-the-badge)](LICENSE)

> **Orquestador de entorno Shell de alto rendimiento.**
> Automatiza, gestiona y embellece tu experiencia en Zsh mediante una arquitectura moderna basada en Python y TUI (Textual).

---

## 📑 Tabla de Contenidos
1. [Objetivo del Proyecto](#-objetivo-del-proyecto)
2. [Arquitectura y Métricas](#-arquitectura-y-métricas)
3. [Instalación](#-instalación)
4. [Guía de Uso](#-guía-de-uso)
5. [Gestión de Plugins (Nueva Funcionalidad)](#-gestión-de-plugins)
6. [Casos de Uso](#-casos-de-uso)
7. [Contribución](#-contribución)

---

## 🎯 Objetivo del Proyecto

Configurar un entorno de terminal profesional (`zsh` + `git` + plugins + temas) suele implicar:
1.  Editar manualmente archivos `.zshrc` frágiles.
2.  Gestionar dependencias de sistemas operativos dispares (apt, pacman, pkg).
3.  Perder configuraciones al cambiar de dispositivo.

**Omega-ZSH** resuelve esto actuando como una capa de abstracción. No es solo un archivo de configuración; es un **gestor de estado** que asegura que tu entorno sea idéntico, rápido y funcional, ya sea en un servidor Ubuntu, una workstation Arch Linux o un teléfono Android con Termux.

---

## 📐 Arquitectura y Métricas

Omega-ZSH se aleja de los scripts de shell tradicionales en favor de una arquitectura de software robusta.

### Terminología y Diseño
*   **Core (Inmutable):** El archivo `~/.zshrc` es generado y gestionado exclusivamente por Omega. Garantiza la carga correcta de módulos.
*   **Userland (Mutable):** Archivos específicos (`personal.zsh`, `custom.zsh`) donde reside la lógica del usuario. Omega los inyecta (source) sin tocarlos.
*   **Escritura Atómica:** Toda modificación de configuración se realiza primero en un archivo temporal y se mueve atómicamente. **Riesgo de corrupción: 0%.**

### Métricas de Rendimiento
*   **Tiempo de Inicio (Boot Time):** Optimizado para cargar en `< 200ms` (dependiendo del hardware) mediante carga diferida (lazy loading) de plugins pesados (como `nvm` o `conda`).
*   **Overhead de Memoria:** El gestor (Python) solo corre bajo demanda. El shell resultante es Zsh nativo puro, sin overhead de Python residente.

---

## 🚀 Instalación

### Requisitos Previos
*   **Sistema Operativo:** Android (Termux), Debian/Ubuntu, Arch Linux, Fedora, Alpine.
*   **Python:** Versión 3.10 o superior.
*   **Acceso a Internet:** Para descargar dependencias (pip).

### Método 1: Bootstrap Automático (Recomendado)
Ideal para entornos nuevos. Detecta la distro, instala Python/venv, y lanza la aplicación.

```bash
git clone https://github.com/SnakePilot10/omega-zsh-python.git
cd omega-zsh-python
chmod +x install.sh
./install.sh
```

### Método 2: Instalación como Paquete Python (Pip)
Ideal para usuarios avanzados que ya gestionan su entorno Python.

```bash
# Desde el directorio raíz del proyecto
pip install .
```

---

## 🎮 Guía de Uso

El sistema ofrece dos interfaces principales para interactuar con tu entorno.

### 1. Interfaz Gráfica de Terminal (TUI)
Ejecuta `omega` para entrar al panel de control visual.

*   **Dashboard:** Vista general del sistema.
*   **Temas:** Previsualiza temas (Powerlevel10k, Bira, etc.) y aplícalos con `Enter`.
*   **Instalador:** Repara o reinstala paquetes del sistema (`fzf`, `eza`, `bat`) automáticamente.

### 2. CLI de Alta Velocidad (`oz`)
La herramienta `oz` es una navaja suiza diseñada para optimizar tu flujo de trabajo diario.

**Comandos "God Tier" disponibles:**
*   `oz banner`: Dashboard con estado del sistema (CPU, RAM, Disco) y herramientas activas.
*   `oz bench`: **Prueba de Hyperdrive**. Mide la velocidad de inicio de tu shell y ofrece **diagnósticos precisos** para acelerarla.
*   `oz stats`: **Telemetría de Comandos**. Analiza qué usas más y te **sugiere alias inteligentes** para ahorrar pulsaciones.
*   `oz themes`: **Arsenal Completo**. Escanea y lista absolutamente todos los temas instalados (Omega, OMZ y Custom).
*   `oz plugins`: **Inspector de Código**. Explica qué alias y funciones añade cada plugin activo.
*   `oz update`: **Protocolo de Sincronización**. Actualiza el núcleo de Omega-ZSH con las últimas mejoras y temas.

---

## 🎨 Temas "God Tier"

Omega-ZSH incluye una colección exclusiva de temas diseñados para ser visualmente impactantes:
*   **Matrix (The Construct):** Flujo de datos binarios con degradados digitales.
*   **Futurista (Night City HUD):** Interfaz Cyberpunk de alta densidad con bloques mecha.
*   **Gótico (Nosferatu):** Estética vampírica con rojo sangre y hierro forjado.
*   **Espacial (Interstellar):** UI de nave estelar con trayectorias orbitales.
*   **Elegante (Royal Gold):** Lujo en oro y pizarra Art Deco.
*   **Retro (Pip-Boy):** Terminal de fósforo verde estilo BIOS/Fallout.
*   **Naturaleza (Elven Forest):** Conectores orgánicos de enredaderas y follaje.

Cada tema utiliza conectores estructurales únicos (`▛`, `╓`, `┏`, `╭〰`) que rompen la estética tradicional de Zsh.

### Interfaz TUI Optimizada
La interfaz gráfica (`omega`) ha sido refinada para una mejor experiencia en pantallas pequeñas (Termux):
*   **Scroll Vertical Inteligente:** Las listas de plugins y temas ahora soportan desplazamiento fluido (`overflow-y: auto`), permitiendo navegar por cientos de opciones con facilidad.
*   **Navegación Táctil:** Optimizado para el uso del ratón y toques en pantalla en emuladores de terminal.

---

## 💡 Casos de Uso

### Caso A: El Desarrollador Móvil (Termux)
*   **Problema:** Configurar Zsh en Android es tedioso y propenso a errores de permisos/rutas.
*   **Solución:** Omega detecta el entorno `com.termux`, ajusta los `shebangs`, configura las rutas de almacenamiento interno y **maneja inteligentemente los permisos de root (sudo/tsu)** para comandos con y sin argumentos.

### Caso B: El "Distro Hopper"
*   **Problema:** Usas Arch en casa y Ubuntu en el servidor. Tus alias de actualización (`pacman` vs `apt`) siempre rompen.
*   **Solución:** Omega estandariza los alias. Usa `oz` para verificar qué herramientas están disponibles en la máquina actual sin cambiar tu memoria muscular.

### Caso C: Gestión de Secretos
*   **Problema:** No quieres subir tus API Keys a GitHub en tu `.zshrc`.
*   **Solución:** Edita `~/.omega-zsh/personal.zsh` (accesible vía alias `zp`). Este archivo está en `.gitignore` por defecto.

---

## 🤝 Contribución

¡Tu ayuda es bienvenida! Para instrucciones detalladas sobre cómo configurar el entorno de desarrollo y ejecutar pruebas, consulta nuestra **[Guía de Contribución](CONTRIBUTING.md)**.

### Estructura del Proyecto
```
omega-zsh-python/
├── omega_zsh/
│   ├── core/       # Lógica de negocio (instaladores, estado)
│   ├── ui/         # Interfaz Textual (TUI)
│   ├── cli/        # Herramienta 'oz'
│   └── platforms/  # Abstracciones de OS (Debian.py, Termux.py)
├── tests/          # Unit tests
└── install.sh      # Bootstrapper
```

### Flujo de Desarrollo
1.  Crear entorno virtual: `python -m venv .venv`
2.  Activar: `source .venv/bin/activate`
3.  Instalar en modo editable: `pip install -e .`
4.  Ejecutar tests: `pytest`

---
Copyright © 2026 SnakePilot10. Licencia MIT.
