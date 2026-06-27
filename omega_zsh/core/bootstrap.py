import logging
import os
import subprocess
import sys
from pathlib import Path

# Importaciones core
from omega_zsh.core.apply import apply_config, link_omega_themes
from omega_zsh.core.context import SystemContext
from omega_zsh.core.installer import PluginInstaller
from omega_zsh.core.manifest import default_manifest_path
from omega_zsh.core.state import StateManager
from omega_zsh.platforms.arch import ArchPlatform
from omega_zsh.platforms.debian import DebianPlatform
from omega_zsh.platforms.termux import TermuxPlatform

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


def install_core_packages(os_id: str):
    packages = CORE_PACKAGES.get(os_id, [])
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


def make_platform(ctx: SystemContext):
    if ctx.is_termux:
        return TermuxPlatform()
    if ctx.package_manager_type in {"apt", "nala"}:
        return DebianPlatform(use_nala=ctx.package_manager_type == "nala")
    if ctx.package_manager_type == "pacman":
        return ArchPlatform()
    raise RuntimeError(f"Package manager no soportado: {ctx.package_manager_type}")


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

    project_dir = Path(__file__).parent.parent.parent
    os_id = detect_os()

    try:
        install_core_packages(os_id)
        venv_dir = setup_venv(project_dir)

        # Sincronizar dependencias Python
        print("Sincronizando dependencias Python...")
        pip_bin = venv_dir / "bin" / "pip"
        subprocess.run([str(pip_bin), "install", "--upgrade", "pip", "--quiet"], check=True)
        subprocess.run([str(pip_bin), "install", "-e", str(project_dir), "--quiet"], check=True)

        # Orquestación de instalación
        ctx = SystemContext()
        plat = make_platform(ctx)
        inst = PluginInstaller(plat, ctx.home)
        sm = StateManager(ctx.omega_dir)

        state = sm.load()

        # Download plugins
        print("Sincronizando plugins...")

        def progress(msg):
            if not args.unattended:
                print(f"  {msg}")

        if not inst.ensure_omz(progress):
            raise RuntimeError("No se pudo instalar Oh My Zsh")

        install_result = inst.install_all_result(state.selected_plugins, progress)
        if not install_result.ok:
            raise RuntimeError("No se pudieron instalar todos los plugins")

        # Sync themes
        if args.sync_themes:
            print("Sincronizando temas...")
            for warning in link_omega_themes(
                ctx.assets_dir,
                ctx.omz_dir,
                default_manifest_path(ctx.home),
            ):
                print(f"  {warning}")

        # Apply
        if args.apply_config:
            print("Aplicando configuración...")
            result = apply_config(ctx, state)
            if not result.ok:
                raise RuntimeError(result.message)

        print("Bootstrap/Install completado.")
    except Exception as e:
        print(f"Error en bootstrap: {e}", file=sys.stderr)
        logging.exception("Error en bootstrap")
        sys.exit(1)

if __name__ == "__main__":
    main()
