# Omega-ZSH (Python Edition)

## Project Overview
Omega-ZSH is a sophisticated Zsh configuration manager designed for Linux and Android (Termux) environments. It replaces manual configuration editing with a modern Terminal User Interface (TUI) powered by Python. It handles system detection, dependency installation, and configuration generation (`.zshrc`), ensuring a robust and aesthetically pleasing shell experience.

### Key Features
- **Cross-Platform:** Supports Termux (Android), Debian/Ubuntu, Arch, Fedora, and Alpine.
- **TUI Interface:** Built with `textual`, offering a mouse-compatible, visual dashboard.
- **Modular Management:** Easily toggle plugins and switch themes.
- **Safe Configuration:** Uses atomic writes and backups to prevent data loss.
- **3-Layer Architecture:** Separates core config, structured personal config, and manual custom overrides.

## Directory Structure
- **`omega_zsh/`**: Core application source code.
    - **`core/`**: Business logic, state management, and installation routines.
    - **`platforms/`**: OS-specific implementations (e.g., `termux.py`, `debian.py`).
    - **`ui/`**: TUI implementation using the Textual framework.
    - **`assets/`**: Contains templates (`.zshrc.j2`) and theme definitions.
- **`install.sh`**: Universal bootstrap script for setting up the environment.
- **`requirements.txt`**: Python dependencies (`textual`, `jinja2`).

## Building and Running

### Prerequisites
- Python 3.10+
- A compatible shell environment (Termux or a standard Linux distro)

### Installation & Execution
The project includes a self-contained installer script that handles virtual environment creation and dependency management.

**Standard User Run:**
```bash
./install.sh
```

**Development Mode:**
To run the application without reinstalling dependencies every time (assuming setup is done):
```bash
source .venv/bin/activate
python -m omega_zsh
```

## Development Conventions

### Architecture
- **Dependency Management:** All dependencies are isolated in a local `.venv` directory.
- **Logging:** Errors and runtime info are logged to `omega_crash.log` in the root directory.
- **Templating:** Configuration files are generated using Jinja2 templates located in `omega_zsh/assets/templates/`.

### Testing
The project uses `pytest` for unit testing. Tests are located in the `tests/` directory.

To run tests:
```bash
source .venv/bin/activate
pytest
```

### Contribution
- **Virtual Environment:** Ensure you are working within the `.venv` created by `install.sh`.
- **Platform Specifics:** When adding new OS support, extend the `platforms/` module.
- **UI Changes:** Modify `omega_zsh/ui/` for interface adjustments. Verify layout on both desktop and mobile (Termux) screen sizes.