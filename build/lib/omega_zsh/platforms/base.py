from abc import ABC, abstractmethod
import subprocess
from typing import List, Callable, Optional

class BasePlatform(ABC):
    @abstractmethod
    def update_repos(self) -> bool:
        """Actualiza los repositorios del sistema."""
        pass

    @abstractmethod
    def install_package(self, package_name: str, on_progress: Optional[Callable[[str], None]] = None) -> bool:
        """Instala un paquete usando el gestor de paquetes nativo."""
        pass

    def _run_command(self, cmd: List[str], on_progress: Optional[Callable[[str], None]] = None) -> bool:
        """Ejecuta un comando y captura la salida línea por línea."""
        try:
            process = subprocess.Popen(
                cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                text=True,
                bufsize=1,
                universal_newlines=True
            )

            if process.stdout:
                for line in process.stdout:
                    if on_progress:
                        on_progress(line.strip())
            
            return process.wait() == 0
        except Exception as e:
            if on_progress:
                on_progress(f"Error ejecutando comando: {e}")
            return False

    @abstractmethod
    def get_essential_tools(self) -> List[str]:
        """Devuelve la lista de herramientas esenciales para esta plataforma."""
        pass
