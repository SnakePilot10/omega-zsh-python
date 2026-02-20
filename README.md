# 👾 Omega-ZSH (Neon Retro Elite Edition) ⚡️

[![Python](https://img.shields.io/badge/Python-3.10%2B-ff00ff?style=for-the-badge&logo=python)](https://www.python.org/)
[![Platform](https://img.shields.io/badge/Platform-Android%20(Termux)%20%7C%20Linux-00ffff?style=for-the-badge)](https://termux.dev/)
[![Edition](https://img.shields.io/badge/Edition-Elite%20Neon-39ff14?style=for-the-badge)](https://github.com/SnakePilot10/omega-zsh-python)

> **Centro de Comando y Control de Entropía Digital.**
> Automatiza, gestiona y domina tu shell Zsh mediante una arquitectura Neon Retro de alta fidelidad basada en Python y Textual.

---

## 📑 Tabla de Contenidos
1. [Visión Neon Retro](#-visión-neon-retro)
2. [Arquitectura de Mando](#-arquitectura-de-mando)
3. [Instalación](#-instalación)
4. [Arsenal CLI (oz)](#-arsenal-cli-oz)
5. [Gestión de Plugins](#-gestión-de-plugins)
6. [Temas God Tier](#-temas-god-tier)

---

## 🎨 Visión Neon Retro

Omega-ZSH v2.2.0 rompe con la estética aburrida de las terminales convencionales. Hemos inyectado una paleta **Cyber-Neon** (Cian, Magenta y Lima) en cada rincón de la interfaz.

*   **Dashboard de Elite:** Un panel visual estático de alta densidad que emula los mainframes de infiltración de los 80.
*   **Interfaz Unificada:** Tanto la TUI (`omega`) como el CLI (`oz`) comparten el mismo ADN visual.
*   **Estabilidad Total:** Optimizado para Android 14+, manejando las restricciones de sistema con elegancia y estilo.

---

## 📐 Arquitectura de Mando

*   **Core Inmutable:** Generación de `.zshrc` mediante el motor Jinja2. **Riesgo de corrupción: 0%.**
*   **Blindaje Android:** Manejo inteligente de permisos de `/proc/stat`. Si el sistema bloquea los sensores, Omega se adapta sin colapsar.
*   **Sincronización de Alta Densidad:** Gestión fluida de más de 30 plugins simultáneos sin degradar el rendimiento.

---

## 🚀 Instalación

### Bootstrap Automático
```bash
git clone https://github.com/SnakePilot10/omega-zsh-python.git
cd omega-zsh-python
chmod +x install.sh
./install.sh
```

**El instalador purgará automáticamente herramientas obsoletas como `bat` y `nala`**, asegurando un entorno ligero y moderno basado en `eza`, `zoxide` y `yazi`.

---

## 🕹️ Arsenal CLI (`oz`)

La herramienta `oz` es tu navaja suiza de nanosegundos. Ahora con alias ultrarrápidos:

*   **`oz b` (Banner):** Telemetría esencial (RAM, Disco, Uptime) con blindaje de seguridad.
*   **`oz v` (Velocidad):** **Hyperdrive Benchmark**. Mide la latencia de arranque con precisión de nanosegundos y ofrece un **Diagnóstico de Entropía** inteligente.
*   **`oz p` (Plugins):** **Manual de Operaciones**. Detalla cada módulo activo, sus alias críticos y "Tips de Elite" para dominar tus herramientas.
*   **`oz u` (Update):** Sincronización inmediata con el núcleo del protocolo Janus.
*   **`oz t` (Themes):** Explorador visual de la librería completa de temas.
*   **`oz s` (Stats):** Analizador de patrones de uso y sugerencia automática de alias.

---

## 📦 Gestión de Plugins

Omega-ZSH gestiona una carga masiva de más de 30 módulos divididos en:
1.  **Plugins OMZ:** `zsh-autosuggestions`, `syntax-highlighting`, `fzf-tab`, `k`, etc.
2.  **Binarios Modernos:** `eza` (ls), `zoxide` (cd), `yazi` (file manager), `fzf`, `ripgrep`, `fd`.

**Sincronización Real:** Lo que seleccionas en la TUI es lo que se carga físicamente. Hemos eliminado los plugins fantasmas y los errores de "not found".

---

## 🤝 Contribución

```bash
# Entorno de Desarrollo Elite
python -m venv .venv
source .venv/bin/activate
pip install -e ".[dev]"

# Calidad de Código
pytest --cov=omega_zsh  # Test de Integridad
ruff check .            # Auditoría de Estilo
```

---
Copyright © 2026 SnakePilot10. By | Janus & Tesavek⚡️👾.
