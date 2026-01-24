# 🐍 Omega-ZSH (Python Edition)

[![Python](https://img.shields.io/badge/Python-3.10%2B-blue?style=for-the-badge&logo=python)](https://www.python.org/)
[![Platform](https://img.shields.io/badge/Platform-Linux%20%7C%20Android%20(Termux)-green?style=for-the-badge)](https://termux.dev/)
[![License](https://img.shields.io/badge/License-MIT-yellow?style=for-the-badge)](LICENSE)
[![CI/CD](https://github.com/SnakePilot10/omega-zsh-python/actions/workflows/ci.yml/badge.svg)](https://github.com/SnakePilot10/omega-zsh-python/actions)

> **Orquestador de entorno Shell de alto rendimiento.**
> Automatiza, gestiona y embellece tu experiencia en Zsh mediante una arquitectura moderna basada en Python y TUI (Textual).

---

## 📑 Tabla de Contenidos
1. [Objetivo del Proyecto](#-objetivo-del-proyecto)
2. [Arquitectura y Métricas](#-arquitectura-y-métricas)
3. [Instalación](#-instalación)
4. [Guía de Uso](#-guía-de-uso)
5. [Gestión de Plugins](#-gestión-de-plugins)
6. [Temas y Personalización](#-temas-y-personalización)
7. [Contribución](#-contribución)

---

## 🎯 Objetivo del Proyecto

Configurar un entorno de terminal profesional (`zsh` + `git` + plugins + temas) suele implicar editar manualmente archivos `.zshrc` frágiles y gestionar dependencias dispares.

**Omega-ZSH** actúa como un **gestor de estado** que asegura que tu entorno sea idéntico, rápido y funcional, ya sea en un servidor Ubuntu, una workstation Arch Linux o un teléfono Android con Termux.

---

## 📐 Arquitectura y Métricas

*   **Core (Inmutable):** El archivo `~/.zshrc` es generado por Omega. Garantiza la carga correcta de módulos.
*   **Userland (Mutable):** Archivos específicos (`personal.zsh`, `custom.zsh`) donde reside la lógica del usuario.
*   **Escritura Atómica:** Toda modificación se realiza primero en un archivo temporal. **Riesgo de corrupción: 0%.**

### Métricas de Rendimiento
*   **Boot Time:** Optimizado para cargar en `< 200ms` mediante carga diferida.
*   **Overhead:** El gestor (Python) solo corre bajo demanda. El shell es Zsh nativo puro.

---

## 🚀 Instalación

### Requisitos Previos
*   **OS:** Android (Termux), Debian/Ubuntu, Arch Linux, Fedora, Alpine.
*   **Python:** 3.10+.
*   **Internet:** Para dependencias.

### Bootstrap Automático
```bash
git clone https://github.com/SnakePilot10/omega-zsh-python.git
cd omega-zsh-python
chmod +x install.sh
./install.sh
```

---

## 🎮 Guía de Uso

### 1. Interfaz Gráfica de Terminal (TUI)
Ejecuta `omega` para entrar al panel de control visual.

#### Novedades v2.2.0:
*   **🎨 Live Preview Real:**
    *   **Temas:** Al navegar por la lista, verás a la derecha una **previsualización real** de cómo luce el prompt (`zsh` renderiza el tema en una sandbox aislada).
    *   **Headers:** Previsualización instantánea de `fastfetch`, `cowsay` o banners `figlet`.
*   **⚡ Navegación Fluida:** Muévete con las flechas del teclado y la previsualización se actualizará al instante (sin necesidad de Enter).
*   **🚀 Quick Apply (`A`):**
    *   Presiona `A` para aplicar cambios de configuración (temas, alias) al instante.
    *   Usa `I` (Full Install) solo cuando necesites descargar nuevos plugins.
*   **🛠️ Dashboard:** Presiona `D` en cualquier momento para cerrar ventanas y volver al inicio.

### 2. CLI de Alta Velocidad (`oz`)
Herramienta de navaja suiza para el día a día.

*   `oz banner`: Estado del sistema (CPU, RAM, Disco).
*   `oz bench`: **Hyperdrive Benchmark**. Mide y diagnostica la velocidad de inicio.
*   `oz stats`: **Telemetría**. Sugiere alias basados en tus comandos más usados.
*   **`oz themes`**: Lista TODOS los temas instalados (Omega, Oh My Zsh Standard y Custom).
*   `oz plugins`: Inspector de código de plugins activos.
*   `oz update`: Actualiza el núcleo de Omega-ZSH.

---

## 🎨 Temas y Personalización

### Integración Total
Omega-ZSH ahora detecta y gestiona temas de tres fuentes:
1.  **Omega God Tier:** Temas exclusivos de alta estética (Matrix, Cyberpunk, Nosferatu, etc.).
2.  **Standard OMZ:** La librería clásica de Oh My Zsh (robbyrussell, agnoster, etc.).
3.  **User Custom:** Tus propios temas en `~/.oh-my-zsh/custom/themes`.

### Colección "God Tier"
Temas diseñados con conectores estructurales únicos (`▛`, `╓`, `┏`):
*   **Matrix (The Construct):** Flujo de datos binarios.
*   **Futurista (Night City HUD):** Interfaz Cyberpunk de alta densidad.
*   **Gótico (Nosferatu):** Estética vampírica con rojo sangre.
*   **Espacial (Interstellar):** UI de nave estelar.
*   **Elegante (Royal Gold):** Lujo Art Deco.
*   **Retro (Pip-Boy):** Fósforo verde estilo Fallout.

---

## 🤝 Contribución

El proyecto cuenta con un pipeline de CI/CD robusto:
*   **Linting:** Código verificado con `ruff` para calidad y estilo.
*   **Tests:** Pruebas unitarias automáticas en cada push.
*   **Releases:** Generación automática de releases en GitHub al crear tags (`v*`).

Para contribuir:
1.  `python -m venv .venv && source .venv/bin/activate`
2.  `pip install -e .`
3.  `pytest`

---
Copyright © 2026 SnakePilot10. Licencia MIT.