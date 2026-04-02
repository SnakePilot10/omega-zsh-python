# OMEGA-ZSH (v2.3.0)

[![Python](https://img.shields.io/badge/Python-3.13%2B-ff006e?style=for-the-badge&logo=python)](https://www.python.org/)
[![Platform](https://img.shields.io/badge/Platform-Termux_%7C_Linux-00f5ff?style=for-the-badge)](https://termux.dev/)
[![Status](https://img.shields.io/badge/Status-Ultra_Fast-00ff9f?style=for-the-badge)](https://github.com/SnakePilot10/omega-zsh-python)

> Gestor de shell Zsh con TUI interactiva y **Motor Hyperdrive**. Controla plugins, temas y headers desde una interfaz visual optimizada para máxima velocidad en entornos ARM y Linux.

---

## Índice

1. [Arquitectura](#arquitectura)
2. [Instalación Inteligente](#instalación-inteligente)
3. [Hyperdrive Engine](#hyperdrive-engine)
4. [CLI — Arsenal `oz`](#cli--arsenal-oz)
5. [TUI — Interfaz Visual](#tui--interfaz-visual)
6. [Registro de Cambios](#registro-de-cambios)

---

## Arquitectura

```
omega-zsh-python/
├── omega_zsh/
│   ├── core/
│   │   ├── context.py      # Detección de entorno resiliente (PRoot/Termux/Linux)
│   │   ├── generator.py    # Motor Jinja2 con Blindaje de Runtime
│   │   ├── state.py        # Persistencia de estado Single-Source-of-Truth
│   │   ├── installer.py    # Gestión polimórfica de paquetes (Apt/Gem/Git)
│   │   └── constants.py    # Definición centralizada de arsenal
│   ├── ui/
│   │   ├── app.py          # Orquestador Textual con gestión de hilos
│   │   └── screens.py      # Pantallas con previsualización asíncrona
│   └── cli/
│       └── oz_tool.py      # CLI oz con Auto-Diagnóstico (zprof)
├── install.sh              # Instalador con Caché de Hash y Auto-Bootstrap
└── pyproject.toml
```

---

## Instalación Inteligente

El nuevo instalador v2.3.0 es **State-Aware** y **Self-Healing**:

```bash
git clone https://github.com/SnakePilot10/omega-zsh-python.git
cd omega-zsh-python
chmod +x install.sh
./install.sh
```

**Capacidades del Instalador:**
- **Auto-Bootstrap:** Si no tienes Oh My Zsh, lo instala y configura automáticamente.
- **Caché de Hash:** Detecta cambios en `pyproject.toml` y código fuente para evitar sincronizaciones de `pip` innecesarias (arranque instantáneo).
- **Inmunidad a Fallos:** Implementa fallbacks (ej: `gem install lolcat`) si el gestor de paquetes del sistema falla.
- **Memoria de Decisión:** Recuerda tus elecciones (como saltar herramientas extras) para no ser repetitivo.

---

## Hyperdrive Engine

Omega-ZSH v2.3.0 incluye un motor de optimización de bajo nivel inyectado directamente en tu `.zshrc`:

- **Z-Compile:** Compilación automática de plugins a bytecode (`.zwc`) para cargas 10x más rápidas.
- **Async Suggestions:** El autocompletado trabaja en segundo plano, eliminando el lag de escritura.
- **Git Turbo:** Desactivación de escaneos pesados en carpetas grandes para prompts instantáneos.
- **Runtime Shield:** Verificación de binarios en microsegundos para evitar errores de "Command Not Found".

---

## CLI — Arsenal `oz`

| Comando | Descripción |
|---|---|
| `oz b` | **Status:** Telemetría esencial del sistema (RAM, Disco, Uptime). |
| `oz v` | **Bench:** Test de latencia Hyperdrive con diagnóstico inteligente. |
| `oz vp` | **Profile:** Perfilado profundo automático (`zprof`) sin editar archivos. |
| `oz p` | **Plugins:** Manual interactivo de herramientas y sus alias. |
| `oz u` | **Update:** Sincronización de código fuente y dependencias. |

---

## TUI — Interfaz Visual

```bash
omega
```

| Tab | Función |
|---|---|
| **Dashboard** | Telemetría en tiempo real basada en `/proc` (Sin dependencias). |
| **Plugins** | Activación dinámica sincronizada con el instalador. |
| **Themes** | Arsenal "God Tier" con previsualización física garantizada. |
| **Headers** | Banners estéticos con blindaje contra fallos de binarios. |

---

## Registro de Cambios

**2026-04-01 — Ultra Performance & Intelligence (v2.3.0):**
- **Hyperdrive:** Implementación de `zcompile` automático y modo asíncrono en `.zshrc`.
- **oz profile:** Nuevo comando de auto-diagnóstico basado en `zprof` automatizado.
- **Smart Installer:** Sincronización basada en hash de código, auto-limpieza de symlinks y bootstrap de OMZ.
- **Resiliencia:** Blindaje de headers contra binarios faltantes y fallbacks de instalación en Termux.
- **Estabilidad:** Resolución de SyntaxErrors en la TUI y normalización de logs.

---
Copyright © 2026 SnakePilot10
