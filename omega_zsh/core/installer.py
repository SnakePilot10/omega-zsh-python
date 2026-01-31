import subprocess
from pathlib import Path
from typing import List, Callable
from .constants import BIN_PLUGINS, EXTERNAL_URLS


class PluginInstaller:
    """
    Gestiona la instalación de plugins, temas y paquetes del sistema.

    Esta clase actúa como fachada para las operaciones de instalación, delegando
    en la plataforma subyacente (Termux/Debian) para paquetes binarios y usando
    Git para plugins externos.
    """

    def __init__(self, platform, home_dir: Path):
        """
        Inicializa el instalador.

        Args:
            platform: Instancia de la clase de plataforma (TermuxPlatform/DebianPlatform).
            home_dir (Path): Ruta al directorio home del usuario.
        """
        self.platform = platform
        self.home = home_dir
        self.custom_dir = self.home / ".oh-my-zsh/custom"

    def install_all(self, selected_ids: List[str], on_progress: Callable[[str], None]):
        """
        Orquestador principal de instalación de plugins.

        Itera sobre una lista de IDs de plugins y decide la estrategia de instalación
        adecuada (binario del sistema, clonación de git, o activación simple).

        Args:
            selected_ids (List[str]): Lista de identificadores de plugins a instalar.
            on_progress (Callable[[str], None]): Función de callback para reportar progreso.
                                                Debe aceptar un string (mensaje).
        """
        for plugin_id in selected_ids:
            # 1. ¿Es un paquete binario del sistema?
            if plugin_id in BIN_PLUGINS:
                on_progress(f"Instalando paquete binario: {plugin_id}")
                self.platform.install_package(plugin_id, on_progress=on_progress)

            # 2. ¿Es un plugin externo de Git?
            elif plugin_id in EXTERNAL_URLS:
                url = EXTERNAL_URLS[plugin_id]
                target_path = self.custom_dir / "plugins" / plugin_id

                if not target_path.exists():
                    on_progress(f"Clonando plugin Git: {plugin_id}")
                    self._git_clone(url, target_path, on_progress)
                else:
                    on_progress(f"Plugin Git ya existe: {plugin_id}")

            # 3. ¿Es un plugin nativo de OMZ?
            # No requiere instalación física, solo estar en la lista del .zshrc
            else:
                on_progress(f"Activando plugin nativo: {plugin_id}")

    def _git_clone(self, url: str, target: Path, on_progress: Callable[[str], None]):
        """
        Clona un repositorio git de forma silenciosa.

        Args:
            url (str): URL del repositorio Git.
            target (Path): Directorio destino local.
            on_progress (Callable[[str], None]): Callback para logs.
        """
        try:
            target.parent.mkdir(parents=True, exist_ok=True)
            process = subprocess.Popen(
                ["git", "clone", "--depth", "1", url, str(target)],
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                text=True,
            )
            if process.stdout:
                for line in process.stdout:
                    on_progress(f"  [git] {line.strip()}")
            process.wait()
        except Exception as e:
            on_progress(f"Error clonando {url}: {e}")

    def ensure_omz(self, on_progress: Callable[[str], None]):
        """
        Asegura que Oh My Zsh esté instalado. Si no existe, lo clona.

        Args:
            on_progress (Callable[[str], None]): Callback para logs.
        """
        omz_dir = self.home / ".oh-my-zsh"
        if not omz_dir.exists():
            on_progress("Oh My Zsh no encontrado. Clonando...")
            self._git_clone(
                "https://github.com/ohmyzsh/ohmyzsh.git", omz_dir, on_progress
            )
