# OMEGA-ZSH (v2.3.0)

[![Python](https://img.shields.io/badge/Python-3.10%2B-ff006e?style=for-the-badge&logo=python)](https://www.python.org/)
[![Platform](https://img.shields.io/badge/Platform-Termux_%7C_Linux-00f5ff?style=for-the-badge)](https://termux.dev/)
[![Status](https://img.shields.io/badge/Status-Audited-00ff9f?style=for-the-badge)](https://github.com/SnakePilot10/omega-zsh-python)

Omega-ZSH is a Zsh configuration manager for Linux and Termux. It provides a Textual TUI, a small `oz` CLI, safe `.zshrc` rendering, recovery tools, and explicit install/apply flows.

The current architecture favors predictable changes over magic: the installer bootstraps dependencies and plugins, while writing `.zshrc` remains an explicit action.

---

## Contents

1. [Architecture](#architecture)
2. [Installation](#installation)
3. [Apply Model](#apply-model)
4. [CLI](#cli)
5. [TUI](#tui)
6. [Safety And Recovery](#safety-and-recovery)
7. [Known Limitations](#known-limitations)
8. [Development](#development)

---

## Architecture

```text
omega-zsh-python/
├── omega_zsh/
│   ├── core/
│   │   ├── apply.py        # Validated config preview/apply and theme linking
│   │   ├── bootstrap.py    # Python install orchestration used by install.sh
│   │   ├── context.py      # System, path, distro, and Termux detection
│   │   ├── doctor.py       # Read-only checks and explicit conservative fixes
│   │   ├── generator.py    # Jinja2 rendering with backup/validation/rollback
│   │   ├── installer.py    # OMZ/plugin/binary installation orchestration
│   │   ├── recovery.py     # Backup restore and shell cleanup helpers
│   │   └── state.py        # State schema, presets, and safe minimal profile
│   ├── platforms/
│   │   ├── arch.py         # pacman backend
│   │   ├── debian.py       # apt/nala backend
│   │   └── termux.py       # pkg/gem backend
│   ├── ui/
│   │   ├── app.py          # Textual application shell
│   │   └── screens.py      # Dashboard, setup, problems, presets, recovery, etc.
│   └── cli/
│       └── oz_tool.py      # Diagnostic and utility CLI
├── install.sh              # Minimal shell wrapper around omega_zsh.core.bootstrap
└── pyproject.toml
```

---

## Installation

Requirements:

- Python `>=3.10`
- Linux or Termux
- A package manager detected by Omega-ZSH: `apt`, `nala`, `pacman`, or Termux `pkg`

```bash
git clone https://github.com/SnakePilot10/omega-zsh-python.git
cd omega-zsh-python
chmod +x install.sh

# Bootstrap base dependencies, Python venv, package install, Oh My Zsh, and plugins.
./install.sh

# Same flow with less progress output.
./install.sh --unattended

# Also sync bundled Omega themes into Oh My Zsh.
./install.sh --sync-themes

# Also apply the currently saved state to ~/.zshrc through the validated apply path.
./install.sh --apply-config
```

`install.sh` is intentionally small. It changes into the repo, sets `PYTHONPATH`, and delegates to `omega_zsh.core.bootstrap`.

Bootstrap currently does this:

- Installs base packages for the detected OS.
- Creates `.venv` if missing.
- Runs `pip install --upgrade pip` and `pip install -e .`.
- Loads saved Omega state from `~/.omega-zsh`.
- Ensures Oh My Zsh exists.
- Installs selected plugins and supported binary tools from saved/imported state.
- Syncs themes only when `--sync-themes` is passed.
- Writes `.zshrc` only when `--apply-config` is passed.

---

## Apply Model

Omega-ZSH separates installation from shell mutation.

- `omega` opens the TUI and lets you review state before applying.
- `./install.sh` prepares dependencies and plugins, but does not write `.zshrc` by default.
- `./install.sh --apply-config` writes `.zshrc` through `apply_config()`.
- Apply uses preview/render, syntax validation when `zsh` exists, backup, manifest ownership, and rollback support.
- Read-only checks such as `omega doctor` do not create logs or mutate files.

---

## CLI

Both entrypoints are installed by the package:

```bash
omega        # TUI when called without arguments
omega doctor # CLI delegation also works through omega
oz help      # CLI help
```

Current `oz` commands:

| Command | Alias | Description |
|---|---:|---|
| `oz banner` | `oz b` | Shows basic system telemetry. |
| `oz plugins` | `oz p` | Lists known tools/plugins and details. |
| `oz bench` | `oz v` | Measures shell startup latency. |
| `oz profile` | `oz vp` | Runs zprof-oriented profiling. |
| `oz stats` | `oz s` | Analyzes shell history and alias opportunities. |
| `oz themes` | `oz t` | Lists available themes from Omega, custom, and OMZ paths. |
| `oz doctor` | `oz doc` | Runs read-only installation/config checks. |
| `oz doctor --fix` | `oz doc --fix` | Runs explicit conservative fixes. |
| `oz update` | `oz u` | Pulls repo changes and reinstalls the editable package. |
| `oz help` | `oz h` | Shows CLI help. |

---

## TUI

```bash
omega
```

The TUI provides:

- Dashboard: system and Omega status.
- Setup: first-run guided state setup when appropriate.
- Problems: read-only doctor output with an explicit double-confirm fix action.
- Presets: safe/minimal/pretty-style state presets that save state before apply.
- Plugins: plugin and tool selection with support/status labels.
- Themes: theme selection and explicit previews.
- Headers: header selection and explicit previews for external commands.
- Recovery: dry-run cleanup and selectable `.zshrc` backup restore with confirmation.

Keyboard shortcuts are shown in the interface. Apply remains explicit.

---

## Safety And Recovery

Implemented safety boundaries include:

- Rotating backups before replacing `.zshrc`.
- Syntax validation with `zsh -n` when `zsh` is available.
- Rollback support for failed config writes.
- Manifest ownership for Omega-managed files and theme symlinks.
- Read-only doctor mode with separate `doctor --fix`.
- Backup listing and selected restore instead of blind latest-only restore.
- Safe minimal state for conservative first-run setup.

User customization files are intentionally separate:

- `personal.zsh`: generated from explicit state/template data.
- `custom.zsh`: manual user-owned aliases/functions.

See `docs/config-files.md` for the rationale.

---

## Known Limitations

- `install_core_packages()` still installs base packages eagerly and does not yet do per-package preflight/idempotency checks.
- `ArchPlatform.update_repos()` uses `pacman -Syu`; it should not be invoked automatically without user confirmation.
- If `zsh` is unavailable, syntax validation is skipped so bootstrap/setup can continue; `doctor` reports missing shell dependencies.
- Fresh-install behavior is covered by mocked tests, but release-grade Debian/Arch/Termux smoke automation is still future hardening.

---

## Development

```bash
python3 -m venv .venv
. .venv/bin/activate
pip install -e '.[dev]'

python3 -m compileall omega_zsh tests
python -m pytest -q
python -m ruff check .
python -m ruff format --check .
```

The audited closeout used:

- `/tmp/opencode/omega-zsh-test-venv/bin/python -m pytest -q`
- `git diff --check`
- `graphify update`

---

Copyright (c) 2026 SnakePilot10
