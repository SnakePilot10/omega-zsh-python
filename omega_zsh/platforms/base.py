import subprocess
from abc import ABC, abstractmethod
from typing import Callable, List, Optional


class BasePlatform(ABC):
    COMMAND_TIMEOUT_SECONDS = 600

    @abstractmethod
    def update_repos(self) -> bool:
        """Actualiza los repositorios del sistema."""
        pass

    @abstractmethod
    def install_package(
        self, package_name: str, on_progress: Optional[Callable[[str], None]] = None
    ) -> bool:
        """Instala un paquete usando el gestor de paquetes nativo."""
        pass

    def _run_command(
        self, cmd: List[str], on_progress: Optional[Callable[[str], None]] = None
    ) -> bool:
        """Ejecuta un comando y captura la salida línea por línea."""
        try:
            process = subprocess.Popen(
                cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                text=True,
                bufsize=1,
            )

            if process.stdout:
                for line in process.stdout:
                    if on_progress:
                        on_progress(line.strip())

            try:
                return process.wait(timeout=self.COMMAND_TIMEOUT_SECONDS) == 0
            except subprocess.TimeoutExpired:
                process.kill()
                try:
                    process.wait(timeout=5)
                except subprocess.TimeoutExpired:
                    if on_progress:
                        on_progress("No se pudo confirmar cierre del proceso tras kill().")

                if on_progress:
                    on_progress(
                        f"Timeout ejecutando comando tras {self.COMMAND_TIMEOUT_SECONDS}s: {' '.join(cmd)}"
                    )
                return False
        except Exception as e:
            if on_progress:
                on_progress(f"Error ejecutando comando: {e}")
            return False

    @abstractmethod
    def get_essential_tools(self) -> List[str]:
        """Devuelve la lista de herramientas esenciales para esta plataforma."""
        pass
