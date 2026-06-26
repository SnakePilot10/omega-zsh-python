import subprocess
from dataclasses import dataclass, field
from pathlib import Path
from shutil import which
from typing import Callable, List

from .constants import (
    EXTERNAL_URLS,
    binary_commands,
    binary_package_name,
    binary_supported,
    is_binary_tool,
    unknown_plugin_ids,
)


def _binary_available(plugin_id: str) -> bool:
    return any(which(cmd) for cmd in binary_commands(plugin_id))


def _platform_package_manager(platform) -> str:
    pkg_mgr = getattr(platform, "pkg_mgr", "")
    if pkg_mgr == "apt-get":
        return "apt"
    return pkg_mgr or "unknown"


@dataclass
class InstallResult:
    ok: bool = True
    installed: list[str] = field(default_factory=list)
    skipped: list[str] = field(default_factory=list)
    failed: list[str] = field(default_factory=list)
    unsupported: list[str] = field(default_factory=list)
    messages: list[str] = field(default_factory=list)


class PluginInstaller:
    """
    Gestiona la instalación de plugins, temas y paquetes del sistema.

    Esta clase actúa como fachada para las operaciones de instalación, delegando
    en la plataforma subyecente (Termux/Debian) para paquetes binarios y usando
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

    def get_missing_binaries(self, plugins: List[str]) -> List[str]:
        """
        Retorna una lista de binarios del sistema que faltan.

        Args:
            plugins (List[str]): Lista de identificadores de plugins.

        Returns:
            List[str]: Subconjunto de binarios no encontrados en el PATH.
        """
        return [p for p in plugins if is_binary_tool(p) and not _binary_available(p)]

    def install_binary(self, plugin: str) -> bool:
        """
        Instala un paquete binario usando la plataforma.

        Args:
            plugin (str): ID del plugin/paquete.

        Returns:
            bool: True si la instalación fue exitosa.
        """
        if not is_binary_tool(plugin):
            return False
        # Las plataformas deben implementar install_package(id, on_progress)
        # Aquí usamos un lambda vacío para on_progress si no se provee
        package_name = binary_package_name(plugin, _platform_package_manager(self.platform))
        return self.platform.install_package(package_name, on_progress=lambda msg: None)

    def get_missing_zsh_plugins(self, plugins: List[str]) -> List[str]:
        """
        Retorna una lista de plugins Git que no están descargados localmente.

        Args:
            plugins (List[str]): Lista de identificadores de plugins.

        Returns:
            List[str]: Subconjunto de plugins externos no encontrados en custom/plugins.
        """
        missing = []
        for pid in plugins:
            if pid in EXTERNAL_URLS:
                target_path = self.custom_dir / "plugins" / pid
                if not target_path.exists():
                    missing.append(pid)
        return missing

    def download_zsh_plugin(self, plugin_id: str) -> bool:
        """
        Descarga un plugin Git específico.

        Args:
            plugin_id (str): Identificador del plugin.

        Returns:
            bool: True si se clonó correctamente.
        """
        if plugin_id not in EXTERNAL_URLS:
            return False
        url = EXTERNAL_URLS[plugin_id]
        target = self.custom_dir / "plugins" / plugin_id
        return self._git_clone(url, target, lambda msg: None)

    def install_all(self, selected_ids: List[str], on_progress: Callable[[str], None]) -> bool:
        return self.install_all_result(selected_ids, on_progress).ok

    def install_all_result(self, selected_ids: List[str], on_progress: Callable[[str], None]) -> InstallResult:

        """
        Orquestador principal de instalación de plugins.

        Itera sobre una lista de IDs de plugins y decide la estrategia de instalación
        adecuada (binario del sistema, clonación de git, o activación simple).

        Args:
            selected_ids (List[str]): Lista de identificadores de plugins a instalar.
            on_progress (Callable[[str], None]): Función de callback para reportar progreso.
                                                Debe aceptar un string (mensaje).
        """
        result = InstallResult()
        unknown = set(unknown_plugin_ids(selected_ids))
        for plugin_id in selected_ids:
            if plugin_id in unknown:
                message = f"ID desconocido omitido: {plugin_id}"
                on_progress(message)
                result.messages.append(message)
                result.skipped.append(plugin_id)
                continue
            # 1. ¿Es un paquete binario del sistema?
            if is_binary_tool(plugin_id):
                package_manager = _platform_package_manager(self.platform)
                if not binary_supported(plugin_id, package_manager):
                    message = f"Herramienta no soportada en {package_manager}: {plugin_id}"
                    on_progress(message)
                    result.messages.append(message)
                    result.unsupported.append(plugin_id)
                    result.skipped.append(plugin_id)
                    continue
                package_name = binary_package_name(plugin_id, package_manager)
                on_progress(f"Instalando paquete binario: {plugin_id}")
                if not self.platform.install_package(package_name, on_progress=on_progress):
                    on_progress(f"Error instalando paquete binario: {plugin_id}")
                    result.failed.append(plugin_id)
                else:
                    result.installed.append(plugin_id)

            # 2. ¿Es un plugin externo de Git?
            elif plugin_id in EXTERNAL_URLS:
                url = EXTERNAL_URLS[plugin_id]
                target_path = self.custom_dir / "plugins" / plugin_id

                if not target_path.exists():
                    on_progress(f"Clonando plugin Git: {plugin_id}")
                    if not self._git_clone(url, target_path, on_progress):
                        on_progress(f"Error clonando plugin Git: {plugin_id}")
                        result.failed.append(plugin_id)
                    else:
                        result.installed.append(plugin_id)
                else:
                    on_progress(f"Plugin Git ya existe: {plugin_id}")
                    result.skipped.append(plugin_id)

            # 3. ¿Es un plugin nativo de OMZ?
            # No requiere instalación física, solo estar en la lista del .zshrc
            else:
                on_progress(f"Activando plugin nativo: {plugin_id}")
                result.skipped.append(plugin_id)

        if result.failed:
            result.ok = False
            message = "Fallaron: " + ", ".join(result.failed)
            on_progress(message)
            result.messages.append(message)
        return result

    def _git_clone(self, url: str, target: Path, on_progress: Callable[[str], None]) -> bool:
        """
        Clona un repositorio git de forma silenciosa con timeout.

        Args:
            url (str): URL del repositorio Git.
            target (Path): Directorio destino local.
            on_progress (Callable[[str], None]): Callback para logs.
        """
        try:
            target.parent.mkdir(parents=True, exist_ok=True)

            if target.exists():
                on_progress(f"Plugin ya existe: {target.name}")
                return True

            process = subprocess.Popen(
                ["git", "clone", "--depth", "1", url, str(target)],
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                text=True,
            )
            if process.stdout:
                for line in process.stdout:
                    on_progress(f"  [git] {line.strip()}")

            try:
                return_code = process.wait(timeout=300)  # 5 minutos máximo
            except subprocess.TimeoutExpired:
                process.kill()
                on_progress(f"Error: Timeout clonando {url}")
                return False

            if return_code != 0:
                on_progress(f"Error: git clone falló con código {return_code}: {url}")
                return False

            return True
        except Exception as e:
            on_progress(f"Error clonando {url}: {e}")
            return False

    def ensure_omz(self, on_progress: Callable[[str], None]) -> bool:
        """
        Asegura que Oh My Zsh esté instalado. Si no existe, lo clona.

        Args:
            on_progress (Callable[[str], None]): Callback para logs.
        """
        omz_dir = self.home / ".oh-my-zsh"
        if omz_dir.exists():
            return True

        on_progress("Oh My Zsh no encontrado. Clonando...")
        return self._git_clone(
            "https://github.com/ohmyzsh/ohmyzsh.git", omz_dir, on_progress
        )
