import sys
import subprocess
import os
from pathlib import Path
from typing import List

# Importamos la lógica de detección de plataformas desde el instalador
from .context import SystemContext
from .installer import PluginInstaller

# Definimos paquetes base por sistema
CORE_PACKAGES = {
    "debian": ["python3", "python3-venv", "zsh", "git", "curl", "wget", "debianutils", "bc"],
    "termux": ["python", "zsh", "git", "curl", "wget", "debianutils", "bc"],
    "arch": ["python", "zsh", "git", "curl", "wget", "which", "bc"],
}

def detect_os() -> str:
    if Path("/etc/debian_version").exists():
        return "debian"
    if "TERMUX_VERSION" in os.environ or Path("/data/data/com.termux").exists():
        return "termux"
    if Path("/etc/arch-release").exists():
        return "arch"
    return "unknown"

def install_core_packages(os_id: str, unattended: bool):
    if os_id == "unknown":
        print("Entorno desconocido, saltando instalación de paquetes base.")
        return
    
    packages = CORE_PACKAGES.get(os_id, [])
    # Detección simplificada de gestor de paquetes
    cmd = []
    if os_id == "debian":
        cmd = ["sudo", "apt-get", "install", "-y"]
    elif os_id == "termux":
        cmd = ["pkg", "install", "-y"]
    elif os_id == "arch":
        cmd = ["sudo", "pacman", "-S", "--noconfirm", "--needed"]
    
    if cmd:
        print(f"Instalando paquetes base: {', '.join(packages)}")
        subprocess.run(cmd + packages, check=True)

def setup_venv(project_dir: Path):
    venv_dir = project_dir / ".venv"
    if not venv_dir.exists():
        print(f"Creando venv en {venv_dir}")
        subprocess.run([sys.executable, "-m", "venv", str(venv_dir)], check=True)
    return venv_dir

def main():
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("--unattended", action="store_true")
    parser.add_argument("--apply-config", action="store_true")
    parser.add_argument("--sync-themes", action="store_true")
    parser.add_argument("--separation-smoke", action="store_true")
    args = parser.parse_args()

    if args.separation_smoke:
        print(f"APPLY_CONFIG={str(args.apply_config).lower()}")
        print(f"SYNC_THEMES={str(args.sync_themes).lower()}")
        print(f"HOME={os.environ.get('HOME')}")
        sys.exit(0)

    if args.apply_config or args.sync_themes:
        parser.error("--apply-config and --sync-themes are temporarily unsupported in bootstrap.py")

    project_dir = Path(__file__).parent.parent.parent
    os_id = detect_os()
    
    try:
        install_core_packages(os_id, args.unattended)
        venv_dir = setup_venv(project_dir)
        # Sincronizar dependencias Python
        print("Sincronizando dependencias Python...")
        pip_bin = venv_dir / "bin" / "pip"
        subprocess.run([str(pip_bin), "install", "--upgrade", "pip", "--quiet"], check=True)
        subprocess.run([str(pip_bin), "install", "-e", str(project_dir), "--quiet"], check=True)
        print("Bootstrap completado.")
    except Exception as e:
        print(f"Error en bootstrap: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
